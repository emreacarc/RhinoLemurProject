# Rhino Lemur

A collection of production-tested Python scripts for Rhino 3D — block management, volume & weight reporting, hole/slot generation, and general workflow automation.

Built for real fabrication/engineering workflows, not toy examples.

## Requirements

- Rhino 6, 7, or 8
- Scripts are written for Rhino's **legacy IronPython (Python 2) engine** (`rhinoscriptsyntax`). They run fine through the classic `RunPythonScript` command on Rhino 6/7, and through the legacy Python 2 engine on Rhino 8. They are **not** written for Rhino 8's newer CPython 3 scripting engine and will need porting (mainly: drop the `unicode()` calls) to run there.
- `BlockNameWriter.py` additionally uses `Eto.Forms` for its settings dialog — included with Rhino by default, no extra install needed.

## Folder Structure

```
RhinoLemur/
├── block-management/
│   ├── BlockNameWriter.py       Labels block instances with their block name
│   ├── BlockVolumeCalc.py       Volume/weight report + CSV export (BOM)
│   ├── DuplicateBlock.py        Converts one instance into a unique block
│   ├── DuplicateBlockBatch.py   Same, but for many instances at once
│   └── SelectSameBlocks.py      Selects all blocks matching the current selection
├── system-tools/
│   └── CreateBackup.py          One-click timestamped file backup
├── fabrication-geometry/
│   ├── CreateBoltSlot.py        Bolt-sized slot hole on a surface
│   ├── Slot.py                  Evenly spaced slot holes along an edge
│   └── Xline.py                 Infinite construction lines (H/V/2-point)
└── selection-tools/
    └── SelectObjectsSameColor.py   Selects everything matching a color
```

## Installation / Usage

Each file is a standalone script — there's no plugin to install.

1. Download or clone this repo.
2. In Rhino, run the `RunPythonScript` command (or drag the `.py` file straight into an open Rhino viewport).
3. Point it at the script you want to run.

If you use a particular tool often, it's worth aliasing it to a Rhino command or toolbar button:

```
! _-RunPythonScript "C:\path\to\RhinoLemur\block-management\BlockNameWriter.py"
```

## Notes

- `BlockVolumeCalc.py` accounts for each block instance's own scale/rotation when computing volume — two instances of the same block placed at different scales will report correctly, not just multiplied by count.
- `BlockNameWriter.py` remembers your last-used text height, font, and placement setting between runs (via `sc.sticky`), and won't stack duplicate labels if you re-run it on the same blocks.
- `CreateBackup.py` defaults to `I:\RhinoBackups` — change `default_dir` near the top of the script if that path doesn't apply to your setup.

## License

MIT — see [LICENSE](LICENSE). Use it, modify it, ship it in your own tools; just keep the copyright notice intact.

## Contributing

This is currently a personal tool library. Issues and pull requests are welcome if you find a bug or want to add a script that fits the same spirit: focused, single-purpose, no unnecessary dependencies.
