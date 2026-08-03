#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import json
import re
from pathlib import Path
from common import DATA, VALIDATION, parse_snapshot


def norm(value):
    return re.sub(r'\s+', ' ', str(value or '').strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--schema', default=str(DATA / 'ccrf_schema.json'))
    parser.add_argument('--snapshot', default=str(DATA / 'ccrf_source_snapshot.tsv'))
    args = parser.parse_args()
    schema = json.loads(Path(args.schema).read_text(encoding='utf-8'))
    source = parse_snapshot(Path(args.snapshot))
    rows = []
    attributes = ['variable', 'type', 'label', 'choices', 'validation', 'min', 'max', 'identifier', 'branching', 'required', 'alignment', 'questionNumber', 'matrixGroup', 'matrixRanking', 'annotation']
    for key, classification in schema['classifications'].items():
        source_rows = source[key]
        if len(source_rows) != len(classification['fields']):
            raise ValueError(f'{key}: source/schema row-count mismatch')
        for source_field, lipo_field in zip(source_rows, classification['fields']):
            differences = [attribute for attribute in attributes if norm(source_field.get(attribute)) != norm(lipo_field.get(attribute))]
            rows.append({
                'classification': key,
                'source_workbook': classification['filename'],
                'source_sheet': 'Data Dictionary',
                'source_row': source_field.get('sourceRow'),
                'source_variable': source_field.get('variable'),
                'LipoScope_variable': lipo_field.get('variable'),
                'source_field_type': source_field.get('type'),
                'LipoScope_field_type': lipo_field.get('type'),
                'choices_preserved': 'yes' if 'choices' not in differences else 'no',
                'branching_preserved': 'yes' if 'branching' not in differences else 'no',
                'validation_preserved': 'yes' if not {'validation', 'min', 'max'} & set(differences) else 'no',
                'required_preserved': 'yes' if 'required' not in differences else 'no',
                'identifier_preserved': 'yes' if 'identifier' not in differences else 'no',
                'transformation_note': 'Whitespace normalisation only' if not differences else 'Differences: ' + ','.join(differences),
                'status': 'matched' if not differences else 'different',
            })
    out = VALIDATION / 'ccrf_field_reconciliation.tsv'
    with out.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        'measure': 'Cumulative REDCap data-dictionary rows across four overlapping CCRF classifications',
        'rows': len(rows),
        'matched': sum(row['status'] == 'matched' for row in rows),
        'different': sum(row['status'] != 'matched' for row in rows),
        'official_cdes_by_classification': {key: value['official_cdes'] for key, value in schema['classifications'].items()},
        'counting_note': 'Dictionary-row reconciliation is a technical implementation check. The classifications overlap and the row total is not a count of unique CCRF CDEs.',
        'passed': all(row['status'] == 'matched' for row in rows),
    }
    (VALIDATION / 'ccrf_reconciliation_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
