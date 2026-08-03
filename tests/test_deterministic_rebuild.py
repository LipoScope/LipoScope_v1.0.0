import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_html_copies_are_byte_identical():
    active=(ROOT/'LipoScope.html').read_bytes()
    assert (ROOT/'templates/LipoScope.template.html').read_bytes()==active
    assert (ROOT/'releases/LipoScope_v1.0.0.html').read_bytes()==active


def test_ccrf_schema_rebuild_is_deterministic(tmp_path):
    output=tmp_path/'ccrf_schema.json'
    subprocess.run([sys.executable,str(ROOT/'scripts/ccrf/03_build_ccrf_schema.py'),'--output',str(output)],check=True)
    assert json.loads(output.read_text(encoding='utf-8'))==json.loads((ROOT/'data/ccrf_schema.json').read_text(encoding='utf-8'))


def test_ccrf_embed_script_preserves_distributed_copies(tmp_path):
    template=tmp_path/'template.html'
    output=tmp_path/'LipoScope.html'
    release=tmp_path/'release.html'
    template.write_bytes((ROOT/'templates/LipoScope.template.html').read_bytes())
    subprocess.run([sys.executable,str(ROOT/'scripts/ccrf/08_embed_ccrf_schema.py'),'--template',str(template),'--output',str(output),'--release-output',str(release)],check=True)
    assert template.read_bytes()==output.read_bytes()==release.read_bytes()
    assert output.read_bytes()==(ROOT/'LipoScope.html').read_bytes()
