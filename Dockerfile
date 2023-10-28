FROM python:3.11-slim-buster

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV DB_HOST=postgres
ENV DB_NAME=dev_db
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres


COPY pyproject.toml poetry.lock /usr/src/app/
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

COPY . /usr/src/app/

WORKDIR /usr/src/app
COPY --from=ghcr.io/ufoscout/docker-compose-wait:latest /wait /wait

CMD /wait && alembic upgrade head && uvicorn "backend.main:app" --host 0.0.0.0 --port 5000

