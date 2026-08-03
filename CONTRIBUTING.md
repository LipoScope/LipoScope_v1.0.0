# Contributing

Changes should preserve the browser-local privacy model, source-conformant CCRF definitions and deterministic validation workflow.

Before proposing a change:

1. update the relevant source, documentation and tests;
2. run `python -m pytest -q`;
3. run `python scripts/18_browser_smoke_test.py --html LipoScope.html`;
4. run `python scripts/20_generate_validation_reports.py`;
5. confirm that generated reports contain no failures.

Do not edit official CCRF field definitions directly in the HTML. Update the frozen source snapshot or official source workflow, rebuild the schema and then regenerate all HTML copies.
