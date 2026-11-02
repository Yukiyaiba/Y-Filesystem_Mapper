# Fájlrendszer-térkép készítő

A `filesystem_map.py` egy megadott könyvtárból kiindulva rekurzívan feltérképezi a mappákat és fájlokat, majd a struktúrát AI számára is áttekinthető Markdown-fájlokba írja. Nem nyitja meg és nem olvassa be a fájlok tartalmát.

## Követelmények

- Python 3
- Külső Python-csomag nem szükséges

## Használat

A parancsot a terminálban futtasd. A `filesystem_map.py` helyett megadhatod a szkript teljes elérési útját is.

```bash
python filesystem_map.py "/elérési/út/a/beolvasandó/mappához" \
  --output-dir "/elérési/út/a/kimenethez" \
  --max-files-per-folder 100 \
  --max-mb 5
```

Windows PowerShellben például:

```powershell
python .\filesystem_map.py "C:\Users\Yuki\Documents\Projekt" `
  --output-dir "C:\Users\Yuki\Documents\Projekt-terkep" `
  --max-files-per-folder 100 `
  --max-mb 5
```

A gyökérkönyvtár kötelező. A többi beállítás elhagyható; ilyenkor az alapértékek érvényesek.

## Beállítások

| Beállítás | Alapérték | Jelentés |
|---|---:|---|
| `root` | kötelező | A bejárás kiinduló mappája. |
| `--output-dir` | `./filesystem-map` | Ide készülnek a Markdown-fájlok. Relatív útvonal esetén a terminál aktuális könyvtárához képest értendő. |
| `--max-files-per-folder` | `100` | Mappánként legfeljebb ennyi fájl- és symlinknevet sorol fel. A mappák teljes fájl- és symlinkdarabszámát a rövidített lista után is kiírja. |
| `--max-mb` | `5` | A kimeneti részek célmérete MiB-ban (1 MiB = 1 048 576 bájt). |
| `--exclude PATTERN` | nincs | Kizárási minta. Többször is megadható; a fájlnévre és a gyökérhez viszonyított relatív útvonalra illeszkedő bejegyzéseket kihagyja. |
| `--include-hidden` | kikapcsolva | A rejtett, ponttal kezdődő fájlok és mappák felvétele. Alapértelmezés szerint ezek kimaradnak. |

A fájlnevek és symlinkek kis- és nagybetűtől független ABC-sorrendben jelennek meg. Ha például a küszöb `5`, a mappában pedig 22 fájl és 3 symlink van, akkor az első öt fájl/symlink neve és célja szerepel, majd egy összesítés: `Összesen 22 fájl és 3 symlink ebben a mappában.` A küszöb a fájlokra és symlinkekre együtt vonatkozik, az almappákra nem.

Az almappák nevei mindig megjelennek, és a szkript minden almappát bejár akkor is, ha a szülőmappában a fájlnevek listája rövidült.

## Kimenet

A szkript egy vagy több ilyen nevű fájlt készít:

```text
filesystem-map-001.md
filesystem-map-002.md
...
```

Minden rész tartalmazza a beolvasott gyökér elérési útját, a beállított küszöböt és méretet, valamint a rész sorszámát. Nagy struktúráknál a Markdown-tartalom több fájlra oszlik. A darabolás a megadott MiB-értékhez igazodik; egyetlen nagyon hosszú sor miatt egy rész a célméretnél nagyobb lehet.

Ha a kimeneti mappa a beolvasott gyökér alatt van, a szkript a kimeneti mappát kihagyja a bejárásból, így a saját korábbi térképfájljait sem veszi fel. A szimbolikus linkeket feltünteti a céljukkal, de nem követi őket. A fájlok tartalmát nem olvassa.

A szkript csak a kimeneti mappában lévő `filesystem-map-*.md` fájlokat törli új futtatás előtt. Más fájlokhoz nem nyúl.

## Példák

Készítsen 10 MiB-os részeket, és mappánként legfeljebb 20 fájl/symlink nevét sorolja fel:

```bash
python filesystem_map.py "./projekt" --output-dir "./projekt-terkep" \
  --max-files-per-folder 20 --max-mb 10
```

A `node_modules` nevű mappák kizárása:

```bash
python filesystem_map.py "./projekt" --exclude "node_modules" \
  --output-dir "./projekt-terkep"
```

A `*.log` mintára illeszkedő elemek kizárása:

```bash
python filesystem_map.py "./projekt" --exclude "*.log"
```

## Hibák és korlátok

- A megadott gyökérkönyvtárnak létező mappának kell lennie.
- A bejáráshoz szükséges hozzáférési jogosultság hiányában az érintett mappához figyelmeztetést ír a térképbe.
- A symlink célját szövegként jegyzi fel, de a célállományt vagy célmappát nem járja be.
- A `--max-files-per-folder` csak azt szabályozza, hány fájl/symlink neve jelenjen meg; az összesítés a mappa teljes darabszámát mutatja.
