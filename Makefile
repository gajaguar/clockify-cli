SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

NPM := pnpm

# Files to scope quality targets to. Accepts paths or globs.
# Usage: make lint FILES="src/foo.py src/bar.py"
FILES ?=

.DEFAULT_GOAL := help

# Extension points. Each language branch appends to these variables from its
# own mk/*.mk; main ships no mk/*.mk (only mk/.gitkeep), so main and the
# language branches never edit the same file.
LANG_INSTALL_TARGETS     :=
LANG_CHECK_TARGETS       :=
LANG_FIX_TARGETS         :=
LANG_FIX_UNSAFE_TARGETS  :=
LANG_TEST_TARGETS        :=

-include mk/*.mk

##@ Help

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Setup

install-tools: ## Install the toolchain pinned in mise.toml
	mise install

install-node: ## Install Node tooling (markdownlint-cli2, cspell) via pnpm
	$(NPM) install

setup-hooks: ## Install the pre-commit git hook
	pre-commit install

install: install-tools install-node $(LANG_INSTALL_TARGETS) setup-hooks ## Install everything

.PHONY: help install-tools install-node setup-hooks install

##@ Read-only checks (never mutate — the CI gate)

makefile-lint: ## Lint the Makefile with checkmake
	checkmake Makefile

md-lint: ## Lint Markdown files with markdownlint-cli2 — accepts FILES="..."
	@if ! command -v pnpm &>/dev/null; then \
		echo "pnpm is not available. Run: make install-node"; \
	else \
		pnpm exec markdownlint-cli2 $(if $(FILES),$(FILES),'**/*.md'); \
	fi

spell: ## Spell-check files with cspell — accepts FILES="..."
	@if ! command -v pnpm &>/dev/null; then \
		echo "pnpm is not available. Run: make install-node"; \
	else \
		pnpm exec cspell --no-progress --no-summary $(if $(FILES),$(FILES),'**'); \
	fi

check: makefile-lint md-lint spell $(LANG_CHECK_TARGETS) ## Run the full read-only validation gate

.PHONY: makefile-lint md-lint spell check

##@ Writable fixes (mutate files in place)

md-fix: ## Auto-fix Markdown files with markdownlint-cli2 — accepts FILES="..."
	@if ! command -v pnpm &>/dev/null; then \
		echo "pnpm is not available. Run: make install-node"; \
	else \
		pnpm exec markdownlint-cli2 --fix $(if $(FILES),$(FILES),'**/*.md'); \
	fi

# Only invoke md-fix with Markdown files — prevents `fix`/`fix-unsafe` from
# forwarding a non-Markdown FILES scope (e.g. FILES="src/main.py") into
# markdownlint-cli2. Not a public target; used internally by fix/fix-unsafe.
_md-fix-scoped:
	@if [ -z "$(FILES)" ]; then $(MAKE) md-fix; else \
		MD_FILES=$$(echo "$(FILES)" | tr ' ' '\n' | grep '\.md$$' | tr '\n' ' ' || true); \
		if [ -n "$$MD_FILES" ]; then $(MAKE) md-fix FILES="$$MD_FILES"; fi; \
	fi

fix: _md-fix-scoped $(LANG_FIX_TARGETS) ## Apply all safe auto-fixes

fix-unsafe: _md-fix-scoped $(LANG_FIX_UNSAFE_TARGETS) ## Apply all auto-fixes, including unsafe ones

.PHONY: md-fix _md-fix-scoped fix fix-unsafe

##@ Test

test: $(LANG_TEST_TARGETS) ## Run the test suite

.PHONY: test
