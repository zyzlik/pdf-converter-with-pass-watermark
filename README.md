# PDF converter with password and watermark 

### To run:
comment out lines in `Dockerfile`:
```
COPY pypl2.crt /etc/ssl/certs
RUN /bin/sh -c 'cat /etc/ssl/certs/pypl2.crt >> /etc/ssl/certs/ca-certificates.crt'
RUN echo "[global]" > /etc/pip.conf && echo "cert = /etc/ssl/certs/ca-certificates.crt" >> /etc/pip.conf
```
run `docker-compose up`

check with `curl http://127.0.0.1:5000/ping`
