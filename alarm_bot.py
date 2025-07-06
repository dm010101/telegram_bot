#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Dict

import pytz
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
        self.weddings_file = 'weddings.json'
        self.admin_chats = set()
        self.application = None
        self.scheduler_running = False
        
        # ID группы "Красавчики 2.0" для автоматической настройки
        self.target_group_id = None  # Будет определен автоматически
        self.target_group_name = "Красавчики 2.0"
        
        # Пользователь с правами администратора для удаления сообщений бота
        self.admin_username = "dmitru_pv"  # Пользователь dmitru_pv может удалять сообщения бота
        
        # Кэш для хранения ID сообщений бота для возможности удаления
        self.bot_messages_cache = {}  # {chat_id: [message_ids...]}
        
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
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        # Проверяем автонастройку для группы Красавчики 2.0
        if await self.auto_setup_target_group(update, context):
            return
            
        welcome_text = """
🎉 **Бот для дней рождения и свадеб!**

📋 **Дни рождения:**
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

🔧 **Дополнительно:**
/chatid - Показать ID чата
/help - Показать полную справку
        """
        
        await update.message.reply_text(welcome_text)
        chat_id = update.effective_chat.id
        self.admin_chats.add(chat_id)
    
    async def auto_setup_target_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Автоматическая настройка для группы Красавчики 2.0"""
        chat = update.effective_chat
        
        # Проверяем, является ли это нашей целевой группой
        if (chat.type in ['group', 'supergroup'] and 
            chat.title and 
            self.target_group_name.lower() in chat.title.lower()):
            
            chat_id = chat.id
            self.target_group_id = chat_id
            
            # Автоматически включаем все функции
            self.admin_chats.add(chat_id)
            
            # Подсчитываем реальное количество записей в базе
            birthdays = self.load_birthdays()
            weddings = self.load_weddings()
            
            birthdays_count = sum(len(chat_birthdays) for chat_birthdays in birthdays.values())
            weddings_count = sum(len(chat_weddings) for chat_weddings in weddings.values())
            
            # Отправляем приветственное сообщение о автонастройке
            welcome_message = f"""
🎉 **АВТОНАСТРОЙКА ГРУППЫ "{chat.title}"**

✅ **Все функции автоматически включены:**

🎂 **Дни рождения:**
• Автоматические поздравления в 00:00
• {birthdays_count} дней рождения уже в базе
• Команды: /list, /today

💒 **Свадьбы:**
• Автоматические поздравления с годовщинами в 00:00
• {weddings_count} свадеб уже в базе
• Команды: /list_weddings, /today_weddings, /upcoming_weddings

🔔 **Уведомления:**
• Все поздравления приходят в эту группу
• Время: каждый день в 00:00 (полночь)
• Никаких дополнительных настроек не требуется

