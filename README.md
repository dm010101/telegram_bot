# 🎉 Telegram Бот для Напоминаний о Днях Рождения

Этот бот поможет вам никогда не забывать о днях рождения друзей и близких! Он может хранить даты, отправлять красивые поздравления и напоминать о предстоящих праздниках.

## ✨ Возможности

- 📅 **Добавление дней рождения** с поддержкой года рождения или без него
- 🎂 **Автоматические поздравления** каждый день в 00:00 (полночь)
- 📋 **Список всех именинников** с сортировкой по датам
- 🗑️ **Удаление записей** через удобное меню
- 🎉 **Проверка именинников сегодня** с персональными поздравлениями
- 📅 **Ближайшие дни рождения** на неделю вперед
- 🌍 **Поддержка часовых поясов**
- 💬 **Красивые поздравления** из набора шаблонов
- 🚀 **Поддержка хостинга на Render** через веб-хуки

## 🚀 Установка и настройка

### 1. Создание Telegram бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/botfather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен бота

### 2. Локальный запуск

1. Клонируйте репозиторий:
   ```
   git clone https://github.com/ваш-логин/telegram_bot.git
   cd telegram_bot
   ```

2. Создайте виртуальное окружение и установите зависимости:
   ```
   python -m venv venv
   source venv/bin/activate  # Для Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Создайте файл `.env` с вашим токеном:
   ```
   BOT_TOKEN=ваш_токен_бота
   TIMEZONE=Europe/Moscow
   ```

4. Запустите бота:
   ```
   python bot.py
   ```

### 3. Деплой на Render

Для деплоя бота на платформу Render следуйте инструкциям в файлах:
- `МИГРАЦИЯ_НА_RENDER.md` - краткая инструкция по миграции
- `ПОДКЛЮЧЕНИЕ_РЕПОЗИТОРИЯ.md` - инструкция по подключению репозитория GitHub
- `ДЕПЛОЙ_НА_RENDER.md` - подробная инструкция по деплою

#### Основные шаги:
1. Создайте репозиторий на GitHub и загрузите код
2. Создайте аккаунт на Render и подключите репозиторий
3. Настройте переменные окружения
4. Запустите деплой

## 📝 Использование

### Основные команды:

- `/start` - Начало работы с ботом
- `/add` - Добавить день рождения (формат: `/add Имя ДД.ММ` или `/add Имя ДД.ММ.ГГГГ`)
- `/list` - Показать все дни рождения
- `/delete` - Удалить день рождения
- `/today` - Проверить именинников сегодня
- `/upcoming` - Показать ближайшие дни рождения (на неделю)
- `/help` - Показать справку

### Примеры:

```
/add Мария 25.12
/add Петр 08.07.1985
```

## 🛠️ Файлы проекта

- `bot.py` - Основной файл бота (для локального запуска)
- `web_bot.py` - Версия бота с поддержкой веб-хуков (для Render)
- `requirements.txt` - Зависимости проекта
- `keep_alive.py` - Скрипт для поддержания бота активным на бесплатном плане Render

## 🤝 Вклад в проект

Предложения и улучшения приветствуются! Вы можете:
1. Форкнуть репозиторий
2. Создать новую ветку (`git checkout -b feature/amazing-feature`)
3. Закоммитить изменения (`git commit -m 'Add amazing feature'`)
4. Отправить изменения в ветку (`git push origin feature/amazing-feature`)
5. Открыть Pull Request

## 🎨 Примеры использования

### Добавление дня рождения
```
/add Мария 25.12
✅ День рождения Мария (25.12) успешно добавлен!
```

### Добавление дня рождения с годом
```
/add Иван 15.08.1985
✅ День рождения Иван (15.08 38 лет) успешно добавлен!
```

### Просмотр списка
```
/list
📅 Список дней рождения:

🎂 Мария - 25.12
🎂 Иван - 15.08.1985 (38 лет)
🎂 Анна - 03.03.1992 (31 лет)
```

### Проверка сегодняшних именинников
```
/today
🎉 Сегодня день рождения у:

