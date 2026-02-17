"""Клиент для работы с OpenRouter API (универсальный LLM клиент)"""

import requests
from typing import Optional, List
from config import get_openrouter_api_key, get_model_for_task
from utils import setup_logger


class OpenRouterClient:
    """Клиент для генерации текста через OpenRouter API"""
    
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self, task: str = "copywriter"):
        """
        Инициализация клиента.
        
        Args:
            task: Название задачи для выбора модели (rss, sonar, trend, copywriter, cover)
        """
        self.api_key = get_openrouter_api_key()
        self.model = get_model_for_task(task)
        self.logger = setup_logger(f"OpenRouterClient-{task}", f"openrouter_{task}.log")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-username/bob_2",
            "X-Title": "AI Content Pipeline"
        }
        
        self.logger.info(f"OpenRouter Client инициализирован (model: {self.model}, task: {task})")
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Генерирует текст через OpenRouter API.
        
        Args:
            system_prompt: Системный промт (роль, стиль)
            user_prompt: Пользовательский промт (задача)
            max_tokens: Максимальное количество токенов
            temperature: Креативность (0-2)
        
        Returns:
            Сгенерированный текст или None при ошибке
        """
        try:
            self.logger.info(f"Генерация текста (max_tokens={max_tokens}, temp={temperature})")
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(
                self.API_URL,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            self.logger.info(f"Текст сгенерирован ({len(content)} символов)")
            
            return content
            
        except requests.exceptions.Timeout:
            self.logger.error("Таймаут запроса к OpenRouter API")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка запроса к OpenRouter API: {e}")
            return None
        except (KeyError, IndexError) as e:
            self.logger.error(f"Ошибка парсинга ответа API: {e}")
            return None
    
    def generate_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        max_retries: int = 3,
        retry_delay: int = 2
    ) -> Optional[str]:
        """
        Генерирует текст с автоматическими повторными попытками.
        
        Args:
            system_prompt: Системный промт
            user_prompt: Пользовательский промт
            max_tokens: Максимальное количество токенов
            temperature: Креативность
            max_retries: Максимальное количество попыток
            retry_delay: Задержка между попытками (секунды)
        
        Returns:
            Сгенерированный текст или None
        """
        import time
        
        for attempt in range(max_retries):
            result = self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if result is not None:
                return result
            
            if attempt < max_retries - 1:
                self.logger.warning(f"Попытка {attempt + 1} не удалась, ждём {retry_delay}с...")
                time.sleep(retry_delay)
        
        self.logger.error(f"Все {max_retries} попыток не удались")
        return None


# Factory function для создания клиента под задачу
_clients = {}


def get_llm_client(task: str = "copywriter") -> OpenRouterClient:
    """
    Получает или создаёт клиента для задачи.
    
    Args:
        task: Название задачи (rss, sonar, trend, copywriter, cover)
    
    Returns:
        OpenRouterClient для задачи
    """
    if task not in _clients:
        _clients[task] = OpenRouterClient(task)
    return _clients[task]
