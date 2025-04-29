# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем необходимые пакеты
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаем необходимые директории
RUN mkdir -p /app/data /app/logs && \
    chmod -R 777 /app/data /app/logs

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1 \
    TZ=Europe/Moscow \
    DB_DIR=/app/data \
    LOG_DIR=/app/logs

# Создаем непривилегированного пользователя
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

# Переключаемся на непривилегированного пользователя
USER botuser

# Запускаем бота
CMD ["python", "bot.py"] 