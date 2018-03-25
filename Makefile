tests:
	py.test ./test -v

lint:
	flake8 .

coverage:
	py.test --cov-report term-missing --cov=wampy ./test/

dev-install-requirements:
	pip install --editable .[dev]
	pip install -r rtd_requirements.txt
