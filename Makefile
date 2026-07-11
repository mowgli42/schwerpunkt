.PHONY: demo test spec install

install:
	pip install -e ".[dev]"

demo:
	./scripts/demo-manual.sh

test:
	pytest tests/ -q -m "not integration"

test-integration:
	pytest tests/integration/ -m integration

spec:
	npx @fission-ai/openspec validate --specs --strict
