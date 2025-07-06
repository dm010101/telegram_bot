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
        self.admin_chats = set()  # Чаты где бот может отправлять уведомления
        self.application = None
        self.scheduler_running = False
        self.tracked_messages = {}  # Для отслеживания сообщений
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
            'text': message.text[:100] if message.text else None,  # Первые 100 символов
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
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        welcome_text = """
🎉 Привет! Я бот для напоминаний о днях рождения с функцией отслеживания!

📋 Доступные команды:
/add - Добавить день рождения
/list - Показать все дни рождения
/delete - Удалить день рождения
/today - Проверить, есть ли именинники сегодня
/upcoming - Ближайшие дни рождения (на неделю)
/help - Показать помощь

🔔 Уведомления:
/enable_notifications - Включить уведомления о ДР в 9:00
/enable_alarm - Включить отслеживание сообщений
/disable_alarm - Выключить отслеживание сообщений
/alarm_status - Статус системы отслеживания

🛡️ Система отслеживания сообщений поможет вам контролировать активность в чате!
        """
        
        await update.message.reply_text(welcome_text)
        
        # Добавляем чат в список для уведомлений
        chat_id = update.effective_chat.id
        self.admin_chats.add(chat_id)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
🆘 Помощь по командам:

📅 **Дни рождения:**
🔸 /add - Добавить новый день рождения
   Формат: /add Иван 15.03 или /add Иван 15.03.1990
🔸 /list - Показать всех именинников
🔸 /delete - Удалить день рождения
🔸 /today - Проверить именинников сегодня
🔸 /upcoming - Ближайшие дни рождения

🔔 **Уведомления:**
🔸 /enable_notifications - Включить уведомления о ДР
🔸 /enable_alarm - Включить отслеживание сообщений
🔸 /disable_alarm - Выключить отслеживание сообщений
🔸 /alarm_status - Статус системы отслеживания

🛡️ **Система отслеживания:**
- Логирует все сообщения в чате
- Отслеживает редактирование сообщений
- Уведомляет о подозрительной активности
- Показывает статистику по типам сообщений

