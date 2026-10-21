from bs4 import BeautifulSoup


def test_main_tabs_and_panels(html_text):
    soup=BeautifulSoup(html_text,'html.parser')
    panels={x.get('id') for x in soup.select('.panel')}
    assert {'panel-browse','panel-analytics','panel-ccrf','panel-live','panel-about','panel-resources'} <= panels
    assert len([x for x in soup.select('.panel') if 'active' in (x.get('class') or [])])==1
    assert soup.find(id='nav-ccrf') is not None


def test_ccrf_workspace_order(html_text):
    soup=BeautifulSoup(html_text,'html.parser')
    ids=[x.get('id') for x in soup.select('#panel-ccrf .atlas-section')]
    assert ids==['ccrf-section-overview','ccrf-section-builder','ccrf-section-gaps','ccrf-section-dataset']
    assert soup.find(id='ccrf-workspace-start') is not None


def test_start_here_is_task_guided_and_has_no_condition_visuals(html_text):
    soup=BeautifulSoup(html_text,'html.parser')
    resources=soup.find(id='panel-resources')
    assert resources is not None
    text=resources.get_text(' ',strip=True)
    assert 'Visual Guides to Lipoedema' not in text
    assert 'Lipoedema Biology Explainer Video' not in text
    assert 'Guided App Walkthrough' in text
    assert len(resources.select('#walkthrough-stage .walkthrough-slide'))==5
    assert 'Find and review papers' in text
    assert 'Prepare a CCRF research record' in text


def test_version_header_and_date(html_text):
    assert "const LIPOSCOPE_VERSION = 'v1.0.0'" in html_text
    assert "const LIPOSCOPE_UPDATED = '22 October 2026'" in html_text
    assert 'An open research workbench for lipoedema literature discovery, PubMed monitoring, and standardised CCRF data collection' in html_text


def test_no_duplicate_html_ids(html_text):
    soup=BeautifulSoup(html_text,'html.parser')
    ids=[x.get('id') for x in soup.find_all(attrs={'id':True})]
    assert len(ids)==len(set(ids))
