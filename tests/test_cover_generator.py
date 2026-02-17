"""Тесты для Cover Generator"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from agents.cover_generator import CoverGenerator, run_cover_generator


class TestCoverGenerator:
    """Тесты для Cover Generator"""
    
    @pytest.fixture
    def generator(self):
        """Создаёт тестовый генератор с моками"""
        with patch('agents.cover_generator.get_sheets_client') as mock_sheets_fn:
            with patch('agents.cover_generator.get_image_gen_client') as mock_image_fn:
                with patch('agents.cover_generator.ensure_directory'):
                    mock_sheets = Mock()
                    mock_image = Mock()
                    mock_sheets_fn.return_value = mock_sheets
                    mock_image_fn.return_value = mock_image
                    return CoverGenerator()
    
    def test_extract_keywords(self, generator):
        """Тест извлечения ключевых слов"""
        text = "OpenAI released GPT-5 with amazing capabilities for AI development"
        
        keywords = generator._extract_keywords(text)
        
        assert "openai" in keywords or "gpt-5" in keywords
        assert "capabilities" in keywords or "development" in keywords
        assert len(keywords) <= 5
    
    def test_extract_keywords_with_emoji(self, generator):
        """Тест извлечения ключевых слов с эмодзи"""
        text = "🔥 AI models are changing the world! 🚀 Amazing technology 💀"
        
        keywords = generator._extract_keywords(text)
        
        assert "models" in keywords or "changing" in keywords
        assert "world" in keywords or "technology" in keywords
    
    def test_extract_keywords_russian(self, generator):
        """Тест извлечения русских ключевых слов"""
        text = "Новая модель ИИ от OpenAI меняет мир технологий"
        
        keywords = generator._extract_keywords(text)
        
        assert len(keywords) > 0
    
    def test_generate_visual_prompt(self, generator):
        """Тест генерации visual prompt"""
        post_text = "GPT-5 released with new capabilities"
        trend = "AI Models"
        
        prompt = generator._generate_visual_prompt(post_text, trend)
        
        assert "AI Models" in prompt
        assert "tech" in prompt.lower() or "technology" in prompt.lower()
        assert "1080x1080" not in prompt  # Размер передаётся отдельно
    
    def test_generate_slug(self, generator):
        """Тест генерации slug"""
        text = "AI Models Trend"
        
        slug = generator._generate_slug(text)
        
        assert "ai" in slug.lower()
        assert len(slug) > 10  # Должен содержать дату и хеш
    
    def test_generate_cover_success(self, generator):
        """Тест успешной генерации обложки"""
        generator.image_client.generate_image.return_value = b"fake_image_data"
        generator.image_client.save_image.return_value = True
        
        cover_path = generator.generate_cover("Post text", "AI Models")
        
        assert cover_path is not None
        assert cover_path.startswith("data/")
        assert cover_path.endswith(".png")
        generator.image_client.generate_image.assert_called_once()
        generator.image_client.save_image.assert_called_once()
    
    def test_generate_cover_failure(self, generator):
        """Тест неудачной генерации обложки"""
        generator.image_client.generate_image.return_value = None
        
        cover_path = generator.generate_cover("Post text", "AI Models")
        
        assert cover_path is None
    
    def test_get_posts_for_covers(self, generator):
        """Тест получения постов для обложек"""
        generator.sheets_client.read_from_sheet.return_value = [
            {
                "trend": "AI Models",
                "post_text": "Post 1",
                "status": "draft",
                "cover_image_url": ""
            },
            {
                "trend": "AI Agents",
                "post_text": "Post 2",
                "status": "approved",
                "cover_image_url": ""
            },
            {
                "trend": "AI Regulation",
                "post_text": "Post 3",
                "status": "draft",
                "cover_image_url": "data/existing.png"  # Уже есть обложка
            }
        ]
        
        posts = generator.get_posts_for_covers()
        
        assert len(posts) == 2  # Только без обложек
        assert all(p.get("cover_image_url") == "" for p in posts)
    
    def test_update_cover_url(self, generator):
        """Тест обновления URL обложки"""
        generator.sheets_client.find_and_update.return_value = True
        
        success = generator.update_cover_url("AI Models", "data/cover.png")
        
        assert success is True
        generator.sheets_client.find_and_update.assert_called_once()
    
    def test_run_full_pipeline(self, generator):
        """Тест полного пайплайна"""
        with patch.object(generator, 'get_posts_for_covers') as mock_get_posts:
            with patch.object(generator, 'generate_cover') as mock_generate:
                with patch.object(generator, 'update_cover_url') as mock_update:
                    mock_get_posts.return_value = [
                        {"trend": "AI Models", "post_text": "Post 1"},
                        {"trend": "AI Agents", "post_text": "Post 2"},
                    ]
                    mock_generate.side_effect = ["data/cover1.png", "data/cover2.png"]
                    mock_update.return_value = True
                    
                    count = generator.run()
                    
                    assert count == 2
                    assert mock_generate.call_count == 2
                    assert mock_update.call_count == 2
    
    def test_run_empty_posts(self, generator):
        """Тест с пустым списком постов"""
        count = generator.run([])
        assert count == 0


class TestRunCoverGenerator:
    """Тесты для точки входа"""
    
    @patch('agents.cover_generator.CoverGenerator')
    def test_run_cover_generator(self, mock_generator_class):
        """Тест функции run_cover_generator"""
        mock_generator = Mock()
        mock_generator.run.return_value = 4
        mock_generator_class.return_value = mock_generator
        
        result = run_cover_generator()
        
        assert result == 4
        mock_generator.run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
