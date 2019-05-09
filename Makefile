DOCKER_COMPOSE_DEV = docker-compose
DOCKER_COMPOSE_CI = docker-compose -f docker-compose.yml -f docker-compose.ci.yml
DOCKER_COMPOSE = $(DOCKER_COMPOSE_DEV)


DEV_RUN_PY2 = $(DOCKER_COMPOSE) run --rm sciencebeam-judge-dev
DEV_RUN_PY3 = $(DOCKER_COMPOSE) run --rm sciencebeam-judge-dev-py3

MOUNT = --volume="$$PWD/example-data:/example-data"

RUN_PY2 = $(DOCKER_COMPOSE) run $(MOUNT) --rm sciencebeam-judge
RUN_PY3 = $(DOCKER_COMPOSE) run $(MOUNT) --rm sciencebeam-judge-py3
RUN = $(RUN_PY2)

PYTEST_ARGS =
TOOL =
EVALUATION_RESULTS_OUTPUT_PATH = /example-data/pmc-sample-1943-cc-by-subset-results/$(TOOL)/evaluation-results

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
	$(DEV_RUN_PY2) ./project_tests.sh


watch-py2: build-dev
	$(DEV_RUN_PY2) pytest-watch -- $(PYTEST_ARGS)


test-py3: build-dev
	$(DEV_RUN_PY3) ./project_tests.sh


watch-py3: build-dev
	$(DEV_RUN_PY3) pytest-watch -- $(PYTEST_ARGS)


test: test-py2

watch: watch-py2

.update-example-data-results:
	$(RUN) ./evaluate.sh \
		--target-file-list /example-data/pmc-sample-1943-cc-by-subset/file-list.tsv \
		--target-file-column=xml_url \
		--prediction-file-list /example-data/pmc-sample-1943-cc-by-subset-results/$(TOOL)/file-list.lst \
		--output-path $(EVALUATION_RESULTS_OUTPUT_PATH) \
		--sequential


update-example-data-results-cermine:
	$(MAKE) TOOL=cermine .update-example-data-results


update-example-data-results-cermine-temp:
	$(MAKE) EVALUATION_RESULTS_OUTPUT_PATH=/tmp update-example-data-results-cermine


update-example-data-results-grobid-tei:
	$(MAKE) TOOL=grobid-tei .update-example-data-results


update-example-data-results-grobid-tei-temp:
	$(MAKE) EVALUATION_RESULTS_OUTPUT_PATH=/tmp update-example-data-results-grobid-tei


update-example-data-results: update-example-data-results-cermine update-example-data-results-grobid-tei 


update-example-data-results-temp: update-example-data-results-cermine-temp update-example-data-results-grobid-tei-temp


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


ci-test-run-evaluation-py2:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" RUN="$(RUN_PY2)" update-example-data-results-temp


ci-test-run-evaluation-py3:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" RUN="$(RUN_PY3)" update-example-data-results-temp


ci-clean:
	$(DOCKER_COMPOSE_CI) down -v
