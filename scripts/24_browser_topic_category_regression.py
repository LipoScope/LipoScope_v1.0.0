#!/usr/bin/env python3
"""Check topic renaming, legacy storage and non-CCRF tabs with synthetic records."""
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


SEED = """() => {
  if (localStorage.getItem('topic_revision_seeded')) return;
  localStorage.setItem('topic_revision_seeded', '1');
  const legacy = (id, title) => ({
    id, title, topic:'Unsupported records', type:'Unclassified / Other',
    year:2026, journal:'Synthetic journal', authors:'Test Author',
    summary:'General observations.', findings:[], color:'#888888',
    customNote:'Unsupported records is a quoted phrase.',
    topicClassification:{topic:'Unsupported records', primaryTopic:'Unsupported records',
      unsupported:true, unsupportedReason:'no-category-specific-evidence',
      resolutionReason:'no-category-specific-evidence', secondaryTopics:[],
      evidence:[{source:'unsupported',value:'No category-specific evidence'}]}
  });
  localStorage.setItem('lip_default_user_papers_v3', JSON.stringify([legacy(880000001,'Observations in lipedema')]));
  localStorage.setItem('lip_default_expanded_default_papers_v1', JSON.stringify([legacy(880000002,'Additional observations in lipedema')]));
  localStorage.setItem('liposcope_living_atlas_complete_v3_papers_v1', JSON.stringify([legacy(880000003,'Further observations in lipedema')]));
  localStorage.setItem('liposcope_living_atlas_complete_v3_checked_v1','123456789');
  localStorage.setItem('topic_revision_ccrf_sentinel', JSON.stringify({responses:{study_id:'test-only'}}));
  localStorage.setItem('liposcope_pubmed_stats_live_v7_expanded_disease_query', JSON.stringify({
    source:'live', fetchedAt:Date.now(), checkedAt:123456789,
    total:3, recentCount:3, uniqueJournals:1, minYear:'2026',
    byYear:{'2026':3}, byTopic:{'Genetics & Genomics':1},
    classifiedTopicCounts:{'Genetics & Genomics':1},
    unsupportedTopicCount:2, unsupportedTopicReasons:{'no-category-specific-evidence':2},
    byStudyType:{'Unclassified / Other':3}, unclassifiedTypeReasons:{},
    byJournal:{'Synthetic journal':3}, topicPubMedURLs:{}, liveRecordCount:3
  }));
}"""


