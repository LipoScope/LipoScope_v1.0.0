from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_ccrf_pipeline_files_exist():
    expected=['00_capture_official_counts.py','01_download_official_dictionaries.py','02_validate_source_workbooks.py','03_build_ccrf_schema.py','04_compare_schema_to_sources.py','05_generate_synthetic_workbooks.py','06_validate_count_alignment.py','07_validate_calculated_fields.py','08_embed_ccrf_schema.py','run_ccrf_build.py','common.py','README.md']
    for name in expected:
        assert (ROOT/'scripts/ccrf'/name).exists(),name


def test_main_validation_scripts_exist():
    for name in ['18_browser_smoke_test.py','20_generate_validation_reports.py','21_build_distribution_archive.py']:
        assert (ROOT/'scripts'/name).exists(),name
