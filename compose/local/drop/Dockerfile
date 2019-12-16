FROM python:3.7-alpine

ENV PYTHONUNBUFFERED 1

RUN apk add --no-cache --virtual build-deps python3-dev musl-dev gcc && \
  apk add --no-cache postgresql-dev

COPY ./requirements /requirements
RUN pip install -r /requirements/local.txt


COPY ./compose/production/drop/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/drop/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
