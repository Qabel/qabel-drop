
FROM python:3.7-alpine

ENV PYTHONUNBUFFERED 1

RUN  apk add --no-cache --virtual build-deps gcc python3-dev musl-dev && \
  apk add --no-cache postgresql-dev 

RUN addgroup -S drop \
  && adduser -S -G drop drop


# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
RUN pip install --no-cache-dir -r /requirements/production.txt \
  && rm -rf /requirements

RUN apk del build-deps

COPY ./compose/production/drop/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint
RUN chown drop /entrypoint

COPY ./compose/production/drop/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start
RUN chown drop /start
COPY . /app

RUN chown -R drop /app

USER drop

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
