#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, py_compile, re
from pathlib import Path
from bs4 import BeautifulSoup
from common import ROOT, VALIDATION, dump_json, sha256_file, utc_now


def main():
    VALIDATION.mkdir(parents=True,exist_ok=True)
    html_path=ROOT/'LipoScope.html';html=html_path.read_text(encoding='utf-8');soup=BeautifulSoup(html,'html.parser')
    ids=[x.get('id') for x in soup.find_all(attrs={'id':True})]
    panels={x.get('id') for x in soup.select('.panel')}
    ccrf_sections=[x.get('id') for x in soup.select('#panel-ccrf .atlas-section')]
    static={
      'generated_at':utc_now(),
      'duplicate_html_ids':sorted({x for x in ids if ids.count(x)>1}),
      'main_panels_present':{'panel-browse','panel-live','panel-analytics','panel-ccrf','panel-resources','panel-about'}.issubset(panels),
      'ccrf_sections':ccrf_sections,
      'ccrf_order_matches':ccrf_sections==['ccrf-section-overview','ccrf-section-builder','ccrf-section-gaps','ccrf-section-dataset'],
    }
    static['passed']=not static['duplicate_html_ids'] and all(v for k,v in static.items() if k not in {'generated_at','duplicate_html_ids','ccrf_sections','passed'})
    dump_json(VALIDATION/'static_html_validation.json',static)

    schema=json.loads((ROOT/'data/ccrf_schema.json').read_text(encoding='utf-8'))
    compact=json.dumps(schema,ensure_ascii=False,separators=(',',':'))
    jszip_path=ROOT/'vendor/jszip/jszip.min.js';jszip=jszip_path.read_text(encoding='utf-8').strip()
    jszip_block='<!-- BEGIN LIPOSCOPE_JSZIP -->\n<script>\n'+jszip+'\n</script>\n<!-- END LIPOSCOPE_JSZIP -->'
    rebuild={
      'generated_at':utc_now(),
      'schema_embedded_exactly':('var CCRF_SCHEMA='+compact+';') in html,
      'jszip_version':'3.10.1',
      'jszip_sha256':sha256_file(jszip_path),
      'jszip_embedded_exactly':jszip_block in html,
      'template_matches':(ROOT/'templates/LipoScope.template.html').read_bytes()==html_path.read_bytes(),
      'release_copy_matches':(ROOT/'releases/LipoScope_v1.0.0.html').read_bytes()==html_path.read_bytes(),
      'html_sha256':sha256_file(html_path),
      'schema_sha256':sha256_file(ROOT/'data/ccrf_schema.json'),
    }
    rebuild['passed']=rebuild['schema_embedded_exactly'] and rebuild['jszip_embedded_exactly'] and rebuild['template_matches'] and rebuild['release_copy_matches']
    dump_json(VALIDATION/'deterministic_rebuild.json',rebuild)

    py_errors=[];py_files=list((ROOT/'scripts').rglob('*.py'))+list((ROOT/'tests').rglob('*.py'))
    for f in py_files:
        try:py_compile.compile(str(f),doraise=True)
        except Exception as e:py_errors.append({'file':str(f.relative_to(ROOT)),'error':str(e)})
    browser_path=VALIDATION/'browser_smoke_test.json';browser=json.loads(browser_path.read_text()) if browser_path.exists() else {'passed':False,'status':'not_run'}
    tests_path=VALIDATION/'automated_test_summary.json';tests=json.loads(tests_path.read_text()) if tests_path.exists() else {'passed':None,'failed':None}
    summary={
      'generated_at':utc_now(),'application_version':'v1.0.0','html_sha256':sha256_file(html_path),
      'ccrf':{'version':schema['source']['ccrfVersion'],'classifications':{k:{'official_cdes':v['official_cdes'],'clinical_cdes':v['clinical_cdes'],'participant_cdes':v['participant_cdes'],'dictionary_rows':v['dictionaryRows']} for k,v in schema['classifications'].items()}},
      'automated_tests':tests,'browser_test':browser,'python_syntax_errors':py_errors,
      'static_html_validation_passed':static['passed'],'deterministic_rebuild_passed':rebuild['passed']
    }
    summary['passed']=static['passed'] and rebuild['passed'] and not py_errors and bool(browser.get('passed')) and tests.get('failed',1)==0
    dump_json(VALIDATION/'local_validation_summary.json',summary)
    lines=['# LipoScope v1.0.0 validation report','',f"Generated: {summary['generated_at']}",'','## Application structure','',f"- Six main tabs and panels: **{'passed' if static['main_panels_present'] else 'failed'}**",f"- CCRF Workspace section order: **{'passed' if static['ccrf_order_matches'] else 'failed'}**",f"- Duplicate HTML identifiers: **{len(static['duplicate_html_ids'])}**",'','## CCRF Version 1','']
    for key,c in summary['ccrf']['classifications'].items():lines.append(f"- {key}: {c['official_cdes']} official CDEs ({c['clinical_cdes']} clinician; {c['participant_cdes']} participant); {c['dictionary_rows']} technical REDCap rows")
    lines += ['','The four dictionaries are cumulative. Technical row totals are not presented as unique CDE totals. Completion uses currently applicable required response fields and excludes direct identifiers from local assessment.','','## Validation','',f"- Automated tests: **{tests.get('passed','not recorded')} passed; {tests.get('failed','not recorded')} failed**",f"- Browser audit: **{'passed' if browser.get('passed') else 'not passed or not recorded'}**",f"- JSZip {rebuild['jszip_version']} embedded ZIP component: **{'passed' if rebuild['jszip_embedded_exactly'] else 'failed'}**",f"- Python syntax errors: **{len(py_errors)}**",f"- Static HTML validation: **{'passed' if static['passed'] else 'failed'}**",f"- Deterministic schema and HTML-copy check: **{'passed' if rebuild['passed'] else 'failed'}**"]
    (VALIDATION/'release_validation_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    if not summary['passed']:raise SystemExit('Validation failed')
    print('Validation reports generated')
    return 0
if __name__=='__main__':raise SystemExit(main())
