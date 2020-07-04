export LC_ALL := en_US.UTF-8

PYTHON ?= python3

test:
	docker-compose run --rm tests make xvfb-cover-pytest

pytest:
	$(PYTHON) -m pytest -vv $(PYTEST_FLAGS) tests/

cover-pytest: PYTEST_FLAGS += --cov=taskwiki
cover-pytest: pytest
	if [ "$$GITHUB_ACTIONS" ]; then coveralls || :; fi

xvfb-%:
	xvfb-run --server-args=-noreset $(MAKE) $*
