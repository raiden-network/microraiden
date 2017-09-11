FROM nginx
MAINTAINER André Vitor de Lima Matos <andre.vmatos@gmail.com>

ENV DEBIAN_FRONTEND noninteractive
RUN useradd -s /bin/nologin -u 1000 -U user -G nginx
RUN mkdir -p /app/web/html -p /app/files/tmpr-p /app/ng/dist
COPY nginx.conf /etc/nginx/nginx.conf
