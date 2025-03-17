FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект, включая уже созданные файлы миграций Alembic
COPY . .

# Запуск миграций при старте контейнера (только применяем, не создаем)
CMD alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000