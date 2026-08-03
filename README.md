# LipoScope v1.0.0

LipoScope is a browser-local research workbench for lipoedema/lipedema literature discovery, PubMed monitoring, analytics and standardised research data collection using the Lipedema Foundation Common Case Report Form (CCRF) Version 1.

**Canonical repository:** https://github.com/LipoScope/LipoScope_v1.0.0

**Launch LipoScope:** https://liposcope.github.io/LipoScope_v1.0.0/

## Application tabs

- **Start Here** — orientation, visual guides and workflow overview.
- **Browse Papers** — filter, review and curate the public literature collection and user-added records.
- **Live Search** — search PubMed or Google Scholar and add selected PubMed records to the local Browse workspace.
- **Analytics** — compare the wider PubMed literature landscape with the currently visible Browse collection.
- **CCRF Workspace** — select an official CCRF classification, complete applicable fields, review required-field gaps, inspect the data dictionary and export research datasets.
- **About** — software information, privacy, citation, licensing and local workspace controls.

## Run LipoScope

Use the [hosted LipoScope application](https://liposcope.github.io/LipoScope_v1.0.0/) or open `LipoScope.html` locally in a current desktop browser. An internet connection is required only for live PubMed, Google Scholar, metadata and open-access figure services. Browse customisation, notes, locally uploaded PDF previews and CCRF records are stored in the current browser unless exported.

## CCRF source implementation

The embedded CCRF schema is generated from frozen row-level snapshots of the four official Version 1 cumulative data dictionaries:

- Core
- Supplemental Highly Recommended
- Supplemental
- Exploratory

The package records the official source URLs, SHA-256 checksums, official CDE counts and every REDCap dictionary row. The schema generator preserves source variable names, form names, section headings, field types, labels, coded choices, notes, validation settings, required-field flags, branching expressions, matrix metadata and annotations.

Direct identifiers are excluded from browser-local storage and exports. Conditional questions use the official branching expressions. A stored response is retained and flagged if its branch later becomes inactive. Calculated fields are not inferred when the official source dictionary does not provide an executable calculation expression.

## Build and validation

Create the Python environment and run:

```bash
python -m pip install -r requirements.lock
python -m playwright install chromium
python -m pytest -q
python scripts/18_browser_smoke_test.py --html LipoScope.html
python scripts/20_generate_validation_reports.py
```

The source-to-schema workflow is documented in `scripts/ccrf/README.md`. The implementation scope and known browser-local constraints are documented in `docs/CCRF_IMPLEMENTATION_SCOPE.md`.

## Package structure

- `index.html` — GitHub Pages entry point that opens the application.
- `LipoScope.html` — complete browser application.
- `data/` — CCRF schema, source manifest, official counts and frozen row snapshot.
- `scripts/ccrf/` — CCRF source capture, validation and schema-generation scripts.
- `tests/` — structural, CCRF, browser, export and package tests.
- `validation/` — generated source reconciliation and validation reports.
- `templates/` and `releases/` — byte-identical HTML copies used by deterministic build checks.
- `docs/` — architecture, data definitions and CCRF behaviour.

## Citation

Citation metadata are supplied in `CITATION.cff`.

## Licence

Software code is released under the MIT License. Original LipoScope documentation is released under CC BY 4.0. Official CCRF materials, publications and other third-party content retain their original ownership and terms.
