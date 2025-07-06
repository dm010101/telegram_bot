#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 УНИВЕРСАЛЬНЫЙ TELEGRAM БОТ
Объединяет все функции из разных версий в один файл

Функции:
- 🎂 Дни рождения (добавление, просмотр, удаление)
- 💒 Свадьбы (годовщины)
- 🛡️ Система отслеживания сообщений
- 🗑️ Управление сообщениями бота (для админа)
- 🔔 Автоматические уведомления в 00:00
- 🎯 Автонастройка для группы "Красавчики 2.0"
"""

import asyncio
import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Dict

import pytz
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import (
    Application, CommandHandler, ContextTypes, 
    CallbackQueryHandler, MessageHandler, filters,
    ChatMemberHandler
)

# Загружаем переменные окружения
load_dotenv()

class UniversalBot:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.timezone = pytz.timezone(os.getenv('TIMEZONE', 'Europe/Moscow'))
        
        # Файлы данных
        self.birthdays_file = 'birthdays.json'
        self.weddings_file = 'weddings.json'
        self.messages_log_file = 'messages_log.json'
        
        # Настройки системы
        self.admin_chats = set()
        self.alarm_enabled_chats = set()
        self.application = None
        self.scheduler_running = False
        
        # Группа "Красавчики 2.0" для автонастройки
        self.target_group_id = None
        self.target_group_name = "Красавчики 2.0"
        
        # Личный чат пользователя для автонастройки
        self.admin_user_id = 500922165
        
        # Администратор для удаления сообщений бота
        self.admin_username = "dmitru_pv"
        
        # Кэш для управления сообщениями
        self.bot_messages_cache = {}  # {chat_id: [message_ids...]}
        self.message_cache = {}  # Для отслеживания удалений
        
        # Шаблоны поздравлений с днем рождения
        self.congratulations = [
            "🎉 Поздравляем с днём рождения, {name}! Желаем счастья, здоровья и исполнения всех желаний! 🎂",
            "🎊 С днём рождения, {name}! Пусть этот день принесёт радость и улыбки! 🎈",
            "🎁 Дорогой {name}, поздравляем с днём рождения! Желаем ярких моментов и прекрасного настроения! ✨",
            "🌟 {name}, с днём рождения! Пусть впереди ждут только хорошие события! 🎉",
            "🎂 Поздравляем {name} с днём рождения! Желаем крепкого здоровья и море позитива! 🎊"
        ]
        
        # Шаблоны поздравлений с годовщиной свадьбы
        self.wedding_congratulations = [
            "💒 Поздравляем {names} с годовщиной свадьбы! {years} лет вместе - это прекрасно! Желаем крепкой любви и семейного счастья! 💕",
            "👰🤵 {names}, с годовщиной вашей свадьбы! {years} лет семейной жизни - это большое достижение! Любви и взаимопонимания! 🥂",
            "💝 Дорогие {names}! Поздравляем с {years}-летием вашего брака! Пусть ваша любовь будет крепнуть с каждым годом! 🌹",
            "🎊 {names}, с прекрасной годовщиной! {years} лет назад вы сказали друг другу 'Да', и это было лучшее решение! 💍",
            "✨ Поздравляем {names} с годовщиной свадьбы! {years} лет счастья позади, впереди еще больше прекрасных моментов! 🎉"
        ]

    # === РАБОТА С ФАЙЛАМИ ===
    
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
    
    def load_weddings(self) -> Dict:
        """Загружает даты свадеб из файла"""
        try:
            if Path(self.weddings_file).exists():
                with open(self.weddings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Ошибка загрузки файла свадеб: {e}")
            return {}
    
    def save_weddings(self, weddings: Dict):
        """Сохраняет даты свадеб в файл"""
        try:
            with open(self.weddings_file, 'w', encoding='utf-8') as f:
                json.dump(weddings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения файла свадеб: {e}")

    def load_messages_log(self) -> Dict:
        """Загружает лог сообщений"""
        try:
            if Path(self.messages_log_file).exists():
                with open(self.messages_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Ошибка загрузки лога сообщений: {e}")
            return {}
    
    def save_messages_log(self, messages_log: Dict):
        """Сохраняет лог сообщений"""
        try:
            with open(self.messages_log_file, 'w', encoding='utf-8') as f:
                json.dump(messages_log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения лога сообщений: {e}")

    # === ОСНОВНЫЕ КОМАНДЫ ===
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        # Проверяем автонастройку для группы Красавчики 2.0
        if await self.auto_setup_target_group(update, context):
            return
        
        welcome_text = """
