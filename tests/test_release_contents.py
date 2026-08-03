from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_organisation_repository_is_canonical():
    for p in [ROOT/'README.md',ROOT/'CITATION.cff',ROOT/'LipoScope.html']:
        text=p.read_text(encoding='utf-8')
        assert 'https://github.com/LipoScope/LipoScope_v1.0.0' in text
        assert 'github.com/selincildir/LipoScope' not in text


def test_licence_files_and_html_are_consistent():
    assert (ROOT/'LICENSE').exists() and 'MIT License' in (ROOT/'LICENSE').read_text()
    assert 'CC BY 4.0' in (ROOT/'CONTENT_LICENSE.md').read_text()
    html=(ROOT/'LipoScope.html').read_text()
    assert 'MIT License' in html and 'CC BY 4.0' in html and 'CC BY-NC-ND' not in html


def test_release_support_files_exist():
    for name in ['ARCHITECTURE.md','RELEASE_STATUS.md','NOTICE.md','CONTRIBUTING.md','Dockerfile','.github/workflows/ci.yml','requirements.lock','docs/CCRF_WORKSPACE_GUIDE.md','docs/CCRF_IMPLEMENTATION_SCOPE.md']:
        assert (ROOT/name).exists(),name


def test_no_embedded_git_history_or_release_instructions():
    assert not (ROOT/'.git').exists()
    assert not any(ROOT.glob('*.bundle'))
    assert not any(ROOT.glob('*commit*.txt'))
