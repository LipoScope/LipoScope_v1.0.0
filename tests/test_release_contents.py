import subprocess, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_organisation_repository_is_canonical():
    for p in [ROOT/'README.md',ROOT/'CITATION.cff',ROOT/'LipoScope.html']:
        text=p.read_text(encoding='utf-8')
        assert 'https://github.com/LipoScope/LipoScope_v1.0.0' in text
        assert 'github.com/selincildir/LipoScope' not in text


def test_licence_files_and_html_are_consistent():
    assert (ROOT/'LICENSE').exists() and 'MIT License' in (ROOT/'LICENSE').read_text(encoding='utf-8')
    assert 'CC BY 4.0' in (ROOT/'CONTENT_LICENSE.md').read_text(encoding='utf-8')
    html=(ROOT/'LipoScope.html').read_text(encoding='utf-8')
    assert 'MIT License' in html and 'CC BY 4.0' in html and 'CC BY-NC-ND' not in html


def test_release_support_files_exist():
    for name in ['ARCHITECTURE.md','RELEASE_STATUS.md','NOTICE.md','CONTRIBUTING.md','Dockerfile','.github/workflows/ci.yml','requirements.lock','docs/CCRF_WORKSPACE_GUIDE.md','docs/CCRF_IMPLEMENTATION_SCOPE.md']:
        assert (ROOT/name).exists(),name


def test_no_embedded_git_history_or_release_instructions(tmp_path):
    archive=tmp_path/'LipoScope_v1.0.0_full_release.zip'
    subprocess.run(
        [sys.executable,str(ROOT/'scripts/21_build_distribution_archive.py'),'--output',str(archive)],
        check=True,
    )
    with zipfile.ZipFile(archive) as z:
        members=[Path(name) for name in z.namelist() if not name.endswith('/')]
    assert Path('LipoScope-v1.0.0/LipoScope.html') in members
    assert not any('.git' in member.parts for member in members)
    assert not any(member.suffix.lower()=='.bundle' for member in members)
    assert not any('commit' in member.name.lower() and member.suffix.lower()=='.txt' for member in members)
