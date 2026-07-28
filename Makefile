.PHONY: test smoke quick notebooks

PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
RUN_ENV = PYTHONPATH=src MPLCONFIGDIR=.cache/matplotlib XDG_CACHE_HOME=.cache

test:
	$(RUN_ENV) $(PYTHON) -m unittest discover -s tests -v

smoke:
	$(RUN_ENV) $(PYTHON) scripts/reproduce.py --profile smoke

quick:
	$(RUN_ENV) $(PYTHON) scripts/reproduce.py --profile quick

notebooks:
	$(RUN_ENV) $(PYTHON) scripts/execute_notebooks.py
