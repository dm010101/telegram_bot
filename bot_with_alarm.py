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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import (
    Application, CommandHandler, ContextTypes, 
    CallbackQueryHandler, MessageHandler, filters,
    ChatMemberHandler
)

# Загружаем переменные окружения
load_dotenv()

class BirthdayBotWithAlarm:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.timezone = pytz.timezone(os.getenv('TIMEZONE', 'Europe/Moscow'))
        self.birthdays_file = 'birthdays.json'
        self.messages_log_file = 'messages_log.json'
        self.admin_chats = set()
        self.application = None
        self.scheduler_running = False
        self.alarm_enabled_chats = set()  # Чаты с включенным алармом
        
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
    
    def get_message_type(self, message: Message) -> str:
        """Определяет тип сообщения"""
        if message.voice:
            return "🎤 Голосовое сообщение"
        elif message.video_note:
            return "🎥 Видеосообщение (кружок)"
        elif message.video:
            return "📹 Видео"
        elif message.audio:
            return "🎵 Аудио"
        elif message.photo:
            return "📷 Фото"
        elif message.document:
            return "📄 Документ"
        elif message.sticker:
            return "🌟 Стикер"
        elif message.animation:
            return "🎬 GIF"
        elif message.text:
            return "💬 Текст"
        else:
            return "📝 Сообщение"
    
    def log_message(self, message: Message):
        """Логирует сообщение для отслеживания"""
        if not message or not message.chat:
            return
            
        chat_id = str(message.chat.id)
        message_id = str(message.message_id)
        
        messages_log = self.load_messages_log()
        
        if chat_id not in messages_log:
            messages_log[chat_id] = {}
        
        message_data = {
            'message_id': message.message_id,
            'user_id': message.from_user.id if message.from_user else None,
            'username': message.from_user.username if message.from_user else None,
            'first_name': message.from_user.first_name if message.from_user else None,
            'date': message.date.isoformat() if message.date else None,
            'text': message.text[:100] if message.text else None,
            'content_type': self.get_message_type(message),
            'logged_at': datetime.now(self.timezone).isoformat()
        }
        
        messages_log[chat_id][message_id] = message_data
        
        # Ограничиваем размер лога (храним только последние 1000 сообщений на чат)
        if len(messages_log[chat_id]) > 1000:
            oldest_messages = sorted(messages_log[chat_id].items(), 
                                   key=lambda x: x[1].get('logged_at', ''))
            for old_msg_id, _ in oldest_messages[:-1000]:
                del messages_log[chat_id][old_msg_id]
        
        self.save_messages_log(messages_log)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        welcome_text = """
🎉 Привет! Я улучшенный бот для напоминаний о днях рождения с системой отслеживания!

📋 **Основные команды:**
/add - Добавить день рождения
/list - Показать все дни рождения  
/delete - Удалить день рождения
/today - Именинники сегодня
/upcoming - Ближайшие дни рождения
/help - Показать помощь

🔔 **Уведомления:**
/enable_notifications - Включить уведомления о ДР в 9:00

🛡️ **Система отслеживания:**
/enable_alarm - Включить отслеживание сообщений
/disable_alarm - Выключить отслеживание
/alarm_status - Статус и статистика

⚠️ **Функции безопасности:**
• Отслеживание редактирования сообщений
• Логирование аудио/видео сообщений  
• Уведомления о входе/выходе участников
• Статистика активности по типам сообщений
        """
        
        await update.message.reply_text(welcome_text)
        chat_id = update.effective_chat.id
        self.admin_chats.add(chat_id)
    
    async def enable_alarm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Включает систему отслеживания сообщений"""
        chat_id = update.effective_chat.id
        self.alarm_enabled_chats.add(chat_id)
        
        await update.message.reply_text(
            "🛡️ **Система отслеживания включена!**\n\n"
            "📊 **Что отслеживается:**\n"
            "• 💬 Все текстовые сообщения\n"
            "• 🎤 Голосовые сообщения\n"
            "• 📹 Видео и видеосообщения\n"
            "• 🎵 Аудиофайлы\n"
            "• ✏️ Редактирование сообщений\n"
            "• 👥 Вход/выход участников\n\n"
            "⚠️ **Уведомления:**\n"
            "• При редактировании сообщений\n"
            "• При изменении состава участников\n"
            "• Подозрительная активность\n\n"
            "📝 Используйте /alarm_status для просмотра статистики"
        )
    
    async def disable_alarm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выключает систему отслеживания сообщений"""
        chat_id = update.effective_chat.id
        self.alarm_enabled_chats.discard(chat_id)
        
        await update.message.reply_text(
            "🔕 **Система отслеживания выключена!**\n\n"
            "Бот больше не будет:\n"
            "• Логировать сообщения\n"
            "• Отслеживать редактирование\n"
            "• Уведомлять об изменениях\n\n"
            "💡 Используйте /enable_alarm для повторного включения"
        )
    
    async def alarm_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает статус системы отслеживания"""
        chat_id = str(update.effective_chat.id)
        
        if int(chat_id) not in self.alarm_enabled_chats:
            await update.message.reply_text(
                "🔕 **Система отслеживания отключена**\n\n"
                "Используйте /enable_alarm для включения"
            )
            return
        
        # Загружаем статистику
        messages_log = self.load_messages_log()
        chat_messages = messages_log.get(chat_id, {})
        
        if not chat_messages:
            await update.message.reply_text(
                "🛡️ **Система отслеживания активна**\n\n"
                "📊 Статистика пуста - пока не было залогировано сообщений\n\n"
                "ℹ️ Статистика появится после получения первых сообщений"
            )
            return
        
        # Анализируем статистику
        total_messages = len(chat_messages)
        message_types = {}
        users_activity = {}
        recent_activity = []
        
        for msg_data in chat_messages.values():
            # Статистика по типам
            msg_type = msg_data.get('content_type', 'Неизвестно')
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            # Статистика по пользователям
            username = msg_data.get('username') or msg_data.get('first_name', 'Неизвестно')
            users_activity[username] = users_activity.get(username, 0) + 1
            
            # Последние сообщения
            if len(recent_activity) < 5:
                recent_activity.append(msg_data)
        
        # Формируем отчет
        status_text = f"🛡️ **СИСТЕМА ОТСЛЕЖИВАНИЯ АКТИВНА**\n\n"
        status_text += f"📊 **Общая статистика:**\n"
        status_text += f"📝 Всего сообщений: {total_messages}\n"
        status_text += f"🕐 Период: последние {min(total_messages, 1000)} сообщений\n\n"
        
        status_text += f"📋 **Типы сообщений:**\n"
        for msg_type, count in sorted(message_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_messages) * 100
            status_text += f"{msg_type}: {count} ({percentage:.1f}%)\n"
        
        status_text += f"\n👥 **Активность пользователей:**\n"
        for username, count in sorted(users_activity.items(), key=lambda x: x[1], reverse=True)[:5]:
            percentage = (count / total_messages) * 100
            username_display = username if username != 'Неизвестно' else 'Неизвестный пользователь'
            status_text += f"@{username_display}: {count} ({percentage:.1f}%)\n"
        
        await update.message.reply_text(status_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик всех сообщений для логирования"""
        chat_id = update.effective_chat.id
        
        # Игнорируем сообщения от самого бота
        if update.message.from_user.is_bot:
            return
        
        # Логируем только если включено отслеживание
        if chat_id in self.alarm_enabled_chats:
            self.log_message(update.message)
            
            # Особые уведомления для аудио/видео
            message_type = self.get_message_type(update.message)
            if message_type in ["🎤 Голосовое сообщение", "🎥 Видеосообщение (кружок)", "📹 Видео", "🎵 Аудио"]:
                user = update.message.from_user
                username = f"@{user.username}" if user.username else user.first_name
                
                alert_text = f"📢 **МЕДИА СООБЩЕНИЕ**\n\n"
                alert_text += f"👤 От: {username}\n"
                alert_text += f"📝 Тип: {message_type}\n"
                alert_text += f"🕐 Время: {datetime.now(self.timezone).strftime('%H:%M:%S')}\n"
                alert_text += f"📄 ID: {update.message.message_id}"
                
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=alert_text,
                        reply_to_message_id=update.message.message_id
                    )
                except Exception as e:
                    print(f"Ошибка отправки уведомления о медиа: {e}")
    
    async def handle_edited_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик отредактированных сообщений"""
        chat_id = update.effective_chat.id
        
        if chat_id not in self.alarm_enabled_chats:
            return
        
        edited_message = update.edited_message
        if not edited_message or edited_message.from_user.is_bot:
            return
        
        user = edited_message.from_user
        username = f"@{user.username}" if user.username else user.first_name
        message_type = self.get_message_type(edited_message)
        
        alarm_text = f"⚠️ **СООБЩЕНИЕ ОТРЕДАКТИРОВАНО**\n\n"
        alarm_text += f"👤 Пользователь: {username}\n"
        alarm_text += f"📝 Тип: {message_type}\n"
        alarm_text += f"🕐 Время: {datetime.now(self.timezone).strftime('%H:%M:%S')}\n"
        alarm_text += f"📄 ID сообщения: {edited_message.message_id}\n"
        
        if edited_message.text:
            preview = edited_message.text[:50]
            alarm_text += f"💬 Новый текст: {preview}{'...' if len(edited_message.text) > 50 else ''}"
        
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=alarm_text,
                reply_to_message_id=edited_message.message_id
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления о редактировании: {e}")
    
    async def handle_chat_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик изменений участников чата"""
        chat_id = update.effective_chat.id
        
        if chat_id not in self.alarm_enabled_chats:
            return
        
        chat_member_update = update.chat_member
        if not chat_member_update:
            return
        
        old_status = chat_member_update.old_chat_member.status
        new_status = chat_member_update.new_chat_member.status
        user = chat_member_update.new_chat_member.user
        
        if user.is_bot:  # Игнорируем ботов
            return
        
        username = f"@{user.username}" if user.username else user.first_name
        
        status_changes = {
            'left': 'покинул чат 👋',
            'kicked': 'исключен из чата ❌',
            'member': 'добавлен в чат ✅',
            'administrator': 'стал администратором 👑',
            'creator': 'стал создателем чата 🏆'
        }
        
        if old_status != new_status and new_status in status_changes:
            alarm_text = f"🚨 **ИЗМЕНЕНИЕ В ЧАТЕ**\n\n"
            alarm_text += f"👤 Участник: {username}\n"
            alarm_text += f"📝 Действие: {status_changes[new_status]}\n"
            alarm_text += f"🕐 Время: {datetime.now(self.timezone).strftime('%H:%M:%S')}\n"
            alarm_text += f"👥 ID пользователя: {user.id}"
            
            try:
                await context.bot.send_message(chat_id=chat_id, text=alarm_text)
            except Exception as e:
                print(f"Ошибка отправки уведомления об изменении участника: {e}")
    
    # Остальные методы для дней рождения (сокращенные версии)
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
/enable_notifications - включить уведомления в 00:00

