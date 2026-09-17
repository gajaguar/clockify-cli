UV := uv

LANG_INSTALL_TARGETS    += install-python
LANG_CHECK_TARGETS      += lint format-check typecheck pylint
LANG_FIX_TARGETS        += format lint-fix
LANG_FIX_UNSAFE_TARGETS += format lint-fix-unsafe
LANG_TEST_TARGETS       += pytest

##@ Python

install-python: ## Sync Python deps and register console scripts
	$(UV) sync
	$(UV) tool install --editable . --force

lint: ## Lint with Ruff — accepts FILES="..." to limit scope
	$(UV) run ruff check --preview $(or $(FILES),.)

format-check: ## Check formatting with Ruff, without writing — accepts FILES="..."
	$(UV) run ruff format --check --preview $(or $(FILES),.)

mypy: ## Type-check with mypy — accepts FILES="..." to limit scope
	$(UV) run mypy $(or $(FILES),.)

pyright: ## Type-check with Pyright — accepts FILES="..." to limit scope
	$(UV) run pyright $(or $(FILES),.)

typecheck: mypy pyright ## Run both type checkers

pylint: ## Self-lint with this repo's own checkers (see github.com/gajaguar/pylint-plugin) — accepts FILES="..."
	$(UV) run pylint $(or $(FILES),src tests)

format: ## Format code with Ruff — accepts FILES="..." to limit scope
	$(UV) run ruff format --preview $(or $(FILES),.)

lint-fix: ## Auto-fix lint issues with Ruff (safe fixes only) — accepts FILES="..."
	$(UV) run ruff check --fix --preview $(or $(FILES),.)

lint-fix-unsafe: ## Auto-fix lint issues with Ruff, including unsafe fixes — accepts FILES="..."
	$(UV) run ruff check --fix --preview --unsafe-fixes $(or $(FILES),.)

pytest: ## Run the test suite — accepts FILES="..." to limit scope
	$(UV) run pytest $(FILES)

coverage: ## Run tests with an HTML coverage report
	$(UV) run pytest --cov --cov-report=html

.PHONY: install-python lint format-check mypy pyright typecheck pylint \
	format lint-fix lint-fix-unsafe pytest coverage
