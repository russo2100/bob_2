"""Агент 1: RSS Collector

Собирает новости из RSS фидов, фильтрует по ключевым словам
и записывает в Google Sheets NewsRaw.
"""

import feedparser
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse

from config import get_env, get_env_list
from utils import setup_logger
from storage.google_sheets import get_sheets_client


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


class RSSCollector:
    """Агент для сбора новостей из RSS фидов"""
    
    def __init__(self):
        self.logger = setup_logger("RSSCollector", "rss_collector.log")
        self.sheets_client = get_sheets_client()
        
        # Загружаем конфигурацию
        self.rss_urls = get_env_list("RSS_URLS")
        self.keywords = get_env_list("KEYWORDS")
        
        self.logger.info(f"Инициализирован RSS Collector")
        self.logger.info(f"RSS URL'ов: {len(self.rss_urls)}, Ключевых слов: {len(self.keywords)}")
    
    def _normalize_date(self, date_tuple) -> str:
        """
        Преобразует date_tuple из feedparser в строку YYYY-MM-DD HH:MM:SS
        
        Args:
            date_tuple: Кортеж даты из feedparser или None
        
        Returns:
            Строка с датой в формате YYYY-MM-DD HH:MM:SS
        """
        if date_tuple is None:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            dt = datetime(*date_tuple[:6])
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError):
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _extract_domain(self, url: str) -> str:
        """Извлекает домен из URL для отображения источника"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except:
            return url
    
    def _matches_keywords(self, text: str) -> bool:
        """
        Проверяет, содержит ли текст хотя бы одно ключевое слово.
        
        Args:
            text: Текст для проверки
        
        Returns:
            True если найдено совпадение
        """
        if not self.keywords:
            return True  # Если ключевых слов нет, принимаем всё
        
        text_lower = text.lower()
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                return True
        return False
    
    def _parse_feed(self, url: str) -> List[Dict]:
        """
        Парсит один RSS фид.
        
        Args:
            url: URL RSS фидa
        
        Returns:
            Список словарей с новостями
        """
        entries = []
        
        try:
            self.logger.info(f"Парсинг фидa: {url}")
            feed = feedparser.parse(url)
            
            for entry in feed.entries:
                # Извлекаем данные
                title = getattr(entry, 'title', '')
                summary = getattr(entry, 'summary', '')
                description = getattr(entry, 'description', '')
                link = getattr(entry, 'link', '')
                published = getattr(entry, 'published_parsed', None)
                
                # Объединяем summary и description
                full_summary = (summary or description or '')[:500]  # Ограничиваем длину
                
                # Проверяем ключевые слова
                search_text = f"{title} {full_summary}"
                if not self._matches_keywords(search_text):
                    continue
                
                # Формируем запись
                record = {
                    "date": self._normalize_date(published),
                    "source_type": "rss",
                    "source": self._extract_domain(url),
                    "title": title[:200],  # Ограничиваем длину
                    "summary": full_summary,
                    "link": link,
                    "brand": "",  # Для RSS бренд не указан
                    "published_at": self._normalize_date(published)
                }
                entries.append(record)
            
            self.logger.info(f"Найдено {len(entries)} записей из {url}")
            
        except Exception as e:
            self.logger.error(f"Ошибка парсинга {url}: {e}")
        
        return entries
    
    def collect(self) -> int:
        """
        Запускает сбор новостей из всех RSS фидов.
        
        Returns:
            Количество добавленных записей
        """
        self.logger.info("=== Запуск RSS Collector ===")
        
        all_entries = []
        
        # Парсим все фиды
        for url in self.rss_urls:
            entries = self._parse_feed(url)
            all_entries.extend(entries)
        
        self.logger.info(f"Всего собрано записей: {len(all_entries)}")
        
        # Записываем в Google Sheets
        if all_entries:
            success_count = 0
            for entry in all_entries:
                values = [
                    entry["date"],
                    entry["source_type"],
                    entry["source"],
                    entry["title"],
                    entry["summary"],
                    entry["link"],
                    entry["brand"],
                    entry["published_at"]
                ]
                
                if self.sheets_client.append_to_sheet(
                    "NewsRaw",
                    values,
                    headers=NEWSRAW_HEADERS
                ):
                    success_count += 1
            
            self.logger.info(f"Записано в NewsRaw: {success_count}/{len(all_entries)}")
            return success_count
        
        self.logger.warning("Нет записей для добавления")
        return 0


def run_rss_collector() -> int:
    """Точка входа для запуска агента"""
    collector = RSSCollector()
    return collector.collect()


if __name__ == "__main__":
    count = run_rss_collector()
    print(f"RSS Collector завершил работу. Добавлено записей: {count}")
