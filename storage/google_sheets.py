"""
Клиент для работы с Google API (Sheets, Drive, Gmail)

Поддерживает два метода авторизации:
1. OAuth 2.0 (личные Gmail аккаунты)
2. Service Account (Google Workspace)
"""

import gspread
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import os
import json

from config import (
    get_google_credentials_path,
    get_google_spreadsheet_id,
    get_google_delegated_email,
    get_google_drive_folder_id,
    get_env
)
from utils import setup_logger


# Scopes для полного доступа
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.read',
]


class GoogleAPIClient:
    """Универсальный клиент для работы с Google API"""
    
    def __init__(self):
        """Инициализация клиента с использованием OAuth 2.0 или Service Account"""
        self.logger = setup_logger("GoogleAPIClient", "google_api_client.log")
        
        credentials_path = get_google_credentials_path()
        self.spreadsheet_id = get_google_spreadsheet_id()
        self.delegated_email = get_google_delegated_email()
        self.drive_folder_id = get_google_drive_folder_id()
        self.token_path = get_env("GOOGLE_TOKEN_PATH", "token.json")
        
        # Определяем тип авторизации
        auth_type = self._detect_auth_type(credentials_path)
        self.logger.info(f"Метод авторизации: {auth_type}")
        
        try:
            if auth_type == 'oauth':
                self.creds = self._load_oauth_credentials(credentials_path)
            else:  # service_account
                self.creds = self._load_service_account_credentials(credentials_path)
            
            # Инициализация клиентов
            self.sheets_client = gspread.authorize(self.creds)
            self.drive_service = build("drive", "v3", credentials=self.creds)
            self.gmail_service = build("gmail", "v1", credentials=self.creds)
            
            self.spreadsheet = self.sheets_client.open_by_key(self.spreadsheet_id)
            
            self.logger.info(f"Google API Client инициализирован (email: {self.delegated_email})")
            
        except FileNotFoundError:
            self.logger.error(f"Файл credentials не найден: {credentials_path}")
            self.logger.info("Запустите: python scripts/google_oauth_authorize.py")
            raise
        except Exception as e:
            self.logger.error(f"Ошибка инициализации Google API: {e}")
            raise
    
    def _detect_auth_type(self, credentials_path: str) -> str:
        """
        Определяет тип авторизации по файлу credentials.
        
        Returns:
            'oauth' или 'service_account'
        """
        try:
            with open(credentials_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'installed' in data or 'web' in data:
                return 'oauth'
            elif 'type' in data and data['type'] == 'service_account':
                return 'service_account'
            else:
                return 'oauth'  # По умолчанию OAuth
        except:
            return 'oauth'
    
    def _load_oauth_credentials(self, credentials_path: str):
        """Загружает OAuth 2.0 credentials"""
        creds = None
        
        # Проверяем сохранённый токен
        if os.path.exists(self.token_path):
            try:
                creds = OAuthCredentials.from_authorized_user_file(self.token_path, SCOPES)
                self.logger.info(f"Токен загружен из {self.token_path}")
            except Exception as e:
                self.logger.warning(f"Ошибка чтения токена: {e}")
                creds = None
        
        # Если токена нет или он истёк
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Обновление токена...")
                try:
                    creds.refresh(Request())
                    self.logger.info("Токен обновлён")
                except Exception as e:
                    self.logger.error(f"Ошибка обновления токена: {e}")
                    creds = None
            
            if not creds:
                # Запускаем авторизацию
                self.logger.info("Запуск OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)
                creds = flow.run_local_server(port=0, open_browser=False)
                
                # Сохраняем токен
                with open(self.token_path, 'w', encoding='utf-8') as f:
                    f.write(creds.to_json())
                self.logger.info(f"Токен сохранён в {self.token_path}")
        
        return creds
    
    def _load_service_account_credentials(self, credentials_path: str):
        """Загружает credentials сервисного аккаунта"""
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES)
        
        # Делегирование от имени вашего email (если указано)
        if self.delegated_email:
            creds = creds.with_subject(self.delegated_email)
        
        self.logger.info(f"Сервисный аккаунт: {creds.service_account_email}")
        
        return creds
    
    # =========================================
    # Google Sheets методы
    # =========================================
    
    def get_worksheet(self, name: str):
        """Получает worksheet по имени"""
        return self.spreadsheet.worksheet(name)
    
    def append_to_sheet(
        self,
        sheet_name: str,
        values: List[Any],
        headers: List[str] = None
    ) -> bool:
        """
        Добавляет строку в таблицу.
        
        Args:
            sheet_name: Имя листа
            values: Список значений для строки
            headers: Заголовки (если нужно создать таблицу)
        
        Returns:
            True если успешно
        """
        try:
            worksheet = self.get_worksheet(sheet_name)
            
            # Если таблица пустая, добавляем заголовки
            if headers:
                existing = worksheet.get_all_values()
                if not existing:
                    worksheet.append_row(headers)
            
            worksheet.append_row(values)
            return True
        except Exception as e:
            self.logger.error(f"Error appending to {sheet_name}: {e}")
            return False
    
    def read_from_sheet(
        self,
        sheet_name: str,
        headers: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Читает все строки из таблицы как список словарей.
        
        Args:
            sheet_name: Имя листа
            headers: Заголовки (если их нет в первой строке)
        
        Returns:
            Список словарей с данными
        """
        try:
            worksheet = self.get_worksheet(sheet_name)
            records = worksheet.get_all_records()
            return records
        except Exception as e:
            self.logger.error(f"Error reading from {sheet_name}: {e}")
            return []
    
    def find_and_update(
        self,
        sheet_name: str,
        search_column: str,
        search_value: Any,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Находит строку по значению и обновляет указанные поля.
        
        Args:
            sheet_name: Имя листа
            search_column: Столбец для поиска
            search_value: Искомое значение
            updates: Словарь {column: value} для обновления
        
        Returns:
            True если найдено и обновлено
        """
        try:
            worksheet = self.get_worksheet(sheet_name)
            all_records = worksheet.get_all_records()
            
            # Находим индекс строки
            for idx, record in enumerate(all_records):
                if str(record.get(search_column)) == str(search_value):
                    # Получаем заголовки
                    headers = worksheet.row_values(1)
                    row_num = idx + 2  # +2 потому что 1-based и первая строка заголовки
                    
                    # Обновляем ячейки
                    for column, value in updates.items():
                        if column in headers:
                            col_idx = headers.index(column) + 1
                            worksheet.update_cell(row_num, col_idx, value)
                    
                    return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error updating {sheet_name}: {e}")
            return False
    
    def get_today_records(self, sheet_name: str, date_column: str = "date") -> List[Dict]:
        """
        Получает все записи за сегодня.
        
        Args:
            sheet_name: Имя листа
            date_column: Название столбца с датой
        
        Returns:
            Список записей за сегодня
        """
        records = self.read_from_sheet(sheet_name)
        today = datetime.now().strftime("%Y-%m-%d")
        
        return [
            record for record in records
            if str(record.get(date_column, "")).startswith(today)
        ]
    
    # =========================================
    # Google Drive методы
    # =========================================
    
    def upload_file(
        self,
        file_path: str,
        file_name: str = None,
        folder_id: str = None,
        mime_type: str = None
    ) -> Optional[str]:
        """
        Загружает файл на Google Drive.
        
        Args:
            file_path: Путь к локальному файлу
            file_name: Имя файла на Drive (если None, используется имя файла)
            folder_id: ID папки (если None, используется корень или GOOGLE_DRIVE_FOLDER_ID)
            mime_type: MIME тип файла
        
        Returns:
            ID файла на Drive или None при ошибке
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.error(f"Файл не найден: {file_path}")
                return None
            
            file_name = file_name or path.name
            folder_id = folder_id or self.drive_folder_id
            
            file_metadata = {"name": file_name}
            
            if folder_id:
                file_metadata["parents"] = [folder_id]
            
            media = MediaFileUpload(str(path), mimetype=mime_type or "application/octet-stream")
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, webViewLink"
            ).execute()
            
            # Делаем файл доступным по ссылке
            self.drive_service.permissions().create(
                fileId=file["id"],
                body={"type": "anyone", "role": "reader"}
            ).execute()
            
            self.logger.info(f"Файл загружен на Drive: {file_name} (ID: {file['id']})")
            
            return file["id"]
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки на Drive: {e}")
            return None
    
    def get_file_url(self, file_id: str) -> str:
        """
        Получает публичную ссылку на файл.
        
        Args:
            file_id: ID файла на Drive
        
        Returns:
            URL файла
        """
        return f"https://drive.google.com/file/d/{file_id}/view"
    
    # =========================================
    # Gmail методы
    # =========================================
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> bool:
        """
        Отправляет email.
        
        Args:
            to: Email получателя
            subject: Тема письма
            body: Текст письма
            html: Если True, тело письма в HTML формате
        
        Returns:
            True если успешно
        """
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import base64
            
            message = MIMEMultipart()
            message["to"] = to
            message["from"] = self.delegated_email
            message["subject"] = subject
            
            content_type = "html" if html else "plain"
            message.attach(MIMEText(body, content_type, "utf-8"))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            
            self.gmail_service.users().messages().send(
                userId="me",
                body={"raw": raw_message}
            ).execute()
            
            self.logger.info(f"Email отправлен: {to}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки email: {e}")
            return False
    
    def send_report_email(
        self,
        to: str = None,
        subject: str = "AI Content Pipeline — Daily Report",
        stats: Dict = None
    ) -> bool:
        """
        Отправляет отчёт о работе пайплайна.
        
        Args:
            to: Email получателя (по умолчанию ваш email)
            subject: Тема письма
            stats: Статистика работы
        
        Returns:
            True если успешно
        """
        to = to or self.delegated_email
        
        # Формируем HTML отчёт
        html_body = f"""
        <html>
        <body>
            <h2>🤖 AI Content Pipeline — Отчёт</h2>
            <p><strong>Дата:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h3>📊 Статистика:</h3>
            <ul>
                <li>📰 RSS Collector: {stats.get('rss_count', 0)} новостей</li>
                <li>🔍 Sonar Scanner: {stats.get('sonar_count', 0)} событий</li>
                <li>📈 Trend Selector: {stats.get('trends_count', 0)} трендов</li>
                <li>✍️ Copywriter: {stats.get('posts_count', 0)} постов</li>
                <li>🎨 Cover Generator: {stats.get('covers_count', 0)} обложек</li>
                <li>📢 Publisher: {stats.get('published_count', 0)} опубликовано</li>
            </ul>
            
            <p><em>Система работает автоматически ежедневно в 09:30 UTC+4</em></p>
        </body>
        </html>
        """
        
        return self.send_email(to, subject, html_body, html=True)


# =========================================
# Функции для обратной совместимости
# =========================================

# Singleton instance
_client: Optional[GoogleAPIClient] = None


def get_google_client() -> GoogleAPIClient:
    """Получает singleton экземпляр клиента"""
    global _client
    if _client is None:
        _client = GoogleAPIClient()
    return _client


def get_sheets_client() -> GoogleAPIClient:
    """
    Получает singleton экземпляр клиента (для обратной совместимости).
    Возвращает тот же объект что и get_google_client().
    """
    return get_google_client()
