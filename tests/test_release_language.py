from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_user_facing_workspace_language(html_text):
    for text in ['CCRF Research Workspace','Standardized Cohort Builder','Cohort Design Gap Radar','CCRF Data Dictionary and Dataset Export','LipoScope does not diagnose a patient']:
        assert text in html_text


def test_package_scope_is_ccrf_and_literature():
    permitted_top_level={'data','scripts','tests','validation','templates','releases','docs','.github','build'}
    assert (ROOT/'scripts/ccrf').is_dir()
    assert (ROOT/'data/ccrf_schema.json').exists()
    assert not any(p.is_dir() for p in (ROOT/'scripts').iterdir() if p.name not in {'ccrf','__pycache__'})


def test_no_obsolete_workspace_labels_or_assets(html_text):
    prohibited=['Molecular Evidence Atlas','Molecular Signal Atlas','Molecular Evidence Map','Molecular Signal Map','Research Opportunity Map','Gene and Literature Evidence Checker']
    for text in prohibited:
        assert text not in html_text
    for root_name in ['data','scripts','tests','validation','docs']:
        for path in (ROOT/root_name).rglob('*'):
            if path.is_file():
                lowered=path.name.lower()
                assert 'molecular_signal_atlas' not in lowered
                assert 'molecular_evidence_atlas' not in lowered


def test_lay_user_guidance_and_default_library_management(html_text):
    assert 'hide all 200 default papers' in html_text.lower()
    assert 'official CCRF Version 1 data-collection levels' in html_text
    assert 'A Simple, Browser-Local Workspace for Lipoedema Research' in html_text
    assert 'Visual Guides to Lipoedema' not in html_text
    assert 'Lipoedema Biology Explainer Video' not in html_text
    assert 'Atlas stays live' not in html_text
