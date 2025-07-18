# 🔧 Настройка переменных окружения для Render

В этом файле описаны переменные окружения, необходимые для работы бота на платформе Render.

## 📋 Переменные окружения

### Для локального использования (.env файл)

Создайте файл `.env` в корне проекта со следующим содержимым:

```
# Токен бота Telegram (обязательно)
BOT_TOKEN=8012067557:AAGkdq_fUfomek-ee9CRsyjm6BHZ0dEl8NA

# Часовой пояс (по умолчанию Europe/Moscow)
TIMEZONE=Europe/Moscow

# URL вашего сервиса на Render (обязательно для веб-хуков)
WEBHOOK_URL=https://your-app-name.onrender.com

# Порт для веб-сервера (Render установит свой порт автоматически)
PORT=10000
```

### Для настройки на Render

В панели управления Render добавьте следующие переменные окружения:

| Ключ | Значение | Описание |
|------|----------|----------|
| `BOT_TOKEN` | `8012067557:AAGkdq_fUfomek-ee9CRsyjm6BHZ0dEl8NA` | Токен вашего Telegram бота |
| `TIMEZONE` | `Europe/Moscow` | Часовой пояс для корректной работы уведомлений |
| `WEBHOOK_URL` | `https://your-app-name.onrender.com` | URL вашего сервиса на Render |

## 🔄 Как добавить переменные окружения на Render

1. Откройте панель управления Render
2. Перейдите на страницу вашего сервиса
3. Выберите вкладку "Environment"
4. Нажмите кнопку "Add Environment Variable"
5. Добавьте каждую переменную из таблицы выше
6. Нажмите "Save Changes"
7. Перезапустите деплой: "Manual Deploy" > "Deploy latest commit"

## ⚠️ Важные замечания

1. **Безопасность**: Не публикуйте файл `.env` с реальными значениями в публичных репозиториях.
2. **Порт**: Render автоматически устанавливает переменную `PORT`, которую должен использовать ваш сервис.
3. **Webhook URL**: Замените `your-app-name.onrender.com` на реальный URL вашего сервиса на Render.

## 🔍 Проверка настроек

После настройки переменных окружения и деплоя, в логах Render вы должны увидеть:

```
🔍 Проверка переменных окружения:
BOT_TOKEN: ✅ Установлен
TIMEZONE: Europe/Moscow
WEBHOOK_URL: ✅ Установлен
PORT: 10000
```

Если какие-то переменные отсутствуют, проверьте настройки в панели управления Render. 