import csv, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_ccrf_snapshot_has_every_schema_row():
    schema=json.loads((ROOT/'data/ccrf_schema.json').read_text())
    with (ROOT/'data/ccrf_source_snapshot.tsv').open(encoding='utf-8') as h: rows=list(csv.DictReader(h,delimiter='	'))
    cumulative_rows=sum(len(x['fields']) for x in schema['classifications'].values())
    assert len(rows)==cumulative_rows==2134  # technical rows across four overlapping cumulative workbooks
    assert {r['classification'] for r in rows}==set(schema['classifications'])
def test_ccrf_source_reconciliation_is_complete():
    with (ROOT/'validation/ccrf_field_reconciliation.tsv').open(encoding='utf-8') as h: rows=list(csv.DictReader(h,delimiter='	'))
    assert len(rows)==2134 and all(r['status']=='matched' for r in rows)  # not 2,134 unique CDEs
def test_ccrf_snapshot_rebuild_matches(tmp_path):
    out=tmp_path/'ccrf.json'
    subprocess.run([sys.executable,str(ROOT/'scripts/ccrf/03_build_ccrf_schema.py'),'--output',str(out)],check=True)
    assert json.loads(out.read_text())==json.loads((ROOT/'data/ccrf_schema.json').read_text())
def test_source_manifest_has_official_urls_and_hashes():
    m=json.loads((ROOT/'data/ccrf_source_manifest.json').read_text())
    assert m['official_page']=='https://www.lipedema.org/ccrf'
    for x in m['files'].values(): assert x['download_url'].startswith('https://www.lipedema.org/') and len(x['sha256'])==64
    assert m['official_count_source']['classifications']['core']['official_cdes']==288
    assert 'not be summed as unique CDEs' in m['counting_note']

def test_redcap_workbook_parser_round_trip(tmp_path):
    fixtures = ROOT / 'build' / 'ccrf_fixture_workbooks'
    generated = tmp_path / 'ccrf_schema.from_fixture.json'
    subprocess.run([sys.executable, str(ROOT / 'scripts/ccrf/05_generate_synthetic_workbooks.py')], check=True)
    subprocess.run([
        sys.executable,
        str(ROOT / 'scripts/ccrf/03_build_ccrf_schema.py'),
        '--input-dir', str(fixtures),
        '--output', str(generated),
    ], check=True)
    committed = json.loads((ROOT / 'data/ccrf_schema.json').read_text(encoding='utf-8'))
    parsed = json.loads(generated.read_text(encoding='utf-8'))
    for key in committed['classifications']:
        assert parsed['classifications'][key]['fields'] == committed['classifications'][key]['fields']
