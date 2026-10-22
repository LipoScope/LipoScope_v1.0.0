#!/usr/bin/env python3
"""Deterministic PubMed count, cache and provenance regression scenarios."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import http.server
import json
from pathlib import Path
import socketserver
import threading

from playwright.sync_api import sync_playwright


LIVE_CHECKS = """async () => await Promise.race([(async()=>{
  const stats=await fetchPubMedStats();
  await renderAnalytics();
  const unique=new Set(livingAtlasPapers.map(p=>p.pmid)).size;
  return {validation_type:'real_service_smoke',query:LIPOEDEMA_PUBMED_QUERY,
    query_match_count:stats.pubmedQueryMatchCount,unique_processed_pmids:unique,
    records_processed:stats.liveRecordCount,query_retrieved_at:stats.pubmedCountRetrievedAt,
    corpus_retrieved_at:stats.processedRecordsRetrievedAt,retrieval_completeness:stats.retrievalCompleteness,
    record_count_difference:stats.recordCountDifference,source:stats.source,error:stats.error,
    topic_query_error:stats.topicQueryError||'',topic_query_retrieved_at:stats.topicCountsRetrievedAt,
    passed:stats.retrievalCompleteness==='complete'&&stats.pubmedQueryMatchCount===stats.liveRecordCount&&
      stats.liveRecordCount===unique&&!stats.error,
    notice:'Real PubMed responses; no expected publication count was hardcoded. This is not a validation of classification accuracy.'};
})(),new Promise((_,reject)=>setTimeout(()=>reject(Error('Live PubMed verification exceeded 180 seconds')),180000))])"""


CHECKS = """async () => {
  if (_pubmedStatsPromise) await _pubmedStatsPromise;
  if (_livingAtlasRefreshPromise) await _livingAtlasRefreshPromise;
  const checks=[],check=(name,passed)=>checks.push({name,passed:!!passed});
  const originalFetch=fetchLivingAtlas,originalTopics=fetchExactTopicPubMedEvidence;
  const originalMerge=mergeLivingAtlasRecords;
  localStorage.clear();livingAtlasPapers=[];livingAtlasSnapshot=null;_pubmedCache=null;_topicQueryMembershipCache=null;
  let mode='good',searches=0,standaloneCounts=0;
  const base=['91000101','91000102','91000103'];
  const inventory=()=>['good','offline','processing-error'].includes(mode)?base:base.concat('91000104');
  const xml=ids=>'<PubmedArticleSet>'+ids.map(id=>{
    const missingInfo=id==='91000102';
    const journal=missingInfo?'':'<Journal><Title>Synthetic journal</Title><JournalIssue><PubDate><Year>2026</Year></PubDate></JournalIssue></Journal>';
    const title=id==='91000101'?'Genomic variants associated with lipedema':'Observations in lipedema';
    return '<PubmedArticle><MedlineCitation Status="MEDLINE"><PMID>'+id+'</PMID><Article><ArticleTitle>'+title+'</ArticleTitle>'+journal+'</Article></MedlineCitation></PubmedArticle>';
  }).join('')+'</PubmedArticleSet>';
  const mocked=async url=>{
    const u=new URL(url),p=u.searchParams;
    if(u.pathname.endsWith('esearch.fcgi')) {
      searches++;if(p.get('retmax')==='0')standaloneCounts++;
      if(mode==='offline')throw Error('Synthetic PubMed outage');
      const list=inventory();return {esearchresult:{count:String(list.length),idlist:list}};
    }
    const requested=p.get('id').split(',');
    if(u.pathname.endsWith('esummary.fcgi'))return {result:Object.fromEntries(requested
      .filter(id=>mode!=='missing-summary'||id!=='91000104')
      .map(id=>[id,{uid:id,title:id==='91000102'?'':'Observations in lipedema'}]))};
    if(u.pathname.endsWith('efetch.fcgi'))return xml(requested.filter(id=>mode!=='missing-efetch'||id!=='91000104'));
    throw Error('Unexpected request in synthetic Analytics test');
  };
  fetchLivingAtlas=mocked;
  fetchExactTopicPubMedEvidence=async()=>{
    const topics=Object.keys(TOPIC_DEFINITIONS);
    const evidence={counts:Object.fromEntries(topics.map((t,i)=>[t,i<2?base.length:0])),
      byPmid:{},idsByTopic:{},fetchedAt:Date.now()-60000};
    saveTopicQueryMembershipCache(evidence);return evidence;
  };
  const complete=await fetchPubMedStats(true);
  check('Completed query, unique inventory and processed corpus reconcile exactly',complete.pubmedQueryMatchCount===base.length &&
    complete.liveRecordCount===base.length && complete.recordCountDifference===0 && complete.retrievalCompleteness==='complete' &&
    new Set(livingAtlasPapers.map(p=>p.pmid)).size===base.length);
  check('Fresh complete retrieval has a shared snapshot identity and two recorded timestamps',!!complete.snapshotId &&
    !!complete.pubmedCountRetrievedAt && !!complete.processedRecordsRetrievedAt && analyticsSourceMeta(complete).badge.includes('Synchronised complete'));
  check('Analytics does not fetch an independent fresh disease-query total',standaloneCounts===0);
  check('Unresolved topics remain in the processed denominator',complete.unresolvedTopicCount>0 &&
    Object.values(complete.classifiedTopicCounts).reduce((a,b)=>a+b,0)+complete.unresolvedTopicCount===base.length);
  check('Missing year, journal and abstract fields retain valid PMIDs',livingAtlasPapers.some(p=>p.pmid==='91000102') &&
    complete.unknownYearCount===1 && complete.unknownJournalCount===1 && livingAtlasPapers.every(p=>!p.abstractText));
  check('Year, journal and study-type counts reconcile with the full denominator',
    Object.values(complete.byYear).reduce((a,b)=>a+b,0)+complete.unknownYearCount===complete.liveRecordCount &&
    Object.values(complete.byJournal).reduce((a,b)=>a+b,0)+complete.unknownJournalCount===complete.liveRecordCount &&
    Object.values(complete.byStudyType).reduce((a,b)=>a+b,0)===complete.liveRecordCount);
  check('Overlapping topic-query counts are independent of the unique corpus size',
    Object.values(complete.byTopic).reduce((a,b)=>a+b,0)>complete.liveRecordCount && complete.topicCountsExact);
  check('Independent topic-query timestamps remain separate from corpus provenance',complete.topicCountsRetrievedAt<complete.processedRecordsRetrievedAt);
  const checked=getLivingAtlasChecked(),snapshot=complete.snapshotId;
  let persisted=localStorage.getItem(livingAtlasStorageKey('papers_v1'));
  const savedStats=localStorage.getItem(pubMedStatsStorageKey('live_v7_expanded_disease_query'));
  saveLivingAtlasStore();
  check('Enrichment-only saves do not advance successful corpus timestamps',getLivingAtlasChecked()===checked && getLivingAtlasSnapshot().id===snapshot);
  persisted=localStorage.getItem(livingAtlasStorageKey('papers_v1'));
  const mixed=Object.assign({},complete,{source:'cached-live',pubmedQueryMatchCount:base.length+2,total:base.length+2,
    pubmedCountRetrievedAt:checked+3600000,retrievalCompleteness:'different-snapshots'});
  _pubmedCache=mixed;await renderAnalytics();
  const note=document.getElementById('analytics-provenance').textContent;
  check('Different retrieval operations display both counts and their original timestamps',
    document.getElementById('pubmed-total-n').textContent===String(base.length+2) &&
    document.getElementById('pubmed-processed-n').textContent===String(base.length) &&
    note.includes(analyticsRetrievedLabel(checked)) && note.includes(analyticsRetrievedLabel(checked+3600000)));
  check('Mixed snapshots show the difference without a false completeness or missing-publication claim',
    document.getElementById('analytics-source-badge').textContent.includes('Different snapshots') &&
    note.includes('2 (query matches minus records processed)') && note.includes('difference alone does not establish missing publications'));
  const equalDifferent=Object.assign({},complete,{source:'cached-live',retrievalCompleteness:'different-snapshots'});
  check('Equal counts alone cannot prove a common retrieval',analyticsSourceMeta(equalDifferent).badge.includes('Different snapshots'));
  const inconsistent=Object.assign({},complete,{pubmedQueryMatchCount:complete.liveRecordCount+1});
  check('A claimed same-snapshot mismatch remains incomplete across repeated rendering',
    analyticsSourceMeta(inconsistent).badge.includes('Incomplete retrieval') && analyticsSourceMeta(inconsistent).badge.includes('Incomplete retrieval') && inconsistent.retrievalCompleteness==='incomplete');
  mode='offline';_pubmedCache=null;
  const failed=await fetchPubMedStats(true);
  check('Failed refresh preserves the last complete corpus and original successful timestamp',
    getLivingAtlasChecked()===checked && localStorage.getItem(livingAtlasStorageKey('papers_v1'))===persisted &&
    failed.processedRecordsRetrievedAt===checked && failed.fetchedAt===complete.fetchedAt);
  check('Failed refresh retains the last successful Analytics cache without overwriting it',
    localStorage.getItem(pubMedStatsStorageKey('live_v7_expanded_disease_query'))===savedStats &&
    failed.source==='cached-live' && analyticsSourceMeta(failed).badge.includes('refresh failed'));
  saveLivingAtlasStore();
  check('Subsequent enrichment saves cannot clear a failed-refresh flag',!!getLivingAtlasError() && getLivingAtlasChecked()===checked);
  mode='missing-summary';
  const missing=await fetchPubMedStats(true);
  check('Missing ESummary citations fail retrieval and never commit partial records',missing.error.includes('citation summaries') &&
    livingAtlasPapers.length===base.length && getLivingAtlasChecked()===checked && !livingAtlasPapers.some(p=>p.pmid==='91000104'));
  check('A failed newer inventory and an older corpus keep distinct count provenance',missing.pubmedQueryMatchCount===base.length+1 &&
    missing.liveRecordCount===base.length && missing.recordCountDifference===1 && missing.retrievalCompleteness==='different-snapshots' &&
    missing.processedRecordsRetrievedAt===checked);
  mode='missing-efetch';
  const omitted=await fetchPubMedStats(true);
  check('An omitted EFetch record is distinguished from a present citation with no abstract',
    omitted.error.includes('EFetch citations') && livingAtlasPapers.length===base.length && getLivingAtlasChecked()===checked);
  mode='processing-error';
  mergeLivingAtlasRecords=(...args)=>originalMerge(...args).map((p,i)=>i? p:Object.assign({},p,{pmid:'91999999'}));
  const corrupt=await fetchPubMedStats(true);mergeLivingAtlasRecords=originalMerge;
  check('A same-count but wrong-PMID processed corpus is rejected',corrupt.error.includes('processed corpus') &&
    localStorage.getItem(livingAtlasStorageKey('papers_v1'))===persisted && getLivingAtlasChecked()===checked);
  let duplicateRejected=false;try{validatePubMedCorpus([{pmid:base[0]},{pmid:base[0]}],base.slice(0,2));}catch(e){duplicateRejected=true;}
  check('Duplicate processed PMIDs are explicitly rejected',duplicateRejected);
  mode='recovery';
  await refreshPubMedAnalytics();
  const recovered=_pubmedCache;
  check('Later complete retrieval restores synchronised status and accurate counts',recovered.pubmedQueryMatchCount===inventory().length &&
    recovered.liveRecordCount===inventory().length && recovered.recordCountDifference===0 && recovered.retrievalCompleteness==='complete' &&
    recovered.snapshotId!==snapshot && !getLivingAtlasError() && analyticsSourceMeta(recovered).badge.includes('Synchronised complete'));
  check('The Analytics refresh control returns to its usable state after recovery',
    !document.getElementById('analytics-refresh-btn').disabled && document.getElementById('analytics-refresh-btn').textContent==='Refresh PubMed data');
  _pubmedCache=null;
  const cached=await fetchPubMedStats();
  check('Reloaded valid statistics are labelled cached while preserving successful timestamps',
    cached.source==='cached-live' && cached.processedRecordsRetrievedAt===recovered.processedRecordsRetrievedAt && analyticsSourceMeta(cached).badge.includes('Cached complete'));
  const topicFetcher=fetchExactTopicPubMedEvidence;
  fetchExactTopicPubMedEvidence=async()=>{throw Error('Synthetic topic-query outage');};
  const topicFailure=await fetchPubMedStats(true);
  check('Independent topic-query failures do not invalidate a complete corpus',topicFailure.retrievalCompleteness==='complete' &&
    !topicFailure.error && !!topicFailure.topicQueryError && !!topicFailure.topicCountsRetrievedAt);
  fetchExactTopicPubMedEvidence=topicFetcher;
  let release;const beforeSearches=searches;
  fetchLivingAtlas=async url=>{
    if(new URL(url).pathname.endsWith('esearch.fcgi'))await new Promise(resolve=>release=resolve);
    return mocked(url);
  };
  const first=refreshLivingAtlasFromPubMed(true),second=refreshLivingAtlasFromPubMed(true);
  await Promise.resolve();release();await Promise.all([first,second]);
  check('Concurrent refresh requests await one completed inventory',searches===beforeSearches+1 && !getLivingAtlasError());
  fetchLivingAtlas=mocked;_pubmedCache=null;await renderAnalytics();
  check('Analytics presents query and processed denominators separately from Browse Papers',
    !!document.getElementById('pubmed-processed-n') && document.getElementById('analytics-provenance').textContent.includes('Browse Papers is your local collection'));
  fetchLivingAtlas=originalFetch;fetchExactTopicPubMedEvidence=originalTopics;
  return {passed:checks.every(c=>c.passed),checks,scope:'Synthetic responses only; exact inventory reconciliation, unknown metadata, overlapping topics, legacy/mixed caches, failures, concurrency and recovery.'};
}"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', type=Path, default=Path('LipoScope.html'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--live', action='store_true', help='Run a real-service smoke test instead of synthetic scenarios')
    args = parser.parse_args()
    with ExitStack() as stack:
        html = args.html.resolve()
        handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(html.parent), **k)
        server = stack.enter_context(socketserver.TCPServer(('127.0.0.1', 0), handler))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        stack.callback(server.shutdown)
        playwright = stack.enter_context(sync_playwright())
        browser = playwright.chromium.launch(headless=True)
        stack.callback(browser.close)
        context = browser.new_context()
        if args.live:
            # Isolate this smoke test from default-corpus and figure enrichment timers.
            context.add_init_script('''(()=>{const original=window.setTimeout;window.setTimeout=(fn,delay,...args)=>[900,1500,4500].includes(delay)?0:original(fn,delay,...args);})();''')
        page = context.new_page()
        allowed = ('http://127.0.0.1:', 'data:', 'blob:') + (('https://eutils.ncbi.nlm.nih.gov/',) if args.live else ())
        page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(allowed) else route.abort())
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'http://127.0.0.1:{server.server_address[1]}/{html.name}', wait_until='domcontentloaded')
        report = page.evaluate(LIVE_CHECKS if args.live else CHECKS)
        report['page_errors'] = errors
        report['passed'] = report['passed'] and not errors
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(json.dumps(report, indent=2))
        return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
