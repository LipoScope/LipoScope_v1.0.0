#!/usr/bin/env python3
"""Fetch or reproducibly embed evidence for the existing default PubMed records."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from xml.etree import ElementTree as ET

import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
START = '/* BEGIN LIPOSCOPE_DEFAULT_PUBMED */'
END = '/* END LIPOSCOPE_DEFAULT_PUBMED */'
EUTILS = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def text(node):
    return ' '.join(''.join(node.itertext()).split()) if node is not None else ''


def embed_snapshot(html, snapshot):
    compact = json.dumps(snapshot, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    block = START + '\nvar DEFAULT_PUBMED_SNAPSHOT = ' + compact + ';\n' + END
    if START in html:
        pattern = re.escape(START) + r'.*?' + re.escape(END)
        updated, count = re.subn(pattern, lambda _: block, html, flags=re.S)
        if count != 1:
            raise ValueError('Expected one default PubMed metadata block')
        return updated
    marker = 'const PAPERS = ['
    if html.count(marker) != 1:
        raise ValueError('Expected one fixed-paper declaration')
    return html.replace(marker, block + '\n\n' + marker, 1)


class Retrieval:
    def __init__(self, cache):
        self.cache = cache
        cache.mkdir(parents=True, exist_ok=True)
        self.last_request = 0
        self.session = requests.Session()

    def get(self, utility, parameters, name):
        """Cache successful responses with their actual request time; <=2.5/s."""
        raw_path, info_path = self.cache / name, self.cache / (name + '.json')
        request_url = requests.Request('GET', EUTILS + utility, params={**parameters, 'tool': 'LipoScope'}).prepare().url
        if info_path.exists() and json.loads(info_path.read_text(encoding='utf-8')).get('url') != request_url:
            # Keep earlier raw evidence when a later request uses another set
            # of identifiers; never reuse a batch merely by its ordinal number.
            suffix = sha(request_url.encode())[:12]
            raw_path = raw_path.with_name(raw_path.stem + '_' + suffix + raw_path.suffix)
            info_path = raw_path.with_name(raw_path.name + '.json')
        if raw_path.exists() and info_path.exists():
            info = json.loads(info_path.read_text(encoding='utf-8'))
            if info.get('url') == request_url and sha(raw_path.read_bytes()) == info['sha256']:
                return raw_path.read_bytes(), info
        for attempt in range(3):
            time.sleep(max(0, .4 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            try:
                response = self.session.get(EUTILS + utility, params={**parameters, 'tool': 'LipoScope'}, timeout=60)
                response.raise_for_status()
                raw = response.content
                if parameters.get('retmode') == 'json':
                    parsed = response.json()
                    if parsed.get('error') or parsed.get('esearchresult', {}).get('ERROR'):
                        raise ValueError('NCBI returned a query error')
                else:
                    parsed = ET.fromstring(raw)
                    if parsed.tag == 'ERROR' or parsed.find('.//ERROR') is not None:
                        raise ValueError('NCBI returned an XML error')
                info = dict(url=response.url, retrievedAt=utc_now(), sha256=sha(raw))
                raw_path.write_bytes(raw)
                dump(info_path, info)
                return raw, info
            except (requests.RequestException, ValueError, ET.ParseError):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)


def bibliography(article):
    citation = article.find('MedlineCitation')
    if citation is None:
        citation = article.find('BookDocument')
    if citation is None:
        raise ValueError('PubMed record has no citation document')
    pmid = text(citation.find('PMID'))
    source = citation.find('Article')
    if source is None:
        source = citation
    title = text(source.find('ArticleTitle'))
    authors = []
    for author in source.findall('AuthorList/Author'):
        collective = text(author.find('CollectiveName'))
        name = ' '.join(filter(None, [text(author.find('LastName')), text(author.find('Initials'))]))
        if collective or name:
            authors.append(collective or name)
    # Reference lists contain ArticleId elements too; only the citation's own
    # top-level identifiers establish its DOI/PMCID identity.
    id_list = article.find('PubmedData/ArticleIdList')
    if id_list is None:
        id_list = article.find('PubmedBookData/ArticleIdList')
    ids = {node.get('IdType'): text(node) for node in id_list} if id_list is not None else {}
    return dict(pmid=pmid, title=title, authors=', '.join(authors),
                firstAuthor=authors[0] if authors else '', lastAuthor=authors[-1] if authors else '',
                doi='https://doi.org/' + ids['doi'] if ids.get('doi') else '',
                pmcid=ids.get('pmc', ''),
                copyrightInformation=text(source.find('Abstract/CopyrightInformation')))


def pmc_evidence(article, record):
    ids = {n.get('pub-id-type'): text(n) for n in article.findall('front/article-meta/article-id')}
    if ids.get('pmid') != record['pmid']:
        return None
    pmc = re.sub(r'^PMC', '', record['pmcid'], flags=re.I)
    source_pmc = ids.get('pmcid') or ids.get('pmc') or ids.get('pmcaid')
    if not source_pmc or re.sub(r'^PMC', '', source_pmc, flags=re.I) != pmc:
        return None
    if ids.get('doi') and record.get('doi') and ids['doi'].casefold() != record['doi'].removeprefix('https://doi.org/').casefold():
        return None
    sections = {}
    parents = {child: parent for parent in article.iter() for child in parent}
    def paragraph_text(section):
        paragraphs = []
        for paragraph in section.iter('p'):
            node = parents.get(paragraph)
            while node is not None and node is not section and node.tag not in {'fig', 'table-wrap', 'ref-list', 'supplementary-material'}:
                node = parents.get(node)
            if node is section:
                paragraphs.append(text(paragraph))
        return ' '.join(paragraphs)
    for section in article.findall('body//sec'):
        label = (section.get('sec-type', '') + ' ' + text(section.find('title'))).strip()
        key = None
        if re.search(r'\b(methods?|materials?|study design)\b', label, re.I):
            key = 'METHODS'
        elif re.search(r'\bresults?\b', label, re.I):
            key = 'RESULTS'
        elif re.search(r'\bconclusions?\b', label, re.I):
            key = 'CONCLUSIONS'
        if key and key not in sections:
            # Paragraph text from the labelled section, without figure/table or
            # reference-list text. These are inputs to the existing classifiers.
            sections[key] = paragraph_text(section)
    return dict(jatsArticleType=article.get('article-type', ''), fullTextSections=sections)


def fetch_snapshot(html, cache):
    retrieval = Retrieval(cache)
    # Use the application's own XML parser and normalization, not a parallel
    # metadata interpretation or classification implementation.
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.route('**/*', lambda route: route.abort())
            page.evaluate("""() => {
              const values=new Map(), storage={getItem:k=>values.get(k)||null,
                setItem:(k,v)=>values.set(k,String(v)),removeItem:k=>values.delete(k)};
              Object.defineProperty(window,'localStorage',{value:storage});
              Object.defineProperty(window,'sessionStorage',{value:storage});
            }""")
            page.set_content(html, wait_until='load')
            inputs = page.evaluate("""() => ({pmids:PAPERS.concat(DEFAULT_EXPANDED_PAPERS).map(p=>String(p.pmid)),
              queries:Object.fromEntries(Object.entries(TOPIC_DEFINITIONS).map(([k,v])=>[k,v.pubMedQuery])),
              topicVersion:TOPIC_CLASSIFIER_VERSION,typeVersion:PUBMED_TYPE_CLASSIFIER_VERSION,
              previousRecords:typeof DEFAULT_PUBMED_SNAPSHOT==='undefined'?{}:DEFAULT_PUBMED_SNAPSHOT.records})""")
            pmids = inputs['pmids']
            assert len(pmids) == len(set(pmids)) == 200
            records = {}
            sources = []
            for offset in range(0, len(pmids), 50):
                ids = pmids[offset:offset + 50]
                raw, info = retrieval.get('efetch.fcgi', dict(db='pubmed', id=','.join(ids), retmode='xml'), f'pubmed_{offset:03}.xml')
                sources.append(info)
                parsed = page.evaluate('xml => parsePubMedAbstractXmlByPmid(xml, true)', raw.decode('utf-8'))
                nodes = {text(n.find('MedlineCitation/PMID') if n.tag == 'PubmedArticle' else n.find('BookDocument/PMID')): n
                         for n in ET.fromstring(raw) if n.tag in {'PubmedArticle', 'PubmedBookArticle'}}
                missing = set(ids) - nodes.keys()
                if missing:
                    raise ValueError('Requested PubMed records not returned; snapshot not replaced: ' + ','.join(sorted(missing)))
                for pmid in ids:
                    meta = parsed[pmid]
                    record = bibliography(nodes[pmid])
                    assert record['pmid'] == pmid and record['title']
                    record.update({k: v for k, v in meta.items() if k not in {'fullText', 'sections', 'journal', 'metadataCheckedAt'}})
                    record.update(abstractSections=meta['sections'], journal=meta['journal']['title'],
                                  journalMetadata=meta['journal'], year=meta['publicationYear'],
                                  pubMedMetadataCheckedAt=int(datetime.fromisoformat(info['retrievedAt']).timestamp() * 1000),
                                  pubMedEvidenceProvenance=dict(source='NCBI PubMed EFetch', identityVerified=True,
                                      retrievedAt=info['retrievedAt'], responseSha256=info['sha256'], url=info['url']))
                    record['pmcid'] = bibliography(nodes[pmid])['pmcid']
                    record['pubMedEvidenceProvenance']['abstractTextFormat'] = 'xml-text-content'
                    record['pubMedEvidenceProvenance']['fieldStatus'] = {
                        key: 'present' if record.get(key) else 'absent-in-returned-record'
                        for key in ['abstractText', 'meshHeadings', 'publicationTypes', 'keywords', 'chemicals', 'supplementaryConcepts', 'pmcid']}
                    records[pmid] = record
                print(f'PubMed: {offset + len(ids)}/200 verified', flush=True)
            queries = {}
            for index, (topic, query) in enumerate(inputs['queries'].items()):
                raw, info = retrieval.get('esearch.fcgi', dict(db='pubmed', term=query, retmax=9999, retmode='json'), f'topic_{index:02}.json')
                result = json.loads(raw)['esearchresult']
                ids = result['idlist']
                if len(ids) != len(set(ids)) or len(ids) != int(result['count']):
                    raise ValueError('Incomplete topic query inventory: ' + topic)
                members = set(ids)
                queries[topic] = dict(query=query, count=len(ids), matchingStartingPmids=[p for p in pmids if p in members], **info)
                print('Topic membership verified: ' + topic, flush=True)
            for pmid, record in records.items():
                record['topicQueryMembership'] = [topic for topic, result in queries.items() if pmid in result['matchingStartingPmids']]
                record['topicQueryEvidence'] = dict(status='complete', retrievedAt=max(q['retrievedAt'] for q in queries.values()))
            pmc_records = [p for p in records.values() if p.get('pmcid')]
            for offset in range(0, len(pmc_records), 10):
                batch = pmc_records[offset:offset + 10]
                try:
                    raw, info = retrieval.get('efetch.fcgi', dict(db='pmc', id=','.join(p['pmcid'].removeprefix('PMC') for p in batch), retmode='xml'), f'pmc_{offset:03}.xml')
                    root = ET.fromstring(raw)
                    articles = root.findall('.//article') if root.tag != 'article' else [root]
                    for record in batch:
                        verified = [a for a in articles if pmc_evidence(a, record) is not None]
                        if len(verified) == 1:
                            record.update(pmc_evidence(verified[0], record))
                            record['fullTextEvidenceSource'] = 'Identity-verified NCBI PMC JATS'
                            record['pmcEvidenceProvenance'] = dict(status='verified', **info)
                        else:
                            record['pmcEvidenceProvenance'] = dict(status='not-returned-or-identity-unverified', **info)
                except (requests.RequestException, ValueError, ET.ParseError) as error:
                    for record in batch:
                        record['pmcEvidenceProvenance'] = dict(status='retrieval-failed', checkedAt=utc_now(), error=str(error))
                print(f'PMC checked: {offset + len(batch)}/{len(pmc_records)}', flush=True)
            for pmid, record in records.items():
                prior = inputs['previousRecords'].get(pmid, {})
                if (record.get('pmcEvidenceProvenance', {}).get('status') != 'verified' and
                    prior.get('pmcEvidenceProvenance', {}).get('status') == 'verified' and prior.get('pmcid') == record.get('pmcid')):
                    attempt = record.get('pmcEvidenceProvenance', {})
                    for key in ['jatsArticleType', 'fullTextSections', 'fullTextMethods', 'fullTextResults', 'fullTextConclusions', 'fullTextEvidenceSource']:
                        if key in prior:
                            record[key] = prior[key]
                    record['pmcEvidenceProvenance'] = {**prior['pmcEvidenceProvenance'], 'lastRefreshAttempt': attempt, 'retainedPriorEvidence': True}
            retrieval_times = [s['retrievedAt'] for s in sources] + [q['retrievedAt'] for q in queries.values()]
            retrieval_times.extend(p['pmcEvidenceProvenance']['retrievedAt'] for p in records.values()
                                   if p.get('pmcEvidenceProvenance', {}).get('retrievedAt'))
            return dict(schemaVersion='default-pubmed-evidence-1', createdAt=utc_now(),
                        retrievalStartedAt=min(retrieval_times), retrievalCompletedAt=max(retrieval_times),
                        scope='Existing 200 default PMIDs; current publication metadata snapshot',
                        classifierVersions=dict(topic=inputs['topicVersion'], studyType=inputs['typeVersion']),
                        pubmedSources=sources, topicQueries=queries, records=records)
        finally:
            browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true', help='Retrieve a new dated snapshot before embedding')
    parser.add_argument('--snapshot', type=Path, default=ROOT / 'data/default_pubmed_snapshot.json')
    parser.add_argument('--cache-dir', type=Path, default=ROOT / '.local/pubmed_snapshot')
    parser.add_argument('--template', type=Path, default=ROOT / 'templates/LipoScope.template.html')
    args = parser.parse_args()
    html = args.template.read_text(encoding='utf-8')
    if args.fetch:
        snapshot = fetch_snapshot(html, args.cache_dir)
        dump(args.snapshot, snapshot)  # Only replace the prior snapshot after verification.
    else:
        snapshot = json.loads(args.snapshot.read_text(encoding='utf-8'))
    updated = embed_snapshot(html, snapshot)
    for path in [args.template, ROOT / 'LipoScope.html', ROOT / 'releases/LipoScope_v1.0.0.html']:
        path.write_text(updated, encoding='utf-8', newline='\n')
    print(f'Embedded {len(snapshot["records"])} default PubMed evidence records; retrieved {snapshot["createdAt"]}')


if __name__ == '__main__':
    main()
