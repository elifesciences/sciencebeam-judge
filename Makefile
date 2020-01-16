DOCKER_COMPOSE_DEV = docker-compose
DOCKER_COMPOSE_CI = docker-compose -f docker-compose.yml -f docker-compose.ci.yml
DOCKER_COMPOSE = $(DOCKER_COMPOSE_DEV)


DEV_RUN = $(DOCKER_COMPOSE) run --name "$(RUN_NAME)" --rm sciencebeam-judge-dev

MOUNT = --volume="$$PWD/example-data:/example-data"

RUN_NAME =
JUDGE_SERVICE = sciencebeam-judge
RUN = $(DOCKER_COMPOSE) run $(MOUNT) --name "$(RUN_NAME)" --rm $(JUDGE_SERVICE)

JUPYTER_MOUNT = --volume="$$PWD/example-data:/home/jovyan/sciencebeam-judge/example-data"
JUPYTER_RUN = $(DOCKER_COMPOSE) run $(JUPYTER_MOUNT) --name "$(RUN_NAME)" --rm sciencebeam-judge-jupyter


PYTEST_ARGS =
TOOL =
EVALUATION_RESULTS_OUTPUT_PATH = /example-data/pmc-sample-1943-cc-by-subset-results/$(TOOL)/evaluation-results
NOTEBOOK_OUTPUT_FILE =
NO_BUILD =


build:
	if [ "$(NO_BUILD)" != "y" ]; then \
		$(DOCKER_COMPOSE) build; \
	fi


dev-venv:
	rm -rf venv || true

	virtualenv -p python3.6 venv

	venv/bin/pip install -r requirements.txt

	venv/bin/pip install -r requirements.prereq.txt

	venv/bin/pip install -r requirements.dev.txt


build-dev:
	if [ "$(NO_BUILD)" != "y" ]; then \
		$(DOCKER_COMPOSE) build sciencebeam-judge-dev; \
	fi


test: build-dev
	$(DEV_RUN) ./project_tests.sh


watch: build-dev
	$(DEV_RUN) pytest-watch -- $(PYTEST_ARGS)


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


update-example-data-results: \
	update-example-data-results-cermine update-example-data-results-grobid-tei 


update-example-data-results-temp: \
	update-example-data-results-cermine-temp update-example-data-results-grobid-tei-temp


update-example-data-notebooks-summary:
	$(JUPYTER_RUN) update-notebook-and-check-no-errors.sh \
		conversion-results-summary.ipynb "$(NOTEBOOK_OUTPUT_FILE)"


update-example-data-notebooks-details:
	$(JUPYTER_RUN) update-notebook-and-check-no-errors.sh \
		conversion-results-details.ipynb "$(NOTEBOOK_OUTPUT_FILE)"


update-example-data-notebooks: \
	update-example-data-notebooks-summary update-example-data-notebooks-details


update-example-data-notebooks-temp:
	$(MAKE) NOTEBOOK_OUTPUT_FILE="/tmp/dummy.ipynb" update-example-data-notebooks


jupyter-build:
	if [ "$(NO_BUILD)" != "y" ]; then \
		$(DOCKER_COMPOSE) build sciencebeam-judge-jupyter; \
	fi


jupyter-shell: jupyter-build
	$(DOCKER_COMPOSE) run --rm sciencebeam-judge-jupyter bash


jupyter-start: jupyter-build
	$(DOCKER_COMPOSE) up -d sciencebeam-judge-jupyter


jupyter-logs:
	$(DOCKER_COMPOSE) logs -f sciencebeam-judge-jupyter


jupyter-stop:
	$(DOCKER_COMPOSE) down


ci-build-all:
	$(DOCKER_COMPOSE_CI) build --parallel


ci-test:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" \
		RUN_NAME="ci-test" \
		test


ci-test-run-evaluation:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" \
		RUN_NAME="ci-test-run-evaluation" \
		JUDGE_SERVICE="$(JUDGE_SERVICE)" update-example-data-results-temp


ci-test-evaluate-and-update-notebooks:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" \
		RUN_NAME="ci-test-evaluate-and-update-notebooks" \
		JUDGE_SERVICE="$(JUDGE_SERVICE)" \
		update-example-data-results update-example-data-notebooks-temp


ci-clean:
	$(DOCKER_COMPOSE_CI) down -v