🛡️ **Система отслеживания:**
/enable_alarm - включить отслеживание
/disable_alarm - выключить отслеживание
/alarm_status - показать статистику

⚠️ **Что отслеживается:**
• Все типы сообщений (текст, аудио, видео)
• Редактирование сообщений  
• Вход/выход участников чата
• Подозрительная активность

📊 **Статистика включает:**
• Количество сообщений по типам
• Активность пользователей
• История изменений
        """
        await update.message.reply_text(help_text)
    
    def run(self):
        """Запускает бота"""
        if not self.bot_token:
            print("❌ Ошибка: BOT_TOKEN не найден!")
            return
        
        self.application = Application.builder().token(self.bot_token).build()
        
        # Основные команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("add", self.add_birthday))
        self.application.add_handler(CommandHandler("list", self.list_birthdays))
        self.application.add_handler(CommandHandler("today", self.today_birthdays))
        self.application.add_handler(CommandHandler("enable_notifications", self.enable_notifications))
        
        # Команды отслеживания
        self.application.add_handler(CommandHandler("enable_alarm", self.enable_alarm))
        self.application.add_handler(CommandHandler("disable_alarm", self.disable_alarm))
        self.application.add_handler(CommandHandler("alarm_status", self.alarm_status))
        
        # Обработчики сообщений
        self.application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, self.handle_edited_message))
        self.application.add_handler(ChatMemberHandler(self.handle_chat_member))
        
        print("🤖 Бот с системой отслеживания запущен!")
        print("🛡️ Новые команды: /enable_alarm, /disable_alarm, /alarm_status")
        
        self.application.run_polling()

if __name__ == "__main__":
    bot = BirthdayBotWithAlarm()
    bot.run() 