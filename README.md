# Setup

If no migrations were applied before, you can run:

```bash
alembic init -t async alembic
alembic revision --autogenerate -m "Init"
alembic upgrade head
```

## Run in docker

```bash
docker build . -t app
docker container run -p 8000:8000 app
```
