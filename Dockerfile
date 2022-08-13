FROM python:3.9

# Not needed for local environment
ARG AWS_ACCESS_KEY_ID=""
ARG AWS_SECRET_ACCESS_KEY=""
# Development by default
ARG FLASK_ENV="development"

# Only needed for PP Mac
# COPY pypl2.crt /etc/ssl/certs
# RUN /bin/sh -c 'cat /etc/ssl/certs/pypl2.crt >> /etc/ssl/certs/ca-certificates.crt'
# RUN echo "[global]" > /etc/pip.conf && echo "cert = /etc/ssl/certs/ca-certificates.crt" >> /etc/pip.conf

ADD . /code
WORKDIR /code

RUN apt-get update && apt-get -y install libreoffice
RUN libreoffice --version
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
