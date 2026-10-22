# LipoScope v1.0.0

LipoScope is a browser-local research workbench for lipoedema/lipedema literature discovery, PubMed monitoring, analytics and standardised research data collection using the Lipedema Foundation Common Case Report Form (CCRF) Version 1.

**Canonical repository:** https://github.com/LipoScope/LipoScope_v1.0.0

**Launch LipoScope:** https://liposcope.github.io/LipoScope_v1.0.0/

**Maintained build:** the application footer reads **Updated 22 October 2026**. The package retains the v1.0.0 version, directory and release filenames, but its contents include maintenance changes since the historical v1.0.0 release. Record the Git commit SHA (`git rev-parse HEAD`) when identifying the version used for validation or research.

## Application tabs

- **Start Here** — orientation, guided walkthrough and workflow overview.
- **Browse Papers** — filter, review and curate the public literature collection and user-added records.
- **Live Search** — search PubMed or Google Scholar and add selected PubMed records to the local Browse workspace.
- **Analytics** — compare the wider PubMed literature landscape with the currently visible Browse collection.
- **CCRF Workspace** — select an official CCRF classification, complete applicable fields, review required-field gaps, inspect the data dictionary and export research datasets.
- **About** — software information, privacy, citation, licensing and local workspace controls.

## Maintenance changes included

- Expanded the shared PubMed disease query and added checks that incomplete PMID retrieval is reported instead of presented as complete.
- Added PubMed book-record handling, publication-identity checks for alternative abstract sources, and abstract-source information in paper details.
- Improved New Paper Alerts handling so failed retrievals do not advance the last successful check time.
- Added source-defined CCRF matrix instructions, masked inactive responses in analysis exports, and preserved the version-pinned CCRF Version 1 field definitions.
- Renamed the unresolved research-topic bucket to **Unresolved category** throughout the literature workspace, including classification output, with migration of existing saved records, shared records and cached Analytics counts. The categorisation criteria and ten research topics are unchanged.

Literature-topic and study-type classifications are automated, rule-based navigation aids. Researchers should review them before using them as research classifications. See [the changelog](docs/CHANGELOG.md) and [release status](RELEASE_STATUS.md) for implementation scope.

## Run LipoScope

Use the [hosted LipoScope application](https://liposcope.github.io/LipoScope_v1.0.0/) or open `LipoScope.html` locally in a current desktop browser. Opening the hosted application and using live PubMed, Google Scholar, metadata and open-access figure services require an internet connection. The standalone HTML includes the application, default paper collection, CCRF schema and ZIP export component.

Browse customisation, notes and saved CCRF records are browser-local. Uploaded figure PDFs can be retained on the same device when local PDF storage is enabled and the browser permits it. Browser storage is specific to the browser profile and application origin; moving between the hosted app and a local HTML file does not transfer the workspace. Clearing browser data can remove saved information. See [security and privacy](SECURITY.md).

## CCRF source implementation

The embedded CCRF schema is generated from frozen row-level snapshots of the four official Version 1 cumulative data dictionaries:

- Core
- Supplemental Highly Recommended
- Supplemental
- Exploratory

The package records the official source URLs, SHA-256 checksums, official CDE counts and every REDCap dictionary row. The schema generator preserves source variable names, form names, section headings, field types, labels, coded choices, notes, validation settings, required-field flags, branching expressions, matrix metadata and annotations.

Direct identifiers are excluded from browser-local storage and exports. Conditional questions use the official branching expressions. An inactive response can remain in local record history and is flagged for review, but its value is masked in analysis-oriented exports. Calculated fields are not inferred when the official source dictionary does not provide an executable calculation expression.

## Build and validation

Use Python 3.12 or 3.13 in a dedicated environment; the repository pins Python 3.13.5 in `.python-version` and CI uses Python 3.13. Run the following from the package root. UTF-8 mode avoids Windows text-decoding errors when validation scripts read the application and source files.

```bash
python -X utf8 -m pip install -r requirements.lock
python -X utf8 -m playwright install chromium
python -X utf8 scripts/19_embed_jszip.py
python -X utf8 -m pytest -q
python -X utf8 scripts/18_browser_smoke_test.py --html LipoScope.html
python -X utf8 scripts/22_browser_pubmed_regression.py --html LipoScope.html --out validation/pubmed_browser_regression.json
python -X utf8 scripts/23_browser_literature_regression.py --html LipoScope.html --out validation/literature_browser_regression.json
python -X utf8 scripts/24_browser_topic_category_regression.py --html LipoScope.html --out validation/topic_category_browser_regression.json
```

The committed test summary records **46 passed, 0 failed** for the maintained application. The browser smoke test covers all six tabs, CCRF behaviour and the seven-file research-package ZIP export. The two PubMed browser regressions use synthetic responses; they do not verify current external-service availability or establish literature-classification accuracy.

The topic-category browser regression checks the five non-CCRF tabs, classifier output, legacy storage and shared-record migration, Browse filtering, Live Search imports and Auto-Discovery wording using synthetic records. CI runs this check alongside the main tests and browser smoke test.

`pytest` reports the current test result but does not update `validation/automated_test_summary.json`. Before regenerating aggregate validation reports, update that file to reflect the completed test run, including its command, date, passed and failed counts. Then run:

```bash
python -X utf8 scripts/20_generate_validation_reports.py
```

The report generator reads the saved test summary and browser smoke-test report. Committed reports are evidence of recorded runs; they do not automatically describe later edits or a hosted deployment.

The source-to-schema workflow is documented in `scripts/ccrf/README.md`. The implementation scope and known browser-local constraints are documented in `docs/CCRF_IMPLEMENTATION_SCOPE.md`.

## Package structure

- `index.html` — GitHub Pages entry point that opens the application.
- `LipoScope.html` — complete browser application.
- `data/` — CCRF schema, source manifest, official counts and frozen row snapshot.
- `config/` — pinned CCRF source URLs and checksums.
- `scripts/` — ZIP embedding, browser smoke and retrieval regressions, validation reporting and distribution packaging.
- `scripts/ccrf/` — CCRF source capture, validation and schema-generation scripts.
- `vendor/jszip/` — pinned JSZip browser build and upstream licence used for ZIP research-package exports.
- `tests/` — structural, CCRF, retrieval-integrity, export and package tests.
- `validation/` — generated source reconciliation and validation reports.
- `templates/` and `releases/` — byte-identical HTML copies used by deterministic build checks.
- `docs/` — changelog, data definitions and CCRF behaviour; `ARCHITECTURE.md` describes the application architecture.
- `MANIFEST.sha256` — SHA-256 checksums for the distributed package files, excluding the manifest itself.

## Citation

Citation metadata are supplied in `CITATION.cff`. The exact software release should be identified using its repository commit or archived release identifier.

## Licence

Software code is released under the MIT License. Original LipoScope documentation is released under CC BY 4.0. Official CCRF materials, publications and other third-party content retain their original ownership and terms.
