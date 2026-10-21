"""Version-pinned CCRF source identity and structural regression checks."""
import csv, hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BLOBS={'ccrf_schema.json':'9bb36c89f4ea597f1c2831d9ad471ca7390fbdda','ccrf_source_snapshot.tsv':'333218105eb82ca676c4fdda540c53d6a61a54c1','ccrf_source_manifest.json':'92881c4b774d4f4b0eabe45448489d183cb9537a'}

def test_original_git_v1_source_bytes_are_unchanged():
 for name,expected in BLOBS.items():
  b=(ROOT/'data'/name).read_bytes()
  observed=hashlib.sha1(('blob %d\0'%len(b)).encode()+b).hexdigest()
  assert observed==expected,(name,observed,expected)

def test_original_ccrf_branch_and_row_inventory_is_structurally_consistent():
 schema=json.loads((ROOT/'data/ccrf_schema.json').read_text())
 counts={key:len(c['fields']) for key,c in schema['classifications'].items()}
 assert counts=={'core':300,'supplemental_highly_recommended':445,'supplemental':650,'exploratory':739}
 assert sum(counts.values())==2134
 branches=0; options=0;calcs=0;missing=[]
 for key,c in schema['classifications'].items():
  variables=[x['variable'] for x in c['fields']]
  assert len(variables)==len(set(variables))
  for f in c['fields']:
   if f.get('branching'):
    branches+=1
    for parent in re.findall(r'\[([A-Za-z0-9_]+)(?:\([^\]]+\))?\]',f['branching']):
     if parent not in variables: missing.append((key,f['variable'],parent))
   if f['type'] in {'radio','dropdown','checkbox'}:
    options+=1
    assert f['choices'],(key,f['variable'])
   if f['type']=='calc':
    calcs+=1
    assert not f['choices'],(key,f['variable'])
 assert branches==752 and options==1153 and calcs==37
 assert not missing,missing

def test_builder_displays_original_matrix_instructions_and_exports_mask_inactive():
 app=(ROOT/'LipoScope.html').read_text()
 assert 'ccrf-matrix-context' in app
 assert 'CCRFEngine.cleanText(field.matrixGroup)' in app
 assert 'Original matrix group headings and shared instructions' in app
 assert '!assessment.fieldStates[v].applicable' in app
 assert 'function ccrfRecordMatchesSource(record)' in app
 assert (ROOT/'templates/LipoScope.template.html').read_bytes()==(ROOT/'LipoScope.html').read_bytes()
 assert (ROOT/'releases/LipoScope_v1.0.0.html').read_bytes()==(ROOT/'LipoScope.html').read_bytes()
