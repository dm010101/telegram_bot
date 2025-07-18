# 🚀 Деплой Telegram бота на Render

Это подробная инструкция по размещению бота для напоминаний о днях рождения на хостинге [Render](https://render.com/).

## 📋 Подготовка

### 1. Требования
- Аккаунт на [Render](https://render.com/) (можно зарегистрироваться бесплатно)
- Репозиторий с кодом бота (GitHub, GitLab или Bitbucket)
- Токен бота от [BotFather](https://t.me/botfather)

### 2. Структура файлов
Убедитесь, что в вашем репозитории есть следующие файлы:
- `web_bot.py` - основной файл бота с поддержкой веб-хуков
- `Procfile` - файл с командой запуска для Render
- `render.yaml` - конфигурация для Render
- `requirements.txt` - список зависимостей Python

## 🔧 Настройка проекта на Render

### 1. Создание нового Web Service

1. Войдите в свой аккаунт на [Render](https://render.com/)
2. Нажмите кнопку "New" в верхнем правом углу
3. Выберите "Web Service"
4. Подключите свой репозиторий с кодом бота
   - Если репозиторий приватный, настройте доступ по SSH

### 2. Настройка параметров Web Service

Заполните следующие поля:
- **Name**: имя вашего сервиса (например, "birthday-bot")
- **Region**: выберите ближайший к вам регион
- **Branch**: ветка репозитория (обычно "main" или "master")
- **Runtime**: выберите "Python"
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python web_bot.py`

### 3. Настройка переменных окружения

В разделе "Environment Variables" добавьте следующие переменные:

| Ключ | Значение | Описание |
|------|----------|----------|
| `BOT_TOKEN` | ваш_токен | Токен бота от BotFather |
| `TIMEZONE` | Europe/Moscow | Часовой пояс (измените при необходимости) |
| `WEBHOOK_URL` | https://your-app-name.onrender.com | URL вашего приложения на Render |
| `PORT` | 10000 | Порт для веб-сервера |

> ⚠️ **Важно**: Замените `your-app-name` на имя вашего сервиса на Render.

### 4. Дополнительные настройки

- **Plan**: выберите "Free" для бесплатного плана
  - Бесплатный план имеет ограничения: сервис "засыпает" после 15 минут неактивности
  - Для постоянной работы рекомендуется "Individual" план ($7/месяц)
- **Auto-Deploy**: включите для автоматического деплоя при обновлении репозитория

## 🚀 Деплой

1. Нажмите кнопку "Create Web Service"
2. Дождитесь завершения процесса деплоя (это может занять несколько минут)
3. После успешного деплоя вы увидите URL вашего сервиса

## ✅ Проверка работы

### 1. Проверка логов

1. Перейдите на страницу вашего сервиса на Render
2. Откройте вкладку "Logs"
3. Убедитесь, что нет ошибок и бот успешно запустился
4. Вы должны увидеть сообщение:
   ```
   🤖 Бот запущен на веб-хуке: https://your-app-name.onrender.com/telegram
   📋 Доступные команды: /start, /add, /list, /delete, /today, /upcoming, /help
   ```

### 2. Проверка бота в Telegram

1. Откройте Telegram и найдите своего бота
2. Отправьте команду `/start`
3. Бот должен ответить приветственным сообщением
4. Проверьте другие команды: `/help`, `/today`, `/upcoming`

## 🔄 Обновление бота

### 1. Обновление кода

1. Внесите изменения в код бота в вашем репозитории
2. Закоммитьте и отправьте изменения в ветку, подключенную к Render
3. Если включен Auto-Deploy, Render автоматически обновит ваш сервис

### 2. Ручное обновление

Если Auto-Deploy выключен:
1. Перейдите на страницу вашего сервиса на Render
2. Нажмите кнопку "Manual Deploy" > "Deploy latest commit"

## 🛠️ Устранение неполадок

### Бот не отвечает

1. **Проверьте логи** на Render для выявления ошибок
2. **Убедитесь, что бот не "заснул"** (на бесплатном плане)
   - Откройте URL вашего сервиса в браузере для "пробуждения"
3. **Проверьте переменные окружения**
   - Особенно `BOT_TOKEN` и `WEBHOOK_URL`

### Ошибка 404 при открытии URL

1. Убедитесь, что путь веб-хука настроен правильно
2. URL должен быть в формате `https://your-app-name.onrender.com/telegram`

### Проблемы с веб-хуком

1. Проверьте, что Telegram может достучаться до вашего сервиса
2. Убедитесь, что URL веб-хука указан правильно в переменной `WEBHOOK_URL`
3. Попробуйте перезапустить сервис на Render

## 💡 Советы

### Поддержание бота активным

Для бесплатного плана Render, чтобы бот не "засыпал":
1. Настройте периодические пинги вашего сервиса (каждые 14 минут)
2. Используйте сервисы вроде [UptimeRobot](https://uptimerobot.com/) для мониторинга

### Мониторинг использования ресурсов

1. На странице вашего сервиса на Render перейдите в раздел "Metrics"
2. Отслеживайте использование CPU, памяти и других ресурсов
3. Если бот потребляет много ресурсов, оптимизируйте код

### Резервное копирование данных

Render не гарантирует постоянное хранение файлов. Для сохранения данных:
1. Периодически делайте резервные копии файла `birthdays.json`
2. Рассмотрите возможность использования внешней базы данных вместо JSON-файла

## 📝 Заключение

Теперь ваш бот для напоминаний о днях рождения размещен на Render и доступен 24/7! Он будет автоматически отправлять поздравления и отвечать на команды пользователей.

Если у вас возникли вопросы или проблемы, обратитесь к документации Render или создайте issue в репозитории проекта.

**Приятного использования! 🎉** 