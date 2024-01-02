init:
	python -m pip install poetry
	poetry install --no-root

test:
	python -m pytest -sv tests
	python -m pytest -q tests --cov . --cov-report html