#!/usr/bin/env python3
"""
Build the pyOrigamiBreak plugin zip for deployment.

Usage:
    python scripts/build_plugin.py [--output PATH] [--src DIR]

The plugin zip contains only the files required by the Foldnano plugin
runtime.  It excludes __init__.py and exportoligos.py (CLI-only) and the
heavy CLI dependencies (openpyxl, svgutils, cn2svg, fastprogress).

Source files are taken from the working tree.  The plugin variants of
autobreak.py and origamidesign.py must already reflect the plugin
adaptations (in-memory I/O, flat imports, Pyodide compatibility) before
running this script.
"""

import argparse
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

PLUGIN_FILES = [
    'autobreak.py',
    'origamidesign.py',
    'plugin.py',
    'scaffolds.py',
    'utilities.py',
    'validate.py',
]


def build(output_path: Path, src_dir: Path) -> None:
    missing = [f for f in PLUGIN_FILES if not (src_dir / f).exists()]
    if missing:
        for f in missing:
            print(f'ERROR: missing source file: {src_dir / f}', file=sys.stderr)
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for fname in PLUGIN_FILES:
            shutil.copy2(src_dir / fname, tmp_path / fname)

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for fname in PLUGIN_FILES:
                zf.write(tmp_path / fname, arcname=fname)

    size_kb = output_path.stat().st_size / 1024
    print(f'Plugin zip written to {output_path}  ({size_kb:.1f} KB)')
    print(f'Included files: {", ".join(PLUGIN_FILES)}')


def main():
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=repo_root / 'autobreak' / 'pyOrigamiBreak.zip',
        help='Output zip path (default: autobreak/pyOrigamiBreak.zip)',
    )
    parser.add_argument(
        '--src', '-s',
        type=Path,
        default=repo_root / 'autobreak',
        help='Directory containing plugin source files (default: autobreak/)',
    )
    args = parser.parse_args()
    build(args.output, args.src)


if __name__ == '__main__':
    main()
