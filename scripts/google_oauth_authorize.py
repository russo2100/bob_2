"""
Скрипт для первой авторизации Google OAuth 2.0

Использование:
    python scripts/google_oauth_authorize.py

Скрипт откроет браузер, запросит разрешение на доступ
и сохранит токен в token.json для последующего использования.
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
import os
import sys

# Scopes для полного доступа
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.read',
]

TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'


def check_files():
    """Проверяет наличие необходимых файлов"""
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"ERROR: File {CREDENTIALS_FILE} not found!")
        print("\nInstruction:")
        print("1. For OAuth 2.0: Download credentials.json from Google Cloud Console")
        return False
    return True


def detect_auth_type():
    """
    Определяет тип авторизации по содержимому credentials.json
    
    Returns:
        str: 'oauth' или 'service_account'
    """
    import json
    with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'installed' in data or 'web' in data:
        return 'oauth'
    elif 'type' in data and data['type'] == 'service_account':
        return 'service_account'
    else:
        return 'unknown'


def authorize_oauth():
    """OAuth 2.0 авторизация для личных аккаунтов"""
    print("\nOAuth 2.0 authorization...")
    print("Browser will open for Google account login")
    
    creds = None
    
    # Проверяем сохранённый токен
    if os.path.exists(TOKEN_FILE):
        print(f"Found existing token: {TOKEN_FILE}")
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"Warning: Token read error: {e}")
            creds = None
    
    # Если токена нет или он истёк
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing token...")
            try:
                creds.refresh(Request())
                print("Token refreshed")
            except Exception as e:
                print(f"Token refresh error: {e}")
                creds = None
        
        if not creds:
            # Новая авторизация
            print("\nRequesting access permission...")
            print("Grant access to all requested resources")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
            
            # Сохраняем токен
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                f.write(creds.to_json())
            
            print(f"\nToken saved to {TOKEN_FILE}")
    else:
        print("Existing token is valid")
    
    # Проверяем результат
    if creds and creds.valid:
        return True
    
    return False


def authorize_service_account():
    """Авторизация сервисного аккаунта"""
    print("\nService Account authorization...")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=SCOPES)
        
        print(f"Service Account: {creds.service_account_email}")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Основная функция"""
    print("=" * 50)
    print("Google API - Авторизация")
    print("=" * 50)
    
    # Проверяем файлы
    if not check_files():
        sys.exit(1)
    
    # Определяем тип авторизации
    auth_type = detect_auth_type()
    
    if auth_type == 'oauth':
        print("\nОбнаружен OAuth 2.0 Client ID")
        success = authorize_oauth()
    elif auth_type == 'service_account':
        print("\nОбнаружен сервисный аккаунт")
        success = authorize_service_account()
    else:
        print("\nНеизвестный формат credentials.json")
        sys.exit(1)
    
    if success:
        print("\n" + "=" * 50)
        print("АВТОРИЗАЦИЯ УСПЕШНА!")
        print("=" * 50)
        print("Теперь вы можете запустить: python main.py --test")
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
