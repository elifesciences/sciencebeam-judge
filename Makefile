DOCKER_COMPOSE_DEV = docker-compose
DOCKER_COMPOSE_CI = docker-compose -f docker-compose.yml -f docker-compose.ci.yml
DOCKER_COMPOSE = $(DOCKER_COMPOSE_DEV)

RUN_PY2 = $(DOCKER_COMPOSE) run --rm sciencebeam-judge-dev
RUN_PY3 = $(DOCKER_COMPOSE) run --rm sciencebeam-judge-dev-py3
PYTEST_ARGS =


build:
	docker-compose build


dev-venv:
	rm -rf venv || true

	virtualenv -p python3.6 venv

	venv/bin/pip install -r requirements.txt

	venv/bin/pip install -r requirements.prereq.txt

	venv/bin/pip install -r requirements.dev.txt


build-dev:
	docker-compose build sciencebeam-judge-dev


test-py2: build-dev
	$(RUN_PY2) ./project_tests.sh


watch-py2: build-dev
	$(RUN_PY2) pytest-watch -- $(PYTEST_ARGS)


test-py3: build-dev
	$(RUN_PY3) ./project_tests.sh


watch-py3: build-dev
	$(RUN_PY3) pytest-watch -- $(PYTEST_ARGS)


test: test-py2

watch: watch-py2

update-example-data-results:
	./update-example-data-results.sh


update-example-data-notebooks:
	./update-example-data-notebooks.sh


jupyter-build:
	docker-compose build sciencebeam-judge-jupyter


jupyter-shell: jupyter-build
	docker-compose run --rm sciencebeam-judge-jupyter bash


jupyter-start: jupyter-build
	docker-compose up -d sciencebeam-judge-jupyter


jupyter-logs:
	docker-compose logs -f sciencebeam-judge-jupyter


jupyter-stop:
	docker-compose down


ci-build-all:
	$(DOCKER_COMPOSE_CI) build  --parallel


ci-test-py2:
	make DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" test-py2


ci-test-py3:
	make DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" test-py3


ci-clean:
	$(DOCKER_COMPOSE_CI) down -v
