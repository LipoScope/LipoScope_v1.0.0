from pathlib import Path
import json
import pytest

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(scope='session')
def html_text():
    return (ROOT / 'LipoScope.html').read_text(encoding='utf-8')

@pytest.fixture(scope='session')
def ccrf():
    return json.loads((ROOT / 'data/ccrf_schema.json').read_text(encoding='utf-8'))
