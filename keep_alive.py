#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для поддержания бота активным на бесплатном плане Render.
Выполняет периодические запросы к URL сервиса, чтобы предотвратить "засыпание".

Запуск:
python keep_alive.py https://your-app-name.onrender.com
"""

import argparse
import logging
import requests
import time
import sys
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("keep_alive.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def ping_service(url, interval=840):
    """
    Отправляет GET-запросы к указанному URL с заданным интервалом.
    
    Args:
        url (str): URL сервиса для пинга
        interval (int): Интервал между запросами в секундах (по умолчанию 14 минут = 840 секунд)
    """
    if not url.startswith('http'):
        url = f'https://{url}'
    
    logger.info(f"Запуск мониторинга для {url} с интервалом {interval} секунд")
    
    while True:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            response = requests.get(url, timeout=30)
            status = response.status_code
            
            if status == 200:
                logger.info(f"[{now}] Успешный пинг: {url} (статус: {status})")
            else:
                logger.warning(f"[{now}] Пинг выполнен, но получен статус: {status}")
                
        except requests.RequestException as e:
            logger.error(f"[{now}] Ошибка при выполнении запроса: {e}")
        
        # Ждем до следующего пинга
        time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description='Скрипт для поддержания сервиса Render активным.')
    parser.add_argument('url', help='URL сервиса для пинга (например, https://your-app-name.onrender.com)')
    parser.add_argument('-i', '--interval', type=int, default=840, 
                        help='Интервал между запросами в секундах (по умолчанию 840 = 14 минут)')
    
    args = parser.parse_args()
    
    try:
        ping_service(args.url, args.interval)
    except KeyboardInterrupt:
        logger.info("Мониторинг остановлен пользователем")
        sys.exit(0)

if __name__ == "__main__":
    main() 