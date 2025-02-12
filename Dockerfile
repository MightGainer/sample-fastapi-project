FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false && poetry install --no-root

COPY . /app

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.presentation.main:app", "-c", "gunicorn_conf.py"]

EXPOSE 8000
