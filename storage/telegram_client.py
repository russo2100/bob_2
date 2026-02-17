"""Клиент для Telegram Bot API"""

import requests
from typing import Optional, Dict
from pathlib import Path

from config import get_env
from utils import setup_logger


class TelegramClient:
    """Клиент для работы с Telegram Bot API"""
    
    def __init__(self):
        self.token = get_env("TELEGRAM_BOT_TOKEN", required=True)
        self.channel_id = get_env("TELEGRAM_CHANNEL_ID", required=True)
        self.logger = setup_logger("TelegramClient", "telegram_client.log")
        
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        self.logger.info(f"Telegram Client инициализирован (channel: {self.channel_id})")
    
    def send_photo(
        self,
        photo_path: str,
        caption: str,
        parse_mode: str = "HTML"
    ) -> Optional[Dict]:
        """
        Отправляет фото с подписью в канал.
        
        Args:
            photo_path: Путь к файлу изображения
            caption: Текст подписи (пост)
            parse_mode: Режим парсинга (HTML, Markdown)
        
        Returns:
            Ответ API или None при ошибке
        """
        try:
            photo = Path(photo_path)
            
            if not photo.exists():
                self.logger.error(f"Файл не найден: {photo_path}")
                return None
            
            self.logger.info(f"Отправка фото: {photo_path}")
            
            url = f"{self.base_url}/sendPhoto"
            
            with open(photo, "rb") as f:
                files = {"photo": f}
                data = {
                    "chat_id": self.channel_id,
                    "caption": caption[:1024],  # Лимит Telegram
                    "parse_mode": parse_mode
                }
                
                response = requests.post(url, files=files, data=data)
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("ok"):
                    message_id = result["result"]["message_id"]
                    self.logger.info(f"Фото отправлено (message_id: {message_id})")
                    return {
                        "ok": True,
                        "message_id": message_id
                    }
                else:
                    self.logger.error(f"Ошибка API: {result}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Ошибка отправки фото: {e}")
            return None
    
    def send_message(
        self,
        text: str,
        parse_mode: str = "HTML"
    ) -> Optional[Dict]:
        """
        Отправляет текстовое сообщение в канал.
        
        Args:
            text: Текст сообщения
            parse_mode: Режим парсинга
        
        Returns:
            Ответ API или None при ошибке
        """
        try:
            self.logger.info("Отправка текстового сообщения")
            
            url = f"{self.base_url}/sendMessage"
            
            data = {
                "chat_id": self.channel_id,
                "text": text[:4096],  # Лимит Telegram
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("ok"):
                message_id = result["result"]["message_id"]
                self.logger.info(f"Сообщение отправлено (message_id: {message_id})")
                return {
                    "ok": True,
                    "message_id": message_id
                }
            else:
                self.logger.error(f"Ошибка API: {result}")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка отправки сообщения: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Проверяет соединение с Telegram API.
        
        Returns:
            True если соединение успешно
        """
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("ok"):
                bot_name = result["result"]["username"]
                self.logger.info(f"Соединение успешно (bot: @{bot_name})")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки соединения: {e}")
            return False


# Singleton instance
_client: Optional[TelegramClient] = None


def get_telegram_client() -> TelegramClient:
    """Получает singleton экземпляр клиента"""
    global _client
    if _client is None:
        _client = TelegramClient()
    return _client
