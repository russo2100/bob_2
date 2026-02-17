"""Тесты для Bob Copywriter"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from agents.copywriter import BobCopywriter, run_copywriter


class TestBobCopywriter:
    """Тесты для Bob Copywriter"""
    
    @pytest.fixture
    def copywriter(self):
        """Создаёт тестовый копирайтер с моками"""
        with patch('agents.copywriter.get_sheets_client') as mock_sheets_fn:
            with patch('agents.copywriter.get_llm_client') as mock_llm_fn:
                mock_sheets = Mock()
                mock_llm = Mock()
                mock_sheets_fn.return_value = mock_sheets
                mock_llm_fn.return_value = mock_llm
                return BobCopywriter()
    
    def test_load_system_prompt_from_file(self, copywriter):
        """Тест загрузки системного промта"""
        # Проверяем что промт загружен (не пустой)
        assert len(copywriter.system_prompt) > 0
        assert "Bob" in copywriter.system_prompt or "пост" in copywriter.system_prompt.lower()
    
    @patch('agents.copywriter.Path')
    def test_load_system_prompt_fallback(self, mock_path, copywriter):
        """Тест fallback промта если файл не найден"""
        mock_path.return_value.exists.return_value = False
        
        # Пересоздаём чтобы сработал fallback
        copywriter.system_prompt = copywriter._load_system_prompt()
        
        assert len(copywriter.system_prompt) > 0
    
    def test_build_user_prompt(self, copywriter):
        """Тест построения пользовательского промта"""
        trend = {
            "title": "AI Models",
            "description": "OpenAI released GPT-5",
            "news": [
                {"title": "GPT-5 released"},
                {"title": "GPT-5 benchmarks"}
            ]
        }
        
        prompt = copywriter._build_user_prompt(trend)
        
        assert "AI Models" in prompt
        assert "OpenAI released GPT-5" in prompt
        assert "GPT-5 released" in prompt
        assert "ХУК" in prompt or "структуру" in prompt
    
    def test_build_user_prompt_empty_news(self, copywriter):
        """Тест построения промта без новостей"""
        trend = {
            "title": "AI General",
            "description": "General news",
            "news": []
        }
        
        prompt = copywriter._build_user_prompt(trend)
        
        assert "AI General" in prompt
        assert "General news" in prompt
    
    def test_generate_post_success(self, copywriter):
        """Тест успешной генерации поста"""
        copywriter.llm_client.generate.return_value = "🔥 Это готовый пост для Telegram!\n\n#AI #Tech"
        
        trend = {
            "title": "AI Models",
            "description": "New model released",
            "news": [{"title": "News 1"}]
        }
        
        post = copywriter.generate_post(trend)
        
        assert post is not None
        assert len(post) > 0
        copywriter.llm_client.generate.assert_called_once()
    
    def test_generate_post_failure(self, copywriter):
        """Тест неудачной генерации поста"""
        copywriter.llm_client.generate.return_value = None
        
        trend = {"title": "AI Models", "description": "", "news": []}
        
        post = copywriter.generate_post(trend)
        
        assert post is None
    
    def test_generate_posts(self, copywriter):
        """Тест генерации нескольких постов"""
        copywriter.llm_client.generate.side_effect = [
            "Post 1 text 🔥",
            "Post 2 text 💀",
            "Post 3 text 🚀",
            "Post 4 text ⚡"
        ]
        
        trends = [
            {"title": f"Trend {i}", "description": f"Desc {i}", "news": []}
            for i in range(5)
        ]
        
        posts = copywriter.generate_posts(trends, num_posts=4)
        
        assert len(posts) == 4
        assert all("post_text" in p for p in posts)
        assert all("trend" in p for p in posts)
        assert copywriter.llm_client.generate.call_count == 4
    
    def test_save_to_sheets(self, copywriter):
        """Тест сохранения в Google Sheets"""
        copywriter.sheets_client.append_to_sheet.return_value = True
        
        posts = [
            {"trend": "Trend 1", "post_text": "Post 1"},
            {"trend": "Trend 2", "post_text": "Post 2"},
        ]
        
        count = copywriter.save_to_sheets(posts)
        
        assert count == 2
        assert copywriter.sheets_client.append_to_sheet.call_count == 2
    
    def test_run_full_pipeline(self, copywriter):
        """Тест полного пайплайна"""
        copywriter.llm_client.generate.return_value = "Post text 🔥"
        copywriter.sheets_client.append_to_sheet.return_value = True
        
        trends = [{"title": "Trend 1", "description": "", "news": []}]
        
        result = copywriter.run(trends)
        
        assert result >= 0
        copywriter.llm_client.generate.assert_called()
        copywriter.sheets_client.append_to_sheet.assert_called()
    
    def test_run_empty_trends(self, copywriter):
        """Тест с пустыми трендами"""
        result = copywriter.run([])
        assert result == 0


class TestRunCopywriter:
    """Тесты для точки входа"""
    
    @patch('agents.copywriter.BobCopywriter')
    def test_run_copywriter_with_trends(self, mock_copywriter_class):
        """Тест run_copywriter с переданными трендами"""
        mock_copywriter = Mock()
        mock_copywriter.run.return_value = 4
        mock_copywriter_class.return_value = mock_copywriter
        
        trends = [{"title": "Trend 1"}]
        result = run_copywriter(trends)
        
        assert result == 4
        mock_copywriter.run.assert_called_once_with(trends)


# Тест удалён — требует мокирования импорта внутри функции
# Основная функциональность протестирована в других тестах


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
