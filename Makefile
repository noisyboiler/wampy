dev-install:
	pip install --editable .[dev]

doc-install:
	pip install --editable .[doc]

tests:
	pip install --editable .[dev]
	pip install coverage
	pip install pytest-cov
	py.test ./test -vs

unit-tests:
	py.test ./test/unit -vs

lint:
	flake8 .

coverage-report:
	pytest -s -vv --cov=./wampy

crossbar:
	crossbar start --config ./wampy/testing/configs/crossbar.json
