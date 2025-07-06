# 🛠️ Исправление ошибок деплоя на Render

## 🔍 Выявленные проблемы

В логах деплоя на Render обнаружены следующие ошибки:

1. **Ошибка: BOT_TOKEN не найден в переменных окружения**
   ```
   Ошибка: BOT_TOKEN не найден в переменных окружения!
   Создайте файл .env и добавьте туда ваш токен бота:
   BOT_TOKEN=your_bot_token_here
   ```

2. **Ошибка с портами**
   ```
   Port scan timeout reached, no open ports detected. Bind your service to at least one port.
   ```

## 🔧 Решения проблем

### 1. Настройка переменных окружения на Render

1. Откройте панель управления Render
2. Перейдите в настройки вашего сервиса (вкладка "Environment")
3. Добавьте следующие переменные окружения:
   - `BOT_TOKEN`: `8012067557:AAGkdq_fUfomek-ee9CRsyjm6BHZ0dEl8NA`
   - `TIMEZONE`: `Europe/Moscow`
   - `WEBHOOK_URL`: URL вашего сервиса на Render (например, `https://birthday-bot.onrender.com`)

### 2. Исправление проблемы с портами

Необходимо явно указать порт, который будет использовать сервис. Для этого:

1. Обновите файл `web_bot.py`, добавив явное указание порта:

```python
# В методе run_webhook добавьте:
port = int(os.environ.get("PORT", 10000))
print(f"🔄 Запуск на порту: {port}")

# И убедитесь, что этот порт используется:
await application.run_webhook(
    listen="0.0.0.0",
    port=port,
    url_path=webhook_path,
    webhook_url=webhook_url
)
```

2. Добавьте переменную окружения `PORT` в Render с любым значением (например, `10000`). Render автоматически заменит это значение на свое.

### 3. Создание файла .env на сервере

Если вы хотите создать файл `.env` непосредственно на сервере Render, добавьте следующий код в начало файла `web_bot.py`:

```python
# Создаем файл .env, если он не существует
if not os.path.exists('.env'):
    with open('.env', 'w') as f:
        f.write(f"BOT_TOKEN={os.environ.get('BOT_TOKEN', '')}\n")
        f.write(f"TIMEZONE={os.environ.get('TIMEZONE', 'Europe/Moscow')}\n")
        f.write(f"WEBHOOK_URL={os.environ.get('WEBHOOK_URL', '')}\n")
    print("✅ Файл .env создан на основе переменных окружения")
```

### 4. Проверка переменных окружения

Добавьте отладочный вывод в начало файла `web_bot.py`:

```python
print("🔍 Проверка переменных окружения:")
print(f"BOT_TOKEN: {'✅ Установлен' if os.environ.get('BOT_TOKEN') else '❌ Отсутствует'}")
print(f"TIMEZONE: {os.environ.get('TIMEZONE', 'Не установлен')}")
print(f"WEBHOOK_URL: {'✅ Установлен' if os.environ.get('WEBHOOK_URL') else '❌ Отсутствует'}")
print(f"PORT: {os.environ.get('PORT', 'Не установлен')}")
```

## 🚀 Перезапуск деплоя

После внесения изменений:

1. Загрузите изменения на GitHub
2. В панели управления Render нажмите "Manual Deploy" > "Deploy latest commit"
3. Следите за логами для выявления оставшихся ошибок

## 📚 Полезные ссылки

- [Документация Render по переменным окружения](https://render.com/docs/environment-variables)
- [Документация Render по портам](https://render.com/docs/web-services#ports)
- [Устранение неполадок при деплое](https://render.com/docs/troubleshooting-deploys) 