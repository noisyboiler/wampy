tests:
	pip install --editable .[dev]
	py.test ./test -vs

lint:
	flake8 .

coverage:
	py.test --cov-report term-missing --cov=wampy ./test/ -vs

dev-install-requirements:
	pip install --editable .[dev]
	pip install -r rtd_requirements.txt

crossbar:
	crossbar start --config ./wampy/testing/configs/crossbar.json
