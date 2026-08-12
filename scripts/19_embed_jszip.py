#!/usr/bin/env python3
"""Embed the vendored JSZip browser build into all distributed HTML copies."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "jszip" / "jszip.min.js"
START = "<!-- BEGIN LIPOSCOPE_JSZIP -->"
END = "<!-- END LIPOSCOPE_JSZIP -->"
APP_SCRIPT = "<script>\nconst LIPOSCOPE_VERSION"


def embed_jszip(html: str, source: str) -> str:
    if "</script>" in source.lower():
        raise RuntimeError("Vendored JSZip contains an unsafe closing script tag")
    block = f"{START}\n<script>\n{source.strip()}\n</script>\n{END}"
    if START in html or END in html:
        start = html.find(START)
        end = html.find(END)
        if start < 0 or end < start:
            raise RuntimeError("Incomplete embedded JSZip marker block")
        return html[:start] + block + html[end + len(END):]
    if html.count(APP_SCRIPT) != 1:
        raise RuntimeError("Expected one LipoScope application script marker")
    return html.replace(APP_SCRIPT, block + "\n\n" + APP_SCRIPT, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vendor", type=Path, default=VENDOR)
    ap.add_argument("--template", type=Path, default=ROOT / "templates" / "LipoScope.template.html")
    ap.add_argument("--output", type=Path, default=ROOT / "LipoScope.html")
    ap.add_argument("--release-output", type=Path, default=ROOT / "releases" / "LipoScope_v1.0.0.html")
    args = ap.parse_args()

    source = args.vendor.read_text(encoding="utf-8")
    updated = embed_jszip(args.template.read_text(encoding="utf-8"), source)
    for path in (args.template, args.output, args.release_output):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(updated, encoding="utf-8", newline="\n")
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
