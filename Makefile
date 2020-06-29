export LC_ALL := en_US.UTF-8

PYTHON ?= python3

test:
	docker-compose run --rm tests

pytest:
	$(PYTHON) -m pytest -vv $(PYTEST_FLAGS) tests/

xvfb-%:
	xvfb-run --server-args=-noreset $(MAKE) $*
