#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import os
import random
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import pytz
import time
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, 
    CallbackQueryHandler, MessageHandler, filters
)

# Загружаем переменные окружения
load_dotenv()

class BirthdayBot:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.timezone = pytz.timezone(os.getenv('TIMEZONE', 'Europe/Moscow'))
        self.birthdays_file = 'birthdays.json'
        self.admin_chats = set()  # Чаты где бот может отправлять уведомления
        self.application = None
        self.scheduler_running = False
        
        # Шаблоны поздравлений
        self.congratulations = [
            "🎉 Поздравляем с днём рождения, {name}! Желаем счастья, здоровья и исполнения всех желаний! 🎂",
            "🎊 С днём рождения, {name}! Пусть этот день принесёт радость и улыбки! 🎈",
            "🎁 Дорогой {name}, поздравляем с днём рождения! Желаем ярких моментов и прекрасного настроения! ✨",
            "🌟 {name}, с днём рождения! Пусть впереди ждут только хорошие события! 🎉",
            "🎂 Поздравляем {name} с днём рождения! Желаем крепкого здоровья и море позитива! 🎊"
        ]
    
    def load_birthdays(self) -> Dict:
        """Загружает дни рождения из файла"""
        try:
            if Path(self.birthdays_file).exists():
                with open(self.birthdays_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Ошибка загрузки файла дней рождения: {e}")
            return {}
    
    def save_birthdays(self, birthdays: Dict):
        """Сохраняет дни рождения в файл"""
        try:
            with open(self.birthdays_file, 'w', encoding='utf-8') as f:
                json.dump(birthdays, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения файла дней рождения: {e}")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        welcome_text = """
🎉 Привет! Я бот для напоминаний о днях рождения!

📋 Доступные команды:
/add - Добавить день рождения
/list - Показать все дни рождения
/delete - Удалить день рождения
/today - Проверить, есть ли именинники сегодня
/upcoming - Ближайшие дни рождения (на неделю)
/help - Показать помощь

🔔 Чтобы получать автоматические уведомления, используйте /enable_notifications
        """
        
        await update.message.reply_text(welcome_text)
        
        # Добавляем чат в список для уведомлений
        chat_id = update.effective_chat.id
        self.admin_chats.add(chat_id)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
🆘 Помощь по командам:

🔸 /add - Добавить новый день рождения
   Формат: /add Иван 15.03 или /add Иван 15.03.1990

🔸 /list - Показать всех именинников

🔸 /delete - Удалить день рождения
   Выберите из списка кого удалить

🔸 /today - Проверить именинников сегодня

🔸 /upcoming - Ближайшие дни рождения

🔸 /enable_notifications - Включить автоуведомления

📝 Примеры:
/add Мария 25.12
/add Петр 08.07.1985
        """
        await update.message.reply_text(help_text)
    
    async def add_birthday(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /add для добавления дня рождения"""
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Неправильный формат!\n"
                "Используйте: /add Имя ДД.ММ или /add Имя ДД.ММ.ГГГГ\n"
                "Пример: /add Иван 15.03.1990"
            )
            return
        
        name = context.args[0]
        date_str = context.args[1]
        
        try:
            # Парсим дату
            if len(date_str.split('.')) == 2:
                day, month = date_str.split('.')
                year = None
            else:
                day, month, year = date_str.split('.')
                year = int(year)
            
            day, month = int(day), int(month)
            
            # Проверяем корректность даты
            if not (1 <= day <= 31 and 1 <= month <= 12):
                raise ValueError("Некорректная дата")
            
            birthdays = self.load_birthdays()
            chat_id = str(update.effective_chat.id)
            
            if chat_id not in birthdays:
                birthdays[chat_id] = {}
            
            birthdays[chat_id][name] = {
                'day': day,
                'month': month,
                'year': year
            }
            
            self.save_birthdays(birthdays)
            
            age_info = f" ({datetime.now().year - year} лет)" if year else ""
            await update.message.reply_text(
                f"✅ День рождения {name} ({day:02d}.{month:02d}{age_info}) успешно добавлен!"
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неправильный формат даты!\n"
                "Используйте: ДД.ММ или ДД.ММ.ГГГГ\n"
                "Пример: 15.03 или 15.03.1990"
            )
    
    async def list_birthdays(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /list для показа всех дней рождения"""
        birthdays = self.load_birthdays()
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in birthdays or not birthdays[chat_id]:
            await update.message.reply_text("📝 Список дней рождения пуст!")
            return
        
        text = "📅 Список дней рождения:\n\n"
        
        # Сортируем по дате
        sorted_birthdays = sorted(
            birthdays[chat_id].items(),
            key=lambda x: (x[1]['month'], x[1]['day'])
        )
        
        for name, data in sorted_birthdays:
            day, month = data['day'], data['month']
            year = data.get('year')
            
            if year:
                age = datetime.now().year - year
                text += f"🎂 {name} - {day:02d}.{month:02d}.{year} ({age} лет)\n"
            else:
                text += f"🎂 {name} - {day:02d}.{month:02d}\n"
        
        await update.message.reply_text(text)
    
    async def delete_birthday(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /delete для удаления дня рождения"""
        birthdays = self.load_birthdays()
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in birthdays or not birthdays[chat_id]:
            await update.message.reply_text("📝 Список дней рождения пуст!")
            return
        
        # Создаем клавиатуру с именами
        keyboard = []
        for name in birthdays[chat_id].keys():
            keyboard.append([InlineKeyboardButton(f"❌ {name}", callback_data=f"delete_{name}")])
        
        keyboard.append([InlineKeyboardButton("🚫 Отмена", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🗑️ Выберите, кого удалить:",
            reply_markup=reply_markup
        )
    
    async def today_birthdays(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /today для проверки именинников сегодня"""
        today = datetime.now(self.timezone)
        birthdays = self.load_birthdays()
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in birthdays:
            await update.message.reply_text("📝 Список дней рождения пуст!")
            return
        
        today_birthdays = []
        for name, data in birthdays[chat_id].items():
            if data['day'] == today.day and data['month'] == today.month:
                today_birthdays.append(name)
        
        if today_birthdays:
            text = "🎉 Сегодня день рождения у:\n\n"
            for name in today_birthdays:
                congratulation = random.choice(self.congratulations).format(name=name)
                text += f"{congratulation}\n\n"
        else:
            text = "📅 Сегодня именинников нет!"
        
        await update.message.reply_text(text)
    
    async def upcoming_birthdays(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /upcoming для показа ближайших дней рождения"""
        today = datetime.now(self.timezone)
        birthdays = self.load_birthdays()
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in birthdays:
            await update.message.reply_text("📝 Список дней рождения пуст!")
            return
        
        upcoming = []
        for name, data in birthdays[chat_id].items():
            # Создаем дату дня рождения в этом году
            try:
                birthday_this_year = datetime(today.year, data['month'], data['day'])
                if birthday_this_year < today:
                    # Если день рождения уже прошел в этом году, берем следующий год
                    birthday_this_year = datetime(today.year + 1, data['month'], data['day'])
                
                days_until = (birthday_this_year - today).days
                
                if 0 <= days_until <= 7:
                    upcoming.append((name, data, days_until, birthday_this_year))
            except ValueError:
                # Обрабатываем случай 29 февраля
                continue
        
        if not upcoming:
            await update.message.reply_text("📅 В ближайшую неделю именинников нет!")
            return
        
        upcoming.sort(key=lambda x: x[2])  # Сортируем по дням до дня рождения
        
        text = "📅 Ближайшие дни рождения (на неделю):\n\n"
        for name, data, days_until, birthday_date in upcoming:
            if days_until == 0:
                text += f"🎉 {name} - СЕГОДНЯ!\n"
            elif days_until == 1:
                text += f"🎂 {name} - завтра ({birthday_date.strftime('%d.%m')})\n"
            else:
                text += f"🎈 {name} - через {days_until} дней ({birthday_date.strftime('%d.%m')})\n"
        
        await update.message.reply_text(text)
    
    async def enable_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Включает автоматические уведомления"""
        chat_id = update.effective_chat.id
        self.admin_chats.add(chat_id)
        
        await update.message.reply_text(
            "🔔 Автоматические уведомления включены!\n"
            "Бот будет присылать уведомления о днях рождения каждый день в 00:00 (полночь)."
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            await query.edit_message_text("❌ Операция отменена.")
            return
        
        if query.data.startswith("delete_"):
            name = query.data[7:]  # Убираем "delete_"
            
            birthdays = self.load_birthdays()
            chat_id = str(update.effective_chat.id)
            
            if chat_id in birthdays and name in birthdays[chat_id]:
                del birthdays[chat_id][name]
                self.save_birthdays(birthdays)
                await query.edit_message_text(f"✅ День рождения {name} удален!")
            else:
                await query.edit_message_text("❌ Ошибка при удалении!")
    
    async def check_and_send_notifications(self):
        """Проверяет и отправляет уведомления о днях рождения"""
        if not self.admin_chats or not self.application:
            return
        
        today = datetime.now(self.timezone)
        birthdays = self.load_birthdays()
        
        for chat_id in self.admin_chats.copy():  # Используем copy для безопасности
            chat_birthdays = birthdays.get(str(chat_id), {})
            
            today_celebrants = []
            for name, data in chat_birthdays.items():
                if data['day'] == today.day and data['month'] == today.month:
                    today_celebrants.append(name)
            
            if today_celebrants:
                for name in today_celebrants:
                    congratulation = random.choice(self.congratulations).format(name=name)
                    try:
                        await self.application.bot.send_message(
                            chat_id=chat_id,
                            text=f"🎉 Напоминание о дне рождения!\n\n{congratulation}"
                        )
                        await asyncio.sleep(1)  # Небольшая задержка между сообщениями
                    except Exception as e:
                        print(f"Ошибка отправки уведомления в чат {chat_id}: {e}")
                        # Удаляем недоступный чат из списка
                        self.admin_chats.discard(chat_id)
    
    async def notification_scheduler(self):
        """Планировщик уведомлений"""
        while self.scheduler_running:
            now = datetime.now(self.timezone)
            
            # Проверяем, если сейчас 00:00 (полночь)
            if now.hour == 0 and now.minute == 0:
                await self.check_and_send_notifications()
                # Ждем минуту, чтобы не отправлять дважды
                await asyncio.sleep(60)
            else:
                # Проверяем каждую минуту
                await asyncio.sleep(60)
    
    def start_scheduler(self):
        """Запускает планировщик в отдельной задаче"""
        if not self.scheduler_running:
            self.scheduler_running = True
            asyncio.create_task(self.notification_scheduler())
            print("🔔 Планировщик уведомлений запущен")
    
    def run(self):
        """Запускает бота"""
        if not self.bot_token:
            print("❌ Ошибка: BOT_TOKEN не найден в переменных окружения!")
            print("Создайте файл .env и добавьте туда ваш токен бота:")
            print("BOT_TOKEN=your_bot_token_here")
            return
        
        # Настройка приложения
        self.application = Application.builder().token(self.bot_token).build()
        
        # Добавляем обработчики команд
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("add", self.add_birthday))
        self.application.add_handler(CommandHandler("list", self.list_birthdays))
        self.application.add_handler(CommandHandler("delete", self.delete_birthday))
        self.application.add_handler(CommandHandler("today", self.today_birthdays))
        self.application.add_handler(CommandHandler("upcoming", self.upcoming_birthdays))
        self.application.add_handler(CommandHandler("enable_notifications", self.enable_notifications))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        print("🤖 Бот запущен!")
        print("📋 Доступные команды: /start, /add, /list, /delete, /today, /upcoming, /help")
        
        # Запускаем планировщик
        self.start_scheduler()
        
        # Запускаем бота
        self.application.run_polling()

if __name__ == "__main__":
    bot = BirthdayBot()
    bot.run() 