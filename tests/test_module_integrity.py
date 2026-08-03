import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def extract_function(text,name):
    starts=[text.find('function '+name+'('),text.find('async function '+name+'(')]
    start=max(starts); assert start>=0,name
    b=text.find('{',start);depth=0;quote=None;esc=False
    for j in range(b,len(text)):
        ch=text[j]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in "'\"`":quote=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return text[start:j+1]
    raise AssertionError(name)

def test_recorded_application_function_hashes(html_text):
    manifest=json.loads((ROOT/'validation/application_function_integrity.json').read_text())
    for name,digest in manifest['functions'].items():
        assert hashlib.sha256(extract_function(html_text,name).encode()).hexdigest()==digest
