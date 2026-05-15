.PHONY: install install-dev uninstall clean test

install:
	pip install --force-reinstall --no-deps .

install-dev:
	pip install --force-reinstall --no-deps -e .

uninstall:
	pip uninstall -y openskills

clean:
	rm -rf build/ dist/ *.egg-info openskills.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

test:
	python -m pytest tests/ -v
