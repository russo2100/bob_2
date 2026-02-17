"""Агент 6: Publisher

Публикует посты в Telegram канал.
Работает только с approved=Y и posted=N записями.
"""

from typing import List, Dict, Optional
from datetime import datetime

from utils import setup_logger
from storage.google_sheets import get_sheets_client
from storage.telegram_client import get_telegram_client


class Publisher:
    """Агент для публикации постов в Telegram"""
    
    def __init__(self):
        self.logger = setup_logger("Publisher", "publisher.log")
        self.sheets_client = get_sheets_client()
        self.telegram_client = get_telegram_client()
        
        self.logger.info("Publisher инициализирован")
    
    def get_posts_for_publish(self) -> List[Dict]:
        """
        Получает посты, готовые к публикации.
        
        Критерии:
        - approved = Y
        - posted = N
        
        Returns:
            Список постов из Texts
        """
        records = self.sheets_client.read_from_sheet("Texts")
        
        # Фильтруем по критериям
        filtered = [
            record for record in records
            if str(record.get("approved", "")).upper() == "Y"
            and str(record.get("posted", "")).upper() == "N"
        ]
        
        self.logger.info(f"Найдено постов для публикации: {len(filtered)}")
        
        return filtered
    
    def publish_post(self, post: Dict) -> Optional[Dict]:
        """
        Публикует один пост в Telegram.
        
        Args:
            post: Словарь поста из Texts
        
        Returns:
            Результат публикации {message_id, success} или None
        """
        trend = post.get("trend", "")
        post_text = post.get("post_text", "")
        cover_url = post.get("cover_image_url", "")
        
        self.logger.info(f"Публикация поста: {trend}")
        
        # Проверяем наличие текста
        if not post_text:
            self.logger.warning(f"Пустой текст поста для {trend}")
            return None
        
        # Если есть обложка — отправляем фото + caption
        if cover_url and cover_url.strip():
            result = self.telegram_client.send_photo(
                photo_path=cover_url,
                caption=post_text
            )
        else:
            # Отправляем только текст
            result = self.telegram_client.send_message(text=post_text)
        
        if result and result.get("ok"):
            self.logger.info(f"Пост опубликован: {trend} (message_id: {result['message_id']})")
            return {
                "success": True,
                "message_id": result["message_id"],
                "trend": trend
            }
        
        self.logger.error(f"Не удалось опубликовать пост: {trend}")
        return None
    
    def update_post_status(
        self,
        trend: str,
        message_id: int
    ) -> bool:
        """
        Обновляет статус поста в Texts.
        
        Args:
            trend: Название тренда
            message_id: ID сообщения в Telegram
        
        Returns:
            True если успешно
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        updates = {
            "posted": "Y",
            "posted_at": now,
            "message_id": str(message_id)
        }
        
        success = self.sheets_client.find_and_update(
            "Texts",
            "trend",
            trend,
            updates
        )
        
        if success:
            self.logger.info(f"Статус обновлён для: {trend}")
        else:
            self.logger.warning(f"Не удалось обновить статус для: {trend}")
        
        return success
    
    def run(self) -> Dict:
        """
        Запускает публикацию постов.
        
        Returns:
            Статистика {published, failed, total}
        """
        self.logger.info("=== Запуск Publisher ===")
        
        # Проверяем соединение
        if not self.telegram_client.test_connection():
            self.logger.error("Нет соединения с Telegram API")
            return {"published": 0, "failed": 0, "total": 0}
        
        # Получаем посты для публикации
        posts = self.get_posts_for_publish()
        
        if not posts:
            self.logger.info("Нет постов для публикации")
            return {"published": 0, "failed": 0, "total": 0}
        
        # Публикуем каждый пост
        published = 0
        failed = 0
        
        for post in posts:
            result = self.publish_post(post)
            
            if result and result.get("success"):
                # Обновляем статус
                self.update_post_status(
                    result["trend"],
                    result["message_id"]
                )
                published += 1
            else:
                failed += 1
        
        self.logger.info(f"Публикация завершена: {published} успешно, {failed} ошибок")
        
        return {
            "published": published,
            "failed": failed,
            "total": len(posts)
        }


def run_publisher() -> Dict:
    """Точка входа для запуска агента"""
    publisher = Publisher()
    return publisher.run()


if __name__ == "__main__":
    stats = run_publisher()
    print(f"Publisher завершил работу.")
    print(f"  Опубликовано: {stats['published']}")
    print(f"  Ошибок: {stats['failed']}")
    print(f"  Всего: {stats['total']}")
