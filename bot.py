import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import schedule
import time
import threading
from config import TELEGRAM_TOKEN, CHECK_INTERVAL_MINUTES
from wb_parser import WildberriesParser
from database import (
    get_user_interval,
    set_user_interval,
    get_user_products,
    add_product,
    remove_product,
    update_product_price,
    get_all_products,
    get_all_user_intervals,
    get_last_check_time,
    update_last_check_time
)
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Интервал проверки по умолчанию
DEFAULT_INTERVAL = CHECK_INTERVAL_MINUTES

# Инициализация парсера
parser = WildberriesParser()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    interval = get_user_interval(user_id)
    
    await update.message.reply_text(
        "Привет! Я бот для отслеживания цен на Wildberries.\n"
        "Отправьте мне ссылку на товар, чтобы начать отслеживание.\n"
        "Используйте /help для получения списка команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/list - Показать список отслеживаемых товаров\n"
        "/remove <артикул> - Удалить товар из отслеживания по артикулу\n"
        "/remove_url <ссылка> - Удалить товар из отслеживания по ссылке\n"
        "/set_interval <минуты> - Изменить интервал проверки цен"
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик URL-сообщений"""
    user_id = update.effective_user.id
    url = update.message.text.strip()
    
    if not parser.is_valid_url(url):
        await update.message.reply_text(
            "Пожалуйста, отправьте корректную ссылку на товар Wildberries."
        )
        return
    
    product_info = parser.get_product_info(url)
    if not product_info:
        await update.message.reply_text(
            "Не удалось получить информацию о товаре."
        )
        return
    
    article = product_info['article']
    add_product(
        user_id,
        article,
        url,
        product_info['name'],
        product_info['price']
    )
    
    await update.message.reply_text(
        f"Товар добавлен в отслеживание:\n"
        f"Название: {product_info['name']}\n"
        f"Артикул: {article}\n"
        f"Текущая цена: {product_info['price']} ₽"
    )

async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /list"""
    user_id = update.effective_user.id
    user_products = get_user_products(user_id)
    
    if not user_products:
        await update.message.reply_text("У вас нет отслеживаемых товаров.")
        return
    
    message = "Ваши отслеживаемые товары:\n\n"
    for article, data in user_products.items():
        message += f"Название: {data['name']}\n"
        message += f"Артикул: {article}\n"
        message += f"Текущая цена: {data['price']} ₽\n\n"
    
    await update.message.reply_text(message)

async def remove_product_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /remove"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "Пожалуйста, укажите артикул товара."
        )
        return
    
    article = context.args[0]
    user_products = get_user_products(user_id)
    
    if article in user_products:
        remove_product(user_id, article)
        await update.message.reply_text(
            f"Товар с артикулом {article} удален из отслеживания."
        )
    else:
        await update.message.reply_text(
            "Товар с таким артикулом не найден."
        )

async def remove_url_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /remove_url"""
    user_id = update.effective_user.id
    user_products = get_user_products(user_id)
    
    if not context.args:
        await update.message.reply_text(
            "Пожалуйста, укажите ссылку на товар."
        )
        return
    
    url = context.args[0]
    if not parser.is_valid_url(url):
        await update.message.reply_text(
            "Пожалуйста, укажите корректную ссылку на товар Wildberries."
        )
        return
    
    # Ищем товар по ссылке
    found = False
    for article, data in user_products.items():
        if data['url'] == url:
            remove_product(user_id, article)
            found = True
            await update.message.reply_text(
                f"Товар удален из отслеживания:\n"
                f"Название: {data['name']}\n"
                f"Артикул: {article}"
            )
            break
    
    if not found:
        await update.message.reply_text(
            "Товар с такой ссылкой не найден в отслеживании."
        )

async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /set_interval"""
    user_id = update.effective_user.id
    
    if not context.args:
        current_interval = get_user_interval(user_id)
        await update.message.reply_text(
            f"Ваш текущий интервал проверки: {current_interval} минут\n"
            "Используйте /set_interval <минуты> для изменения интервала"
        )
        return
    
    try:
        new_interval = int(context.args[0])
        if new_interval < 1:
            await update.message.reply_text(
                "Интервал должен быть не менее 1 минуты"
            )
            return
        
        set_user_interval(user_id, new_interval)
        await update.message.reply_text(
            f"Ваш интервал проверки цен изменен на {new_interval} минут"
        )
    except ValueError:
        await update.message.reply_text(
            "Пожалуйста, укажите корректное число минут"
        )

