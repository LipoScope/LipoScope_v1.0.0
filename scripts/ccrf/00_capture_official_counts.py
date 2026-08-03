#!/usr/bin/env python3
"""Capture the Lipedema Foundation's published CCRF CDE counts.

This network-assisted utility is for source refreshes. The exact v1.0.0 rebuild
uses data/ccrf_official_counts.json and does not contact the website.
"""
from __future__ import annotations
import argparse
import json
import re
from datetime import date
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from common import DATA, load_sources

LABELS = {
    'core': 'Core',
    'supplemental_highly_recommended': 'Supplemental Highly Recommended',
    'supplemental': 'Supplemental',
    'exploratory': 'Exploratory (Complete CCRF)',
}


def parse_counts(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    text = '\n'.join(line.strip() for line in soup.get_text('\n').splitlines() if line.strip())
    patterns = {
        'exploratory': r'Exploratory.*?Total CDEs:\s*(\d+).*?(\d+)\s+Clinical Form.*?(\d+)\s+Participant Form',
        'supplemental': r'(?<!Highly Recommended\s)Supplemental\s+\|.*?Total CDEs:\s*(\d+).*?(\d+)\s+Clinical Form.*?(\d+)\s+Participant Form',
        'supplemental_highly_recommended': r'Supplemental\s+Highly Recommended.*?Total CDEs:\s*(\d+).*?(\d+)\s+Clinical Form.*?(\d+)\s+Participant Form',
        'core': r'Core\s+\|.*?Total CDEs:\s*(\d+).*?(\d+)\s+Clinical Form.*?(\d+)\s+Participant Form',
    }
    output = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, flags=re.S | re.I)
        if not match:
            raise ValueError(f'Could not parse official count for {key}')
        total, clinical, participant = map(int, match.groups())
        if clinical + participant != total:
            raise ValueError(f'{key}: clinical + participant does not equal total')
        output[key] = {
            'label': LABELS[key],
            'official_cdes': total,
            'clinical_cdes': clinical,
            'participant_cdes': participant,
        }
    return output


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', default=str(DATA / 'ccrf_official_counts.refreshed.json'))
    ap.add_argument('--allow-count-change', action='store_true')
    args = ap.parse_args()
    cfg = load_sources()
    response = requests.get(cfg['official_page'], timeout=120)
    response.raise_for_status()
    counts = parse_counts(response.text)
    current = json.loads((DATA / 'ccrf_official_counts.json').read_text(encoding='utf-8'))
    for key, item in counts.items():
        for field in ('estimated_minutes_clinical', 'estimated_minutes_participant'):
            item[field] = current['classifications'][key][field]
    refreshed = {
        'source_title': current['source_title'],
        'source_url': cfg['official_page'],
        'accessed_date': date.today().isoformat(),
        'definition': current['definition'],
        'classifications': counts,
    }
    changed = any(
        refreshed['classifications'][key]['official_cdes'] != current['classifications'][key]['official_cdes']
        or refreshed['classifications'][key]['clinical_cdes'] != current['classifications'][key]['clinical_cdes']
        or refreshed['classifications'][key]['participant_cdes'] != current['classifications'][key]['participant_cdes']
        for key in counts
    )
    if changed and not args.allow_count_change:
        raise SystemExit('Official CCRF counts changed. Review the source and rerun with --allow-count-change before updating the frozen snapshot.')
    Path(args.output).write_text(json.dumps(refreshed, indent=2) + '\n', encoding='utf-8')
    print(Path(args.output))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
