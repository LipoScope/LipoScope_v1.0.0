PYTHON ?= python

.PHONY: install syntax embed-jszip test browser reports package

install:
	$(PYTHON) -m pip install -r requirements.lock
	$(PYTHON) -m playwright install chromium

syntax:
	$(PYTHON) -m py_compile scripts/ccrf/*.py scripts/*.py tests/*.py

embed-jszip:
	$(PYTHON) scripts/19_embed_jszip.py

test: syntax
	$(PYTHON) -m pytest -q

browser:
	$(PYTHON) scripts/18_browser_smoke_test.py --html LipoScope.html

reports:
	$(PYTHON) scripts/20_generate_validation_reports.py

package:
	$(PYTHON) scripts/21_build_distribution_archive.py
