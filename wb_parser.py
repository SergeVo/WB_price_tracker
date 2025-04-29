import requests
import logging
import re
import json
from config import HEADERS, WB_BASE_URL

logger = logging.getLogger(__name__)

class WildberriesParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        # Добавляем специфичные заголовки для API
        self.session.headers.update({
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Referer': 'https://www.wildberries.ru/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="91", "Chromium";v="91"',
            'sec-ch-ua-mobile': '?0'
        })

    def get_product_info(self, url):
        try:
            # Извлекаем ID товара из URL
            product_id = self._extract_product_id(url)
            if not product_id:
                logger.error(f"Не удалось извлечь ID товара из URL: {url}")
                return None

            # Формируем URL для API с дополнительными параметрами
            api_url = (
                f"https://card.wb.ru/cards/detail?"
                f"nm={product_id}&"
                f"curr=rub&"
                f"dest=-1257786&"
                f"regions=80,38,83,4,64,33,68,70,69,30,86,75,40,1,66,110,22,31,48,71,114&"
                f"spp=0"
            )
            
            response = self.session.get(api_url)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('data', {}).get('products'):
                logger.error(f"Товар не найден в API: {url}")
                return None
            
            product = data['data']['products'][0]
            
            # Формируем данные о товаре
            product_data = {
                'name': product.get('name', ''),
                'price': product.get('salePriceU', 0) // 100,  # Цена в копейках
                'article': str(product.get('id', '')),
                'brand': product.get('brand', ''),
                'rating': product.get('rating', 0),
                'feedbacks': product.get('feedbacks', 0)
            }
            
            # Проверяем наличие всех необходимых данных
            if not all([product_data['name'], product_data['price'], product_data['article']]):
                logger.error(f"Неполные данные о товаре: {product_data}")
                return None
            
            return product_data
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе к API Wildberries: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении данных о товаре: {e}")
            return None

    def _extract_product_id(self, url):
        """Извлекает ID товара из URL"""
        try:
            # Пробуем найти ID в URL
            match = re.search(r'/catalog/(\d+)/', url)
            if match:
                return match.group(1)
            
            # Если не нашли в URL, пробуем извлечь из последней части
            parts = url.split('/')
            if parts:
                last_part = parts[-1].split('?')[0]
                if last_part.isdigit():
                    return last_part
            
            return None
        except Exception as e:
            logger.error(f"Ошибка при извлечении ID товара: {e}")
            return None

    def is_valid_url(self, url):
        return url.startswith(WB_BASE_URL) 