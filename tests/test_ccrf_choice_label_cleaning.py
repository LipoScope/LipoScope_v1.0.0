import json
import subprocess


def _run_ccrf_engine(html_text, assertions):
    marker = html_text.index('/* LipoScope CCRF Engine')
    start = html_text.index('(function(root,factory){', marker)
    end = html_text.index('/* LipoScope CCRF user interface', start)
    script = html_text[start:end] + '\n' + assertions
    result = subprocess.run(
        ['node'], input=script, text=True, capture_output=True, check=True
    )
    return json.loads(result.stdout)


def test_choice_markup_is_cleaned_for_readable_outputs_not_source_dictionary(ccrf, html_text):
    source_choices = ccrf['classifications']['exploratory']['fields']
    source_choices = next(f for f in source_choices if f['variable'] == 'liq_bfl')['choices']
    assert '<b>No impairment </b>' in source_choices

    result = _run_ccrf_engine(
        html_text,
        r"""
const raw = '0, <b>No impairment</b> | 1, <b>Mild (present <25% of time)</b>';
const field = {variable:'severity', form:'Test', type:'radio', choices:raw};
const parsed = CCRFEngine.parseChoices(raw);
process.stdout.write(JSON.stringify({
  parsedLabel: parsed[1].label,
  cleanedText: CCRFEngine.cleanText(parsed[1].label),
  readableLabel: CCRFEngine.responseLabelForCsv(field, '1'),
  dictionaryChoices: CCRFEngine.dictionaryRows({fields:[field]})[1][5]
}));
""",
    )

    assert result == {
        'parsedLabel': '<b>Mild (present <25% of time)</b>',
        'cleanedText': 'Mild (present <25% of time)',
        'readableLabel': 'Mild (present <25% of time)',
        'dictionaryChoices': '0, <b>No impairment</b> | 1, <b>Mild (present <25% of time)</b>',
    }


def test_all_builder_choice_presentations_use_cleaned_labels(html_text):
    assert html_text.count('ccrfEsc(CCRFEngine.cleanText(c.label))') == 4
