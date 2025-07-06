# 🛠️ Исправление ошибки AttributeError с Updater

## 🔍 Проблема

В логах деплоя на Render обнаружена следующая ошибка:

```
AttributeError: 'Updater' object has no attribute '_Updater__polling_cleanup_cb' and no __dict__ for setting new attributes
```

Эта ошибка связана с несовместимостью версии библиотеки python-telegram-bot 20.8 с текущей конфигурацией.

## 🔧 Решение

### 1. Обновление версии библиотеки

Изменена версия библиотеки python-telegram-bot в файле requirements.txt:

```diff
- python-telegram-bot==20.8
+ python-telegram-bot==20.6
```

Версия 20.6 более стабильна и не содержит проблемы с атрибутом `_Updater__polling_cleanup_cb`.

### 2. Перезапуск деплоя

После обновления версии библиотеки необходимо перезапустить деплой:

1. Загрузите изменения на GitHub
2. В панели управления Render нажмите "Manual Deploy" > "Deploy latest commit"
3. Следите за логами для выявления оставшихся ошибок

## 📋 Проверка результата

После успешного деплоя в логах должны отсутствовать ошибки AttributeError, связанные с Updater.

## 🔍 Дополнительная информация

Если проблема сохраняется, можно попробовать следующие версии библиотеки:
- python-telegram-bot==20.5
- python-telegram-bot==20.4
- python-telegram-bot==20.3

Или использовать последнюю стабильную версию без явного указания:
```
python-telegram-bot>=20.0,<21.0
```

## 📚 Полезные ссылки

- [Документация python-telegram-bot](https://python-telegram-bot.readthedocs.io/)
- [Список версий python-telegram-bot на PyPI](https://pypi.org/project/python-telegram-bot/#history)
- [Устранение неполадок при деплое на Render](https://render.com/docs/troubleshooting-deploys)

# Исправление ошибки с Updater в python-telegram-bot 20.8

При деплое на Render была обнаружена ошибка:

```
AttributeError: 'Updater' object has no attribute '_Updater__polling_cleanup_cb' and no __dict__ for setting new attributes
```

## Причина ошибки

Данная ошибка связана с несовместимостью версии библиотеки python-telegram-bot 20.8 с текущей реализацией бота. В версии 20.8 изменился внутренний механизм работы класса `Updater`.

## Решение проблемы

Есть несколько способов решить эту проблему:

### Способ 1: Понизить версию библиотеки (не сработало)

1. Измените версию библиотеки в файле `requirements.txt`:
   ```
   python-telegram-bot==20.6
   ```

2. Перезапустите деплой на Render.

### Способ 2: Изменить код бота (удалить параметр webhook_url)

Если по каким-то причинам вы хотите использовать версию 20.8, необходимо:

1. Изменить метод `run_webhook()` в файле `web_bot.py`:
   ```python
   async def run_webhook(self):
       # ...
       # Удалить параметр webhook_url
       await application.run_webhook(
           listen="0.0.0.0",
           port=port,
           url_path=webhook_path
       )
   ```

2. Изменить метод `check_and_send_notifications()`:
   ```python
   async def check_and_send_notifications(self):
       # ...
       # Использовать Bot напрямую вместо Application
       from telegram import Bot
       bot = Bot(token=self.bot_token)
       
       # Заменить application.bot на bot
       await bot.send_message(...)
   ```

### Способ 3: Полностью избежать использования Application.builder() и Updater (окончательное решение)

Это решение полностью избегает использования классов Application.builder() и Updater:

1. Добавьте библиотеку aiohttp в `requirements.txt`:
   ```
   aiohttp==3.9.3
   ```

2. Полностью переработайте метод `run_webhook()`:
   ```python
   async def run_webhook(self):
       # ...
       # Создаем бота напрямую без использования Application.builder()
       from telegram import Bot
       from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler
       from aiohttp import web
       
       # Создаем бота
       bot = Bot(token=self.bot_token)
       
       # Создаем диспетчер вручную
       dispatcher = Dispatcher()
       
       # Регистрируем обработчики команд
       dispatcher.add_handler(CommandHandler("start", self.start))
       # ... добавляем остальные обработчики ...
       
       # Устанавливаем веб-хук
       await bot.set_webhook(url=webhook_url)
       
       # Создаем обработчик веб-хуков
       async def webhook_handler(request):
           update_data = await request.json()
           
           # Создаем объект Update из JSON
           from telegram import Update
           update = Update.de_json(data=update_data, bot=bot)
           
           # Обрабатываем обновление через диспетчер
           await dispatcher.process_update(update)
           
           return web.Response()
       
       # Создаем и запускаем веб-приложение с aiohttp
       app = web.Application()
       app.router.add_post(f"/{webhook_path}", webhook_handler)
       app.router.add_get("/", lambda request: web.Response(text="Бот работает!"))
       
       runner = web.AppRunner(app)
       await runner.setup()
       site = web.TCPSite(runner, "0.0.0.0", port)
       
       await site.start()
       # Держим приложение запущенным
       while True:
           await asyncio.sleep(3600)
   ```

## Дополнительная информация

Если вы видите ошибки, связанные с отсутствием атрибутов у объектов (например, `У объекта "None" нет атрибута "reply_text"`), это может быть связано с проблемами в обработке обновлений от Telegram. В этом случае рекомендуется добавить дополнительные проверки на None в обработчиках команд.

## Статус исправления

- [x] Понижена версия библиотеки до 20.6 (не помогло)
- [x] Полностью переработан метод run_webhook() для использования Dispatcher напрямую
- [x] Добавлена библиотека aiohttp в зависимости
- [x] Изменен метод check_and_send_notifications()
- [x] Добавлен обработчик для проверки работоспособности по маршруту "/"
- [ ] Проверена работоспособность бота после изменений 