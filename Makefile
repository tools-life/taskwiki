test:
	mkdir -p /tmp/taskwiki-coverage
	docker-compose up --exit-code-from tests
