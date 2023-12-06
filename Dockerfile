FROM python:3.10.11

ENV DockerHOME=.

RUN mkdir -p $DockerHOME

WORKDIR $DockerHOME

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

COPY requirements.txt .
COPY . $DockerHOME

RUN pip install -r requirements.txt

COPY . .