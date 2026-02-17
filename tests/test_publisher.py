"""Тесты для Publisher"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from agents.publisher import Publisher, run_publisher


class TestPublisher:
    """Тесты для Publisher"""
    
    @pytest.fixture
    def publisher(self):
        """Создаёт тестовый publisher с моками"""
        with patch('agents.publisher.get_sheets_client') as mock_sheets_fn:
            with patch('agents.publisher.get_telegram_client') as mock_telegram_fn:
                mock_sheets = Mock()
                mock_telegram = Mock()
                mock_sheets_fn.return_value = mock_sheets
                mock_telegram_fn.return_value = mock_telegram
                return Publisher()
    
    def test_get_posts_for_publish(self, publisher):
        """Тест получения постов для публикации"""
        publisher.sheets_client.read_from_sheet.return_value = [
            {
                "trend": "AI Models",
                "post_text": "Post 1",
                "approved": "Y",
                "posted": "N",
                "cover_image_url": "data/cover.png"
            },
            {
                "trend": "AI Agents",
                "post_text": "Post 2",
                "approved": "Y",
                "posted": "N",
                "cover_image_url": ""
            },
            {
                "trend": "AI Regulation",
                "post_text": "Post 3",
                "approved": "N",  # Не одобрен
                "posted": "N",
                "cover_image_url": ""
            },
            {
                "trend": "AI Business",
                "post_text": "Post 4",
                "approved": "Y",
                "posted": "Y",  # Уже опубликован
                "cover_image_url": ""
            }
        ]
        
        posts = publisher.get_posts_for_publish()
        
        assert len(posts) == 2  # Только approved=Y и posted=N
        assert all(p["approved"] == "Y" for p in posts)
        assert all(p["posted"] == "N" for p in posts)
    
    def test_get_posts_for_publish_empty(self, publisher):
        """Тест с пустым списком постов"""
        publisher.sheets_client.read_from_sheet.return_value = []
        
        posts = publisher.get_posts_for_publish()
        
        assert len(posts) == 0
    
    def test_publish_post_with_cover(self, publisher):
        """Тест публикации поста с обложкой"""
        publisher.telegram_client.send_photo.return_value = {"ok": True, "message_id": 12345}
        
        post = {
            "trend": "AI Models",
            "post_text": "Post text 🔥",
            "cover_image_url": "data/cover.png"
        }
        
        result = publisher.publish_post(post)
        
        assert result is not None
        assert result["success"] is True
        assert result["message_id"] == 12345
        publisher.telegram_client.send_photo.assert_called_once()
    
    def test_publish_post_without_cover(self, publisher):
        """Тест публикации поста без обложки"""
        publisher.telegram_client.send_message.return_value = {"ok": True, "message_id": 12346}
        
        post = {
            "trend": "AI Agents",
            "post_text": "Post text 💀",
            "cover_image_url": ""
        }
        
        result = publisher.publish_post(post)
        
        assert result is not None
        assert result["success"] is True
        publisher.telegram_client.send_message.assert_called_once()
    
    def test_publish_post_failure(self, publisher):
        """Тест неудачной публикации"""
        publisher.telegram_client.send_photo.return_value = None
        
        post = {
            "trend": "AI Models",
            "post_text": "Post text",
            "cover_image_url": "data/cover.png"
        }
        
        result = publisher.publish_post(post)
        
        assert result is None
    
    def test_update_post_status(self, publisher):
        """Тест обновления статуса поста"""
        publisher.sheets_client.find_and_update.return_value = True
        
        success = publisher.update_post_status("AI Models", 12345)
        
        assert success is True
        publisher.sheets_client.find_and_update.assert_called_once()
        
        # Проверяем переданные данные
        call_args = publisher.sheets_client.find_and_update.call_args
        updates = call_args[0][3]  # Третий аргумент — updates
        
        assert updates["posted"] == "Y"
        assert "posted_at" in updates
        assert updates["message_id"] == "12345"
    
    def test_run_full_pipeline(self, publisher):
        """Тест полного пайплайна публикации"""
        publisher.telegram_client.test_connection.return_value = True
        
        with patch.object(publisher, 'get_posts_for_publish') as mock_get_posts:
            with patch.object(publisher, 'update_post_status') as mock_update:
                mock_get_posts.return_value = [
                    {"trend": "AI Models", "post_text": "Post 1", "cover_image_url": "data/cover1.png"},
                    {"trend": "AI Agents", "post_text": "Post 2", "cover_image_url": ""},
                ]
                
                publisher.telegram_client.send_photo.return_value = {"ok": True, "message_id": 100}
                publisher.telegram_client.send_message.return_value = {"ok": True, "message_id": 101}
                mock_update.return_value = True
                
                stats = publisher.run()
                
                assert stats["published"] == 2
                assert stats["failed"] == 0
                assert stats["total"] == 2
                assert mock_update.call_count == 2
    
    def test_run_connection_failure(self, publisher):
        """Тест при ошибке соединения"""
        publisher.telegram_client.test_connection.return_value = False
        
        stats = publisher.run()
        
        assert stats["published"] == 0
        assert stats["failed"] == 0
        assert stats["total"] == 0
    
    def test_run_no_posts(self, publisher):
        """Тест когда нет постов для публикации"""
        publisher.telegram_client.test_connection.return_value = True
        
        with patch.object(publisher, 'get_posts_for_publish') as mock_get_posts:
            mock_get_posts.return_value = []
            
            stats = publisher.run()
            
            assert stats["published"] == 0
            assert stats["failed"] == 0
            assert stats["total"] == 0


class TestRunPublisher:
    """Тесты для точки входа"""
    
    @patch('agents.publisher.Publisher')
    def test_run_publisher(self, mock_publisher_class):
        """Тест функции run_publisher"""
        mock_publisher = Mock()
        mock_publisher.run.return_value = {
            "published": 4,
            "failed": 0,
            "total": 4
        }
        mock_publisher_class.return_value = mock_publisher
        
        result = run_publisher()
        
        assert result["published"] == 4
        assert result["total"] == 4
        mock_publisher.run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