🎉 **УНИВЕРСАЛЬНЫЙ БОТ ДЛЯ ДНЕЙ РОЖДЕНИЯ И СВАДЕБ**

📅 **Дни рождения:**
/add - Добавить день рождения
/list - Показать все дни рождения  
/today - Именинники сегодня

💒 **Свадьбы:**
/add_wedding - Добавить дату свадьбы
/list_weddings - Показать все свадьбы
/today_weddings - Годовщины сегодня
/upcoming_weddings - Ближайшие годовщины

🔔 **Уведомления:**
/enable_notifications - Включить уведомления в 00:00

🛡️ **Система отслеживания:**
/enable_alarm - включить отслеживание
/disable_alarm - выключить отслеживание
/alarm_status - показать статистику

/help - полная справка
        """
        
        await update.message.reply_text(welcome_text)
        
        # Добавляем чат в список для уведомлений
        chat_id = update.effective_chat.id
        self.admin_chats.add(chat_id)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
🆘 **СПРАВКА ПО КОМАНДАМ**

📅 **Дни рождения:**
/add Имя ДД.ММ - добавить день рождения  
/list - показать всех именинников
/today - именинники сегодня

💒 **Свадьбы:**
/add_wedding "Имя1 и Имя2" ДД.ММ.ГГГГ - добавить свадьбу
/list_weddings - показать все свадьбы
/today_weddings - годовщины сегодня
/upcoming_weddings - ближайшие годовщины

🔔 **Уведомления:**
/enable_notifications - включить уведомления в 00:00

🛡️ **Система отслеживания:**
/enable_alarm - включить отслеживание
/disable_alarm - выключить отслеживание
/alarm_status - показать статистику

💡 **Примеры:**
/add Мария 25.12
/add_wedding "Иван и Анна" 15.06.2020

🗑️ **Управление сообщениями бота** (только для @dmitru_pv):
/delete_bot [N] - удалить последние N сообщений бота
📝 Удаление по реплаю: ответьте на сообщение бота текстом "удалить"
        """
        response = await update.message.reply_text(help_text)
        self.cache_bot_message(update.effective_chat.id, response.message_id)

    # === УПРАВЛЕНИЕ СООБЩЕНИЯМИ БОТА ===
    
    def is_admin_user(self, user) -> bool:
        """Проверяет, является ли пользователь администратором"""
        if not user:
            return False
        return user.username == self.admin_username
    
    def cache_bot_message(self, chat_id: int, message_id: int):
        """Кэширует ID сообщения бота для возможности удаления"""
        chat_id_str = str(chat_id)
        if chat_id_str not in self.bot_messages_cache:
            self.bot_messages_cache[chat_id_str] = []
        
        self.bot_messages_cache[chat_id_str].append(message_id)
        
        # Ограничиваем кэш (последние 50 сообщений)
        if len(self.bot_messages_cache[chat_id_str]) > 50:
            self.bot_messages_cache[chat_id_str] = self.bot_messages_cache[chat_id_str][-50:]

    async def delete_bot_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /delete_bot для удаления сообщений бота"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        if not self.is_admin_user(user):
            await update.message.reply_text(
                f"❌ У вас нет прав для удаления сообщений бота!\n"
                f"Только @{self.admin_username} может удалять сообщения бота."
            )
            return
        
        # Количество сообщений для удаления
        count = 1
        if context.args:
            try:
                count = int(context.args[0])
                if count < 1 or count > 20:
                    await update.message.reply_text("❌ Можно удалить от 1 до 20 сообщений!")
                    return
            except ValueError:
                await update.message.reply_text("❌ Неправильный формат! Используйте: /delete_bot [количество]")
                return
        
        chat_id_str = str(chat_id)
        if chat_id_str not in self.bot_messages_cache or not self.bot_messages_cache[chat_id_str]:
            await update.message.reply_text("❌ Нет сообщений бота для удаления!")
            return
        
        deleted_count = 0
        messages_to_delete = self.bot_messages_cache[chat_id_str][-count:]
        
        for message_id in reversed(messages_to_delete):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                self.bot_messages_cache[chat_id_str].remove(message_id)
                deleted_count += 1
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Не удалось удалить сообщение {message_id}: {e}")
                if message_id in self.bot_messages_cache[chat_id_str]:
                    self.bot_messages_cache[chat_id_str].remove(message_id)
        
        if deleted_count > 0:
            response = await update.message.reply_text(
                f"✅ Удалено {deleted_count} сообщений бота из {count} запрошенных!"
            )
            self.cache_bot_message(chat_id, response.message_id)
        else:
            response = await update.message.reply_text("❌ Не удалось удалить ни одного сообщения!")
            self.cache_bot_message(chat_id, response.message_id)

    async def handle_reply_to_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик для удаления сообщений бота по реплаю"""
        if not update.message.reply_to_message:
            return
        
        user = update.effective_user
        chat_id = update.effective_chat.id
        replied_message = update.message.reply_to_message
        
        # Проверяем, что реплай на сообщение бота
        if not replied_message.from_user or not replied_message.from_user.is_bot:
            return
        
        # Проверяем права пользователя
        if not self.is_admin_user(user):
            return
        
        # Проверяем команду
        if update.message.text and update.message.text.lower() in ['/del', '/delete', 'удалить', 'delete']:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=replied_message.message_id)
                
                # Удаляем из кэша
                chat_id_str = str(chat_id)
                if chat_id_str in self.bot_messages_cache and replied_message.message_id in self.bot_messages_cache[chat_id_str]:
                    self.bot_messages_cache[chat_id_str].remove(replied_message.message_id)
                
                # Подтверждение
                response = await update.message.reply_text("✅ Сообщение бота удалено!")
                self.cache_bot_message(chat_id, response.message_id)
                
                # Удаляем команду пользователя
                await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
                
            except Exception as e:
                response = await update.message.reply_text(f"❌ Не удалось удалить сообщение: {e}")
                self.cache_bot_message(chat_id, response.message_id)

    async def auto_setup_target_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Автоматическая настройка для группы Красавчики 2.0 и личного чата"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Проверяем группу "Красавчики 2.0"
        if (chat.type in ['group', 'supergroup'] and 
            chat.title and 
            self.target_group_name.lower() in chat.title.lower()):
            
            chat_id = chat.id
            self.target_group_id = chat_id
            
            # Автоматически включаем все функции
            self.admin_chats.add(chat_id)
            self.alarm_enabled_chats.add(chat_id)
            
            # Подсчитываем записи
            birthdays = self.load_birthdays()
            weddings = self.load_weddings()
            
            chat_birthdays = birthdays.get(str(chat_id), {})
            chat_weddings = weddings.get(str(chat_id), {})
            
            # Приветственное сообщение
            welcome_message = f"""
