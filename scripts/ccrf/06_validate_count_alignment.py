#!/usr/bin/env python3
"""Validate that official CCRF CDE counts, REDCap rows and LipoScope labels remain distinct."""
from __future__ import annotations
import json
from pathlib import Path
from common import DATA, VALIDATION, load_official_counts

INPUT_TYPES = {'text','notes','radio','dropdown','checkbox','slider','file'}


def main() -> int:
    schema = json.loads((DATA / 'ccrf_schema.json').read_text(encoding='utf-8'))
    official = load_official_counts()
    report = {
        'source_url': official['source_url'],
        'source_accessed_date': official['accessed_date'],
        'count_definitions': {
            'official_cdes': 'Published CDE count for each cumulative CCRF classification.',
            'dictionary_rows': 'Rows in the corresponding REDCap implementation workbook, including response fields, instructions, calculations, identifiers and other technical rows.',
            'completion_denominator': 'Currently applicable required response fields; identifiers excluded from browser storage are reported separately.',
        },
        'classifications': {},
        'cumulative_dictionary_rows_across_four_workbooks': 0,
        'passed': True,
    }
    for key, expected in official['classifications'].items():
        cls = schema['classifications'][key]
        response_rows = sum(str(field.get('type','')).lower() in INPUT_TYPES for field in cls['fields'])
        required_response_rows = sum(field.get('required') and str(field.get('type','')).lower() in INPUT_TYPES for field in cls['fields'])
        item = {
            'official_cdes': cls['official_cdes'],
            'clinical_cdes': cls['clinical_cdes'],
            'participant_cdes': cls['participant_cdes'],
            'dictionary_rows': cls['dictionaryRows'],
            'response_rows': response_rows,
            'required_response_rows_before_branching': required_response_rows,
            'checks': {
                'official_total_matches_source': cls['official_cdes'] == expected['official_cdes'],
                'clinical_count_matches_source': cls['clinical_cdes'] == expected['clinical_cdes'],
                'participant_count_matches_source': cls['participant_cdes'] == expected['participant_cdes'],
                'clinical_plus_participant_equals_total': cls['clinical_cdes'] + cls['participant_cdes'] == cls['official_cdes'],
                'dictionary_metadata_matches_fields': cls['dictionaryRows'] == len(cls['fields']),
                'response_metadata_matches_fields': cls['responseRows'] == response_rows,
                'required_response_metadata_matches_fields': cls['requiredResponseRows'] == required_response_rows,
            },
        }
        item['passed'] = all(item['checks'].values())
        report['passed'] = report['passed'] and item['passed']
        report['classifications'][key] = item
        report['cumulative_dictionary_rows_across_four_workbooks'] += cls['dictionaryRows']
    report['cumulative_count_note'] = 'The four classifications are cumulative and overlap. The summed dictionary-row count is a technical reconciliation total, not a count of unique CDEs.'
    VALIDATION.mkdir(exist_ok=True)
    (VALIDATION / 'ccrf_count_alignment.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