📝 **Примеры:**
/add Мария 25.12
/add Петр 08.07.1985
/enable_alarm
        """
        await update.message.reply_text(help_text)
    
    async def enable_alarm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Включает систему отслеживания сообщений"""
        chat_id = update.effective_chat.id
        self.alarm_enabled_chats.add(chat_id)
        
        await update.message.reply_text(
            "🛡️ Система отслеживания сообщений включена!\n\n"
            "📊 Теперь бот будет:\n"
            "• Логировать все сообщения\n"
            "• Отслеживать редактирование\n"
            "• Уведомлять о подозрительной активности\n"
            "• Вести статистику по типам сообщений\n\n"
            "📝 Используйте /alarm_status для просмотра статистики"
        )
    
    async def disable_alarm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выключает систему отслеживания сообщений"""
        chat_id = update.effective_chat.id
        self.alarm_enabled_chats.discard(chat_id)
        
        await update.message.reply_text(
            "🔕 Система отслеживания сообщений выключена!\n\n"
            "Бот больше не будет логировать сообщения в этом чате."
        )
    
    async def alarm_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает статус системы отслеживания"""
        chat_id = str(update.effective_chat.id)
        
        if int(chat_id) not in self.alarm_enabled_chats:
            await update.message.reply_text(
                "🔕 Система отслеживания сообщений отключена\n\n"
                "Используйте /enable_alarm для включения"
            )
            return
        
        # Загружаем статистику
        messages_log = self.load_messages_log()
        chat_messages = messages_log.get(chat_id, {})
        
        if not chat_messages:
            await update.message.reply_text(
                "🛡️ Система отслеживания включена\n\n"
                "📊 Статистика пуста - пока не было залогировано сообщений"
            )
            return
        
        # Анализируем статистику
        total_messages = len(chat_messages)
        message_types = {}
        users_activity = {}
        
        for msg_data in chat_messages.values():
            # Статистика по типам
            msg_type = msg_data.get('content_type', 'Неизвестно')
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            # Статистика по пользователям
            username = msg_data.get('username') or msg_data.get('first_name', 'Неизвестно')
            users_activity[username] = users_activity.get(username, 0) + 1
        
        # Формируем отчет
        status_text = f"🛡️ **Система отслеживания активна**\n\n"
        status_text += f"📊 **Общая статистика:**\n"
        status_text += f"📝 Всего сообщений: {total_messages}\n\n"
        
        status_text += f"📋 **По типам сообщений:**\n"
        for msg_type, count in sorted(message_types.items(), key=lambda x: x[1], reverse=True)[:5]:
            status_text += f"{msg_type}: {count}\n"
        
        status_text += f"\n👥 **Топ активных пользователей:**\n"
        for username, count in sorted(users_activity.items(), key=lambda x: x[1], reverse=True)[:5]:
            status_text += f"@{username}: {count} сообщений\n"
        
        await update.message.reply_text(status_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик всех сообщений для логирования"""
        chat_id = update.effective_chat.id
        
        # Логируем только если включено отслеживание
        if chat_id in self.alarm_enabled_chats:
            self.log_message(update.message)
    
    async def handle_edited_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик отредактированных сообщений"""
        chat_id = update.effective_chat.id
        
        if chat_id not in self.alarm_enabled_chats:
            return
        
        edited_message = update.edited_message
        if not edited_message:
            return
        
        # Получаем информацию о пользователе
        user = edited_message.from_user
        username = f"@{user.username}" if user.username else user.first_name
        message_type = self.get_message_type(edited_message)
        
        # Отправляем уведомление о редактировании
        alarm_text = f"⚠️ **УВЕДОМЛЕНИЕ О РЕДАКТИРОВАНИИ**\n\n"
        alarm_text += f"👤 Пользователь: {username}\n"
        alarm_text += f"📝 Тип: {message_type}\n"
        alarm_text += f"🕐 Время: {datetime.now(self.timezone).strftime('%H:%M:%S')}\n"
        alarm_text += f"📄 ID сообщения: {edited_message.message_id}\n"
        
        if edited_message.text:
            preview = edited_message.text[:50]
            alarm_text += f"💬 Текст: {preview}{'...' if len(edited_message.text) > 50 else ''}"
        
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
        
        username = f"@{user.username}" if user.username else user.first_name
        
        # Уведомляем о важных изменениях
        if old_status != new_status:
            status_changes = {
                'left': 'покинул чат',
                'kicked': 'исключен из чата',
                'member': 'добавлен в чат',
                'administrator': 'стал администратором',
                'creator': 'стал создателем чата'
            }
            
            if new_status in status_changes:
                alarm_text = f"🚨 **ИЗМЕНЕНИЕ В ЧАТЕ**\n\n"
                alarm_text += f"👤 Пользователь: {username}\n"
                alarm_text += f"📝 Действие: {status_changes[new_status]}\n"
                alarm_text += f"🕐 Время: {datetime.now(self.timezone).strftime('%H:%M:%S')}"
                
                try:
                    await context.bot.send_message(chat_id=chat_id, text=alarm_text)
                except Exception as e:
                    print(f"Ошибка отправки уведомления об изменении участника: {e}")
    
    # Остальные методы остаются без изменений (добавление ДР, список и т.д.)
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
        
        # Новые команды для системы отслеживания
        self.application.add_handler(CommandHandler("enable_alarm", self.enable_alarm))
        self.application.add_handler(CommandHandler("disable_alarm", self.disable_alarm))
        self.application.add_handler(CommandHandler("alarm_status", self.alarm_status))
        
        # Обработчики для отслеживания сообщений
        self.application.add_handler(MessageHandler(filters.ALL, self.handle_message))
        self.application.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, self.handle_edited_message))
        self.application.add_handler(ChatMemberHandler(self.handle_chat_member))
        
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        print("🤖 Бот с системой отслеживания запущен!")
        print("📋 Команды ДР: /start, /add, /list, /delete, /today, /upcoming, /help")
        print("🛡️ Команды отслеживания: /enable_alarm, /disable_alarm, /alarm_status")
        
        # Запускаем планировщик
        self.start_scheduler()
        
        # Запускаем бота
        self.application.run_polling()

if __name__ == "__main__":
    bot = BirthdayBotWithAlarm()
    bot.run() 