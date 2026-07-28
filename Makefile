.PHONY: help setup test smoke quick paper notebooks

PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
RUN_ENV = PYTHONPATH=src MPLCONFIGDIR=.cache/matplotlib XDG_CACHE_HOME=.cache

help:
	@echo "Swappy reproduction commands"
	@echo "  make setup      create the environment and install dependencies"
	@echo "  make test       verify physics invariants and conventions"
	@echo "  make smoke      run the smallest end-to-end check"
	@echo "  make quick      reproduce the core story on a laptop"
	@echo "  make notebooks  execute and save both walkthroughs"
	@echo "  make paper      launch the resumable HPC-scale profile"

setup:
	python3 -m venv --system-site-packages .venv
	.venv/bin/python -m pip install -e ".[notebooks]"

test:
	$(RUN_ENV) $(PYTHON) -m unittest discover -s tests -v

smoke:
	$(RUN_ENV) $(PYTHON) -m swappy --profile smoke

quick:
	$(RUN_ENV) $(PYTHON) -m swappy --profile quick

paper:
	$(RUN_ENV) $(PYTHON) -m swappy --profile paper

notebooks:
	$(RUN_ENV) $(PYTHON) -m swappy --notebooks
