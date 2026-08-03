#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from common import DATA, VALIDATION


def main() -> int:
    schema = json.loads((DATA / 'ccrf_schema.json').read_text(encoding='utf-8'))
    classifications = {}
    all_rows = []
    for key, cls in schema['classifications'].items():
        rows = []
        for field in cls['fields']:
            if field.get('type') != 'calc':
                continue
            expression = field.get('choices')
            row = {
                'variable': field['variable'],
                'label': field.get('label'),
                'form': field.get('form'),
                'section': field.get('section'),
                'source_row': field.get('sourceRow'),
                'official_expression': expression,
                'expression_available': bool(expression),
                'liposcope_action': 'execute only after exact official REDCap expression and behaviour are validated' if expression else 'leave unavailable; do not infer or substitute a formula',
            }
            rows.append(row)
            all_rows.append({'classification': key, **row})
        classifications[key] = {
            'calculated_rows': len(rows),
            'official_expression_rows': sum(r['expression_available'] for r in rows),
            'rows': rows,
        }
    report = {
        'ccrf_version': schema['source']['ccrfVersion'],
        'schema_version': schema['schemaVersion'],
        'policy': schema['source']['calculationPolicy'],
        'calculated_rows_across_cumulative_dictionaries': len(all_rows),
        'unique_calculated_variables': sorted({r['variable'] for r in all_rows}),
        'official_expression_rows': sum(r['expression_available'] for r in all_rows),
        'classifications': classifications,
        'passed': all(classifications[key]['official_expression_rows'] == cls.get('calculationExpressionRows') for key, cls in schema['classifications'].items()) and all(not r['expression_available'] for r in all_rows),
    }
    VALIDATION.mkdir(exist_ok=True)
    out = VALIDATION / 'ccrf_calculated_fields.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
