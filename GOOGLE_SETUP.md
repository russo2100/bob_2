# 🔐 Настройка Google API — Полное руководство

## Вариант 1: Сервисный аккаунт (Google Workspace)

**Рекомендуется для бизнеса и production**

### Шаг 1-6: См. [GOOGLE_SETUP.md](./GOOGLE_SETUP.md)

### Преимущества
- ✅ Простая настройка
- ✅ Не требует взаимодействия с пользователем
- ✅ Стабильная работа

### Ограничения
- ❌ Требует Google Workspace для делегирования домена
- ❌ Не работает с личными @gmail.com аккаунтами

---

## Вариант 2: OAuth 2.0 (Личные Gmail аккаунты)

**Рекомендуется для личных аккаунтов @gmail.com**

### Шаг 1: Создание проекта в Google Cloud Console

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект: `AI Content Pipeline`
3. Запомните **Project ID**

### Шаг 2: Включение API

В разделе **APIs & Services > Library** включите:

- ✅ **Gmail API**
- ✅ **Google Drive API**
- ✅ **Google Sheets API**

### Шаг 3: Создание OAuth 2.0 Client ID

1. Перейдите в **APIs & Services > Credentials**
2. Нажмите **Create Credentials > OAuth client ID**
3. Выберите тип приложения: **Desktop app** (или **Web application** для ботов)
4. Нажмите **Create**
5. Скачайте файл `credentials.json` (OAuth 2.0 Client ID)

### Шаг 4: Настройка OAuth consent screen

1. Перейдите в **APIs & Services > OAuth consent screen**
2. Выберите **External** (для личного использования)
3. Заполните:
   - App name: `AI Content Pipeline`
   - User support email: ваш email
   - Developer contact: ваш email
4. Нажмите **Save and Continue**
5. **Scopes**: пропустите (добавим в коде)
6. **Test users**: добавьте ваш email
7. Нажмите **Save and Continue**

### Шаг 5: Установка зависимостей

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Шаг 6: Первая авторизация

Запустите скрипт авторизации:

```bash
python scripts/google_oauth_authorize.py
```

Скрипт:
1. Откроет браузер
2. Запросит разрешение на доступ
3. Сохранит токен в `token.json`

### Шаг 7: Настройка .env

```env
# Google API — OAuth 2.0
GOOGLE_AUTH_METHOD=oauth  # или "service_account"
GOOGLE_CREDENTIALS_PATH=credentials.json  # OAuth 2.0 Client ID
GOOGLE_TOKEN_PATH=token.json  # Сохранённый токен
GOOGLE_DELEGATED_EMAIL=your-email@gmail.com  # Ваш email
GOOGLE_SPREADSHEET_ID=ваш_id_таблицы
GOOGLE_DRIVE_FOLDER_ID=ваш_id_папки (опционально)
```

---

## Сравнение методов

| Характеристика | Сервисный аккаунт | OAuth 2.0 |
|---------------|------------------|-----------|
| Тип аккаунта | Google Workspace | Личный Gmail |
| Файл credentials | Service Account JSON | OAuth 2.0 Client ID |
| Дополнительный файл | — | token.json |
| Верификация приложения | Требуется | Требуется для production |
| Автоматическое обновление токена | ✅ | ✅ |
| Срок действия токена | Бессрочно | 1 час (обновляется) |

---

## Scopes (Области доступа)

Система запрашивает следующие разрешения:

```python
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',  # Таблицы
    'https://www.googleapis.com/auth/drive',         # Диск
    'https://www.googleapis.com/auth/gmail.send',    # Отправка писем
    'https://www.googleapis.com/auth/gmail.read',    # Чтение писем
]
```

### Уровень доступа

| Scope | Уровень | Описание |
|-------|---------|----------|
| `spreadsheets` | Sensitive | Создание, чтение, запись таблиц |
| `drive` | Restricted | Полный доступ ко всем файлам |
| `gmail.send` | Restricted | Отправка писем от вашего имени |
| `gmail.read` | Restricted | Чтение писем |

**Restricted scopes** требуют верификации приложения для публикации. Для личного использования достаточно добавить email в тестовые пользователи.

---

## Скрипт авторизации

Создайте файл `scripts/google_oauth_authorize.py`:

```python
"""Скрипт для первой авторизации Google OAuth 2.0"""

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import pickle
import os

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.read',
]

def main():
    creds = None
    
    # Проверяем сохранённый токен
    if os.path.exists('token.json'):
        with open('token.json', 'r') as f:
            creds = Credentials.from_authorized_user_file(f, SCOPES)
    
    # Если токена нет или он истёк
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Сохраняем токен
        with open('token.json', 'w') as f:
            f.write(creds.to_json())
        
        print("✅ Токен сохранён в token.json")
    else:
        print("✅ Токен действителен")

if __name__ == '__main__':
    main()
```

---

## Решение проблем

### Ошибка "The app has no verified scopes"

Для личного использования:
1. Добавьте email в **Test users** в OAuth consent screen
2. При авторизации нажмите **Continue** (не Go to Production)

### Ошибка "Token expired"

Запустите скрипт авторизации повторно:
```bash
python scripts/google_oauth_authorize.py
```

### Ошибка "credentials.json not found"

Убедитесь, что скачали правильный файл:
- **Service Account**: JSON с ключом сервисного аккаунта
- **OAuth 2.0**: JSON с `client_id`, `client_secret`, `redirect_uris`

### Ошибка "Access blocked: This app's request is invalid"

Проверьте:
1. OAuth consent screen настроен
2. Email добавлен в **Test users**
3. Scopes в коде совпадают с запрошенными

---

## Production развёртывание

### Для Google Workspace

1. Пройдите верификацию приложения в [Security Assessment](https://console.cloud.google.com/apis/credentials/consent)
2. Используйте сервисный аккаунт с domain-wide delegation

### Для личных аккаунтов

1. Пройдите верификацию (требуется для >100 пользователей)
2. Используйте OAuth 2.0 с refresh token
3. Храните токен в безопасном месте

---

## Дополнительные ресурсы

- [OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Gmail API Scopes](https://developers.google.com/gmail/api/auth/scopes)
- [Google Drive API](https://developers.google.com/drive/api/v3/about-auth)
- [Google Sheets API](https://developers.google.com/sheets/api/guides/authorizing)
