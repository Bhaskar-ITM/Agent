COMPOSE_BASE=docker compose -f docker/docker-compose.yml

.PHONY: dev test staging down

dev:
	$(COMPOSE_BASE) --env-file .env.dev -f docker/docker-compose.dev.yml up --build

test:
	$(COMPOSE_BASE) --env-file .env.test -f docker/docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from backend-test

staging:
	$(COMPOSE_BASE) --env-file .env.staging -f docker/docker-compose.staging.yml up --build -d

down:
	$(COMPOSE_BASE) -f docker/docker-compose.dev.yml -f docker/docker-compose.staging.yml -f docker/docker-compose.test.yml down --volumes --remove-orphans
