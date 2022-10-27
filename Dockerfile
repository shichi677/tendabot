FROM python:3
USER root

RUN apt-get update
RUN apt update && apt install -y \
    locales && \
    locale-gen ja_JP.UTF-8

ENV TZ Asia/Tokyo
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV PYTHON_VERSION 3.10.7

RUN apt install -y ffmpeg
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
CMD python discordbot.py
