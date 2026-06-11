PYTHON ?= python3

.PHONY: install test demo scan verify

install:
	$(PYTHON) -m pip install --quiet .

test:
	$(PYTHON) -m unittest discover -s tests -v

demo:
	$(PYTHON) scripts/demo.py

scan:
	$(PYTHON) scripts/public_safety_scan.py --term "$${BANNED_TERM:-}"

verify: test demo scan
