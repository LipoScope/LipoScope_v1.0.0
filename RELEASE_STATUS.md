# LipoScope software distribution

This package contains the maintained LipoScope application, embedded Lipedema Foundation CCRF Version 1 source schema, supporting source files, build scripts, and software regression tests. The CCRF data-dictionary definitions are unchanged from the version-pinned v1.0.0 source files.

The application uses the canonical PubMed disease query including lipedema/lipoedema, their NLM entry-term synonyms, and lipohyperplasia dolorosa. Literature-topic and study-type classifications are automated, rule-based navigation aids rather than clinically or independently certified findings.

Full validation of a hosted deployment and reproducible literature sampling requires access to external PubMed services. Source and deterministic software tests do not themselves establish literature-classification accuracy or clinical validity.

For installation and standard test commands, see `README.md`. For source metadata and local-storage handling, see `docs/` and `SECURITY.md`.
