#!/usr/bin/env python3
"""Create an AI-readable Markdown map of a directory tree.

Example:
  python filesystem_map.py /path/to/project --output-dir ./map --max-files-per-folder 80 --max-mb 5
"""
from __future__ import annotations

import argparse
import fnmatch
import os
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Recursively map folders and files to size-limited Markdown parts."
    )
    p.add_argument("root", type=Path, help="Root directory to scan")
    p.add_argument("--output-dir", type=Path, default=Path("filesystem-map"),
                   help="Where Markdown output is written (default: ./filesystem-map)")
    p.add_argument("--max-files-per-folder", type=int, default=100,
                   help="Maximum number of file/symlink names listed per folder; totals are always shown (default: 100)")
    p.add_argument("--max-mb", type=float, default=5,
                   help="Approximate maximum size per Markdown part in MiB (default: 5)")
    p.add_argument("--exclude", action="append", default=[], metavar="PATTERN",
                   help="Exclude entries matching a name/path glob; repeat as needed")
    p.add_argument("--include-hidden", action="store_true",
                   help="Include hidden files and folders (included by default)")
    return p.parse_args()


def sort_key(name: str) -> tuple[str, str]:
    return (name.casefold(), name)


def is_excluded(path: Path, root: Path, patterns: list[str], output_dir: Path) -> bool:
    try:
        if path.resolve() == output_dir.resolve() or output_dir.resolve() in path.resolve().parents:
            return True
    except OSError:
        pass
    rel = path.relative_to(root).as_posix()
    return any(fnmatch.fnmatch(path.name, pat) or fnmatch.fnmatch(rel, pat) for pat in patterns)


def scan(root: Path, output_dir: Path, patterns: list[str], include_hidden: bool):
    """Return nested nodes; symlinks are recorded but never followed."""
    def visit(folder: Path):
        dirs, files, links, errors = [], [], [], []
        try:
            entries = sorted(os.scandir(folder), key=lambda e: sort_key(e.name))
        except OSError as e:
            return {"name": folder.name, "dirs": [], "files": [], "links": [],
                    "errors": [f"Could not read directory: {e}"]}
        for entry in entries:
            path = Path(entry.path)
            if not include_hidden and entry.name.startswith("."):
                continue
            if is_excluded(path, root, patterns, output_dir):
                continue
            try:
                if entry.is_symlink():
                    try:
                        target = os.readlink(path)
                    except OSError:
                        target = "ismeretlen cél"
                    links.append({"name": entry.name, "target": target})
                elif entry.is_dir(follow_symlinks=False):
                    dirs.append(visit(path))
                else:
                    files.append(entry.name)
            except OSError as e:
                errors.append(f"{entry.name} (metadata unavailable: {e})")
        return {"name": folder.name or str(folder), "dirs": dirs, "files": files,
                "links": links, "errors": errors}
    return visit(root)


def escape_name(name: str) -> str:
    # Inline code keeps spaces and Markdown punctuation unambiguous.
    return "`" + name.replace("`", "\\`") + "`"


def render_tree(node, threshold: int) -> list[str]:
    lines = [f"- 📁 {escape_name(node['name'])}/"]
    def render_children(n, depth):
        indent = "  " * depth
        dirs, files, links, errors = n["dirs"], n["files"], n["links"], n["errors"]
        entries = sorted(
            [(name, "file", name) for name in files]
            + [(link["name"], "link", link["target"]) for link in links],
            key=lambda item: sort_key(item[0]),
        )
        for name, kind, target in entries[:threshold]:
            if kind == "file":
                lines.append(f"{indent}- 📄 {escape_name(name)}")
            else:
                lines.append(f"{indent}- 🔗 {escape_name(name)} --> {escape_name(target)}")
        if len(entries) > threshold:
            lines.append(
                f"{indent}- … A felsorolás a {threshold}. bejegyzésnél rövidítve; "
                f"összesen {len(files)} fájl és {len(links)} symlink ebben a mappában."
            )
        else:
            lines.append(f"{indent}- Összesen {len(files)} fájl és {len(links)} symlink ebben a mappában.")
        for msg in errors:
            lines.append(f"{indent}- ⚠️ {escape_name(msg)}")
        for child in dirs:
            lines.append(f"{indent}- 📁 {escape_name(child['name'])}/")
            render_children(child, depth + 1)
    render_children(node, 1)
    return lines


def split_lines(lines: Iterable[str], header: str, byte_limit: int) -> list[list[str]]:
    parts, current = [], []
    used = len((header + "\n\n").encode("utf-8"))
    for line in lines:
        size = len((line + "\n").encode("utf-8"))
        if current and used + size > byte_limit:
            parts.append(current)
            current = []
            used = len((header + "\n\n").encode("utf-8"))
        current.append(line)
        used += size
    if current or not parts:
        parts.append(current)
    return parts


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Hiba: a megadott gyökérkönyvtár nem érhető el: {root}")
    if args.max_files_per_folder < 0:
        raise SystemExit("Hiba: --max-files-per-folder nem lehet negatív.")
    if args.max_mb <= 0:
        raise SystemExit("Hiba: --max-mb értékének nullánál nagyobbnak kell lennie.")

    tree = scan(root, output_dir, args.exclude, args.include_hidden)
    lines = render_tree(tree, args.max_files_per_folder)
    limit = int(args.max_mb * 1024 * 1024)
    # Reserve space for the part label and metadata.
    header_base = ("# Fájlrendszer-térkép\n\n"
                   f"- Gyökér: `{root}`\n"
                   f"- Fájlnév-listázási küszöb/mappa: {args.max_files_per_folder}\n"
                   f"- Darabolási célméret: {args.max_mb:g} MiB\n")
    provisional = split_lines(lines, header_base, limit)
    output_dir.mkdir(parents=True, exist_ok=True)
    # Remove only prior files created by this script's naming scheme.
    for old in output_dir.glob("filesystem-map-*.md"):
        old.unlink()
    total = len(provisional)
    for index, part in enumerate(provisional, 1):
        header = header_base + f"- Rész: {index}/{total}\n\n> A fa folytatódhat a következő részben.\n"
        # Header grows with part count; split budget was reserved conservatively.
        content = header + "\n".join(part) + "\n"
        path = output_dir / f"filesystem-map-{index:03d}.md"
        path.write_text(content, encoding="utf-8")
    print(f"Elkészült: {total} Markdown fájl itt: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
