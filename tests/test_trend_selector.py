"""Тесты для Trend Selector"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import os

from agents.trend_selector import TrendSelector, run_trend_selector


class TestTrendSelector:
    """Тесты для Trend Selector"""
    
    @pytest.fixture
    def selector(self):
        """Создаёт тестовый селектор с моками"""
        with patch('agents.trend_selector.get_sheets_client') as mock_fn:
            mock_client = Mock()
            mock_fn.return_value = mock_client
            return TrendSelector()
    
    def test_classify_topic_ai_models(self, selector):
        """Тест классификации: AI Models"""
        assert selector._classify_topic("GPT-5 released with new capabilities") == "AI Models"
        assert selector._classify_topic("New LLM benchmark results") == "AI Models"
        assert selector._classify_topic("Claude 3 performance analysis") == "AI Models"
    
    def test_classify_topic_ai_agents(self, selector):
        """Тест классификации: AI Agents"""
        assert selector._classify_topic("Autonomous agents for workflow") == "AI Agents"
        assert selector._classify_topic("Copilot new automation features") == "AI Agents"
    
    def test_classify_topic_ai_regulation(self, selector):
        """Тест классификации: AI Regulation"""
        assert selector._classify_topic("EU AI Act new regulations") == "AI Regulation"
        assert selector._classify_topic("AI safety policy announced") == "AI Regulation"
    
    def test_classify_topic_default(self, selector):
        """Тест классификации: тема по умолчанию"""
        assert selector._classify_topic("Random news about weather") == "AI General"
    
    def test_calculate_score(self, selector):
        """Тест расчёта score кластера"""
        cluster = [
            {"brand": "OpenAI", "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            {"brand": "OpenAI", "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            {"brand": "Google", "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        ]
        
        score = selector._calculate_score(cluster, "AI Models")
        
        # frequency=3, brand=6 (3 бренда * 2), recency > 0
        assert score >= 9  # Минимум 9 с учётом новизны
    
    def test_calculate_score_no_brand(self, selector):
        """Тест расчёта score без брендов"""
        cluster = [
            {"brand": "", "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            {"brand": "", "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        ]
        
        score = selector._calculate_score(cluster, "AI General")
        
        # frequency=2, brand=0, recency > 0
        assert score >= 2
    
    def test_generate_description(self, selector):
        """Тест генерации описания тренда"""
        cluster = [
            {"title": "OpenAI releases GPT-5", "brand": "OpenAI"},
            {"title": "GPT-5 benchmarks", "brand": "OpenAI"},
        ]
        
        description = selector._generate_description(cluster, "AI Models")
        
        assert "AI Models" in description
        assert "OpenAI" in description
        assert "2" in description  # Количество новостей
    
    def test_cluster_news(self, selector):
        """Тест кластеризации новостей"""
        records = [
            {"title": "GPT-5 released", "summary": "New model from OpenAI"},
            {"title": "EU AI Act passed", "summary": "New regulation"},
            {"title": "Agent workflow automation", "summary": "Autonomous agents"},
            {"title": "LLM benchmark results", "summary": "Performance analysis"},
        ]
        
        clusters = selector.cluster_news(records)
        
        assert "AI Models" in clusters
        assert "AI Regulation" in clusters
        assert "AI Agents" in clusters
        assert len(clusters["AI Models"]) == 2  # GPT-5 и LLM
    
    def test_select_top_trends(self, selector):
        """Тест выбора TOP трендов"""
        clusters = {
            "AI Models": [{"title": "News 1"}, {"title": "News 2"}, {"title": "News 3"}],
            "AI Agents": [{"title": "News 1"}],
            "AI Regulation": [{"title": "News 1"}, {"title": "News 2"}],
        }
        
        top_trends = selector.select_top_trends(clusters, top_n=2)
        
        assert len(top_trends) == 2
        assert top_trends[0]["title"] == "AI Models"  # Самый высокий score
        assert "score" in top_trends[0]
        assert "description" in top_trends[0]
    
    @patch('builtins.open')
    def test_generate_trends_md(self, mock_open, selector):
        """Тест генерации trends.md"""
        trends = [
            {
                "title": "AI Models",
                "description": "OpenAI released new model",
                "score": 10.5,
                "count": 5
            }
        ]
        
        content = selector.generate_trends_md(trends, output_path="test_trends.md")
        
        assert "# 🔥 TOP-5 AI Trends" in content
        assert "AI Models" in content
        assert "10.5" in content
        mock_open.assert_called_once()
    
    def test_run_full_pipeline(self, selector):
        """Тест полного пайплайна"""
        # Мокаем данные из Google Sheets
        selector.sheets_client.get_today_records.return_value = [
            {"title": "GPT-5 released", "summary": "New model", "date": datetime.now().strftime("%Y-%m-%d")},
            {"title": "EU AI Act", "summary": "Regulation", "date": datetime.now().strftime("%Y-%m-%d")},
        ]
        
        with patch.object(selector, 'generate_trends_md'):
            trends = selector.run()
        
        assert len(trends) <= 5
        assert selector.sheets_client.get_today_records.called


class TestRunTrendSelector:
    """Тесты для точки входа"""
    
    @patch('agents.trend_selector.TrendSelector')
    def test_run_trend_selector(self, mock_selector_class):
        """Тест функции run_trend_selector"""
        mock_selector = Mock()
        mock_selector.run.return_value = [
            {"title": "Trend 1", "score": 10},
            {"title": "Trend 2", "score": 8},
        ]
        mock_selector_class.return_value = mock_selector
        
        result = run_trend_selector()
        
        assert len(result) == 2
        mock_selector.run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
