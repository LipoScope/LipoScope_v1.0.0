#!/usr/bin/env python3
"""Offline regression of complete Live Search retrieval, batching and imports."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import http.server
import json
from pathlib import Path
import socketserver
import threading
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright


CHECKS = """async () => {
  const checks=[];
  const check=(name,passed)=>checks.push({name,passed:!!passed});
  const ids=(start,count)=>Array.from({length:count},(_,i)=>String(start+i));
  const requests=[];
  let summaryFailure=false, releaseSearch, releaseSummary;
  const originalFetcher=fetchLivingAtlas, originalAbstract=fetchPubMedAbstract;
  const searchResult=list=>({esearchresult:{count:String(list.length),idlist:list}});
  fetchPubMedAbstract=async()=>({abstractText:'General observations.',fullText:'General observations.',sections:{}});
  fetchLivingAtlas=async url=>{
    const parsed=new URL(url),p=parsed.searchParams;
    if (parsed.pathname.endsWith('esearch.fcgi')) {
      const term=p.get('term'); requests.push({kind:'search',term,retmax:Number(p.get('retmax'))});
      if(term.includes('slow-search')) return new Promise(resolve=>releaseSearch=()=>resolve(searchResult(ids(780000000,3))));
      if(term.includes('slow-summary')) return searchResult(ids(781000000,3));
      if(term.includes('empty-case')) return searchResult([]);
      if(term.includes('partial-case')) return {esearchresult:{count:'75',idlist:ids(782000000,74)}};
      if(term.includes('error-case')) throw new Error('Synthetic outage <img src=x>');
      if(term.includes('new-case')) return searchResult(ids(783000000,2));
      if(term.includes('retry-case')) return searchResult(ids(784000000,75));
      return searchResult(ids(770000000,123));
    }
    if(parsed.pathname.endsWith('esummary.fcgi')) {
      const list=p.get('id').split(','); requests.push({kind:'summary',ids:list});
      const response=()=>({result:Object.fromEntries(list.map(id=>[id,{
        uid:id,title:id==='770000099'?'Synthetic <img src=x onerror=alert(1)> observations in lipedema':'Synthetic observations in lipedema '+id,
        authors:[{name:'Test <b>Author</b>'}],pubdate:'2026',source:'Synthetic <b>journal</b>',articleids:[]
      }]))});
      if(list[0]==='781000000') return new Promise(resolve=>releaseSummary=()=>resolve(response()));
      const data=response();
      if(summaryFailure) {summaryFailure=false;delete data.result[list[list.length-1]];}
      return data;
    }
    throw new Error('Unexpected synthetic request');
  };
  const run=async query=>{document.getElementById('live-query').value=query;await runLiveSearch();};
  const count=()=>document.querySelectorAll('#live-results .live-card').length;
  document.getElementById('nav-live').click();
  await run('batch-case');
  check('First batch shows 50 of all 123 matching records',count()===50 && liveSearchState.total===123 &&
    !document.getElementById('live-pagination').hidden && document.getElementById('live-status').textContent.includes('123'));
  check('The complete search retains the canonical disease scope',requests[0].term==='(batch-case) AND '+LIPOEDEMA_PUBMED_QUERY && requests[0].retmax>20);
  await Promise.all([loadMoreLiveResults(),loadMoreLiveResults()]);
  check('Repeated Load more clicks fetch a batch only once',count()===100 && requests.filter(r=>r.kind==='summary').length===2);
  const target='770000075',before=userPapers.filter(p=>p.pmid===target).length;
  await Promise.all([addFromCard(target),addFromCard(target)]);
  check('A record beyond the first 20 and first batch can be added once',before===0 && userPapers.filter(p=>p.pmid===target).length===1 &&
    document.getElementById('add-btn-'+target).disabled);
  check('Added records retain current topic classification',userPapers.find(p=>p.pmid===target).topic==='Unresolved category');
  await loadMoreLiveResults();
  check('Final batch makes every match available and hides Load more',count()===123 && Object.keys(window._live).length===123 &&
    document.getElementById('live-pagination').hidden && document.getElementById('live-status').textContent.includes('All matching results are shown'));
  check('Citation metadata remains text when cards are appended',!document.querySelector('#live-results img') &&
    !document.querySelector('#live-results b') && document.getElementById('live-results').textContent.includes('<img src=x'));
  check('First and last results both retain Add to Browse controls',!!document.getElementById('add-btn-770000000') && !!document.getElementById('add-btn-770000122'));
  await run('retry-case');summaryFailure=true;await loadMoreLiveResults();
  check('Incomplete citation batches retain previous results and a retry control',count()===50 && liveSearchState.loaded===50 &&
    document.getElementById('live-more-btn').textContent.includes('Retry') && !document.getElementById('live-pagination').hidden);
  await loadMoreLiveResults();
  check('Retry resumes the failed batch without omissions or duplicates',count()===75 && liveSearchState.loaded===75 && Object.keys(window._live).length===75);
  await run('partial-case');
  check('An incomplete PMID inventory is reported instead of silently truncated',count()===0 &&
    document.getElementById('live-status').textContent.includes('incomplete result list') && !document.getElementById('live-btn').disabled);
  await run('empty-case');
  check('A zero-result search clears old records and pagination',count()===0 && Object.keys(window._live).length===0 &&
    document.getElementById('live-pagination').hidden && document.getElementById('live-status').textContent==='No results found.');
  await run('error-case');
  check('Failed searches restore controls and display errors as text',!document.getElementById('live-btn').disabled &&
    !document.querySelector('#live-status img') && document.getElementById('live-status').textContent.includes('Synthetic outage'));
  const slow=run('slow-search');
  await Promise.resolve();await run('new-case');releaseSearch();await slow;
  check('A late search response cannot overwrite a newer query',count()===2 && Object.keys(window._live).every(id=>id.startsWith('783')));
  const slowBatch=run('slow-summary');
  for(let i=0;i<30&&!releaseSummary;i++)await Promise.resolve();
  await run('new-case');releaseSummary();await slowBatch;
  check('A late citation batch cannot overwrite a newer query',count()===2 && Object.keys(window._live).every(id=>id.startsWith('783')));
  const switched=run('slow-search');await Promise.resolve();
  setLiveSource('scholar',document.getElementById('src-scholar'));releaseSearch();await switched;
  check('Changing sources clears and cancels pending PubMed results',count()===0 && Object.keys(window._live).length===0 && document.getElementById('live-pagination').hidden);
  const originalOpen=window.open;let scholarUrl='';window.open=url=>{scholarUrl=url;};
  await run('new-case');window.open=originalOpen;
  check('Google Scholar continues to open its own disease-scoped search',scholarUrl.startsWith('https://scholar.google.com/') &&
    scholarUrl.includes('lipedema') && document.getElementById('live-pagination').hidden);
  setLiveSource('pubmed',document.getElementById('src-pubmed'));
  let largeRequests=0;
  fetchLivingAtlas=async url=>{
    largeRequests++;
    const term=new URL(url).searchParams.get('term');
    if(term==='large-inventory')return {esearchresult:{count:'10001',idlist:ids(1,9999)}};
    if(term.includes('NOT'))return searchResult(ids(5001,5001));
    return searchResult(ids(1,5000));
  };
  const large=await fetchAllLiveSearchIds('large-inventory',()=>true);
  check('Searches above the PubMed single-query limit retain all matching PMIDs',large.total===10001 && large.ids.length===10001 && new Set(large.ids).size===10001 && largeRequests===3);
  fetchLivingAtlas=async()=>({esearchresult:{count:'10001',idlist:ids(1,9999)}});
  let rejected=false;try{await fetchAllLiveSearchIds('ignored-partition',()=>true);}catch(e){rejected=e.message.includes('could not divide');}
  check('A server that ignores partition constraints cannot cause infinite retrieval',rejected);
  fetchLivingAtlas=originalFetcher;fetchPubMedAbstract=originalAbstract;
  for(const tab of ['resources','browse','live','analytics','about']) {
    document.getElementById('nav-'+tab).click();
    check(tab+' tab opens without the obsolete 20-result limit',document.getElementById('panel-'+tab).classList.contains('active') &&
      !/up to 20|20 recent results|top 20 results/i.test(document.getElementById('panel-'+tab).textContent));
  }
  return {passed:checks.every(c=>c.passed),checks,
    scope:'Synthetic PubMed responses: complete inventories, batches, imports, retries, source/query races, large searches, and five non-CCRF tabs.'};
}"""


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--html', type=Path, default=Path('LipoScope.html'))
    source.add_argument('--url')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with ExitStack() as stack:
        if args.url:
            url = args.url
        else:
            html = args.html.resolve()
            handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(html.parent), **k)
            server = stack.enter_context(socketserver.TCPServer(('127.0.0.1', 0), handler))
            threading.Thread(target=server.serve_forever, daemon=True).start()
            stack.callback(server.shutdown)
            url = f'http://127.0.0.1:{server.server_address[1]}/{html.name}'
        origin = '{0.scheme}://{0.netloc}/'.format(urlsplit(url))
        playwright = stack.enter_context(sync_playwright())
        browser = playwright.chromium.launch(headless=True)
        stack.callback(browser.close)
        page = browser.new_page()
        page.route('**/*', lambda route: route.continue_() if route.request.url.startswith((origin, 'data:', 'blob:')) else route.abort())
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url, wait_until='domcontentloaded', timeout=40000)
        report = page.evaluate(CHECKS)
        report['page_errors'] = errors
        report['passed'] = report['passed'] and not errors
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(json.dumps(report, indent=2))
        return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
