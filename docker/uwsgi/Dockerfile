FROM python:3
MAINTAINER André Vitor de Lima Matos <andre@brainbot.com>

RUN useradd -ms /bin/bash user -u 1000 -U && mkdir /app
COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt && \
    UWSGI_PROFILE=gevent pip install --no-cache-dir uwsgi

RUN chown -R user:user /app
WORKDIR /app
USER user

ENTRYPOINT ["python3"]
