FROM python:2.7

COPY . /code
WORKDIR /code
RUN pip install -r requirements.txt
WORKDIR /code

ENTRYPOINT ["/code/docker-entrypoint.sh"]
EXPOSE 80
