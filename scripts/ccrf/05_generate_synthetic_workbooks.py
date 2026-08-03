#!/usr/bin/env python3
from __future__ import annotations
import csv
from pathlib import Path
from openpyxl import Workbook
from common import BUILD, DATA, load_sources


def main() -> int:
    output = BUILD / 'ccrf_fixture_workbooks'
    output.mkdir(parents=True, exist_ok=True)
    grouped = {}
    with (DATA / 'ccrf_source_snapshot.tsv').open(encoding='utf-8') as handle:
        for row in csv.DictReader(handle, delimiter='\t'):
            grouped.setdefault(row['classification'], []).append(row)
    metadata_columns = {'classification', 'source_filename', 'source_sha256', 'source_row'}
    sources = load_sources()['sources']
    for key, rows in grouped.items():
        headers = [column for column in rows[0] if column not in metadata_columns]
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'REDCap Data Dictionary'
        sheet.append(headers)
        for row in rows:
            values = []
            for column in headers:
                value = row[column]
                if column in {'Text Validation Min', 'Text Validation Max'} and value not in {'', None}:
                    try:
                        number = float(value)
                        value = int(number) if number.is_integer() else number
                    except ValueError:
                        pass
                values.append(value)
            sheet.append(values)
        path = output / sources[key]['filename']
        workbook.save(path)
        print(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
