FROM python:2.7.14-stretch
ARG tensorflow_version=1.4.0

ENV PROJECT_HOME=/srv/sciencebeam-judge
WORKDIR ${PROJECT_HOME}

ENV VENV=${PROJECT_HOME}/venv
RUN virtualenv ${VENV}
ENV PYTHONUSERBASE=${VENV} PATH=${VENV}/bin:$PATH

RUN pip install tensorflow==${tensorflow_version}
RUN pip install https://github.com/elifesciences/sciencebeam-gym/archive/develop.zip

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY sciencebeam_judge ./sciencebeam_judge
COPY *.conf *.sh *.in *.py /srv/sciencebeam-judge/
