"""Тесты для RSS Collector"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from agents.rss_collector import RSSCollector, run_rss_collector


class TestRSSCollector:
    """Тесты для RSS Collector"""
    
    @pytest.fixture
    def collector(self):
        """Создаёт тестовый коллектор с моками"""
        with patch('agents.rss_collector.get_sheets_client') as mock_sheets_fn:
            with patch('agents.rss_collector.get_env_list') as mock_env:
                mock_env.return_value = ["AI", "machine learning"]
                mock_client = Mock()
                mock_sheets_fn.return_value = mock_client
                return RSSCollector()
    
    def test_normalize_date_with_valid_tuple(self, collector):
        """Тест нормализации корректной даты"""
        date_tuple = (2024, 2, 17, 10, 30, 0, 0, 0, 0)
        result = collector._normalize_date(date_tuple)
        assert result == "2024-02-17 10:30:00"
    
    def test_normalize_date_with_none(self, collector):
        """Тест нормализации None (должна вернуть текущую дату)"""
        result = collector._normalize_date(None)
        assert result.startswith(datetime.now().strftime("%Y-%m-%d"))
    
    def test_extract_domain(self, collector):
        """Тест извлечения домена из URL"""
        assert collector._extract_domain("https://example.com/rss") == "example.com"
        assert collector._extract_domain("https://www.example.com/rss") == "example.com"
    
    def test_matches_keywords_positive(self, collector):
        """Тест совпадения по ключевым словам (положительный)"""
        assert collector._matches_keywords("AI is changing the world") is True
        assert collector._matches_keywords("Machine Learning applications") is True
    
    def test_matches_keywords_negative(self, collector):
        """Тест совпадения по ключевым словам (отрицательный)"""
        assert collector._matches_keywords("Weather forecast today") is False
    
    def test_matches_keywords_empty_text(self, collector):
        """Тест совпадения по ключевым словам (пустой текст)"""
        assert collector._matches_keywords("") is False
    
    @patch('agents.rss_collector.feedparser.parse')
    def test_parse_feed(self, mock_parse, collector):
        """Тест парсинга RSS фидa"""
        # Мокаем ответ feedparser
        mock_feed = Mock()
        mock_feed.entries = [
            Mock(
                title="New AI Model Released",
                summary="This is about artificial intelligence",
                description="",
                link="https://example.com/ai-news",
                published_parsed=(2024, 2, 17, 10, 0, 0, 0, 0, 0)
            ),
            Mock(
                title="Weather Update",
                summary="Sunny today",
                description="",
                link="https://example.com/weather",
                published_parsed=(2024, 2, 17, 9, 0, 0, 0, 0, 0)
            )
        ]
        mock_parse.return_value = mock_feed
        
        entries = collector._parse_feed("https://example.com/rss")
        
        # Должна остаться только запись с AI (фильтрация по ключевым словам)
        assert len(entries) == 1
        assert entries[0]["title"] == "New AI Model Released"
        assert entries[0]["source_type"] == "rss"
    
    @patch('agents.rss_collector.feedparser.parse')
    def test_parse_feed_error_handling(self, mock_parse, collector):
        """Тест обработки ошибок при парсинге"""
        mock_parse.side_effect = Exception("Network error")
        
        entries = collector._parse_feed("https://invalid.com/rss")
        
        assert entries == []
    
    def test_collect(self, collector):
        """Тест основного метода collect"""
        # Мокаем _parse_feed
        with patch.object(collector, '_parse_feed') as mock_parse:
            mock_parse.side_effect = [
                [{"title": "AI News 1", "date": "2024-02-17 10:00:00", "source_type": "rss", 
                  "source": "example.com", "summary": "Summary", "link": "http://link", 
                  "brand": "", "published_at": "2024-02-17 10:00:00"}],
                [{"title": "AI News 2", "date": "2024-02-17 11:00:00", "source_type": "rss",
                  "source": "tech.com", "summary": "Summary", "link": "http://link2",
                  "brand": "", "published_at": "2024-02-17 11:00:00"}]
            ]
            collector.sheets_client.append_to_sheet.return_value = True
            
            count = collector.collect()
            
            assert count == 2
            assert mock_parse.call_count == 2
            assert collector.sheets_client.append_to_sheet.call_count == 2


class TestRunRSSCollector:
    """Тесты для точки входа"""
    
    @patch('agents.rss_collector.RSSCollector')
    def test_run_rss_collector(self, mock_collector_class):
        """Тест функции run_rss_collector"""
        mock_collector = Mock()
        mock_collector.collect.return_value = 5
        mock_collector_class.return_value = mock_collector
        
        result = run_rss_collector()
        
        assert result == 5
        mock_collector.collect.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
