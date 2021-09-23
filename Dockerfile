FROM python:3.8.7-buster AS base

ENV PROJECT_HOME=/srv/sciencebeam-judge
WORKDIR ${PROJECT_HOME}

ENV VENV=${PROJECT_HOME}/venv
RUN python3 -m venv ${VENV}
ENV PYTHONUSERBASE=${VENV} PATH=${VENV}/bin:$PATH

COPY requirements.build.txt ./
RUN pip install -r requirements.build.txt


FROM base as dev

COPY requirements.prereq.txt requirements.txt  requirements.dev.txt ./
RUN pip install \
  -r requirements.prereq.txt \
  -r requirements.txt \
  -r requirements.dev.txt

COPY sciencebeam_judge ./sciencebeam_judge
COPY *.conf *.sh *.in *.txt *.py evaluation.yml evaluation.schema.json /srv/sciencebeam-judge/
COPY tests ./tests
COPY .pylintrc .flake8 pytest.ini ${PROJECT_HOME}/


FROM base as runtime

COPY requirements.prereq.txt requirements.txt ./
RUN pip install \
  -r requirements.prereq.txt \
  -r requirements.txt

COPY sciencebeam_judge ./sciencebeam_judge
COPY *.conf *.sh *.in *.txt *.py evaluation.yml evaluation.schema.json /srv/sciencebeam-judge/
