.PHONY: test golden benchmark-prd audit-data api web compose-check compose-up compose-down

PYTHON ?= $(or $(firstword $(wildcard .venv/bin/python .venv/Scripts/python.exe)),python3)

test:
	$(PYTHON) -m unittest discover -s backend/tests -v

golden:
	$(PYTHON) tools/verify_golden_research.py

benchmark-prd:
	$(PYTHON) tools/benchmark_prd_scale.py

audit-data:
	$(PYTHON) tools/audit_dataset_storage.py

api:
	cd backend && alembic upgrade head && python3 -m uvicorn app.main:app --reload --port 8000

web:
	cd frontend && npm run dev

compose-check:
	$(PYTHON) tools/verify_compose_config.py

compose-up:
	docker compose up --build

compose-down:
	docker compose down
