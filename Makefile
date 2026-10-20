# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT

# Every target runs what CI runs, from the same hash-pinned requirements.
# Install them first into a virtual environment:
#   pip install --require-hashes -r requirements/test.txt
#   pip install --no-deps -e .
.PHONY: help test lint format type-check audit verify-versions pip-compile benchmark examples check clean

PYTHON ?= python3
SOURCES = camt053_loader_mt940/ tests/ examples/ benches/ scripts/

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-14s\033[0m %s\n", $$1, $$2}'

test: ## Tests with the 100% line and branch coverage gate, and docstrings
	$(PYTHON) -m pytest tests/
	interrogate -c pyproject.toml camt053_loader_mt940

lint: ## Ruff lint and format check (needs requirements/lint.txt)
	ruff check $(SOURCES)
	ruff format --check $(SOURCES)

format: ## Apply ruff fixes and formatting
	ruff check --fix $(SOURCES)
	ruff format $(SOURCES)

type-check: ## mypy --strict over the package and scripts
	mypy camt053_loader_mt940/ scripts/

audit: ## pip-audit every hash-pinned requirements file (needs requirements/audit.txt)
	@for f in requirements/*.txt; do \
		echo "--- $$f"; \
		pip-audit --progress-spinner off --require-hashes --disable-pip -r "$$f" || exit 1; \
	done

verify-versions: ## Every restatement of the version agrees with pyproject.toml
	$(PYTHON) scripts/verify_versions.py

pip-compile: ## Regenerate hash-pinned requirements/*.txt from requirements/*.in
	@command -v uv >/dev/null || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
	@for f in requirements/*.in; do \
		echo "compiling $$f"; \
		uv pip compile --quiet --generate-hashes --universal \
			--python-version 3.10 "$$f" -o "$${f%.in}.txt"; \
	done

benchmark: ## Run the benchmark in quick mode
	$(PYTHON) benches/bench_parse_mt940.py --quick

examples: ## Run every example end to end
	@for example in examples/*.py; do echo "--- $$example"; $(PYTHON) "$$example" || exit 1; done

check: lint type-check verify-versions test benchmark examples ## Everything CI runs on a pull request

clean: ## Remove build artefacts and caches
	rm -rf build/ dist/ *.egg-info .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/ coverage.xml .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
