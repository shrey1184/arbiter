.PHONY: install dev api ui test lint up down eval
install:; python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
api:;     uvicorn app.api.main:app --reload --port 8000
ui:;      streamlit run ui/app.py
test:;    pytest -q
lint:;    ruff check . && ruff format --check .
up:;      docker compose up --build
down:;    docker compose down
eval:;    python -m eval.run_eval
