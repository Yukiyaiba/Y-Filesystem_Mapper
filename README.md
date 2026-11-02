# Filesystem Map Generator

`filesystem_map.py` recursively scans folders and files starting from a directory you specify, then writes the structure to Markdown files in a format that is easy for AI tools to understand. It does not open or read file contents.

## Requirements

- Python 3
- No external Python packages required

## Usage

Run the command in a terminal. You can use the full path to the script instead of `filesystem_map.py`.

```bash
python filesystem_map.py "/path/to/the/directory/to/scan" \
  --output-dir "/path/to/output" \
  --max-files-per-folder 100 \
  --max-mb 5
```

Example for Windows PowerShell:

```powershell
python .\filesystem_map.py "C:\Users\Yuki\Documents\Project" `
  --output-dir "C:\Users\Yuki\Documents\Project-map" `
  --max-files-per-folder 100 `
  --max-mb 5
```

The root directory is required. All other options are optional; their default values are used when omitted.

## Options

| Option | Default | Description |
|---|---:|---|
| `root` | required | The directory where scanning starts. |
| `--output-dir` | `./filesystem-map` | Where the Markdown files are written. Relative paths are resolved from the terminal's current working directory. |
| `--max-files-per-folder` | `100` | Lists up to this many file and symlink names per folder. The folder's total file and symlink counts are still shown after a shortened list. |
| `--max-mb` | `5` | Target size for each output part in MiB (1 MiB = 1,048,576 bytes). |
| `--exclude PATTERN` | none | An exclusion pattern. Can be specified multiple times; entries matching by name or by path relative to the root are skipped. |
| `--include-hidden` | off | Include hidden files and folders whose names start with a dot. These are skipped by default. |

File and symlink names are listed in case-insensitive alphabetical order. For example, if the limit is `5` and a folder contains 22 files and 3 symlinks, the first five file/symlink names and symlink targets are listed, followed by a summary such as: `22 files and 3 symlinks in this folder in total.` The limit applies to files and symlinks together, not to subfolders.

Subfolder names are always included, and the script scans every subfolder even when the file list in its parent folder is shortened.

## Output

The script creates one or more files named like these:

```text
filesystem-map-001.md
filesystem-map-002.md
...
```

Each part includes the scanned root path, the configured limit and size, and the part number. Large structures are split across multiple files. Splitting aims for the specified MiB size; a single very long line may cause a part to exceed the target size.

If the output directory is inside the scanned root, the script skips it during scanning so it does not include its own previous map files. Symlinks are listed with their targets but are not followed. File contents are not read.

Before each run, the script deletes only `filesystem-map-*.md` files in the output directory. It does not touch other files.

## Examples

Create 10 MiB parts and list up to 20 file/symlink names per folder:

```bash
python filesystem_map.py "./project" --output-dir "./project-map" \
  --max-files-per-folder 20 --max-mb 10
```

Exclude folders named `node_modules`:

```bash
python filesystem_map.py "./project" --exclude "node_modules" \
  --output-dir "./project-map"
```

Exclude entries matching `*.log`:

```bash
python filesystem_map.py "./project" --exclude "*.log"
```

## Errors and limitations

- The specified root must be an existing directory.
- If the script cannot access a directory during scanning, it adds a warning for that directory to the map.
- Symlink targets are recorded as text, but the target file or directory is not scanned.
- `--max-files-per-folder` controls how many file/symlink names are shown; the summary reports the total counts in that folder.
