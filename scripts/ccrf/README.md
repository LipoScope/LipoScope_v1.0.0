# CCRF source workflow

The CCRF scripts validate and reconstruct the browser schema from the frozen official Version 1 source representation.

| Script | Purpose |
|---|---|
| `00_capture_official_counts.py` | Record the Foundation's published CDE totals and clinician/participant split. |
| `01_download_official_dictionaries.py` | Retrieve official REDCap dictionaries and verify configured checksums. |
| `02_validate_source_workbooks.py` | Validate workbook headers, rows and source identity. |
| `03_build_ccrf_schema.py` | Generate the browser schema without changing official field definitions. |
| `04_compare_schema_to_sources.py` | Produce field-level source-to-schema reconciliation. |
| `05_generate_synthetic_workbooks.py` | Generate source-equivalent fixtures used by offline automated tests. |
| `06_validate_count_alignment.py` | Keep official CDE counts distinct from technical dictionary-row counts. |
| `07_validate_calculated_fields.py` | Confirm that no calculation is inferred where the official expression is absent. |
| `08_embed_ccrf_schema.py` | Embed the generated schema into the template, active HTML and versioned release copy. |
| `run_ccrf_build.py` | Run schema generation, reconciliation, count checks, calculated-field audit and HTML embedding in sequence. |

Conditional fields use the official branching expression. Direct identifiers remain unpopulated, and inactive conditional responses remain available in local record history for audit, but are masked in analysis-oriented exports and flagged in the data-quality report.

Run the complete offline build with:

```bash
python scripts/ccrf/run_ccrf_build.py
```
