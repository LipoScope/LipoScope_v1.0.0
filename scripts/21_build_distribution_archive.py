#!/usr/bin/env python3
from __future__ import annotations
import hashlib, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'LipoScope_v1.0.0_full_release.zip'
ARCHIVE_ROOT=Path('LipoScope-v1.0.0')
EXCLUDE={'.git','.venv','__pycache__','.pytest_cache','build'}

def main():
    files=[p for p in ROOT.rglob('*') if p.is_file() and not any(part in EXCLUDE for part in p.relative_to(ROOT).parts)]
    with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):z.write(p,ARCHIVE_ROOT/p.relative_to(ROOT))
    print(f'{OUT} sha256={hashlib.sha256(OUT.read_bytes()).hexdigest()} files={len(files)}')
    return 0
if __name__=='__main__':raise SystemExit(main())