def check_prices():
    """Функция проверки цен"""
    logger.info("Начало проверки цен")
    
    tracked_products = get_all_products()
    user_intervals = get_all_user_intervals()
    
    if not tracked_products:
        logger.info("Нет отслеживаемых товаров")
        return
    
    total_products = sum(len(products) for products in tracked_products.values())
    logger.info(f"Проверка {total_products} товаров")
    
    current_time = datetime.now()
    
    for user_id, user_products in tracked_products.items():
        try:
            interval = user_intervals.get(user_id, DEFAULT_INTERVAL)
            
            # Проверяем, прошло ли достаточно времени с последней проверки
            last_check = get_last_check_time(user_id)
            if last_check and (current_time - last_check).total_seconds() < interval * 60:
                logger.info(
                    f"Пропуск проверки для пользователя {user_id}: "
                    f"прошло {(current_time - last_check).total_seconds() / 60:.1f} минут "
                    f"из {interval} минут"
                )
                continue
            
            logger.info(
                f"Проверка товаров пользователя {user_id} "
                f"(интервал: {interval} минут)"
            )
            
            for article, data in user_products.items():
                try:
                    logger.info(
                        f"Проверка товара: {data['name']} "
                        f"(артикул: {article})"
                    )
                    product_info = parser.get_product_info(data['url'])
                    
                    if not product_info:
                        logger.error(
                            f"Не удалось получить информацию о товаре: "
                            f"{data['url']}"
                        )
                        continue
                    
                    if product_info['price'] != data['price']:
                        old_price = data['price']
                        new_price = product_info['price']
                        update_product_price(user_id, article, new_price)
                        
                        logger.info(
                            f"Обнаружено изменение цены:\n"
                            f"Товар: {data['name']}\n"
                            f"Артикул: {article}\n"
                            f"Старая цена: {old_price} ₽\n"
                            f"Новая цена: {new_price} ₽\n"
                            f"Изменение: {new_price - old_price} ₽"
                        )
                        
                        message = (
                            f"Изменение цены на товар:\n"
                            f"Название: {data['name']}\n"
                            f"Артикул: {article}\n"
                            f"Старая цена: {old_price} ₽\n"
                            f"Новая цена: {new_price} ₽\n"
                            f"Изменение: {new_price - old_price} ₽"
                        )
                        
                        # Отправка уведомления
                        application.bot.send_message(
                            chat_id=user_id,
                            text=message
                        )
                    else:
                        logger.info(
                            f"Цена не изменилась: {data['name']} "
                            f"(артикул: {article})"
                        )
                        
                except Exception as e:
                    logger.error(f"Ошибка при проверке товара {article}: {e}")
            
            # Обновляем время последней проверки
            update_last_check_time(user_id, current_time)
                    
        except Exception as e:
            logger.error(f"Ошибка при проверке товаров пользователя {user_id}: {e}")
    
    logger.info("Завершение проверки цен")

def run_scheduler():
    """Запуск планировщика"""
    # Запускаем проверку каждую минуту
    schedule.every(1).minutes.do(check_prices)
    while True:
        schedule.run_pending()
        time.sleep(60)

def main():
    """Основная функция"""
    global application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_products))
    application.add_handler(CommandHandler("remove", remove_product_command))
    application.add_handler(CommandHandler("remove_url", remove_url_command))
    application.add_handler(CommandHandler("set_interval", set_interval))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url)
    )
    
    # Запуск планировщика в отдельном потоке
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main() 