🎉 **АВТОНАСТРОЙКА ГРУППЫ "{chat.title}"**

✅ **Все функции автоматически включены:**

🎂 **Дни рождения:** {len(chat_birthdays)} записей
💒 **Свадьбы:** {len(chat_weddings)} записей
🔔 **Автоматические поздравления в 00:00**
🛡️ **Система отслеживания активна**
🗑️ **Управление сообщениями для @{self.admin_username}**

📱 **Команды:** /help для полного списка
            """
            
            try:
                await context.bot.send_message(chat_id=chat_id, text=welcome_message)
                print(f"🎯 Автонастройка группы '{chat.title}' (ID: {chat_id}) завершена")
            except Exception as e:
                print(f"Ошибка отправки приветствия в группу: {e}")
            
            return True
        
        # Проверяем личный чат пользователя
        elif (chat.type == 'private' and 
              user and 
              user.id == self.admin_user_id):
            
            chat_id = chat.id
            
            # Автоматически включаем все функции
            self.admin_chats.add(chat_id)
            self.alarm_enabled_chats.add(chat_id)
            
            # Подсчитываем записи
            birthdays = self.load_birthdays()
            weddings = self.load_weddings()
            
            chat_birthdays = birthdays.get(str(chat_id), {})
            chat_weddings = weddings.get(str(chat_id), {})
            
            # Приветственное сообщение
            welcome_message = f"""
