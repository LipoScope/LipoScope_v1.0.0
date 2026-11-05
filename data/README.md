# Data files

The committed data files support the CCRF Version 1 workspace and its validation.

- `ccrf_official_counts.json`
- `ccrf_source_manifest.json`
- `ccrf_source_snapshot.tsv`
- `ccrf_schema.json`

The source snapshot contains technical REDCap rows across four overlapping cumulative classifications; it is not a count of unique CCRF CDEs.

`default_pubmed_snapshot.json` contains dated NCBI publication evidence for the existing 200 default PMIDs. It is embedded in the three distributed HTML copies for offline classification. Source request timestamps and response checksums are retained; they are independent of the application's displayed release date. It contains classification inputs, not per-publication category overrides.

Re-embed the saved snapshot with `python scripts/27_default_pubmed_snapshot.py`. To obtain new evidence, run `python scripts/27_default_pubmed_snapshot.py --fetch --cache-dir .local/pubmed_snapshot_new`, using a new cache directory for each new retrieval. Reusing a cache preserves its original request timestamps. The script verifies returned PMIDs and PMC identifiers, retrieves the unchanged topic-query inventories, throttles NCBI requests, and replaces the snapshot only after the requested PubMed records and query inventories are complete.
