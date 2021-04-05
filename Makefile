install:
	pip3 install --editable .[dev]

docs:
	pip3 install --editable .[doc]

tests:
	pip3 install --editable .[dev]
	pip3 install coverage
	pip3 install pytest-cov
	py.test ./test -vs

unit-tests:
	py.test ./test/unit -vs

lint:
	flake8 .

coverage:
	coverage run --source ./wampy -m py.test ./test/ && coverage report

crossbar:
	crossbar start --config ./wampy/testing/configs/crossbar.json

deploy:
	pip install -U twine wheel setuptools
	python setup.py bdist_wheel --universal
	twine upload dist/*
