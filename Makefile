
.PHONY: lint mock test

lint:
	npx -y @stoplight/spectral-cli lint openapi.yaml

mock:
	npx -y @stoplight/prism-cli mock openapi.yaml --port 4010

test:
	python -m pytest -q
