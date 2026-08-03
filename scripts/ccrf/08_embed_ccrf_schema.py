#!/usr/bin/env python3
"""Embed the generated CCRF schema into all distributed LipoScope HTML copies."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from common import DATA

ROOT=Path(__file__).resolve().parents[2]
START='/* BEGIN LIPOSCOPE_CCRF_SCHEMA */'
END='/* END LIPOSCOPE_CCRF_SCHEMA */'


def replace_schema(html:str,schema:dict)->str:
    compact=json.dumps(schema,ensure_ascii=False,separators=(',',':'))
    block=f'{START}\nvar CCRF_SCHEMA={compact};\n{END}'
    pattern=re.escape(START)+r'.*?'+re.escape(END)
    updated,count=re.subn(pattern,lambda _m: block,html,flags=re.S)
    if count!=1:raise RuntimeError(f'Expected one CCRF schema block; found {count}')
    return updated


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--schema',default=str(DATA/'ccrf_schema.json'))
    ap.add_argument('--template',default=str(ROOT/'templates/LipoScope.template.html'))
    ap.add_argument('--output',default=str(ROOT/'LipoScope.html'))
    ap.add_argument('--release-output',default=str(ROOT/'releases/LipoScope_v1.0.0.html'))
    args=ap.parse_args()
    schema=json.loads(Path(args.schema).read_text(encoding='utf-8'))
    template_path=Path(args.template)
    updated=replace_schema(template_path.read_text(encoding='utf-8'),schema)
    # Keep template and both distributed copies identical.
    for path in [template_path,Path(args.output),Path(args.release_output)]:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(updated,encoding='utf-8')
        print(f'Wrote {path}')
    return 0
if __name__=='__main__':raise SystemExit(main())
