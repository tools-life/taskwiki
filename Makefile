test:
	mkdir -p /tmp/taskwiki-coverage
	docker-compose up --force-recreate --exit-code-from tests
