# Package data dictionary

## `data/ccrf_official_counts.json`

Frozen official CDE totals and clinician/participant splits for the four CCRF Version 1 classifications.

## `data/ccrf_source_manifest.json`

Official source page, workbook filenames, download URLs, SHA-256 checksums, row counts and counting notes.

## `data/ccrf_source_snapshot.tsv`

One normalised row for every REDCap data-dictionary row across the four cumulative official workbooks. Repeated fields across cumulative classifications remain separate source rows.

## `data/ccrf_schema.json`

Browser schema generated from the source snapshot. Each classification contains source metadata, forms, sections, counts and complete field definitions.

## `validation/ccrf_field_reconciliation.tsv`

Row-level comparison between the generated schema and frozen source snapshot.

## `validation/ccrf_count_alignment.json`

Comparison of official CDE counts, clinician/participant splits, technical dictionary rows and response-field counts.

## `validation/ccrf_calculated_fields.json`

Audit of fields marked as calculated and whether an official calculation expression is supplied by the frozen dictionaries.
