FROM python:2.7.14-stretch
ARG tensorflow_version=1.4.0
WORKDIR /srv/sciencebeam-judge
RUN virtualenv venv
RUN venv/bin/pip install tensorflow==${tensorflow_version}
COPY sciencebeam_judge /srv/sciencebeam-judge/sciencebeam_judge
COPY *.conf *.sh *.in *.txt *.py /srv/sciencebeam-judge/
RUN venv/bin/pip install -r requirements.txt