🤖 **АВТОНАСТРОЙКА ЛИЧНОГО ЧАТА**

✅ **Все функции автоматически включены:**

🎂 **Дни рождения:** {len(chat_birthdays)} записей
💒 **Свадьбы:** {len(chat_weddings)} записей
🔔 **Автоматические поздравления в 00:00**
🛡️ **Система отслеживания активна**
🗑️ **Управление сообщениями доступно**

📱 **Команды:** /help для полного списка
            """
            
            try:
                await context.bot.send_message(chat_id=chat_id, text=welcome_message)
                print(f"🎯 Автонастройка личного чата (ID: {chat_id}) завершена")
            except Exception as e:
                print(f"Ошибка отправки приветствия в личный чат: {e}")
            
            return True
        
        return False

    # === ДНИ РОЖДЕНИЯ ===
    
    async def add_birthday(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /add для добавления дня рождения"""
        if not context.args or len(context.args) < 2:
            response = await update.message.reply_text(
                "❌ Неправильный формат!\n"
                "Используйте: /add Имя ДД.ММ или /add Имя ДД.ММ.ГГГГ\n"
                "Пример: /add Иван 15.03.1990"
            )
            self.cache_bot_message(update.effective_chat.id, response.message_id)
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
            response = await update.message.reply_text(
                f"✅ День рождения {name} ({day:02d}.{month:02d}{age_info}) успешно добавлен!"
            )
            self.cache_bot_message(update.effective_chat.id, response.message_id)
            
        except ValueError:
            response = await update.message.reply_text(
                "❌ Неправильный формат даты!\n"
                "Используйте: ДД.ММ или ДД.ММ.ГГГГ\n"
                "Пример: 15.03 или 15.03.1990"
            )
            self.cache_bot_message(update.effective_chat.id, response.message_id)

    async def list_birthdays(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /list для показа всех дней рождения"""
        birthdays = self.load_birthdays()
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in birthdays or not birthdays[chat_id]:
            response = await update.message.reply_text("📝 Список дней рождения пуст!")
            self.cache_bot_message(update.effective_chat.id, response.message_id)
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
        
        response = await update.message.reply_text(text)
        self.cache_bot_message(update.effective_chat.id, response.message_id)

    async def today_birthdays(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /today для проверки именинников сегодня"""
        today = datetime.now(self.timezone)
        birthdays = self.load_birthdays()
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in birthdays:
            response = await update.message.reply_text("📝 Список дней рождения пуст!")
            self.cache_bot_message(update.effective_chat.id, response.message_id)
            return
        
        today_celebrants = []
        for name, data in birthdays[chat_id].items():
            if data['day'] == today.day and data['month'] == today.month:
                today_celebrants.append(name)
        
        if today_celebrants:
            text = "🎉 **Сегодня день рождения у:**\n\n"
            for name in today_celebrants:
                congratulation = random.choice(self.congratulations).format(name=name)
                text += f"{congratulation}\n\n"
        else:
            text = "📅 Сегодня именинников нет!"
        
        response = await update.message.reply_text(text)
        self.cache_bot_message(update.effective_chat.id, response.message_id)

    # === СВАДЬБЫ ===

    async def add_wedding(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /add_wedding для добавления даты свадьбы"""
        if not context.args or len(context.args) < 2:
            response = await update.message.reply_text(
                "❌ Неправильный формат!\n"
                "Используйте: /add_wedding \"Имя1 и Имя2\" ДД.ММ.ГГГГ\n"
                "Пример: /add_wedding \"Иван и Анна\" 15.06.2020"
            )
            self.cache_bot_message(update.effective_chat.id, response.message_id)
            return
        
        # Объединяем все аргументы кроме последнего (дата)
        names = " ".join(context.args[:-1]).strip('"')
        date_str = context.args[-1]
        
        try:
            day, month, year = date_str.split('.')
            day, month, year = int(day), int(month), int(year)
            
            if not (1 <= day <= 31 and 1 <= month <= 12 and year >= 1900):
                raise ValueError("Некорректная дата")
            
            weddings = self.load_weddings()
            chat_id = str(update.effective_chat.id)
            
            if chat_id not in weddings:
                weddings[chat_id] = {}
            
            weddings[chat_id][names] = {
                'day': day, 
                'month': month, 
                'year': year,
                'names': names
            }
            self.save_weddings(weddings)
            
            years_together = datetime.now().year - year
            response = await update.message.reply_text(
                f"💒 Свадьба {names} ({day:02d}.{month:02d}.{year}) добавлена!\n"
                f"🎊 В этом году: {years_together} лет вместе!"
            )
            self.cache_bot_message(update.effective_chat.id, response.message_id)
            
        except ValueError:
            response = await update.message.reply_text(
                "❌ Неправильный формат даты!\nИспользуйте: ДД.ММ.ГГГГ\nПример: 15.06.2020"
            )
            self.cache_bot_message(update.effective_chat.id, response.message_id)

    async def list_weddings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /list_weddings для показа всех свадеб"""
        weddings = self.load_weddings()
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in weddings or not weddings[chat_id]:
            response = await update.message.reply_text("💒 Список свадеб пуст!")
            self.cache_bot_message(update.effective_chat.id, response.message_id)
            return
        
        text = "💒 **Список свадеб:**\n\n"
        sorted_weddings = sorted(weddings[chat_id].items(), key=lambda x: (x[1]['month'], x[1]['day']))
        
        for couple, data in sorted_weddings:
            day, month, year = data['day'], data['month'], data['year']
            years_together = datetime.now().year - year
            
            text += f"👰🤵 {couple}\n"
            text += f"📅 Дата свадьбы: {day:02d}.{month:02d}.{year}\n"
            text += f"💕 Вместе: {years_together} лет\n\n"
        
        response = await update.message.reply_text(text)
        self.cache_bot_message(update.effective_chat.id, response.message_id)

    async def today_weddings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /today_weddings для проверки годовщин сегодня"""
        today = datetime.now(self.timezone)
        weddings = self.load_weddings()
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in weddings:
            response = await update.message.reply_text("💒 Список свадеб пуст!")
            self.cache_bot_message(update.effective_chat.id, response.message_id)
            return
        
        today_anniversaries = []
        for couple, data in weddings[chat_id].items():
            if data['day'] == today.day and data['month'] == today.month:
                years_together = today.year - data['year']
                today_anniversaries.append((couple, years_together))
        
        if today_anniversaries:
            text = "💒 **Сегодня годовщина свадьбы у:**\n\n"
            for couple, years in today_anniversaries:
                congratulation = random.choice(self.wedding_congratulations).format(
                    names=couple, years=years
                )
                text += f"{congratulation}\n\n"
        else:
            text = "💒 Сегодня годовщин нет!"
        
        response = await update.message.reply_text(text)
        self.cache_bot_message(update.effective_chat.id, response.message_id)

    # === УВЕДОМЛЕНИЯ И СИСТЕМА ОТСЛЕЖИВАНИЯ ===

    async def enable_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /enable_notifications для включения уведомлений"""
        chat_id = update.effective_chat.id
        self.admin_chats.add(chat_id)
        
        response = await update.message.reply_text(
            "🔔 Уведомления включены!\n"
            "Бот будет присылать поздравления каждый день в 00:00 (полночь)."
        )
        self.cache_bot_message(chat_id, response.message_id)

    async def enable_alarm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /enable_alarm для включения системы отслеживания"""
        chat_id = update.effective_chat.id
        self.alarm_enabled_chats.add(chat_id)
        
        response = await update.message.reply_text(
            "🛡️ **Система отслеживания включена!**\n\n"
            "📋 **Что отслеживается:**\n"
            "• Все типы сообщений\n" 
            "• Редактирование сообщений\n"
            "• Удаление сообщений\n"
            "• Вход/выход участников\n\n"
            "📊 Используйте /alarm_status для просмотра статистики"
        )
        self.cache_bot_message(chat_id, response.message_id)

    async def disable_alarm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /disable_alarm для выключения системы отслеживания"""
        chat_id = update.effective_chat.id
        self.alarm_enabled_chats.discard(chat_id)
        
        response = await update.message.reply_text(
            "🛡️ Система отслеживания выключена для этого чата."
        )
        self.cache_bot_message(chat_id, response.message_id)

    async def alarm_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /alarm_status для показа статистики"""
        chat_id = update.effective_chat.id
        
        # Загружаем статистику
        messages_log = self.load_messages_log()
        chat_stats = messages_log.get(str(chat_id), {})
        
        # Считаем статистику
        total_messages = len(chat_stats.get('messages', []))
        edited_messages = len(chat_stats.get('edited', []))
        
        status_text = f"📊 **СТАТИСТИКА ЧАТА**\n\n"
        status_text += f"🛡️ **Система отслеживания:** {'✅ ВКЛ' if chat_id in self.alarm_enabled_chats else '❌ ВЫКЛ'}\n"
        status_text += f"📝 **Всего сообщений:** {total_messages}\n"
        status_text += f"✏️ **Отредактировано:** {edited_messages}\n"
        status_text += f"🔔 **Уведомления:** {'✅ ВКЛ' if chat_id in self.admin_chats else '❌ ВЫКЛ'}\n\n"
        
        if chat_id == self.target_group_id:
            status_text += f"🎯 **Автонастройка группы '{self.target_group_name}': ✅ АКТИВНА**\n"
        
        status_text += f"🗑️ **Управление сообщениями:** доступно для @{self.admin_username}"
        
        response = await update.message.reply_text(status_text)
        self.cache_bot_message(chat_id, response.message_id)

    # === СИСТЕМА ОТСЛЕЖИВАНИЯ СООБЩЕНИЙ ===
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик всех сообщений для системы отслеживания"""
        if not update.message:
            return
            
        chat_id = update.effective_chat.id
        
        # Автоматически включаем отслеживание для целевых чатов
        if (chat_id == self.target_group_id or chat_id == self.admin_user_id):
            self.alarm_enabled_chats.add(chat_id)
        
        # Отслеживаем только если включено
        if chat_id not in self.alarm_enabled_chats:
            return
        
        message = update.message
        user = message.from_user
        
        # Не отслеживаем сообщения ботов
        if user and user.is_bot:
            return
        
        username = f"@{user.username}" if user.username else user.first_name
        
        # Определяем тип контента
        content_type = "💬 Текст"
        message_text = message.text or ""
        
        if message.photo:
            content_type = "📷 Фото"
            message_text = message.caption or ""
        elif message.video:
            content_type = "🎥 Видео"
            message_text = message.caption or ""
        elif message.document:
            content_type = "📎 Документ"
            message_text = message.caption or ""
        elif message.voice:
            content_type = "🎤 Голосовое"
        elif message.sticker:
            content_type = "🎭 Стикер"
        elif message.audio:
            content_type = "🎵 Аудио"
        elif message.location:
            content_type = "📍 Геолокация"
        elif message.contact:
            content_type = "👤 Контакт"
        
        # Сохраняем в кэш для отслеживания удалений
        self.message_cache[message.message_id] = {
            'chat_id': chat_id,
            'user_id': user.id if user else None,
            'username': username,
            'timestamp': message.date.isoformat(),
            'text': message_text,
            'message_type': content_type
        }
        
        # Логируем сообщение
        messages_log = self.load_messages_log()
        chat_id_str = str(chat_id)
        
        if chat_id_str not in messages_log:
            messages_log[chat_id_str] = {}
        
        messages_log[chat_id_str][str(message.message_id)] = {
            'message_id': message.message_id,
            'user_id': user.id if user else None,
            'username': user.username if user else None,
            'first_name': user.first_name if user else None,
            'date': message.date.isoformat(),
            'text': message_text,
            'content_type': content_type,
            'logged_at': datetime.now(self.timezone).isoformat()
        }
        
        self.save_messages_log(messages_log)
        
        # Периодически проверяем удаленные сообщения (каждые 100 сообщений)
        if len(self.message_cache) % 100 == 0:
            await self.check_deleted_messages(context)

    async def handle_edited_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик отредактированных сообщений"""
        if not update.edited_message:
            return
            
        chat_id = update.effective_chat.id
        
        # Автоматически включаем отслеживание для целевых чатов
        if (chat_id == self.target_group_id or chat_id == self.admin_user_id):
            self.alarm_enabled_chats.add(chat_id)
        
        # Отслеживаем только если включено
        if chat_id not in self.alarm_enabled_chats:
            return
        
        edited_message = update.edited_message
        user = edited_message.from_user
        
        # Не отслеживаем редактирование сообщений ботов
        if user and user.is_bot:
            return
        
        username = f"@{user.username}" if user.username else user.first_name
        
        # Логируем редактирование
        messages_log = self.load_messages_log()
        chat_id_str = str(chat_id)
        
        if chat_id_str not in messages_log:
            messages_log[chat_id_str] = {}
        
        if 'edited' not in messages_log[chat_id_str]:
            messages_log[chat_id_str]['edited'] = []
        
        # Получаем оригинальный текст из лога
        original_text = ""
        message_id_str = str(edited_message.message_id)
        if message_id_str in messages_log[chat_id_str]:
            original_text = messages_log[chat_id_str][message_id_str].get('text', '')
        
        edit_data = {
            'message_id': edited_message.message_id,
            'user_id': user.id if user else None,
            'username': username,
            'edited_time': datetime.now(self.timezone).isoformat(),
            'original_text': original_text,
            'new_text': edited_message.text or edited_message.caption or ""
        }
        
        messages_log[chat_id_str]['edited'].append(edit_data)
        self.save_messages_log(messages_log)
        
        # Отправляем уведомление о редактировании
        if original_text != edit_data['new_text']:
            notification = f"✏️ **Сообщение отредактировано**\n\n"
            notification += f"👤 **Пользователь:** {username}\n"
            notification += f"🔗 **ID сообщения:** {edited_message.message_id}\n\n"
            notification += f"**Было:** {original_text[:100]}{'...' if len(original_text) > 100 else ''}\n\n"
            notification += f"**Стало:** {edit_data['new_text'][:100]}{'...' if len(edit_data['new_text']) > 100 else ''}"
            
            try:
                response = await context.bot.send_message(chat_id=chat_id, text=notification)
                self.cache_bot_message(chat_id, response.message_id)
            except Exception as e:
                print(f"Ошибка отправки уведомления о редактировании: {e}")

    async def check_deleted_messages(self, context):
        """Проверяет удаленные сообщения"""
        current_time = datetime.now(self.timezone)
        messages_to_remove = []
        
        for message_id, msg_info in list(self.message_cache.items()):
            try:
                # Парсим timestamp
                message_time = datetime.fromisoformat(msg_info['timestamp'].replace('Z', '+00:00'))
                time_diff = (current_time - message_time).total_seconds()
                
                # Проверяем сообщения возрастом от 2 минут до 10 минут
                if 120 <= time_diff <= 600:
                    chat_id = msg_info['chat_id']
                    
                    # Проверяем только если отслеживание включено
                    if (chat_id not in self.alarm_enabled_chats and 
                        chat_id != self.target_group_id and 
                        chat_id != self.admin_user_id):
                        messages_to_remove.append(message_id)
                        continue
                    
                    try:
                        # Пытаемся получить сообщение
                        await context.bot.get_chat_member(chat_id=chat_id, user_id=context.bot.id)
                        await asyncio.sleep(0.1)  # Небольшая задержка между проверками
                    except Exception:
                        # Если не можем получить информацию о чате, удаляем из кэша
                        messages_to_remove.append(message_id)
                        continue
                    
                    # Если сообщение старше 10 минут, удаляем из кэша
                elif time_diff > 600:
                    messages_to_remove.append(message_id)
                    
            except Exception as e:
                print(f"Ошибка при проверке сообщения {message_id}: {e}")
                messages_to_remove.append(message_id)
        
        # Удаляем старые сообщения из кэша
        for message_id in messages_to_remove:
            if message_id in self.message_cache:
                del self.message_cache[message_id]

    # === ЗАПУСК БОТА ===
    
    def run(self):
        """Запуск бота"""
        print("🤖 Универсальный бот с полным функционалом запущен!")
        print("🎂 Дни рождения: ВКЛ")
        print("💒 Свадьбы: ВКЛ") 
        print("🛡️ Система отслеживания: ВКЛ")
        print("🗑️ Управление сообщениями: доступно для @dmitru_pv")
        print("🔔 Планировщик уведомлений: каждый день в 00:00")
        print("🎯 Автонастройка для группы 'Красавчики 2.0': ВКЛ")
        
        # Создаем приложение
        self.application = Application.builder().token(self.bot_token).build()
        
        # Регистрируем обработчики команд
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Дни рождения
        self.application.add_handler(CommandHandler("add", self.add_birthday))
        self.application.add_handler(CommandHandler("list", self.list_birthdays))
        self.application.add_handler(CommandHandler("today", self.today_birthdays))
        
        # Свадьбы
        self.application.add_handler(CommandHandler("add_wedding", self.add_wedding))
        self.application.add_handler(CommandHandler("list_weddings", self.list_weddings))
        self.application.add_handler(CommandHandler("today_weddings", self.today_weddings))
        
        # Уведомления и система отслеживания
        self.application.add_handler(CommandHandler("enable_notifications", self.enable_notifications))
        self.application.add_handler(CommandHandler("enable_alarm", self.enable_alarm))
        self.application.add_handler(CommandHandler("disable_alarm", self.disable_alarm))
        self.application.add_handler(CommandHandler("alarm_status", self.alarm_status))
        
        # Управление сообщениями бота
        self.application.add_handler(CommandHandler("delete_bot", self.delete_bot_messages))
        
        # Система отслеживания сообщений (ПЕРВЫМ! до остальных обработчиков)
        self.application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.handle_message))
        
        # Обработчик отредактированных сообщений
        from telegram.ext import BaseHandler
        
        class EditedMessageHandler(BaseHandler):
            def __init__(self, callback):
                super().__init__(callback)
                
            def check_update(self, update):
                return update.edited_message is not None
        
        self.application.add_handler(EditedMessageHandler(self.handle_edited_message))
        
        # Обработчик сообщений для реплаев (ПОСЛЕДНИМ!)
        self.application.add_handler(MessageHandler(filters.TEXT & filters.REPLY, self.handle_reply_to_bot))
        
        # Запускаем бота
        self.application.run_polling()

if __name__ == "__main__":
    bot = UniversalBot()
    bot.run() 