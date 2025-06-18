# Используем официальный Python-образ
FROM python:3.11-slim

# Создадим рабочую директорию в контейнере
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё остальное
COPY app/ .

EXPOSE 8030

# Применяем миграции Alembic и запускаем приложение
CMD ["sh", "-c", "alembic upgrade head && python run_main.py"]