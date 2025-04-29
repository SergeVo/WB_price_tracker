# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем необходимые пакеты
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Создаем непривилегированного пользователя
RUN useradd -m -u 1000 botuser

# Создаем необходимые директории и устанавливаем права
RUN mkdir -p /app/data /app/logs && \
    chown -R botuser:botuser /app && \
    chmod -R 755 /app && \
    chmod -R 777 /app/data /app/logs

# Копируем файлы зависимостей
COPY --chown=botuser:botuser requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY --chown=botuser:botuser . .

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1 \
    TZ=Europe/Moscow \
    DB_DIR=/app/data \
    LOG_DIR=/app/logs

# Переключаемся на непривилегированного пользователя
USER botuser

# Запускаем бота
CMD ["python", "bot.py"] 