FROM python:2.7.14-stretch

ENV PROJECT_HOME=/srv/sciencebeam-judge
WORKDIR ${PROJECT_HOME}

ENV VENV=${PROJECT_HOME}/venv
RUN virtualenv ${VENV}
ENV PYTHONUSERBASE=${VENV} PATH=${VENV}/bin:$PATH

COPY requirements.prereq.txt ./
RUN pip install -r requirements.prereq.txt

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY sciencebeam_judge ./sciencebeam_judge
COPY *.conf *.sh *.in *.txt *.py /srv/sciencebeam-judge/

# tests
COPY .pylintrc .flake8 ${PROJECT_HOME}/
