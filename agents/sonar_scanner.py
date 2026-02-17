"""Агент 2: Perplexity Sonar Scanner

Сканирует новости о AI-брендах через Perplexity Sonar API
и записывает в Google Sheets NewsRaw.
"""

from typing import List
from config import get_env_list
from utils import setup_logger
from storage.google_sheets import get_sheets_client
from storage.perplexity_client import get_perplexity_sonar_client


# Заголовки для Google Sheets NewsRaw
NEWSRAW_HEADERS = [
    "date",
    "source_type",
    "source",
    "title",
    "summary",
    "link",
    "brand",
    "published_at"
]


class SonarScanner:
    """Агент для сканирования новостей о брендах через Perplexity"""
    
    def __init__(self):
        self.logger = setup_logger("SonarScanner", "sonar_scanner.log")
        self.sheets_client = get_sheets_client()
        self.perplexity_client = get_perplexity_sonar_client()
        
        # Загружаем список брендов
        self.brands = get_env_list("SONAR_BRANDS")
        
        self.logger.info(f"Инициализирован Sonar Scanner")
        self.logger.info(f"Брендов для сканирования: {len(self.brands)}")
    
    def scan(self) -> int:
        """
        Запускает сканирование новостей по всем брендам.
        
        Returns:
            Количество добавленных записей
        """
        self.logger.info("=== Запуск Sonar Scanner ===")
        
        all_events = []
        
        # Сканируем каждый бренд
        for brand in self.brands:
            events = self.perplexity_client.search_brand_news(brand)
            all_events.extend(events)
            self.logger.info(f"{brand}: {len(events)} событий")
        
        self.logger.info(f"Всего собрано событий: {len(all_events)}")
        
        # Записываем в Google Sheets
        if all_events:
            success_count = 0
            for event in all_events:
                values = [
                    event["date"],
                    event["source_type"],
                    event["source"],
                    event["title"],
                    event["summary"],
                    event["link"],
                    event["brand"],
                    event["published_at"]
                ]
                
                if self.sheets_client.append_to_sheet(
                    "NewsRaw",
                    values,
                    headers=NEWSRAW_HEADERS
                ):
                    success_count += 1
            
            self.logger.info(f"Записано в NewsRaw: {success_count}/{len(all_events)}")
            return success_count
        
        self.logger.warning("Нет событий для добавления")
        return 0


def run_sonar_scanner() -> int:
    """Точка входа для запуска агента"""
    scanner = SonarScanner()
    return scanner.scan()


if __name__ == "__main__":
    count = run_sonar_scanner()
    print(f"Sonar Scanner завершил работу. Добавлено событий: {count}")
