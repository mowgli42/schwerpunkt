.PHONY: demo test spec install

install:
	pip install -e ".[dev]"

demo:
	./scripts/demo-manual.sh

test:
	pytest tests/ -q

spec:
	npx @fission-ai/openspec validate --specs --strict
