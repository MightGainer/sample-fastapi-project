# Используем официальный базовый образ Python
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы pyproject.toml и poetry.lock для установки зависимостей
COPY pyproject.toml poetry.lock /app/

# Устанавливаем зависимости приложения
RUN poetry config virtualenvs.create false && poetry install --no-dev

# Копируем остальной код приложения
COPY . /app

# Указываем команду для запуска приложения
CMD ["gunicorn", "app.main:app", "-c", "gunicorn_conf.py"]

# Открываем порт, который будет использоваться приложением
EXPOSE 8000
