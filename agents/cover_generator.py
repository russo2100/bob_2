"""Агент 5: Cover Generator

Генерирует обложки для постов на основе текста.
Создаёт visual prompt и использует DALL-E API.
"""

from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import re
import hashlib

from utils import setup_logger
from storage.google_sheets import get_sheets_client
from storage.image_client import get_image_gen_client
from storage.local_fs import ensure_directory


class CoverGenerator:
    """Агент для генерации обложек к постам"""
    
    # Стили для обложек
    COVER_STYLES = {
        "tech": "futuristic technology style, neon blue and purple, digital art",
        "dramatic": "dramatic lighting, high contrast, cinematic composition",
        "minimal": "minimalist design, clean lines, modern aesthetic",
        "abstract": "abstract geometric shapes, vibrant colors, dynamic",
        "cyberpunk": "cyberpunk aesthetic, neon lights, dark atmosphere"
    }
    
    def __init__(self):
        self.logger = setup_logger("CoverGenerator", "cover_generator.log")
        self.sheets_client = get_sheets_client()
        self.image_client = get_image_gen_client()
        
        # Создаём директорию для обложек
        ensure_directory("data")
        
        self.logger.info("Cover Generator инициализирован")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Извлекает ключевые слова из текста поста.
        
        Args:
            text: Текст поста
        
        Returns:
            Список ключевых слов
        """
        # Удаляем эмодзи и специальные символы
        text = re.sub(r'[^\w\sа-яА-ЯёЁ]', ' ', text)
        
        # Короткие стоп-слова
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'в', 'на', 'по', 'с', 'со', 'за', 'под', 'над', 'для', 'от',
            'и', 'или', 'но', 'а', 'же', 'ли', 'бы', 'что', 'кто', 'где'
        }
        
        words = text.lower().split()
        keywords = [
            word for word in words
            if len(word) > 3 and word not in stop_words
        ]
        
        # Возвращаем TOP-5 уникальных
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
                if len(unique_keywords) >= 5:
                    break
        
        return unique_keywords
    
    def _generate_visual_prompt(self, post_text: str, trend: str) -> str:
        """
        Генерирует visual prompt для DALL-E на основе текста поста.
        
        Args:
            post_text: Текст поста
            trend: Название тренда
        
        Returns:
            Промт для генерации изображения
        """
        keywords = self._extract_keywords(post_text)
        keywords_str = ", ".join(keywords) if keywords else "AI, technology, future"
        
        # Выбираем стиль на основе тренда
        style = self.COVER_STYLES.get("tech")  # Default tech style
        
        visual_prompt = (
            f"Cover image for social media post about {trend}. "
            f"Key concepts: {keywords_str}. "
            f"Style: {style}. "
            f"Square format, bold composition, eye-catching design, "
            f"professional quality, 4k resolution"
        )
        
        self.logger.debug(f"Visual prompt: {visual_prompt[:100]}...")
        
        return visual_prompt
    
    def _generate_slug(self, text: str) -> str:
        """
        Генерирует slug для имени файла.
        
        Args:
            text: Текст для создания slug
        
        Returns:
            Slug (например, "ai-models-2024-02-17")
        """
        # Хешируем текст для уникальности
        hash_part = hashlib.md5(text.encode()).hexdigest()[:8]
        date_part = datetime.now().strftime("%Y%m%d")
        
        # Очищаем от специальных символов
        clean_text = re.sub(r'[^\w\sа-яА-ЯёЁ-]', '', text[:30])
        slug_text = clean_text.lower().replace(' ', '-')
        
        return f"{slug_text}-{date_part}-{hash_part}"
    
    def generate_cover(self, post_text: str, trend: str) -> Optional[str]:
        """
        Генерирует обложку для поста.
        
        Args:
            post_text: Текст поста
            trend: Название тренда
        
        Returns:
            Путь к файлу обложки или None
        """
        self.logger.info(f"Генерация обложки для тренда: {trend}")
        
        # Генерируем visual prompt
        visual_prompt = self._generate_visual_prompt(post_text, trend)
        
        # Генерируем изображение
        image_data = self.image_client.generate_image(
            prompt=visual_prompt,
            size="1080x1080"
        )
        
        if not image_data:
            self.logger.error("Не удалось сгенерировать изображение")
            return None
        
        # Генерируем slug для имени файла
        slug = self._generate_slug(f"{trend}-{post_text[:50]}")
        filepath = f"data/{slug}.png"
        
        # Сохраняем изображение
        if self.image_client.save_image(image_data, filepath):
            self.logger.info(f"Обложка сохранена: {filepath}")
            return filepath
        
        return None
    
    def get_posts_for_covers(self) -> List[Dict]:
        """
        Получает посты со статусом draft/approved без обложек.
        
        Returns:
            Список постов из Texts
        """
        # Читаем все записи из Texts
        records = self.sheets_client.read_from_sheet("Texts")
        
        # Фильтруем: status=draft или approved, без cover_image_url
        filtered = [
            record for record in records
            if record.get("status") in ["draft", "approved"]
            and not record.get("cover_image_url", "")
        ]
        
        self.logger.info(f"Найдено постов для обложек: {len(filtered)}")
        
        return filtered
    
    def update_cover_url(self, trend: str, cover_path: str) -> bool:
        """
        Обновляет запись в Texts с путём к обложке.
        
        Args:
            trend: Название тренда
            cover_path: Путь к файлу обложки
        
        Returns:
            True если успешно
        """
        # Используем абсолютный путь или относительный
        if not cover_path.startswith("http"):
            # Локальный путь
            cover_url = cover_path
        
        success = self.sheets_client.find_and_update(
            "Texts",
            "trend",
            trend,
            {"cover_image_url": cover_url}
        )
        
        if success:
            self.logger.info(f"Обновлена обложка для тренда: {trend}")
        else:
            self.logger.warning(f"Не найдено записи для тренда: {trend}")
        
        return success
    
    def run(self, posts: List[Dict] = None) -> int:
        """
        Запускает генерацию обложек.
        
        Args:
            posts: Список постов (опционально, если None — загрузит из Texts)
        
        Returns:
            Количество сгенерированных обложек
        """
        self.logger.info("=== Запуск Cover Generator ===")
        
        # Если посты не переданы, загружаем из Texts
        if posts is None:
            posts = self.get_posts_for_covers()
        
        if not posts:
            self.logger.warning("Нет постов для генерации обложек")
            return 0
        
        generated_count = 0
        
        for post in posts:
            trend = post.get("trend", "")
            post_text = post.get("post_text", "")
            
            if not trend or not post_text:
                self.logger.warning("Пост без trend или post_text, пропускаем")
                continue
            
            # Генерируем обложку
            cover_path = self.generate_cover(post_text, trend)
            
            if cover_path:
                # Обновляем запись в Texts
                self.update_cover_url(trend, cover_path)
                generated_count += 1
        
        self.logger.info(f"Сгенерировано обложек: {generated_count}/{len(posts)}")
        
        return generated_count


def run_cover_generator(posts: List[Dict] = None) -> int:
    """Точка входа для запуска агента"""
    generator = CoverGenerator()
    return generator.run(posts)


if __name__ == "__main__":
    count = run_cover_generator()
    print(f"Cover Generator завершил работу. Сгенерировано обложек: {count}")
