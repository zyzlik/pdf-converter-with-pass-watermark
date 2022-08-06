FROM python:3.9

COPY pypl2.crt /etc/ssl/certs
RUN /bin/sh -c 'cat /etc/ssl/certs/pypl2.crt >> /etc/ssl/certs/ca-certificates.crt'
RUN echo "[global]" > /etc/pip.conf && echo "cert = /etc/ssl/certs/ca-certificates.crt" >> /etc/pip.conf

ADD . /code
WORKDIR /code

RUN apt-get update && apt-get -y install libreoffice
RUN libreoffice --version
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