🎉 Поздравляем с днём рождения, Мария! Желаем счастья, здоровья и исполнения всех желаний! 🎂
```

### Ближайшие дни рождения
```
/upcoming
📅 Ближайшие дни рождения (на неделю):

🎂 Анна - завтра (03.03)
🎈 Иван - через 5 дней (15.08)
```

## 🔔 Автоматические уведомления

Бот может автоматически отправлять поздравления каждый день в 00:00 (полночь). Для включения используйте команду `/enable_notifications`.

После включения бот будет:
- Проверять каждый день в 00:00, есть ли именинники
- Отправлять персональные поздравления для каждого именинника
- Использовать случайные поздравления из набора шаблонов

## 📁 Структура файлов

```
├── main.py              # Основной файл бота (polling режим)
├── web_bot.py           # Версия бота для Render (webhook режим)
├── Procfile             # Файл для Render с командой запуска
├── render.yaml          # Конфигурация для Render
├── main_improved.py     # Улучшенная версия с лучшим планировщиком
├── start.py             # Автоматическая настройка и запуск
├── demo.py              # Демонстрация работы с тестовыми данными
├── requirements.txt     # Зависимости Python
├── birthdays.json       # База данных дней рождения (с тестовыми данными)
├── .env                 # Переменные окружения (создайте самостоятельно)
├── README.md            # Подробная документация
├── БЫСТРЫЙ_СТАРТ.md     # Краткая инструкция
└── ПРИМЕРЫ.md           # Примеры использования команд
```

## 🧪 Тестовые данные

В файле `birthdays.json` уже добавлены тестовые дни рождения (18 человек) для демонстрации работы бота. Чтобы посмотреть, как это выглядит:

```bash
python3 demo.py
```

## 🛠️ Технические детали

- **Python 3.7+** - Минимальная версия Python
- **python-telegram-bot** - Библиотека для работы с Telegram API
- **JSON** - Хранение данных в файле `birthdays.json`
- **Schedule** - Планировщик для автоматических уведомлений
- **pytz** - Работа с часовыми поясами
- **asyncio** - Асинхронная обработка команд
- **Webhook** - Режим работы на Render через веб-хуки

## 🔄 Режимы работы бота

### Polling (локальный запуск)
- Бот активно опрашивает сервер Telegram на наличие новых сообщений
- Используется для локального запуска и тестирования
- Запуск: `python main.py`

### Webhook (на хостинге Render)
- Telegram сам отправляет обновления на ваш сервер
- Более эффективно для постоянно работающего бота
- Требует публичный URL (предоставляется Render)
- Запуск: `python web_bot.py` (или через Procfile на Render)

## 🔒 Безопасность

- Данные хранятся локально в файле `birthdays.json`
- Каждый чат имеет свою изолированную базу дней рождения
- Токен бота хранится в переменных окружения
- Никакие данные не передаются третьим лицам

## 🐛 Устранение неполадок

### Бот не запускается
- Проверьте, что создан файл `.env` с правильным токеном
- Убедитесь, что установлены все зависимости: `pip install -r requirements.txt`
- Проверьте, что токен бота действителен

### Проблемы с деплоем на Render
- Убедитесь, что все переменные окружения заданы правильно
- Проверьте логи на Render для выявления ошибок
- Проверьте, что URL веб-хука указан правильно

### Уведомления не приходят
- Убедитесь, что вызвали команду `/enable_notifications`
- Проверьте часовой пояс в файле `.env`
- Убедитесь, что бот запущен и работает

### Ошибки с датами
- Используйте формат ДД.ММ или ДД.ММ.ГГГГ
- Проверьте корректность введенной даты
- Помните, что день и месяц должны быть разделены точками

## 🤝 Поддержка

Если у вас возникли вопросы или проблемы:
1. Проверьте этот README
2. Убедитесь, что все зависимости установлены
3. Проверьте логи в консоли при запуске бота

## 📝 Лицензия

Этот проект распространяется свободно. Вы можете использовать, изменять и распространять код по своему усмотрению.

---

**Приятного использования! 🎉** 