#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import requests
from common import BUILD, load_sources, sha256_file

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output-dir',default=str(BUILD/'ccrf_sources'))
    ap.add_argument('--accept-third-party-terms',action='store_true')
    ap.add_argument('--allow-updated-source',action='store_true')
    args=ap.parse_args()
    if not args.accept_third_party_terms:
        raise SystemExit('Downloading official CCRF files requires --accept-third-party-terms after reviewing https://www.lipedema.org/terms-of-use')
    cfg=load_sources(); out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    for key,s in cfg['sources'].items():
        p=out/s['filename']; r=requests.get(s['url'],timeout=120,allow_redirects=True); r.raise_for_status(); p.write_bytes(r.content)
        digest=sha256_file(p)
        if digest!=s['sha256'] and not args.allow_updated_source:
            p.unlink(missing_ok=True)
            raise SystemExit(f'{key}: official file hash changed ({digest}); review the new source before updating config/ccrf_sources.yaml')
        print(f'{key}: {p} sha256={digest}')
    return 0
if __name__=='__main__': raise SystemExit(main())
