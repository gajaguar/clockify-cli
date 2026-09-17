OPENAPI_URL  := https://docs.clockify.me/openapi.json
OPENAPI_SPEC := .cache/openapi.json

##@ Clockify

openapi-fetch: ## Download Clockify's OpenAPI document into .cache/
	mkdir -p $(dir $(OPENAPI_SPEC))
	curl -fsSL -o $(OPENAPI_SPEC) $(OPENAPI_URL)

coverage-report: ## Compare docs/coverage.md with the cached OpenAPI document (run openapi-fetch first)
	$(UV) run python -m scripts.coverage_report --spec $(OPENAPI_SPEC) --coverage docs/coverage.md

.PHONY: openapi-fetch coverage-report
