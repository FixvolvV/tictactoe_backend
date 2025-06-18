# Используем официальный Python-образ
FROM python:3.11-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_DB_URL=postgresql+asyncpg://admin:abobys@localhost:5432/tictactoeDB
ENV APP_GUNICORN_WORKERS=1
ENV APP_HTTPCORS_URLS=["https://localhost:5173"]

# Создадим рабочую директорию в контейнере
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копируем всё остальное
COPY . .

# Применяем миграции Alembic и запускаем приложение
CMD ["sh", "-c", "alembic upgrade head && python run_main.py"]