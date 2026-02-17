"""Клиент для Perplexity Sonar API через OpenRouter

Использует модель perplexity/sonar через OpenRouter API
"""

from typing import List, Dict, Optional
from datetime import datetime
import time

from config import get_openrouter_api_key, get_model_for_task
from utils import setup_logger
import requests


class PerplexitySonarClient:
    """Клиент для работы с Perplexity Sonar через OpenRouter"""
    
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # секунды
    
    def __init__(self):
        self.api_key = get_openrouter_api_key()
        self.model = get_model_for_task("sonar")  # perplexity/sonar
        self.logger = setup_logger("PerplexitySonarClient", "sonar_client.log")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-username/bob_2",
            "X-Title": "AI Content Pipeline - Sonar Scanner"
        }
        
        self.logger.info(f"Perplexity Sonar Client инициализирован (model: {self.model})")
    
    def _make_request(self, query: str) -> Optional[Dict]:
        """
        Делает запрос к Sonar API через OpenRouter с retry logic.
        
        Args:
            query: Текст запроса
        
        Returns:
            Ответ API или None при ошибке
        """
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are Perplexity Sonar, a real-time AI search engine. Provide concise, factual summaries of recent events with sources. Return only the key facts, no introductions or conclusions."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.2
        }
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.post(
                    self.API_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 429:
                    # Rate limit
                    retry_after = int(response.headers.get('Retry-After', self.RETRY_DELAY))
                    self.logger.warning(f"Rate limit, ждём {retry_after}с")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                self.logger.warning(f"Таймаут запроса (попытка {attempt + 1})")
                time.sleep(self.RETRY_DELAY)
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Ошибка запроса: {e}")
                return None
        
        self.logger.error(f"Превышено количество попыток ({self.MAX_RETRIES})")
        return None
    
    def search_brand_news(self, brand: str, days: int = 1) -> List[Dict]:
        """
        Ищет последние новости о бренде через Perplexity Sonar.
        
        Args:
            brand: Название бренда (OpenAI, Google, etc.)
            days: За сколько дней искать новости
        
        Returns:
            Список событий (3-5 на бренд)
        """
        query = f"latest AI updates {brand} today. List 3-5 key events with brief descriptions and sources."
        
        self.logger.info(f"Поиск новостей для бренда: {brand}")
        response_data = self._make_request(query)
        
        if not response_data:
            return []
        
        try:
            content = response_data["choices"][0]["message"]["content"]
            events = self._parse_events(content, brand)
            self.logger.info(f"Найдено {len(events)} событий для {brand}")
            return events
        except (KeyError, IndexError) as e:
            self.logger.error(f"Ошибка парсинга ответа: {e}")
            return []
    
    def _parse_events(self, content: str, brand: str) -> List[Dict]:
        """
        Парсит текст ответа в список событий.
        
        Args:
            content: Текст ответа от API
            brand: Название бренда
        
        Returns:
            Список словарей с событиями
        """
        events = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith(('-', '*', '•')):
                line = line.lstrip('-*•').strip()
            
            if len(line) > 20:  # Минимальная длина события
                events.append({
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source_type": "sonar",
                    "source": "Perplexity Sonar",
                    "title": line[:150],
                    "summary": line,
                    "link": "",
                    "brand": brand,
                    "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # Возвращаем максимум 5 событий
        return events[:5]


# Singleton instance
_client: Optional[PerplexitySonarClient] = None


def get_perplexity_sonar_client() -> PerplexitySonarClient:
    """Получает singleton экземпляр клиента"""
    global _client
    if _client is None:
        _client = PerplexitySonarClient()
    return _client
