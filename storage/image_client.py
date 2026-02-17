"""Клиент для генерации изображений (DALL-E API)"""

from openai import OpenAI
from typing import Optional, List
from pathlib import Path
import base64
import requests

from config import get_env
from utils import setup_logger


class ImageGenClient:
    """Клиент для генерации изображений через DALL-E API"""
    
    def __init__(self):
        self.api_key = get_env("LLM_API_KEY")  # DALL-E использует тот же ключ
        self.logger = setup_logger("ImageGenClient", "image_gen_client.log")
        
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        
        self.logger.info("Image Gen Client инициализирован")
    
    def generate_image(
        self,
        prompt: str,
        size: str = "1080x1080"
    ) -> Optional[bytes]:
        """
        Генерирует изображение по промту.
        
        Args:
            prompt: Описание изображения
            size: Размер (1080x1080, 1024x1024, 1792x1024)
        
        Returns:
            Байты изображения или None при ошибке
        """
        if not self.client:
            self.logger.error("API ключ не настроен")
            return None
        
        try:
            self.logger.info(f"Генерация изображения: {prompt[:50]}...")
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1
            )
            
            # Получаем URL изображения
            image_url = response.data[0].url
            
            # Скачиваем изображение
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            self.logger.info("Изображение сгенерировано")
            
            return image_response.content
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации изображения: {e}")
            return None
    
    def save_image(self, image_data: bytes, filepath: str) -> bool:
        """
        Сохраняет изображение в файл.
        
        Args:
            image_data: Байты изображения
            filepath: Путь для сохранения
        
        Returns:
            True если успешно
        """
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, "wb") as f:
                f.write(image_data)
            
            self.logger.info(f"Изображение сохранено: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения изображения: {e}")
            return False


# Singleton instance
_client: Optional[ImageGenClient] = None


def get_image_gen_client() -> ImageGenClient:
    """Получает singleton экземпляр клиента"""
    global _client
    if _client is None:
        _client = ImageGenClient()
    return _client
