import json

OFFICIAL={
    'core':{'cdes':288,'clinical':86,'participant':202,'rows':300},
    'supplemental_highly_recommended':{'cdes':424,'clinical':89,'participant':335,'rows':445},
    'supplemental':{'cdes':618,'clinical':89,'participant':529,'rows':650},
    'exploratory':{'cdes':682,'clinical':120,'participant':562,'rows':739},
}

def test_ccrf_version_and_classifications(ccrf):
    assert ccrf['source']['ccrfVersion']=='Version 1'
    assert set(ccrf['classifications'])==set(OFFICIAL)
    assert 'delphiPaper' not in ccrf['source']

def test_ccrf_official_counts_and_source_checksums(ccrf):
    for key,expected in OFFICIAL.items():
        cls=ccrf['classifications'][key]
        assert cls['official_cdes']==expected['cdes']
        assert cls['clinical_cdes']==expected['clinical']
        assert cls['participant_cdes']==expected['participant']
        assert len(cls['fields'])==cls['dictionaryRows']==expected['rows']
        source=ccrf['source']['files'][key]
        assert source['dictionaryRows']==expected['rows']
        assert len(source['sha256'])==64

def test_ccrf_schema_matches_embedded_html(ccrf,html_text):
    compact=json.dumps(ccrf,ensure_ascii=False,separators=(',',':'))
    assert 'var CCRF_SCHEMA='+compact+';' in html_text
