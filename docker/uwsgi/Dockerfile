FROM ubuntu:16.04
MAINTAINER André Vitor de Lima Matos <andre.vmatos@gmail.com>

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && \
    apt-get install -y \
        build-essential python3 python3-dev python3-pip \
        libpq-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt
RUN UWSGI_PROFILE=gevent pip3 install uwsgi
RUN useradd -ms /bin/bash user -u 1000 -U

RUN mkdir /app && chown -R user:user /app
WORKDIR /app

COPY app.ini /app.ini

EXPOSE 9000
ENTRYPOINT ["uwsgi", "--gevent", "100", "--ini", "/app.ini"]