📱 **Доступные команды:**
/start - показать все команды
/help - полная справка
/list - дни рождения
/list_weddings - свадьбы
            """
            
            try:
                await context.bot.send_message(chat_id=chat_id, text=welcome_message)
                print(f"🎯 Автонастройка группы '{chat.title}' (ID: {chat_id}) завершена")
            except Exception as e:
                print(f"Ошибка отправки приветствия в группу: {e}")
            
            return True
        
        return False
    
    async def add_birthday(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /add для добавления дня рождения"""
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Неправильный формат!\nИспользуйте: /add Имя ДД.ММ\nПример: /add Анна 15.03"
            )
            return
        
        name = context.args[0]
        date_str = context.args[1]
        
        try:
            if len(date_str.split('.')) == 2:
                day, month = date_str.split('.')
                year = None
            else:
                day, month, year = date_str.split('.')
                year = int(year)
            
            day, month = int(day), int(month)
            
            if not (1 <= day <= 31 and 1 <= month <= 12):
                raise ValueError("Некорректная дата")
            
            birthdays = self.load_birthdays()
            chat_id = str(update.effective_chat.id)
            
            if chat_id not in birthdays:
                birthdays[chat_id] = {}
            
            birthdays[chat_id][name] = {'day': day, 'month': month, 'year': year}
            self.save_birthdays(birthdays)
            
            age_info = f" ({datetime.now().year - year} лет)" if year else ""
            await update.message.reply_text(
                f"✅ День рождения {name} ({day:02d}.{month:02d}{age_info}) добавлен!"
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неправильный формат даты!\nИспользуйте: ДД.ММ или ДД.ММ.ГГГГ"
            )
    
    async def list_birthdays(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /list для показа всех дней рождения"""
        birthdays = self.load_birthdays()
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in birthdays or not birthdays[chat_id]:
            await update.message.reply_text("📝 Список дней рождения пуст!")
            return
        
        text = "📅 **Список дней рождения:**\n\n"
        sorted_birthdays = sorted(birthdays[chat_id].items(), key=lambda x: (x[1]['month'], x[1]['day']))
        
        for name, data in sorted_birthdays:
            day, month = data['day'], data['month']
            year = data.get('year')
            
            if year:
                age = datetime.now().year - year
                text += f"🎂 {name} - {day:02d}.{month:02d}.{year} ({age} лет)\n"
            else:
                text += f"🎂 {name} - {day:02d}.{month:02d}\n"
        
        await update.message.reply_text(text)
    
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
            text = "🎉 **Сегодня день рождения у:**\n\n"
            for name in today_birthdays:
                congratulation = random.choice(self.congratulations).format(name=name)
                text += f"{congratulation}\n\n"
        else:
            text = "📅 Сегодня именинников нет!"
        
        await update.message.reply_text(text)
    
    async def enable_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Включает автоматические уведомления"""
        chat_id = update.effective_chat.id
        self.admin_chats.add(chat_id)
        
        await update.message.reply_text(
            "🔔 **Уведомления о днях рождения включены!**\n"
            "Бот будет присылать поздравления каждый день в 00:00 (полночь)."
        )
    
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

🔧 **Дополнительно:**
/chatid - показать ID чата
/help - эта справка

🗑️ **Управление сообщениями бота:**
Ответьте на сообщение бота для его удаления (только для администратора)

📝 **Примеры использования:**

**Добавить день рождения:**
/add Анна 15.03
/add Петр 22.05.1990

**Добавить свадьбу:**
/add_wedding "Иван и Мария" 15.06.2020
/add_wedding "Петр и Анна" 10.08.2018

**Автоматические уведомления:**
Бот автоматически поздравляет в 00:00 (полночь) каждый день.
Включите уведомления командой /enable_notifications
        """
        
        await update.message.reply_text(help_text)
    
    async def show_chat_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /chatid - показывает ID чата"""
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        chat_title = getattr(update.effective_chat, 'title', 'Приватный чат')
        
        info_text = f"🆔 **Информация о чате:**\n\n"
        info_text += f"📊 **ID чата:** `{chat_id}`\n"
        info_text += f"📝 **Тип чата:** {chat_type}\n"
        info_text += f"👥 **Название:** {chat_title}\n\n"
        info_text += f"💡 **Для настройки уведомлений используйте этот ID**"
        
        try:
            message = await update.message.reply_text(info_text)
            self.cache_bot_message(chat_id, message.message_id)
        except Exception as e:
            print(f"Ошибка отправки информации о чате: {e}")
    
    def is_admin_user(self, user) -> bool:
        """Проверяет, является ли пользователь администратором"""
        if not user:
            return False
        return user.username == self.admin_username
    
    def cache_bot_message(self, chat_id: int, message_id: int):
        """Кэширует ID сообщения бота для возможности удаления"""
        if chat_id not in self.bot_messages_cache:
            self.bot_messages_cache[chat_id] = []
        
        self.bot_messages_cache[chat_id].append(message_id)
        
        # Ограничиваем размер кэша (храним только последние 100 сообщений на чат)
        if len(self.bot_messages_cache[chat_id]) > 100:
            self.bot_messages_cache[chat_id] = self.bot_messages_cache[chat_id][-100:]
    
    async def send_cached_message(self, chat_id: int, text: str, **kwargs):
        """Отправляет сообщение и кэширует его ID"""
        try:
            if self.application and self.application.bot:
                message = await self.application.bot.send_message(chat_id=chat_id, text=text, **kwargs)
                self.cache_bot_message(chat_id, message.message_id)
                return message
        except Exception as e:
            print(f"Ошибка отправки кэшированного сообщения: {e}")
            return None
    
    async def delete_bot_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /delete_bot для удаления всех сообщений бота в чате"""
        if not self.is_admin_user(update.effective_user):
            await update.message.reply_text("❌ У вас нет прав для этой команды!")
            return
        
        chat_id = update.effective_chat.id
        
        if chat_id not in self.bot_messages_cache or not self.bot_messages_cache[chat_id]:
            await update.message.reply_text("📝 Нет сообщений бота для удаления в этом чате!")
            return
        
        deleted_count = 0
        failed_count = 0
        
        # Пытаемся удалить все кэшированные сообщения бота
        for message_id in self.bot_messages_cache[chat_id][:]:  # Копируем список для итерации
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                deleted_count += 1
                # Удаляем из кэша успешно удаленные сообщения
                self.bot_messages_cache[chat_id].remove(message_id)
                
                # Небольшая задержка чтобы избежать лимитов API
                await asyncio.sleep(0.1)
                
            except Exception as e:
                failed_count += 1
                # Если сообщение не найдено, удаляем его из кэша
                if "message to delete not found" in str(e).lower():
                    if message_id in self.bot_messages_cache[chat_id]:
                        self.bot_messages_cache[chat_id].remove(message_id)
        
        # Отправляем отчет о результатах
        result_text = f"🗑️ **Операция завершена!**\n\n"
        result_text += f"✅ Удалено сообщений: {deleted_count}\n"
        if failed_count > 0:
            result_text += f"❌ Не удалось удалить: {failed_count}\n"
        result_text += f"📊 Осталось в кэше: {len(self.bot_messages_cache.get(chat_id, []))}"
        
        # Это сообщение тоже нужно кэшировать
        try:
            message = await update.message.reply_text(result_text)
            self.cache_bot_message(chat_id, message.message_id)
        except Exception as e:
            print(f"Ошибка отправки отчета об удалении: {e}")
    
    async def handle_reply_to_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик реплаев на сообщения бота для их удаления"""
        # Проверяем, что это ответ на сообщение
        if not update.message.reply_to_message:
            return
        
        # Проверяем, что пользователь имеет права администратора
        if not self.is_admin_user(update.effective_user):
            return
        
        replied_message = update.message.reply_to_message
        
        # Проверяем, что это сообщение от нашего бота
        if replied_message.from_user.id != context.bot.id:
            return
        
        chat_id = update.effective_chat.id
        message_id_to_delete = replied_message.message_id
        user_message_id = update.message.message_id
        
        try:
            # Удаляем сообщение бота
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id_to_delete)
            
            # Удаляем команду пользователя
            await context.bot.delete_message(chat_id=chat_id, message_id=user_message_id)
            
            # Убираем из кэша
            if chat_id in self.bot_messages_cache and message_id_to_delete in self.bot_messages_cache[chat_id]:
                self.bot_messages_cache[chat_id].remove(message_id_to_delete)
            
            print(f"🗑️ Администратор удалил сообщение бота {message_id_to_delete} в чате {chat_id}")
            
        except Exception as e:
            print(f"❌ Ошибка удаления сообщения по реплаю: {e}")
            # Если не удалось удалить - отправляем сообщение об ошибке
            try:
                error_message = await update.message.reply_text(
                    f"❌ Не удалось удалить сообщение: {str(e)[:100]}"
                )
                # Кэшируем сообщение об ошибке
                self.cache_bot_message(chat_id, error_message.message_id)
            except:
                pass
    
    async def check_and_send_notifications(self):
        """Проверяет и отправляет уведомления о днях рождения и годовщинах"""
        today = datetime.now(self.timezone)
        
        # Загружаем данные
        birthdays = self.load_birthdays()
        weddings = self.load_weddings()
        
        # Определяем чаты для отправки уведомлений
        target_chats = list(self.admin_chats)
        
        for chat_id in target_chats:
            # Проверяем дни рождения
            chat_birthdays = birthdays.get(str(chat_id), {})
            today_celebrants = []
            for name, data in chat_birthdays.items():
                if data['day'] == today.day and data['month'] == today.month:
                    today_celebrants.append(name)
            
            # Отправляем поздравления с днями рождения
            if today_celebrants:
                for name in today_celebrants:
                    congratulation = random.choice(self.congratulations).format(name=name)
                    try:
                        await self.send_cached_message(
                            chat_id,
                            f"🎉 Напоминание о дне рождения!\n\n{congratulation}"
                        )
                        await asyncio.sleep(1)  # Небольшая задержка между сообщениями
                    except Exception as e:
                        print(f"Ошибка отправки уведомления о ДР в чат {chat_id}: {e}")
                        # Удаляем недоступный чат из списка
                        if chat_id in self.admin_chats:
                            self.admin_chats.discard(chat_id)
            
            # Проверяем годовщины свадеб  
            chat_weddings = weddings.get(str(chat_id), {})
            today_anniversaries = []
            for couple, data in chat_weddings.items():
                if data['day'] == today.day and data['month'] == today.month:
                    years_together = today.year - data['year']
                    today_anniversaries.append((couple, years_together))
            
            # Отправляем поздравления с годовщинами
            if today_anniversaries:
                for couple, years in today_anniversaries:
                    congratulation = random.choice(self.wedding_congratulations).format(
                        names=couple, years=years
                    )
                    try:
                        await self.send_cached_message(
                            chat_id,
                            f"💒 Напоминание о годовщине свадьбы!\n\n{congratulation}"
                        )
                        await asyncio.sleep(1)  # Небольшая задержка между сообщениями
                    except Exception as e:
                        print(f"Ошибка отправки уведомления о годовщине в чат {chat_id}: {e}")
                        # Удаляем недоступный чат из списка
                        if chat_id in self.admin_chats:
                            self.admin_chats.discard(chat_id)
    
    async def notification_scheduler(self):
        """Планировщик уведомлений"""
        last_notification_check = 0  # Время последней проверки уведомлений
        
        while self.scheduler_running:
            try:
                now = datetime.now(self.timezone)
                current_timestamp = now.timestamp()
                
                # Проверяем, если сейчас 00:00 (полночь) и не проверяли в последнюю минуту
                if now.hour == 0 and now.minute == 0 and (current_timestamp - last_notification_check) > 60:
                    print(f"🔔 Отправка уведомлений в полночь: {now.strftime('%H:%M:%S')}")
                    await self.check_and_send_notifications()
                    last_notification_check = current_timestamp
                
                # Ждем 30 секунд до следующей проверки
                await asyncio.sleep(30)
                    
            except Exception as e:
                print(f"❌ Ошибка в планировщике: {e}")
                await asyncio.sleep(30)

    def start_scheduler(self):
        """Запускает планировщик в отдельном потоке"""
        if not self.scheduler_running:
            self.scheduler_running = True
            import threading
            scheduler_thread = threading.Thread(target=self.run_scheduler)
            scheduler_thread.daemon = True
            scheduler_thread.start()
            print("🔔 Планировщик уведомлений запущен (00:00)")
    
    def run_scheduler(self):
        """Запускает асинхронный планировщик в отдельном потоке"""
        import asyncio
        asyncio.run(self.notification_scheduler())
    
    def run(self):
        """Запускает бота"""
        if not self.bot_token:
            print("❌ Ошибка: BOT_TOKEN не найден!")
            return
        
        # Настраиваем Application
        from telegram.ext import ApplicationBuilder
        
        builder = ApplicationBuilder()
        builder.token(self.bot_token)
        self.application = builder.build()
        
        # Основные команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("add", self.add_birthday))
        self.application.add_handler(CommandHandler("list", self.list_birthdays))
        self.application.add_handler(CommandHandler("today", self.today_birthdays))
        self.application.add_handler(CommandHandler("enable_notifications", self.enable_notifications))
        self.application.add_handler(CommandHandler("chatid", self.show_chat_id))
        
        # Команды для свадеб
        self.application.add_handler(CommandHandler("add_wedding", self.add_wedding))
        self.application.add_handler(CommandHandler("list_weddings", self.list_weddings))
        self.application.add_handler(CommandHandler("today_weddings", self.today_weddings))
        self.application.add_handler(CommandHandler("upcoming_weddings", self.upcoming_weddings))
        
        # Команды управления сообщениями бота (только для администратора)
        self.application.add_handler(CommandHandler("delete_bot", self.delete_bot_messages))
        
        # Обработчик для реплаев на сообщения бота (для удаления)
        self.application.add_handler(MessageHandler(filters.REPLY & filters.TEXT, self.handle_reply_to_bot))
        
        print("🤖 Бот для дней рождения и свадеб запущен!")
        print("🕛 Уведомления о днях рождения: каждый день в 00:00")
        print("💒 Поддержка свадеб: ВКЛ")
        print(f"🗑️ Управление сообщениями: доступно для @{self.admin_username}")
        
        # Запускаем планировщик в отдельном потоке
        self.start_scheduler()
        
        self.application.run_polling()

    # Команды для работы со свадьбами
    async def add_wedding(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /add_wedding для добавления даты свадьбы"""
        if not context.args or len(context.args) < 3:
            await update.message.reply_text(
                "❌ Неправильный формат!\nИспользуйте: /add_wedding \"Имя1 и Имя2\" ДД.ММ.ГГГГ\nПример: /add_wedding \"Иван и Мария\" 15.06.2020"
            )
            return
        
        # Объединяем все аргументы кроме последнего (даты)
        names = " ".join(context.args[:-1]).strip('"').strip("'")
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
            await update.message.reply_text(
                f"💒 Свадьба {names} ({day:02d}.{month:02d}.{year}) добавлена!\n"
                f"🎊 В этом году: {years_together} лет вместе!"
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неправильный формат даты!\nИспользуйте: ДД.ММ.ГГГГ\nПример: 15.06.2020"
            )

    async def list_weddings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /list_weddings для показа всех свадеб"""
        weddings = self.load_weddings()
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in weddings or not weddings[chat_id]:
            await update.message.reply_text("💒 Список свадеб пуст!")
            return
        
        text = "💒 **Список свадеб:**\n\n"
        sorted_weddings = sorted(weddings[chat_id].items(), key=lambda x: (x[1]['month'], x[1]['day']))
        
        for couple, data in sorted_weddings:
            day, month, year = data['day'], data['month'], data['year']
            years_together = datetime.now().year - year
            
            text += f"👰🤵 {couple}\n"
            text += f"📅 Дата свадьбы: {day:02d}.{month:02d}.{year}\n"
            text += f"💕 Вместе: {years_together} лет\n\n"
        
        await update.message.reply_text(text)

    async def today_weddings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /today_weddings для проверки годовщин сегодня"""
        today = datetime.now(self.timezone)
        weddings = self.load_weddings()
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in weddings:
            await update.message.reply_text("💒 Список свадеб пуст!")
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
        
        await update.message.reply_text(text)

    async def upcoming_weddings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /upcoming_weddings для показа ближайших годовщин"""
        today = datetime.now(self.timezone)
        weddings = self.load_weddings()
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in weddings or not weddings[chat_id]:
            await update.message.reply_text("💒 Список свадеб пуст!")
            return
        
        upcoming = []
        
        for couple, data in weddings[chat_id].items():
            day, month, year = data['day'], data['month'], data['year']
            
            # Определяем дату годовщины в этом году
            try:
                anniversary_this_year = datetime(today.year, month, day, tzinfo=self.timezone)
                
                # Если годовщина уже прошла в этом году, берем следующий год
                if anniversary_this_year < today:
                    anniversary_this_year = datetime(today.year + 1, month, day, tzinfo=self.timezone)
                
                days_until = (anniversary_this_year.date() - today.date()).days
                years_together = anniversary_this_year.year - year
                
                upcoming.append((couple, anniversary_this_year, days_until, years_together))
                
            except ValueError:
                continue  # Пропускаем некорректные даты
        
        if not upcoming:
            await update.message.reply_text("💒 Нет предстоящих годовщин!")
            return
        
        # Сортируем по количеству дней до события
        upcoming.sort(key=lambda x: x[2])
        
        text = "💒 **Ближайшие годовщины свадеб:**\n\n"
        for couple, anniversary_date, days_until, years_together in upcoming[:10]:  # Показываем не более 10
            if days_until == 0:
                text += f"🎊 **СЕГОДНЯ:** {couple} - {years_together} лет!\n"
            elif days_until == 1:
                text += f"🔔 **ЗАВТРА:** {couple} - {years_together} лет!\n"
            else:
                text += f"📅 Через {days_until} дней: {couple} - {years_together} лет\n"
            
            text += f"   📆 {anniversary_date.strftime('%d.%m.%Y')}\n\n"
        
        await update.message.reply_text(text)

if __name__ == "__main__":
    bot = BirthdayBot()
    bot.run() 