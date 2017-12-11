FROM python:3
MAINTAINER André Vitor de Lima Matos <andre@brainbot.com>

RUN useradd -ms /bin/bash user -u 1000 -U && mkdir /app
COPY ./app/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt && \
    UWSGI_PROFILE=gevent pip install --no-cache-dir uwsgi

COPY ./app/ /app/
RUN chown -R user:user /app
WORKDIR /app
USER user

EXPOSE 9000
ENTRYPOINT ["uwsgi", "--socket", ":9000", "--master", "--pidfile", "/tmp/uwsgi.pid"]
