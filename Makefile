export LC_ALL := en_US.UTF-8

PYTHON ?= python3

test:
	docker-compose run --rm tests

pytest:
	$(PYTHON) -m pytest -vv $(PYTEST_FLAGS) tests/

cover-pytest: pytest
	coverage combine
	coverage report
	if [ "$$TRAVIS" ]; then coveralls; fi

xvfb-%:
	xvfb-run --server-args=-noreset $(MAKE) $*
