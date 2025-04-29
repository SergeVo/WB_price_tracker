import sqlite3
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Путь к файлу базы данных
DB_DIR = os.getenv('DB_DIR', 'data')
DB_FILE = os.path.join(DB_DIR, 'bot_data.db')

# Создаем директорию для базы данных, если она не существует
os.makedirs(DB_DIR, exist_ok=True)


def init_db():
    """Инициализация базы данных"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Создаем таблицу пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                check_interval INTEGER DEFAULT 180,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Создаем таблицу товаров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                article TEXT,
                url TEXT,
                name TEXT,
                price INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, article)
            )
        ''')
        
        conn.commit()
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
    finally:
        conn.close()


def get_user_interval(user_id):
    """Получение интервала проверки пользователя"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT check_interval FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        return 180  # Значение по умолчанию
    except Exception as e:
        logger.error(f"Ошибка при получении интервала пользователя: {e}")
        return 180
    finally:
        conn.close()


def set_user_interval(user_id, interval):
    """Установка интервала проверки пользователя"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, check_interval)
            VALUES (?, ?)
        ''', (user_id, interval))
        
        conn.commit()
        logger.info(f"Интервал пользователя {user_id} установлен на {interval} минут")
    except Exception as e:
        logger.error(f"Ошибка при установке интервала пользователя: {e}")
    finally:
        conn.close()


def get_user_products(user_id):
    """Получение товаров пользователя"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT article, url, name, price
            FROM products
            WHERE user_id = ?
        ''', (user_id,))
        
        products = {}
        for row in cursor.fetchall():
            article, url, name, price = row
            products[article] = {
                'url': url,
                'name': name,
                'price': price
            }
        
        return products
    except Exception as e:
        logger.error(f"Ошибка при получении товаров пользователя: {e}")
        return {}
    finally:
        conn.close()


def add_product(user_id, article, url, name, price):
    """Добавление товара"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO products 
            (user_id, article, url, name, price, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, article, url, name, price))
        
        conn.commit()
        logger.info(f"Товар {article} добавлен для пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара: {e}")
    finally:
        conn.close()


def remove_product(user_id, article):
    """Удаление товара"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM products
            WHERE user_id = ? AND article = ?
        ''', (user_id, article))
        
        conn.commit()
        logger.info(f"Товар {article} удален у пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при удалении товара: {e}")
    finally:
        conn.close()


def update_product_price(user_id, article, new_price):
    """Обновление цены товара"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE products
            SET price = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND article = ?
        ''', (new_price, user_id, article))
        
        conn.commit()
        logger.info(f"Цена товара {article} обновлена для пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при обновлении цены товара: {e}")
    finally:
        conn.close()


def get_all_products():
    """Получение всех товаров"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, article, url, name, price
            FROM products
        ''')
        
        products = {}
        for row in cursor.fetchall():
            user_id, article, url, name, price = row
            if user_id not in products:
                products[user_id] = {}
            products[user_id][article] = {
                'url': url,
                'name': name,
                'price': price
            }
        
        return products
    except Exception as e:
        logger.error(f"Ошибка при получении всех товаров: {e}")
        return {}
    finally:
        conn.close()


def get_all_user_intervals():
    """Получение интервалов всех пользователей"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, check_interval FROM users')
        
        intervals = {}
        for row in cursor.fetchall():
            user_id, interval = row
            intervals[user_id] = interval
        
        return intervals
    except Exception as e:
        logger.error(f"Ошибка при получении интервалов пользователей: {e}")
        return {}
    finally:
        conn.close()


# Инициализация базы данных при импорте модуля
init_db() 