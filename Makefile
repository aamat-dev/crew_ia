.PHONY: test run-e2e

test:
	pytest -q

run-e2e:
	pytest -q tests/e2e/test_mini_flow.py
