# Analytics count provenance — 23 October 2026

- Bound completed query totals and processed-record denominators to the same validated PMID inventory. Rejected duplicate/invalid PMIDs, missing ESummary or EFetch citations, and wrong-PMID processed sets before replacing the corpus; absent abstract, year, journal and resolved topic information do not exclude valid records.
- Separated corpus persistence from successful-retrieval timestamp updates. Classification/summary enrichment preserves the original timestamp and refresh-error flag. Concurrent refresh callers await the same retrieval.
- Added query and corpus timestamps, processed-record counts, status, differences and a refresh control to the existing Analytics summary. Cached and mixed snapshots are explicit; a difference between separate retrievals is not automatically evidence of missing publications.
- Retained independent topic-query counts and timestamps, record-level classifications and local Browse counts as distinct quantities. Record-level recent/oldest metrics now use the processed corpus rather than additional fresh queries.
- Verified mismatch mechanisms in the previous code: a fresh ESearch count combined with a TTL-cached corpus, unconditional Live labelling, and enrichment saves advancing the corpus timestamp. These findings do not retrospectively establish the cause of any particular historical count difference.
- Added synthetic count/provenance regression scenarios and an optional real-PubMed smoke test; retained the existing v1.0.0 layout, disease query, classifiers, Live Search and CCRF source bytes.

# Complete Live Literature Search — 22 October 2026

- Removed the 20-result total limit from Live Literature Search. All matching PubMed identifiers are retrieved and validated; citations are displayed in batches of 50 using Load more results.
- Partitioned large searches into disjoint PMID ranges so the PubMed per-query identifier limit does not silently truncate the result list.
- Preserved displayed records during failed batches and added retry controls, protection against obsolete search responses, and duplicate-safe imports from later batches.
- Updated the relevant interface guidance and README. Added a browser regression for retrieval, batching, imports, failures and all five non-CCRF tabs. CCRF Workspace and v1.0.0 are unchanged.

# Topic-category terminology — 22 October 2026

- Renamed the literature topic bucket from "Unsupported records" to "Unresolved category" across Browse Papers, Analytics, About and Auto-Discovery.
- Renamed classifier and Analytics fields to use unresolved terminology, preserving existing categorisation criteria, reason codes, counts and retrieval timestamps.
- Added compatibility for legacy saved records, cached Analytics and shared Browse records, including the misspelled legacy label "Unspported records".
- Added a browser regression covering all five non-CCRF tabs and the affected import, filter and storage paths. CCRF Workspace and v1.0.0 are unchanged.

# Maintained build — 21 October 2026

- Extended canonical PubMed terminology to recognised lipedema synonyms and lipohyperplasia dolorosa.
- Strengthened PubMed PMID completeness, metadata retrieval, book-record parsing and attribution safeguards.
- Improved handling of failed New Paper Alerts requests and safe display of returned citation text.
- Displayed source-defined CCRF matrix instructions and masked inactive response values in analysis exports.
- Preserved the version-pinned official CCRF Version 1 source definitions.
- Added reproducible source and browser regression checks.

# Changelog

## v1.0.0 maintenance correction — 13 August 2026

- Embedded the pinned JSZip 3.10.1 browser build so complete CCRF research-package ZIP exports work in the standalone application and on GitHub Pages.
- Added an end-to-end browser check that creates and reopens the ZIP and verifies all seven expected research-package files.

## v1.0.0 — 3 August 2026

- Released the browser-local LipoScope literature workbench.
- Added Browse Papers, Live Search and PubMed-wide Analytics.
- Added the CCRF Research Workspace using the four official Version 1 cumulative classifications.
- Added source-conformant branching, validation, completion review, Gap Radar and research exports.
- Added frozen CCRF source records, source-to-schema generation and automated browser validation.
