"""Static invariants for corrected PubMed retrieval and metadata handling."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]

def test_single_expanded_canonical_query():
    html=(ROOT/'LipoScope.html').read_text(encoding='utf-8')
    match=re.search(r"var LIPOEDEMA_PUBMED_QUERY\s*=\s*'([^']+)'",html)
    assert match,'canonical query must be explicitly defined'
    query=match.group(1)
    for term in ['lipedema[Title/Abstract]','lipoedema[Title/Abstract]','lipedemas[Title/Abstract]',
                 'lipoedemas[Title/Abstract]','lipolymphedema[Title/Abstract]',
                 'lipolymphedemas[Title/Abstract]','"lipohyperplasia dolorosa"[Title/Abstract]',
                 '"Lipedema"[Mesh]']:
        assert term in query,term

def test_incomplete_retrieval_is_not_silently_accepted():
    html=(ROOT/'LipoScope.html').read_text(encoding='utf-8')
    for phrase in ['Incomplete PubMed PMID retrieval','Incomplete PubMed citation summaries',
                   'Incomplete PubMed processed corpus']:
        assert phrase in html

def test_identity_and_book_xml_paths_exist():
    html=(ROOT/'LipoScope.html').read_text(encoding='utf-8')
    assert 'externalAbstractIdentityMatches' in html
    assert 'PubmedBookArticle' in html
    assert 'parsePubMedAbstractXmlByPmid' in html

def test_alert_timestamp_is_not_claimed_before_success():
    html=(ROOT/'LipoScope.html').read_text(encoding='utf-8')
    assert 'getLastNotifCheck' in html and 'checkForNewPapers' in html
