#!/usr/bin/env python3
"""Offline regression of literature retrieval and identity checks using mocked PubMed responses."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json,shutil,argparse
ap=argparse.ArgumentParser();ap.add_argument('--html',required=True);ap.add_argument('--out',required=True);args=ap.parse_args()
html=Path(args.html).read_text(encoding='utf-8')
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path=shutil.which('chromium') or None,args=['--no-sandbox','--disable-dev-shm-usage'])
 page=browser.new_page();page.route('**/*',lambda r:r.abort())
 page.evaluate('''()=>{const s=new Map();let api={getItem:k=>s.get(k)??null,setItem:(k,v)=>s.set(k,String(v)),removeItem:k=>s.delete(k),clear:()=>s.clear()};Object.defineProperty(window,'localStorage',{configurable:true,value:api});Object.defineProperty(window,'sessionStorage',{configurable:true,value:api});}''')
 page.set_content(html,wait_until='domcontentloaded',timeout=75000)
 results=page.evaluate('''async()=>{
  let failures=[],steps=[];
  function check(ok,label){steps.push({label,passed:!!ok});if(!ok)failures.push(label);}
  const originalFetcher=fetchLivingAtlas;
  fetchLivingAtlas=async(url)=>({esearchresult:{count:'503',idlist:Array.from({length:500},(_,i)=>String(i+1))}});
  let partialError='';try{await fetchAllLivingAtlasPubMedIds('test')}catch(e){partialError=String(e.message)}
  check(partialError.includes('Incomplete PubMed PMID retrieval'),'partial ESearch pagination must throw');
  fetchLivingAtlas=async(url)=>{
    if(url.includes('retstart=500'))return {esearchresult:{count:'503',idlist:['501','502','503']}};
    return {esearchresult:{count:'503',idlist:Array.from({length:500},(_,i)=>String(i+1))}};
  };
  const full=await fetchAllLivingAtlasPubMedIds('test');
  check(full.complete===true&&full.total===503&&full.ids.length===503,'complete ESearch pagination accepted');
  check(externalAbstractIdentityMatches({pmid:'111',doi:'10.7/abc'},{externalIds:{PubMed:'111',DOI:'10.7/abc'}}),'verified PubMed/DOI match accepted');
  check(!externalAbstractIdentityMatches({pmid:'111'},{externalIds:{PubMed:'222'},title:'Same name'}),'conflicting PMID rejected');
  check(!externalAbstractIdentityMatches({pmid:'111'},{title:'Same name'}),'title-only Semantic Scholar abstract rejected when PMID available');
  check(isLipedemaSpecificText('Lipohyperplasia dolorosa trial',''),'LiDo title accepted');
  check(isLipedemaSpecificText('Lipolymphedema therapy',''),'MeSH entry-term title accepted');
  // A mocked PubMed ESearch result of an incomplete citation cannot be
  // silently discarded as a disease-text false-negative after PubMed membership.
  fetchLivingAtlas=async(url)=>{
    if(url.includes('esearch.fcgi')) return {esearchresult:{count:'2',idlist:['99910','99911']}};
    if(url.includes('esummary.fcgi')) return {result:{'99910':{uid:'99910',title:'Lipedema diagnosis',source:'Example',pubdate:'2025'},'99911':{uid:'99911',title:'Secondary vascular observations',source:'Example',pubdate:'2024'}}};
    throw Error('Unexpected request '+url);
  };
  fetchPubMedAbstractsBatch=async()=>({});
  fetchExactTopicPubMedEvidence=async()=>({counts:{},byPmid:{},idsByTopic:{},fetchedAt:Date.now()});
  livingAtlasPapers=[];_livingAtlasRefreshing=false;
  await refreshLivingAtlasFromPubMed(true);
  check(livingAtlasPapers.length===2,'all 2 canonical ESearch PMIDs retained even if no abstract disease-text');
  const retrieval_debug={error:getLivingAtlasError(),papers:livingAtlasPapers.map(p=>p.pmid),mockCalls:typeof fetchLivingAtlas};
  check(livingAtlasPapers.some(p=>p.pmid==='99911'),'MeSH or entry-term retrieval not double-filtered by missing abstract');
  fetchLivingAtlas=originalFetcher;
  return {passed:failures.length===0,checks:steps,failures,retrieval_debug,mock_data_notice:'All PMID and citation data in this JS regression are synthetic test fixtures, not observed PubMed results.'};
}''')
 browser.close()
Path(args.out).parent.mkdir(parents=True,exist_ok=True)
Path(args.out).write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,indent=2))
if not results['passed']:raise SystemExit(1)
