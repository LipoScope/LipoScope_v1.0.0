from __future__ import annotations
import csv, hashlib, json, re
from pathlib import Path
from typing import Any
import yaml

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'; CONFIG=ROOT/'config'; VALIDATION=ROOT/'validation'; BUILD=ROOT/'build'

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def load_sources(): return yaml.safe_load((CONFIG/'ccrf_sources.yaml').read_text(encoding='utf-8'))

def load_official_counts():
    cfg=load_sources()
    path=ROOT/cfg['official_counts_snapshot']
    return json.loads(path.read_text(encoding='utf-8'))

def parse_bound(v):
    if v in (None,''): return None
    if isinstance(v,(int,float)): return v
    text=str(v).strip()
    try:
        number=float(text)
        return int(number) if number.is_integer() else number
    except ValueError:
        return text

def clean(v:Any):
    if v is None: return None
    if isinstance(v,bool): return v
    return str(v).strip()

HEADER_ALIASES={
 'variable':['Variable / Field Name','Variable / Field name','Variable'],
 'form':['Form Name','Form name'],
 'sourceSectionHeader':['Section Header','Section header'],
 'type':['Field Type','Field type'],
 'label':['Field Label','Field label'],
 'choices':['Choices, Calculations, OR Slider Labels','Choices, Calculations, OR Slider Labels '],
 'note':['Field Note','Field note'],
 'validation':['Text Validation Type OR Show Slider Number','Text Validation Type or Show Slider Number'],
 'min':['Text Validation Min','Text validation min'],
 'max':['Text Validation Max','Text validation max'],
 'identifier':['Identifier?','Identifier'],
 'branching':['Branching Logic (Show field only if...)','Branching Logic (Show field only if…)','Branching Logic'],
 'required':['Required Field?','Required Field'],
 'alignment':['Custom Alignment','Custom alignment'],
 'questionNumber':['Question Number (surveys only)','Question Number'],
 'matrixGroup':['Matrix Group Name','Matrix group name'],
 'matrixRanking':['Matrix Ranking?','Matrix Ranking'],
 'annotation':['Field Annotation','Field annotation'],
}

def bool_yn(v): return str(v or '').strip().casefold() in {'y','yes','true','1'}

def canonical_header_map(headers):
    normal={str(h or '').strip():i for i,h in enumerate(headers)}; out={}
    for target,aliases in HEADER_ALIASES.items():
        for a in aliases:
            if a in normal: out[target]=normal[a]; break
    missing=[x for x in ['variable','form','type','label'] if x not in out]
    if missing: raise ValueError(f'Missing required REDCap columns: {missing}; observed={list(normal)}')
    return out

def derive_section(fields):
    current_by_form={}; out=[]
    for f in fields:
        header=f.get('sourceSectionHeader')
        if header: current_by_form[f['form']]=header
        f['section']=current_by_form.get(f['form']) or f['form']
        out.append(f)
    return out

def parse_snapshot(path:Path):
    grouped={}
    with path.open(encoding='utf-8') as h:
        for r in csv.DictReader(h,delimiter='	'):
            key=r['classification']; grouped.setdefault(key,[])
            f={
              'variable':r['Variable / Field Name'],'form':r['Form Name'],'sourceSectionHeader':r['Section Header'] or None,
              'type':r['Field Type'] or 'text','label':r['Field Label'] or None,'choices':r['Choices, Calculations, OR Slider Labels'] or None,
              'note':r['Field Note'] or None,'validation':r['Text Validation Type OR Show Slider Number'] or None,
              'min':parse_bound(r['Text Validation Min']),'max':parse_bound(r['Text Validation Max']),'identifier':bool_yn(r['Identifier?']),
              'branching':r['Branching Logic (Show field only if...)'] or None,'required':bool_yn(r['Required Field?']),
              'alignment':r['Custom Alignment'] or None,'questionNumber':r['Question Number (surveys only)'] or None,
              'matrixGroup':r['Matrix Group Name'] or None,'matrixRanking':r['Matrix Ranking?'] or None,
              'annotation':r['Field Annotation'] or None,'sourceRow':int(r['source_row']) if r['source_row'] else None,
            }
            grouped[key].append(f)
    return {k:derive_section(v) for k,v in grouped.items()}
