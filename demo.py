#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from datetime import datetime
import random

def load_birthdays():
    """Загружает дни рождения из файла"""
    with open('birthdays.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def demo_list_birthdays():
    """Демонстрация списка дней рождения"""
    print("📅 Демонстрация: Список дней рождения")
    print("=" * 50)
    
    birthdays = load_birthdays()
    chat_birthdays = birthdays.get("example_chat", {})
    
    if not chat_birthdays:
        print("📝 Список дней рождения пуст!")
        return
    
    # Сортируем по дате
    sorted_birthdays = sorted(
        chat_birthdays.items(),
        key=lambda x: (x[1]['month'], x[1]['day'])
    )
    
    for name, data in sorted_birthdays:
        day, month = data['day'], data['month']
        print(f"🎂 {name} - {day:02d}.{month:02d}")
    
    print(f"\nВсего именинников: {len(chat_birthdays)}")

def demo_upcoming_birthdays():
    """Демонстрация ближайших дней рождения"""
    print("\n📅 Демонстрация: Ближайшие дни рождения")
    print("=" * 50)
    
    today = datetime.now()
    birthdays = load_birthdays()
    chat_birthdays = birthdays.get("example_chat", {})
    
    upcoming = []
    for name, data in chat_birthdays.items():
        try:
            birthday_this_year = datetime(today.year, data['month'], data['day'])
            if birthday_this_year < today:
                birthday_this_year = datetime(today.year + 1, data['month'], data['day'])
            
            days_until = (birthday_this_year - today).days
            
            if 0 <= days_until <= 30:  # Показываем на месяц вперед
                upcoming.append((name, data, days_until, birthday_this_year))
        except ValueError:
            continue
    
    if not upcoming:
        print("📅 В ближайший месяц именинников нет!")
        return
    
    upcoming.sort(key=lambda x: x[2])
    
    for name, data, days_until, birthday_date in upcoming:
        if days_until == 0:
            print(f"🎉 {name} - СЕГОДНЯ!")
        elif days_until == 1:
            print(f"🎂 {name} - завтра ({birthday_date.strftime('%d.%m')})")
        else:
            print(f"🎈 {name} - через {days_until} дней ({birthday_date.strftime('%d.%m')})")

def demo_today_birthdays():
    """Демонстрация именинников сегодня"""
    print("\n🎉 Демонстрация: Именинники сегодня")
    print("=" * 50)
    
    today = datetime.now()
    birthdays = load_birthdays()
    chat_birthdays = birthdays.get("example_chat", {})
    
    today_birthdays = []
    for name, data in chat_birthdays.items():
        if data['day'] == today.day and data['month'] == today.month:
            today_birthdays.append(name)
    
    if today_birthdays:
        congratulations = [
            "🎉 Поздравляем с днём рождения, {name}! Желаем счастья, здоровья и исполнения всех желаний! 🎂",
            "🎊 С днём рождения, {name}! Пусть этот день принесёт радость и улыбки! 🎈",
            "🎁 Дорогой {name}, поздравляем с днём рождения! Желаем ярких моментов и прекрасного настроения! ✨",
            "🌟 {name}, с днём рождения! Пусть впереди ждут только хорошие события! 🎉",
            "🎂 Поздравляем {name} с днём рождения! Желаем крепкого здоровья и море позитива! 🎊"
        ]
        
        for name in today_birthdays:
            congratulation = random.choice(congratulations).format(name=name)
            print(f"{congratulation}\n")
    else:
        print(f"📅 Сегодня ({today.strftime('%d.%m')}) именинников нет!")

def demo_month_statistics():
    """Демонстрация статистики по месяцам"""
    print("\n📊 Демонстрация: Статистика по месяцам")
    print("=" * 50)
    
    months = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    
    birthdays = load_birthdays()
    chat_birthdays = birthdays.get("example_chat", {})
    
    month_count = {}
    for name, data in chat_birthdays.items():
        month = data['month']
        if month not in month_count:
            month_count[month] = []
        month_count[month].append(name)
    
    for month in sorted(month_count.keys()):
        names = month_count[month]
        print(f"{months[month]}: {len(names)} чел. - {', '.join(names)}")

if __name__ == "__main__":
    print("🎉 ДЕМОНСТРАЦИЯ TELEGRAM БОТА ДЛЯ ДНЕЙ РОЖДЕНИЯ")
    print("=" * 60)
    
    try:
        demo_list_birthdays()
        demo_upcoming_birthdays()
        demo_today_birthdays()
        demo_month_statistics()
        
        print("\n" + "=" * 60)
        print("✅ Демонстрация завершена!")
        print("💡 Для запуска настоящего бота используйте: python start.py")
        
    except FileNotFoundError:
        print("❌ Файл birthdays.json не найден!")
        print("Убедитесь, что файл существует в текущей директории.")
    except Exception as e:
        print(f"❌ Ошибка при демонстрации: {e}") 