FROM nginx
MAINTAINER André Vitor de Lima Matos <andre@brainbot.com>

ENV DEBIAN_FRONTEND noninteractive
RUN useradd -s /bin/nologin -u 1000 -U user -G nginx
COPY nginx.conf /etc/nginx/nginx.conf