CHECKS = """async () => {
  const checks=[];
  const check=(name,passed)=>checks.push({name,passed:!!passed});
  const label='Unresolved category';
  const legacyText=/unsupported records|unspported records/i;
  const classifier=runTopicClassifierValidationTests();
  check('Existing topic-classifier scenarios retain their expected categories', classifier.passed===classifier.total);
  const fallback=classifyPaperTopicDetailed('Observations in lipedema','General observations.',{});
  check('New classifier output uses the new label and property names',
    fallback.topic===label && fallback.primaryTopic===label && fallback.unresolved===true &&
    !!fallback.unresolvedReason && !('unsupported' in fallback) && !('unsupportedReason' in fallback));
  const ambiguous=classifyPaperTopicDetailed('Molecular biology of lipedema','',{
    publicationTypes:[{label:'Journal Article'}],topicQueryMembership:['Adipose Biology','Pathophysiology']});
  check('Equivalent topic evidence retains its abstention reason',
    ambiguous.topic===label && ambiguous.unresolvedReason==='multiple-equivalent-topic-evidence');
  check('Ten research topics remain unchanged',Object.keys(TOPIC_DEFINITIONS).length===10);
  for (const suffix of ['user_papers_v3','expanded_default_papers_v1']) {
    const records=JSON.parse(localStorage.getItem('lip_default_'+suffix));
    const paper=records.find(p=>p.id===880000001 || p.id===880000002);
    check('Legacy '+suffix+' migrates and remains saved',paper && paper.topic===label &&
      paper.topicClassification.primaryTopic===label && paper.topicClassification.unresolved===true &&
      !('unsupported' in paper.topicClassification) && paper.customNote==='Unsupported records is a quoted phrase.');
  }
  const live=JSON.parse(localStorage.getItem(livingAtlasStorageKey('papers_v1')))[0];
  check('Cached live records migrate without advancing retrieval time',live.topic===label && getLivingAtlasChecked()===123456789);
  const stats=loadStoredPubMedStats();
  check('Cached Analytics counts and reasons survive the property rename',stats.unresolvedTopicCount===2 &&
    stats.unresolvedTopicReasons['no-category-specific-evidence']===2 && stats.checkedAt===123456789 &&
    !('unsupportedTopicCount' in stats) && !('unsupportedTopicReasons' in stats));
  const savedStats=JSON.parse(localStorage.getItem(pubMedStatsStorageKey('live_v7_expanded_disease_query')));
  check('Renamed Analytics fields are persisted',savedStats.unresolvedTopicCount===2 && !('unsupportedTopicCount' in savedStats));
  const mapped=normalizeStoredTopicStats({unsupportedTopicCount:2,
    byTopic:{'Unsupported records':2},classifiedTopicCounts:{'Unsupported records':2}});
  check('Legacy chart map keys migrate without losing counts',mapped.byTopic[label]===2 && mapped.classifiedTopicCounts[label]===2 && !('Unsupported records' in mapped.byTopic));
  check('Legacy shared records and misspelled labels use the new category',
    buildShareSafePaper({topic:'Unsupported records'}).topic===label &&
    assignSharedIdsToInline([{topic:'Unspported records',title:'Shared test'}],990000000)[0].topic===label);
  const fresh=buildPubMedStatsFromLiveRecords([
    {pmid:'999999998',title:'Observations in lipedema',abstractText:'General observations.',year:2026,journal:'Synthetic journal'}
  ],1,1);
  check('Fresh Analytics reports count unresolved records under the new properties',fresh.unresolvedTopicCount===1 &&
    Object.values(fresh.unresolvedTopicReasons).reduce((a,b)=>a+b,0)===1 && !('unsupportedTopicCount' in fresh));
  await renderAnalytics();
  check('Analytics displays the category, count and explanation',document.getElementById('chart-topics').textContent.includes(label) &&
    document.getElementById('chart-topics').textContent.includes('Why records remain in the Unresolved category:'));
  for (const tab of ['resources','browse','live','analytics','about']) {
    document.getElementById('nav-'+tab).click();
    check(tab+' tab opens with no legacy topic labels',document.getElementById('panel-'+tab).classList.contains('active') &&
      !legacyText.test(document.getElementById('panel-'+tab).textContent));
  }
  document.getElementById('nav-browse').click();
  updateFilterDropdowns(getAllPapers());
  document.getElementById('f-topic').value=label;
  filterPapers();
  check('Browse filter selects migrated unresolved records',filteredPapers.length===2 && filteredPapers.every(p=>p.topic===label));
  openModal(880000001);
  check('Paper details display the new category and reason',document.getElementById('modal-meta').textContent.includes(label) &&
    document.getElementById('modal-meta').textContent.includes('No category-specific evidence'));
  closeModalDirect();
  document.getElementById('nav-live').click();
  const originalAbstract=fetchPubMedAbstract;
  fetchPubMedAbstract=async()=>({abstractText:'General observations.',fullText:'General observations.',sections:{}});
  await addPaperFromLive({pmid:'999999999',title:'Synthetic observations in lipedema',authors:'Test Author',journal:'Synthetic journal',year:2026});
  fetchPubMedAbstract=originalAbstract;
  check('Live Search imports use the new category',userPapers.some(p=>p.pmid==='999999999' && p.topic===label && p.topicClassification.unresolved));
  const originalSearch=searchPubMedForTopic;
  searchPubMedForTopic=async()=>({totalHits:0,papers:[]});
  document.querySelectorAll('.disc-topic-cb').forEach((cb,i)=>cb.checked=i===0);
  await runAutoDiscovery();
  searchPubMedForTopic=originalSearch;
  check('Auto-Discovery results use the new wording',document.getElementById('disc-results-body').textContent.includes(label) &&
    !legacyText.test(document.getElementById('disc-results-body').textContent));
  check('Unrelated CCRF storage is untouched',localStorage.getItem('topic_revision_ccrf_sentinel')===JSON.stringify({responses:{study_id:'test-only'}}));
  return {passed:checks.every(c=>c.passed),checks,
    scope:'Five non-CCRF tabs, classifier output, legacy local/cache/shared data, and imports. All records and responses are synthetic.'};
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
        context = browser.new_context()
        context.add_init_script('(' + SEED + ')();')
        page = context.new_page()
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
