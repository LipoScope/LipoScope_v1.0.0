#!/usr/bin/env python3
"""Rebuild and validate the CCRF schema and distributed LipoScope HTML."""
from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
STEPS=[
 ['03_build_ccrf_schema.py','--output',str(ROOT/'data/ccrf_schema.json')],
 ['04_compare_schema_to_sources.py'],
 ['06_validate_count_alignment.py'],
 ['07_validate_calculated_fields.py'],
 ['08_embed_ccrf_schema.py'],
]

def main()->int:
    base=Path(__file__).resolve().parent
    for step in STEPS:
        cmd=[sys.executable,str(base/step[0]),*step[1:]]
        print('+',' '.join(cmd),flush=True)
        subprocess.run(cmd,check=True,cwd=ROOT)
    return 0
if __name__=='__main__':raise SystemExit(main())
