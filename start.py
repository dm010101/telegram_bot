#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

def setup_bot():
    """Помощник для настройки бота"""
    print("🎉 Настройка Telegram бота для напоминаний о днях рождения")
    print("="*60)
    
    # Проверяем наличие файла .env
    if not Path('.env').exists():
        print("📝 Файл .env не найден. Создаем...")
        
        # Запрашиваем токен бота
        print("\n1. Получите токен бота:")
        print("   - Откройте Telegram и найдите @BotFather")
        print("   - Отправьте команду /newbot")
        print("   - Следуйте инструкциям для создания бота")
        print("   - Скопируйте полученный токен")
        
        token = input("\n🤖 Введите токен вашего бота: ").strip()
        
        if not token:
            print("❌ Токен не может быть пустым!")
            return False
        
        # Запрашиваем часовой пояс
        print("\n2. Выберите часовой пояс:")
        timezones = {
            '1': 'Europe/Moscow',
            '2': 'Europe/Kiev', 
            '3': 'Europe/London',
            '4': 'Asia/Almaty',
            '5': 'Asia/Tashkent',
            '6': 'America/New_York',
            '7': 'Asia/Tokyo'
        }
        
        print("   1) Москва (Europe/Moscow)")
        print("   2) Киев (Europe/Kiev)")
        print("   3) Лондон (Europe/London)")
        print("   4) Алматы (Asia/Almaty)")
        print("   5) Ташкент (Asia/Tashkent)")
        print("   6) Нью-Йорк (America/New_York)")
        print("   7) Токио (Asia/Tokyo)")
        
        choice = input("\n🌍 Выберите часовой пояс (1-7) или введите свой: ").strip()
        
        if choice in timezones:
            timezone = timezones[choice]
        elif choice:
            timezone = choice
        else:
            timezone = 'Europe/Moscow'
        
        # Создаем файл .env
        try:
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(f"BOT_TOKEN={token}\n")
                f.write(f"TIMEZONE={timezone}\n")
            
            print(f"✅ Файл .env создан успешно!")
            print(f"🌍 Часовой пояс: {timezone}")
            
        except Exception as e:
            print(f"❌ Ошибка создания файла .env: {e}")
            return False
    
    else:
        print("✅ Файл .env уже существует")
    
    # Проверяем зависимости
    print("\n📦 Проверка зависимостей...")
    try:
        import telegram
        import dotenv
        import pytz
        print("✅ Все зависимости установлены")
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("📥 Установите зависимости командой: pip install -r requirements.txt")
        return False
    
    return True

if __name__ == "__main__":
    if setup_bot():
        print("\n🚀 Запуск бота...")
        print("=" * 60)
        
        # Импортируем и запускаем бота
        try:
            from main import BirthdayBot
            bot = BirthdayBot()
            bot.run()
        except KeyboardInterrupt:
            print("\n👋 Бот остановлен пользователем")
        except Exception as e:
            print(f"\n❌ Ошибка запуска бота: {e}")
    else:
        print("\n❌ Настройка не завершена. Исправьте ошибки и запустите снова.") 