import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_calculated_fields_are_preserved_without_inferred_formulas(ccrf):
    variables = set()
    total = 0
    for cls in ccrf['classifications'].values():
        calculated = [field for field in cls['fields'] if field['type'] == 'calc']
        total += len(calculated)
        variables.update(field['variable'] for field in calculated)
        assert cls['calculatedRows'] == len(calculated)
        assert cls['calculationExpressionRows'] == 0
        assert all(not field.get('choices') for field in calculated)
    assert total == 37  # cumulative rows across the four overlapping dictionaries
    assert variables == {
        'age', 'beighton_score', 'beight_over50', 'beight_49under', 'bmi',
        'waist_hip_ratio', 'waist_height_ratio', 'age_onset', 'soaal_rapprich',
        'she_current_calc', 'she_current_percep', 'she_prior_calc', 'she_prior_percep',
    }
    assert 'does not calculate those values' in ccrf['source']['calculationPolicy']


def test_calculation_audit_matches_schema():
    report = json.loads((ROOT / 'validation/ccrf_calculated_fields.json').read_text(encoding='utf-8'))
    assert report['passed']
    assert report['official_expression_rows'] == 0
    assert report['calculated_rows_across_cumulative_dictionaries'] == 37


def test_html_discloses_calculation_source_limit(html_text):
    assert 'The official data dictionary does not provide the calculation expression' in html_text
    assert 'LipoScope leaves this value unavailable rather than inferring a formula' in html_text
