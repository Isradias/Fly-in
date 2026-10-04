.PHONY: install run debug clean lint lint-strict test

PYTHON := python3

install:
	$(PYTHON) -m pip install -r requirements-dev.txt

run:
	$(PYTHON) -m flyin $(MAP) $(ARGS)

debug:
	$(PYTHON) -m pdb -m flyin $(MAP)

clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache .coverage

lint:
	flake8 --jobs=1 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 --jobs=1 .
	mypy . --strict

test:
	$(PYTHON) -m unittest discover -s tests
