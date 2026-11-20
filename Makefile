SHELL := /bin/bash

UV ?= uv
PYTHON_VERSION ?= 3.12
BACKEND := backend
FRONTEND := frontend
VENV := $(BACKEND)/.venv
PY := $(VENV)/bin/python

.PHONY: setup seed train dev test e2e gen-types demo-csv

setup:
	$(UV) venv --python $(PYTHON_VERSION) $(VENV)
	$(UV) pip install --python $(PY) -r $(BACKEND)/requirements.txt
	cd $(FRONTEND) && npm install
	$(MAKE) gen-types

seed:
	cd $(BACKEND) && .venv/bin/python -m ml.generate_data

train:
	@echo "pendiente — Hito 2"

dev:
	@echo "API: http://localhost:8000 · Frontend: http://localhost:5173"
	@trap 'kill 0' INT TERM EXIT; \
	(cd $(BACKEND) && .venv/bin/uvicorn app.main:app --reload --port 8000) & \
	(cd $(FRONTEND) && npm run dev) & \
	wait

test:
	cd $(BACKEND) && .venv/bin/python -m pytest -q
	cd $(FRONTEND) && npm run typecheck
	cd $(FRONTEND) && npm run build

e2e:
	@echo "pendiente — Hito 7"

gen-types:
	cd $(BACKEND) && .venv/bin/python scripts/export_openapi.py
	cd $(FRONTEND) && npx openapi-typescript src/api/openapi.json -o src/api/schema.d.ts

demo-csv:
	@echo "pendiente — Hito 6"
