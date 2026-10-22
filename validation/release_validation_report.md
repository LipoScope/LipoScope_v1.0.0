# LipoScope v1.0.0 validation report

Generated: 2026-10-22T14:26:44+00:00

## Application structure

- Six main tabs and panels: **passed**
- CCRF Workspace section order: **passed**
- Duplicate HTML identifiers: **0**

## CCRF Version 1

- exploratory: 682 official CDEs (120 clinician; 562 participant); 739 technical REDCap rows
- supplemental: 618 official CDEs (89 clinician; 529 participant); 650 technical REDCap rows
- supplemental_highly_recommended: 424 official CDEs (89 clinician; 335 participant); 445 technical REDCap rows
- core: 288 official CDEs (86 clinician; 202 participant); 300 technical REDCap rows

The four dictionaries are cumulative. Technical row totals are not presented as unique CDE totals. Completion uses currently applicable required response fields and excludes direct identifiers from local assessment.

## Validation

- Automated tests: **46 passed; 0 failed**
- Browser audit: **passed**
- JSZip 3.10.1 embedded ZIP component: **passed**
- Python syntax errors: **0**
- Static HTML validation: **passed**
- Deterministic schema and HTML-copy check: **passed**

## Analytics retrieval provenance

- Synthetic snapshot regression: **passed** (27 scenarios)
- Optional real PubMed smoke: **passed**
The real-service smoke obtains its expected corpus size from the actual canonical query; its counts are not hardcoded and it does not establish classification accuracy.
PubMed collection spans a retrieval interval. Independently retrieved topic-query counts retain their own timestamps and may overlap.
