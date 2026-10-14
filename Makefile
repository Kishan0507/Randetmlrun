.PHONY: setup test lint reproduce dashboard

setup:
	pip install -r requirements.txt

test:
	pytest -q

lint:
	ruff check src tests

# T-P9-01: regenerate all final tables (fill in as experiments are added)
reproduce:
	@echo "TODO: python -m src.eval.run_all --config configs/default.yaml"

dashboard:
	streamlit run dashboard/app.py
