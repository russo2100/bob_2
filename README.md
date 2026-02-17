# 🤖 AI Content Pipeline v1.0

Мультиагентная система для автоматического сбора новостей об ИИ → выделения трендов → генерации постов → создания обложек → публикации в Telegram.

**Работает через OpenRouter API + Google API (Gmail, Drive, Sheets)**

## 📋 Описание

Система состоит из 6 агентов, которые работают последовательно:

| Агент | Время | Функция | Выход |
|-------|-------|---------|-------|
| 1. RSS Collector | 09:30 | Парсинг RSS фидов | NewsRaw (source_type=rss) |
| 2. Sonar Scanner | 09:40 | Perplexity API запросы | NewsRaw (source_type=sonar) |
| 3. Trend Selector | 09:50 | Кластеризация и выбор трендов | trends.md |
| 4. Bob Copywriter | 10:10 | Генерация постов | Texts (drafts) |
| 5. Cover Generator | 10:30 | Генерация обложек | data/*.png |
| 6. Publisher | 11:00 | Публикация в Telegram | Telegram Posts |

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка OpenRouter API

1. Зарегистрируйтесь на [OpenRouter.ai](https://openrouter.ai/)
2. Создайте API ключ в [Keys](https://openrouter.ai/keys)
3. Пополните баланс (минимум $5)

📖 **Подробная инструкция:** [OPENROUTER_SETUP.md](./OPENROUTER_SETUP.md)

### 3. Настройка Google API

1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com/)
2. Включите Google Sheets, Drive, Gmail API
3. Создайте сервисный аккаунт и скачайте `credentials.json`
4. Настройте делегирование домена для email `rus967697@gmail.com`

📖 **Подробная инструкция:** [GOOGLE_SETUP.md](./GOOGLE_SETUP.md)

### 4. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
```

**Обязательные переменные:**

```env
# OpenRouter API
OPENROUTER_API_KEY=sk-or-v1-...

# Google API
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-sa@project.iam.gserviceaccount.com
GOOGLE_DELEGATED_EMAIL=rus967697@gmail.com
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=your_channel_id

# RSS
RSS_URLS=https://example.com/rss1,https://example.com/rss2,...
KEYWORDS=AI,artificial intelligence,automation
```

### 5. Запуск

**Разовый запуск всех агентов:**

```bash
python main.py
```

**Запуск с планировщиком (ежедневно в 09:30 UTC+4):**

```bash
python main.py --schedule
```

**Тестовый запуск (проверка соединений):**

```bash
python main.py --test
```

## 📁 Структура проекта

```
bob_2/
├── agents/                 # Агенты 1-6
│   ├── rss_collector.py    # Агент 1: RSS парсинг
│   ├── sonar_scanner.py    # Агент 2: Perplexity API
│   ├── trend_selector.py   # Агент 3: Выбор трендов
│   ├── copywriter.py       # Агент 4: Генерация постов
│   ├── cover_generator.py  # Агент 5: Обложки
│   └── publisher.py        # Агент 6: Публикация
├── storage/                # Клиенты внешних API
│   ├── google_sheets.py    # Google API (Sheets, Drive, Gmail)
│   ├── perplexity_client.py # Perplexity Sonar
│   ├── llm_client.py       # OpenRouter API
│   ├── image_client.py     # DALL-E API
│   ├── telegram_client.py  # Telegram Bot
│   └── local_fs.py         # Локальная ФС
├── tests/                  # Тесты
├── prompts/                # Промты
│   └── bob_2_0.md          # Профиль копирайтера
├── logs/                   # Логи агентов
├── data/                   # Сгенерированные обложки
├── main.py                 # Оркестратор
├── config.py               # Конфигурация
├── utils.py                # Утилиты
├── .env.example            # Шаблон переменных
├── requirements.txt        # Зависимости
├── README.md               # Этот файл
├── OPENROUTER_SETUP.md     # Настройка OpenRouter
└── GOOGLE_SETUP.md         # Настройка Google API
```

## 🧪 Тесты

Запуск всех тестов:

```bash
pytest tests/ -v
```

## 📊 Google Sheets структура

### Лист 1: NewsRaw

| Column | Описание |
|--------|----------|
| date | Дата добавления |
| source_type | Источник (rss/sonar) |
| source | Источник (домен или Perplexity) |
| title | Заголовок новости |
| summary | Краткое описание |
| link | Ссылка на новость |
| brand | Бренд (для Sonar) |
| published_at | Дата публикации |

### Лист 2: Texts

| Column | Описание |
|--------|----------|
| date | Дата создания |
| trend | Название тренда |
| post_text | Текст поста |
| status | Статус (draft/approved) |
| approved | Одобрено (Y/N) |
| posted | Опубликовано (Y/N) |
| cover_image_url | Путь к обложке |
| posted_at | Дата публикации |
| message_id | ID сообщения в Telegram |

## 🔧 Настройка

### OpenRouter модели

В `.env` можно указать модели для каждой задачи:

```env
RSS_MODEL_NAME=openai/gpt-4o-mini
SONAR_MODEL_NAME=openai/gpt-4o-mini
TREND_MODEL_NAME=openai/gpt-4o-mini
COPYWRITER_MODEL_NAME=openai/gpt-4o-mini
COVER_MODEL_NAME=openai/gpt-4o-mini
IMAGE_MODEL_NAME=dall-e-3
```

### Google API

Сервисный аккаунт работает от имени `rus967697@gmail.com` через делегирование домена.

**Требуется Google Workspace** для делегирования.

### Telegram Bot

1. Создайте бота через [@BotFather](https://t.me/botfather)
2. Получите токен
3. Добавьте бота в канал как администратора
4. Получите ID канала (через @getmyid_bot)

## 📝 Логи

Логи сохраняются в папку `logs/`:

- `orchestrator.log` — общий пайплайн
- `rss_collector.log` — парсинг RSS
- `sonar_scanner.log` — Perplexity запросы
- `trend_selector.log` — выбор трендов
- `copywriter.log` — генерация постов
- `cover_generator.log` — генерация обложек
- `publisher.log` — публикация
- `google_api_client.log` — Google API
- `openrouter_*.log` — OpenRouter запросы

## ⚙️ Планировщик

По умолчанию пайплайн запускается ежедневно в **09:30 UTC+4** (Europe/Samara).

Для изменения времени отредактируйте в `main.py`:

```python
SCHEDULER_TIMEZONE = "Europe/Samara"
DAILY_RUN_HOUR = 9
DAILY_RUN_MINUTE = 30
```

## 💰 Стоимость

**Ежедневный пайплайн:** ~$0.20-0.30
- OpenRouter (текст + Sonar): ~$0.005-0.01
- DALL-E (4 изображения): ~$0.16

**Ежемесячно:** ~$6-9

## 🛡️ Безопасность

- Никогда не коммитьте `.env` и `credentials.json`
- Все секреты храните в `.env`
- Используйте `.gitignore` для исключения чувствительных файлов

## 📈 Мониторинг

Проверяйте логи для отслеживания статуса:

```bash
tail -f logs/orchestrator.log
```

Отчёт о работе отправляется на email `rus967697@gmail.com` после каждого запуска.

## 🤝 Вклад

1. Fork репозиторий
2. Создайте ветку (`git checkout -b feature/amazing-feature`)
3. Commit изменений (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

MIT

## 📞 Контакты

Вопросы и предложения — через Issues на GitHub.
