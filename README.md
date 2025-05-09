# Wildberries Price Tracker Bot

Телеграм бот для отслеживания цен на товары Wildberries.

## Возможности

- Отслеживание цен на товары Wildberries
- Уведомления об изменении цен
- Настраиваемый интервал проверки цен (по умолчанию 3 часа)
- Управление списком отслеживаемых товаров
- Индивидуальные настройки для каждого пользователя

## Установка

### Локальная установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd wbparser
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` в корневой директории проекта и добавьте в него настройки:
```
TELEGRAM_TOKEN=your_bot_token_here
CHECK_INTERVAL_MINUTES=180  # Интервал проверки в минутах (по умолчанию 180)
```

4. Запустите бота:
```bash
python bot.py
```

### Запуск в Docker

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd wbparser
```

2. Создайте файл `.env` в корневой директории проекта и добавьте в него настройки:
```
TELEGRAM_TOKEN=your_bot_token_here
CHECK_INTERVAL_MINUTES=180  # Интервал проверки в минутах (по умолчанию 180)
```

3. Запустите бота в Docker:
```bash
docker-compose up -d
```

4. Для просмотра логов:
```bash
# Логи контейнера
docker-compose logs -f

# Логи приложения
tail -f logs/bot.log
```

5. Для остановки бота:
```bash
docker-compose down
```

6. Для пересборки и перезапуска:
```bash
docker-compose up -d --build
```

## Структура проекта

```
.
├── bot.py              # Основной файл бота
├── config.py           # Конфигурация
├── database.py         # Работа с базой данных
├── wb_parser.py        # Парсер Wildberries
├── requirements.txt    # Зависимости
├── Dockerfile         # Конфигурация Docker
├── docker-compose.yml # Конфигурация Docker Compose
├── .env               # Переменные окружения
├── data/              # Директория для базы данных
└── logs/              # Директория для логов
```

## Использование

1. Найдите бота в Telegram по его имени
2. Отправьте команду `/start` для начала работы
3. Отправьте ссылку на товар Wildberries для начала отслеживания
4. Используйте команды:
   - `/help` - показать список доступных команд
   - `/list` - показать список отслеживаемых товаров
   - `/remove <артикул>` - удалить товар из отслеживания по артикулу
   - `/remove_url <ссылка>` - удалить товар из отслеживания по ссылке
   - `/set_interval <минуты>` - изменить интервал проверки цен

## Требования

- Python 3.7+ (для локальной установки)
- Docker и Docker Compose (для запуска в контейнере)
- Доступ к интернету
- Токен Telegram бота 