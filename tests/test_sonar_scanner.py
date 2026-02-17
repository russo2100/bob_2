"""Тесты для Sonar Scanner"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from agents.sonar_scanner import SonarScanner, run_sonar_scanner
from storage.perplexity_client import PerplexitySonarClient


class TestPerplexitySonarClient:
    """Тесты для Perplexity Sonar клиента"""
    
    @pytest.fixture
    def client(self):
        """Создаёт тестовый клиент с моками"""
        with patch('storage.perplexity_client.get_openrouter_api_key') as mock_key:
            mock_key.return_value = "test_api_key"
            return PerplexitySonarClient()
    
    @patch('storage.perplexity_client.requests.post')
    def test_make_request_success(self, mock_post, client):
        """Тест успешного запроса"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Event 1\nEvent 2\nEvent 3"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = client._make_request("test query")
        
        assert result is not None
        assert "choices" in result
    
    @patch('storage.perplexity_client.requests.post')
    def test_make_request_rate_limit(self, mock_post, client):
        """Тест обработки rate limit (429)"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '1'}
        mock_post.return_value = mock_response
        
        # После нескольких попыток должен вернуть None
        result = client._make_request("test query")
        
        assert mock_post.call_count <= client.MAX_RETRIES
    
    @patch('storage.perplexity_client.requests.post')
    def test_search_brand_news(self, mock_post, client):
        """Тест поиска новостей о бренде"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "OpenAI released GPT-5\nGoogle announced new TPU\nMeta open-sourced LLM"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        events = client.search_brand_news("OpenAI")
        
        assert len(events) <= 5
        assert all(e["brand"] == "OpenAI" for e in events)
        assert all(e["source_type"] == "sonar" for e in events)
    
    def test_parse_events(self, client):
        """Тест парсинга событий из текста"""
        content = """
        - OpenAI released new model
        * Google announced partnership
        • Meta open-sourced framework
        """
        
        events = client._parse_events(content, "TestBrand")
        
        assert len(events) == 3
        assert events[0]["title"] == "OpenAI released new model"
        assert events[0]["brand"] == "TestBrand"
    
    def test_parse_events_empty(self, client):
        """Тест парсинга пустого ответа"""
        events = client._parse_events("", "TestBrand")
        assert events == []


class TestSonarScanner:
    """Тесты для Sonar Scanner агента"""
    
    @pytest.fixture
    def scanner(self):
        """Создаёт тестовый сканер с моками"""
        with patch('agents.sonar_scanner.get_sheets_client') as mock_sheets_fn:
            with patch('agents.sonar_scanner.get_perplexity_sonar_client') as mock_perplexity_fn:
                with patch('agents.sonar_scanner.get_env_list') as mock_env:
                    mock_env.return_value = ["OpenAI", "Google"]
                    
                    # Создаём моки клиентов
                    mock_sheets = Mock()
                    mock_perplexity = Mock()
                    mock_sheets_fn.return_value = mock_sheets
                    mock_perplexity_fn.return_value = mock_perplexity
                    
                    return SonarScanner()
    
    def test_scan(self, scanner):
        """Тест основного метода scan"""
        # Мокаем ответы от Perplexity
        scanner.perplexity_client.search_brand_news.side_effect = [
            [
                {"date": "2024-02-17 10:00:00", "source_type": "sonar", 
                 "source": "Perplexity Sonar", "title": "OpenAI News", 
                 "summary": "Summary", "link": "", "brand": "OpenAI",
                 "published_at": "2024-02-17 10:00:00"}
            ],
            [
                {"date": "2024-02-17 11:00:00", "source_type": "sonar",
                 "source": "Perplexity Sonar", "title": "Google News",
                 "summary": "Summary", "link": "", "brand": "Google",
                 "published_at": "2024-02-17 11:00:00"}
            ]
        ]
        scanner.sheets_client.append_to_sheet.return_value = True
        
        count = scanner.scan()
        
        assert count == 2
        assert scanner.perplexity_client.search_brand_news.call_count == 2
        assert scanner.sheets_client.append_to_sheet.call_count == 2


class TestRunSonarScanner:
    """Тесты для точки входа"""
    
    @patch('agents.sonar_scanner.SonarScanner')
    def test_run_sonar_scanner(self, mock_scanner_class):
        """Тест функции run_sonar_scanner"""
        mock_scanner = Mock()
        mock_scanner.scan.return_value = 10
        mock_scanner_class.return_value = mock_scanner
        
        result = run_sonar_scanner()
        
        assert result == 10
        mock_scanner.scan.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
