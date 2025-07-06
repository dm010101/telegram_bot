#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для тестирования Telegram бота в режиме polling
Использует токен бота для подключения к Telegram API
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Загружаем переменные окружения
load_dotenv()

# Токен бота
BOT_TOKEN = "8012067557:AAGkdq_fUfomek-ee9CRsyjm6BHZ0dEl8NA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Привет! Я тестовый бот для проверки подключения.\n"
        "Токен подключен успешно!"
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /info"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username or "Не указано"
    
    await update.message.reply_text(
        f"📊 Информация о чате:\n"
        f"ID чата: {chat_id}\n"
        f"ID пользователя: {user_id}\n"
        f"Имя пользователя: @{username}\n"
        f"\n"
        f"🤖 Информация о боте:\n"
        f"Токен: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "🆘 Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/info - Получить информацию о чате и боте\n"
        "/help - Показать эту справку"
    )

def main():
    """Основная функция для запуска бота"""
    print("🔄 Запуск бота в режиме polling...")
    print(f"🔑 Используется токен: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("help", help_command))
    
    # Запускаем бота
    print("🤖 Бот запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling()

if __name__ == "__main__":
    main() 