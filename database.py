import sqlite3
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Путь к файлу базы данных
DB_DIR = os.getenv('DB_DIR', 'data')
DB_FILE = os.path.join(DB_DIR, 'bot_data.db')

# Создаем директорию для базы данных, если она не существует
try:
    os.makedirs(DB_DIR, exist_ok=True)
    logger.info(f"Директория {DB_DIR} создана или уже существует")
except Exception as e:
    logger.error(f"Ошибка при создании директории {DB_DIR}: {e}")
    raise


def get_db_connection():
    """Создание соединения с базой данных"""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Ошибка при создании соединения с базой данных: {e}")
        raise


def migrate_db():
    """Миграция базы данных"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем наличие колонки last_check_time
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'last_check_time' not in columns:
            cursor.execute('''
                ALTER TABLE users
                ADD COLUMN last_check_time TIMESTAMP
            ''')
            conn.commit()
            logger.info("Добавлена колонка last_check_time в таблицу users")
    except Exception as e:
        logger.error(f"Ошибка при миграции базы данных: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def init_db():
    """Инициализация базы данных"""
    conn = None
    try:
        # Проверяем права доступа к директории
        if not os.access(DB_DIR, os.W_OK):
            raise PermissionError(f"Нет прав на запись в директорию {DB_DIR}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Создаем таблицу пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                check_interval INTEGER DEFAULT 180,
                last_check_time TIMESTAMP,
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
        
        # Выполняем миграцию
        migrate_db()
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        if conn is not None:
            try:
                conn.rollback()
            except Exception as rollback_error:
                logger.error(f"Ошибка при откате транзакции: {rollback_error}")
        raise
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as close_error:
                logger.error(f"Ошибка при закрытии соединения: {close_error}")


def get_user_interval(user_id):
    """Получение интервала проверки пользователя"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT check_interval FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        
        if result:
            return result['check_interval']
        return 180  # Значение по умолчанию
    except Exception as e:
        logger.error(f"Ошибка при получении интервала пользователя: {e}")
        return 180
    finally:
        if conn:
            conn.close()


def set_user_interval(user_id, interval):
    """Установка интервала проверки пользователя"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, check_interval)
            VALUES (?, ?)
        ''', (user_id, interval))
        
        conn.commit()
        logger.info(f"Интервал пользователя {user_id} установлен на {interval} минут")
    except Exception as e:
        logger.error(f"Ошибка при установке интервала пользователя: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def get_user_products(user_id):
    """Получение товаров пользователя"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT article, url, name, price
            FROM products
            WHERE user_id = ?
        ''', (user_id,))
        
        products = {}
        for row in cursor.fetchall():
            products[row['article']] = {
                'url': row['url'],
                'name': row['name'],
                'price': row['price']
            }
        
        return products
    except Exception as e:
        logger.error(f"Ошибка при получении товаров пользователя: {e}")
        return {}
    finally:
        if conn:
            conn.close()


def add_product(user_id, article, url, name, price):
    """Добавление товара"""
    conn = None
    try:
        conn = get_db_connection()
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
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def remove_product(user_id, article):
    """Удаление товара"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM products
            WHERE user_id = ? AND article = ?
        ''', (user_id, article))
        
        conn.commit()
        logger.info(f"Товар {article} удален у пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при удалении товара: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def update_product_price(user_id, article, new_price):
    """Обновление цены товара"""
    conn = None
    try:
        conn = get_db_connection()
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
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def get_all_products():
    """Получение всех товаров"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, article, url, name, price
            FROM products
        ''')
        
        products = {}
        for row in cursor.fetchall():
            user_id = row['user_id']
            if user_id not in products:
                products[user_id] = {}
            products[user_id][row['article']] = {
                'url': row['url'],
                'name': row['name'],
                'price': row['price']
            }
        
        return products
    except Exception as e:
        logger.error(f"Ошибка при получении всех товаров: {e}")
        return {}
    finally:
        if conn:
            conn.close()


def get_all_user_intervals():
    """Получение интервалов всех пользователей"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, check_interval FROM users')
        
        intervals = {}
        for row in cursor.fetchall():
            intervals[row['user_id']] = row['check_interval']
        
        return intervals
    except Exception as e:
        logger.error(f"Ошибка при получении интервалов пользователей: {e}")
        return {}
    finally:
        if conn:
            conn.close()


def get_last_check_time(user_id):
    """Получение времени последней проверки пользователя"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT last_check_time FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        
        if result and result['last_check_time']:
            return datetime.fromisoformat(result['last_check_time'])
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении времени последней проверки: {e}")
        return None
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as close_error:
                logger.error(f"Ошибка при закрытии соединения: {close_error}")


def update_last_check_time(user_id, check_time):
    """Обновление времени последней проверки пользователя"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET last_check_time = ?
            WHERE user_id = ?
        ''', (check_time.isoformat(), user_id))
        
        conn.commit()
        logger.info(f"Время последней проверки обновлено для пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при обновлении времени последней проверки: {e}")
        if conn is not None:
            try:
                conn.rollback()
            except Exception as rollback_error:
                logger.error(f"Ошибка при откате транзакции: {rollback_error}")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as close_error:
                logger.error(f"Ошибка при закрытии соединения: {close_error}")


# Инициализация базы данных при импорте модуля
init_db() 