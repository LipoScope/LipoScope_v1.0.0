#!/usr/bin/env python3
"""Synthetic offline browser regression of PubMed XML and New Paper Alerts."""
import argparse,json,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
ap=argparse.ArgumentParser();ap.add_argument('--html',required=True);ap.add_argument('--out',required=True);args=ap.parse_args()
html=Path(args.html).read_text(encoding='utf-8')
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path=shutil.which('chromium') or None,args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page()
    page.route('**/*',lambda r:r.abort())
    page.evaluate('''()=>{
      const s=new Map();let api={getItem:k=>s.get(k)??null,setItem:(k,v)=>s.set(k,String(v)),removeItem:k=>s.delete(k),clear:()=>s.clear()};
      Object.defineProperty(window,'localStorage',{configurable:true,value:api});
      Object.defineProperty(window,'sessionStorage',{configurable:true,value:api});
    }''')
    page.set_content(html,wait_until='domcontentloaded',timeout=75000)
    findings=page.evaluate('''async()=>{
      const results=[];function check(name,passed,detail){results.push({name,passed:!!passed,detail:detail||''});}
      const mixedXML=`<?xml version="1.0"?><PubmedArticleSet>
        <PubmedArticle><MedlineCitation><PMID>12345</PMID><Article><Journal><Title>Journal of Tests</Title></Journal><Abstract><AbstractText Label="Results">Journal result.</AbstractText></Abstract></Article></MedlineCitation></PubmedArticle>
        <PubmedBookArticle><BookDocument><PMID>34424639</PMID><ArticleTitle>Lipedema</ArticleTitle><Book><BookTitle>StatPearls</BookTitle><PubDate><Year>2025</Year></PubDate></Book><Abstract><AbstractText Label="Abstract">Book entry with verified PMID.</AbstractText></Abstract></BookDocument></PubmedBookArticle>
      </PubmedArticleSet>`;
      const data=parsePubMedAbstractXmlByPmid(mixedXML);
      check('Journal PMID retained from mixed EFetch',!!data['12345'] && data['12345'].abstractText.includes('Journal result'));
      check('Book PMID retained from mixed EFetch',!!data['34424639'] && data['34424639'].recordType==='book_chapter');
      check('Book source and year preserved',data['34424639'].journal.title==='StatPearls' && data['34424639'].publicationYear===2025);
      check('Book abstract preserved',data['34424639'].abstractText.includes('Book entry'));
      const oldFetch=window.fetch;
      window.fetch=async()=>{throw Error('Synthetic network outage')};
      localStorage.removeItem(notifKey('last_check_v1'));
      await checkForNewPapers(true);
      check('Failed PubMed alert request does not advance clock',getLastNotifCheck()===null);
      window.fetch=async()=>({ok:true,json:async()=>({esearchresult:{count:'0',idlist:[]}})});
      await checkForNewPapers(true);
      check('Successful zero-result check advances clock',!!getLastNotifCheck());
      localStorage.removeItem(notifKey('last_check_v1'));
      window.fetch=async(url)=>url.includes('esearch')
        ? {ok:true,json:async()=>({esearchresult:{count:'1',idlist:['54321']}})}
        : {ok:false,status:503};
      await checkForNewPapers(true);
      check('Failed ESummary does not advance clock',getLastNotifCheck()===null);
      window.fetch=oldFetch;
      return {passed:results.every(r=>r.passed),checks:results,notice:'Only synthetic PubMed XML and network outcomes were used.'};
    }''')
    browser.close()
out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(findings,indent=2)+'\n',encoding='utf-8');print(json.dumps(findings,indent=2));
if not findings['passed']:raise SystemExit(1)
