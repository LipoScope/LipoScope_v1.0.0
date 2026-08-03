# LipoScope architecture

## Static browser application

LipoScope is distributed as one HTML application containing its interface, styles, JavaScript logic, public Browse collection and CCRF schema. No application backend or user account is required.

## Literature workspace

The literature layer contains a public Browse collection and browser-local additions. PubMed-wide Analytics and Live Search retrieve current public metadata when network access is available. User curation, notes and locally uploaded PDF previews remain local to the browser unless explicitly exported or shared through a Browse-only link.

## CCRF Workspace

The CCRF Workspace reads one embedded Version 1 schema generated from frozen official REDCap data-dictionary rows. The same schema drives:

- classification selection;
- form and section navigation;
- input rendering;
- coded choices;
- validation;
- branching;
- completion assessment;
- Gap Radar summaries;
- data-dictionary inspection;
- coded, labelled, long-format and quality-control exports.

The four classifications are cumulative. Official CDE counts are reported separately from technical REDCap dictionary-row counts and from the number of currently applicable required response fields.

## Browser-local record model

CCRF records use a local study record identifier, classification, schema version, source checksum, timestamps and response object. Direct identifiers are excluded. Conditional responses are retained if an earlier answer makes their branch inactive, but they are flagged and excluded from active completion calculations.

## Deterministic build boundary

`data/ccrf_source_snapshot.tsv` is the frozen row-level source input. `scripts/ccrf/03_build_ccrf_schema.py` reconstructs `data/ccrf_schema.json`. The compact schema is embedded into `LipoScope.html`, `templates/LipoScope.template.html` and `releases/LipoScope_v1.0.0.html`. Validation requires these three HTML copies and the rebuilt schema to agree.
