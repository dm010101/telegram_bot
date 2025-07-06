#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для настройки веб-хука Telegram бота на Render
Использует предоставленные IP-адреса серверов Render
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# IP-адреса серверов Render
RENDER_IPS = [
    "18.156.158.53",
    "18.156.42.200",
    "52.59.103.54"
]

# Токен бота (можно переопределить из .env)
BOT_TOKEN = os.getenv('BOT_TOKEN', "8012067557:AAGkdq_fUfomek-ee9CRsyjm6BHZ0dEl8NA")

def setup_webhook():
    """Настраивает веб-хук для бота с учетом IP-адресов Render"""
    
    # Получаем URL веб-хука из переменных окружения
    webhook_url = os.getenv('WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ Ошибка: WEBHOOK_URL не найден в переменных окружения!")
        webhook_url = input("Введите URL вашего сервиса на Render (например, https://birthday-bot.onrender.com): ")
        if not webhook_url:
            print("❌ URL не указан. Операция отменена.")
            return False
    
    # Формируем URL для настройки веб-хука
    webhook_path = "telegram"
    full_webhook_url = f"{webhook_url}/{webhook_path}"
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    
    # Параметры запроса
    params = {
        'url': full_webhook_url,
        'allowed_updates': ['message', 'callback_query'],
        'ip_address': RENDER_IPS[0]  # Используем первый IP из списка
    }
    
    try:
        # Отправляем запрос на настройку веб-хука
        print(f"🔄 Настройка веб-хука на URL: {full_webhook_url}")
        print(f"🔄 Используемый IP-адрес: {RENDER_IPS[0]}")
        print(f"🔑 Используется токен: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}")
        
        response = requests.post(api_url, json=params)
        result = response.json()
        
        if result.get('ok'):
            print(f"✅ Веб-хук успешно настроен!")
            print(f"📋 Ответ API: {result}")
            return True
        else:
            print(f"❌ Ошибка при настройке веб-хука: {result}")
            return False
    
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")
        return False

def get_webhook_info():
    """Получает информацию о текущем веб-хуке"""
    
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    
    try:
        print(f"🔑 Используется токен: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}")
        response = requests.get(api_url)
        result = response.json()
        
        if result.get('ok'):
            webhook_info = result.get('result', {})
            print("\n📋 Информация о веб-хуке:")
            print(f"URL: {webhook_info.get('url', 'Не установлен')}")
            print(f"Использует IP: {webhook_info.get('ip_address', 'Не указан')}")
            print(f"Последняя ошибка: {webhook_info.get('last_error_message', 'Нет ошибок')}")
            print(f"Ожидающие обновления: {webhook_info.get('pending_update_count', 0)}")
            return True
        else:
            print(f"❌ Ошибка при получении информации о веб-хуке: {result}")
            return False
    
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")
        return False

def delete_webhook():
    """Удаляет текущий веб-хук"""
    
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    
    try:
        print(f"🔑 Используется токен: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}")
        response = requests.get(api_url)
        result = response.json()
        
        if result.get('ok'):
            print("✅ Веб-хук успешно удален!")
            return True
        else:
            print(f"❌ Ошибка при удалении веб-хука: {result}")
            return False
    
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")
        return False

def print_help():
    """Выводит справку по использованию скрипта"""
    print("""
🔧 Скрипт для настройки веб-хука Telegram бота на Render

Использование:
  python setup_webhook.py [команда]

Доступные команды:
  setup    - Настроить веб-хук с IP-адресами Render
  info     - Получить информацию о текущем веб-хуке
  delete   - Удалить текущий веб-хук
  help     - Показать эту справку
    """)

if __name__ == "__main__":
    # Если нет аргументов, показываем справку
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "setup":
        setup_webhook()
        get_webhook_info()
    elif command == "info":
        get_webhook_info()
    elif command == "delete":
        delete_webhook()
    elif command == "help":
        print_help()
    else:
        print(f"❌ Неизвестная команда: {command}")
        print_help()
        sys.exit(1) 