FROM python:3.9-slim-buster

RUN mkdir /app

COPY requirements.txt /.

RUN pip install -r /requirements.txt

RUN mkdir /data
RUN mkdir /data/json && mkdir /data/csv

COPY src/. /app/.

WORKDIR /app

ENTRYPOINT [ "python", "runupdate.py" ]
CMD []
