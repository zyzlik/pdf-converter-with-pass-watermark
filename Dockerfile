FROM python:3.9

COPY pypl2.crt /etc/ssl/certs
RUN /bin/sh -c 'cat /etc/ssl/certs/pypl2.crt >> /etc/ssl/certs/ca-certificates.crt'

ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
CMD python app.py
