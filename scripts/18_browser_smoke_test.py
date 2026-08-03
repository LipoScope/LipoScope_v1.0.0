#!/usr/bin/env python3
"""Browser-level validation for LipoScope v1.0.0."""
from __future__ import annotations
import argparse, http.server, json, shutil, socketserver, threading
from pathlib import Path
from common import ROOT, VALIDATION

OFFICIAL_COUNTS={
 'core':{'official':288,'clinical':86,'participant':202,'rows':300},
 'supplemental_highly_recommended':{'official':424,'clinical':89,'participant':335,'rows':445},
 'supplemental':{'official':618,'clinical':89,'participant':529,'rows':650},
 'exploratory':{'official':682,'clinical':120,'participant':562,'rows':739},
}

def launch(playwright):
    try:return playwright.chromium.launch(headless=True)
    except Exception:
        exe=shutil.which('chromium') or shutil.which('google-chrome') or shutil.which('google-chrome-stable')
        if not exe:raise
        return playwright.chromium.launch(headless=True,executable_path=exe,args=['--no-sandbox','--disable-dev-shm-usage'])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--html',default=str(ROOT/'LipoScope.html'));ap.add_argument('--port',type=int,default=0);args=ap.parse_args()
    html=Path(args.html).resolve();directory=html.parent
    handler=lambda *a,**k:http.server.SimpleHTTPRequestHandler(*a,directory=str(directory),**k)
    socketserver.TCPServer.allow_reuse_address=True
    with socketserver.TCPServer(('127.0.0.1',args.port),handler) as server:
        threading.Thread(target=server.serve_forever,daemon=True).start()
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=launch(p);page=browser.new_page(viewport={'width':1440,'height':1000})
            errors=[];console=[]
            page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(('http://127.0.0.1:','data:','blob:')) else route.abort())
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:console.append(m.text) if m.type=='error' and 'Failed to load resource' not in m.text else None)
            port=server.server_address[1]
            try:
                page.goto(f'http://127.0.0.1:{port}/{html.name}',wait_until='domcontentloaded',timeout=20000);mode='local_http'
            except Exception as exc:
                if 'ERR_BLOCKED_BY_ADMINISTRATOR' not in str(exc):raise
                page.set_content(html.read_text(encoding='utf-8'),wait_until='domcontentloaded',timeout=120000);mode='set_content_fallback'
            page.wait_for_timeout(1200)
            tabs={}
            for tab in ['resources','browse','live','analytics','ccrf','about']:
                page.locator(f'#nav-{tab}').click();page.wait_for_timeout(120)
                tabs[tab]=page.locator(f'#panel-{tab}.active').count()==1
            page.locator('#nav-ccrf').click();page.wait_for_timeout(250)
            structure={
              'ccrf_panel':page.locator('#panel-ccrf').count()==1,
              'builder':page.locator('#ccrf-section-builder').count()==1,
              'gap_radar':page.locator('#ccrf-section-gaps').count()==1,
              'dictionary_export':page.locator('#ccrf-section-dataset').count()==1,
              'section_order':page.evaluate("() => Array.from(document.querySelectorAll('#panel-ccrf .atlas-section')).map(x=>x.id).join('|')")=='ccrf-section-overview|ccrf-section-builder|ccrf-section-gaps|ccrf-section-dataset',
            }
            ccrf={}
            for key,expected in OFFICIAL_COUNTS.items():
                page.select_option('#ccrf-classification',key);page.wait_for_timeout(100)
                meta=page.locator('#ccrf-classification-meta').inner_text()
                cards=page.locator('#ccrf-field-container .ccrf-field-card').count()
                section=page.locator('#ccrf-field-container .ccrf-section-heading').inner_text()
                schema=page.evaluate("""key=>{const c=CCRF_SCHEMA.classifications[key],r=CCRFEngine.createRecord(CCRF_SCHEMA,key),a=CCRFEngine.assessRecord(c,r,{excludeIdentifiers:true});return {official:c.official_cdes,clinical:c.clinical_cdes,participant:c.participant_cdes,rows:c.dictionaryRows,fields:c.fields.length,required:a.counts.requiredApplicable,local:a.counts.requiredLocallyAssessable,privacy:a.counts.requiredPrivacyExcluded,calc:c.calculationExpressionRows};}""",key)
                ccrf[key]={
                  'official_count':schema['official']==expected['official'],
                  'split':schema['clinical']==expected['clinical'] and schema['participant']==expected['participant'],
                  'dictionary_rows':schema['rows']==expected['rows']==schema['fields'],
                  'meta':f"{expected['official']} official CDEs" in meta and f"{expected['rows']} REDCap dictionary rows" in meta,
                  'render_count':f"{cards} field(s) currently shown" in section,
                  'completion_denominator':schema['required']!=schema['official'] and schema['local']==schema['required']-schema['privacy'],
                  'no_inferred_calc':schema['calc']==0,
                }
            self_tests=page.evaluate('runCcrfBrowserSelfTests()')
            ccrf['self_tests']=all(x.get('pass') for x in self_tests)
            ccrf['inactive_retention']=page.evaluate("""()=>{const f={variable:'follow_up',type:'text',required:false,branching:"[parent]='1'"};return CCRFEngine.assessField(f,{parent:'0',follow_up:'kept'},{excludeIdentifiers:true}).status==='inactive_with_value';}""")
            effective=[e for e in errors if not(mode=='set_content_fallback' and 'localStorage' in e and 'Access is denied' in e)]
            passed=all(tabs.values()) and all(structure.values()) and not effective and not console and all(all(v for v in x.values()) for x in ccrf.values() if isinstance(x,dict)) and ccrf['self_tests'] and ccrf['inactive_retention']
            report={'passed':passed,'navigation_mode':mode,'tabs':tabs,'structure':structure,'ccrf':ccrf,'page_errors':effective,'console_errors':console}
            VALIDATION.mkdir(parents=True,exist_ok=True);(VALIDATION/'browser_smoke_test.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
            browser.close()
            print(json.dumps(report,indent=2));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
