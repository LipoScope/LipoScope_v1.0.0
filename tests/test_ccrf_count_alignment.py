import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OFFICIAL={
    'core':(288,86,202,300),
    'supplemental_highly_recommended':(424,89,335,445),
    'supplemental':(618,89,529,650),
    'exploratory':(682,120,562,739),
}

def test_official_cde_counts_and_dictionary_rows_are_distinct(ccrf):
    for key,(total,clinical,participant,rows) in OFFICIAL.items():
        cls=ccrf['classifications'][key]
        assert cls['official_cdes']==total
        assert cls['clinical_cdes']==clinical
        assert cls['participant_cdes']==participant
        assert clinical+participant==total
        assert cls['dictionaryRows']==len(cls['fields'])==rows

def test_count_source_is_recorded(ccrf):
    assert ccrf['source']['officialCountSource']=='https://www.lipedema.org/ccrf'
    assert ccrf['source']['officialCountAccessedDate']=='2026-08-02'
    assert 'REDCap dictionary-row counts' in ccrf['source']['notice']

def test_response_row_metadata_matches_actual_schema(ccrf):
    input_types={'text','notes','radio','dropdown','checkbox','slider','file'}
    for cls in ccrf['classifications'].values():
        response=sum(f['type'] in input_types for f in cls['fields'])
        required=sum(f['required'] and f['type'] in input_types for f in cls['fields'])
        assert cls['responseRows']==response
        assert cls['requiredResponseRows']==required

def test_html_explains_actual_counting_behavior(html_text):
    required=[
        'Completion below is calculated only from applicable required response fields',
        'it is not a percentage of all ',
        'Conditional questions appear only when their official branching conditions are met.',
        'Applicable required response completion',
        'Official CDE totals were checked against the Foundation webpage',
        'Conditional questions are included normally when their official branching conditions are met.',
    ]
    for phrase in required: assert phrase in html_text
    assert '2,134 CDEs' not in html_text

def test_validation_report_distinguishes_counts():
    report=json.loads((ROOT/'validation/ccrf_count_alignment.json').read_text())
    assert report['passed']
    assert report['cumulative_dictionary_rows_across_four_workbooks']==2134
    assert 'not a count of unique CDEs' in report['cumulative_count_note']
