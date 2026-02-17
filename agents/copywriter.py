"""Агент 4: Bob Copywriter

Генерирует провокационные посты для Telegram на основе трендов.
Использует профиль Bob 2.0 для стиля и тона.
"""

from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from utils import setup_logger
from storage.google_sheets import get_sheets_client
from storage.llm_client import get_llm_client


# Заголовки для Google Sheets Texts
TEXTS_HEADERS = [
    "date",
    "trend",
    "post_text",
    "status",
    "approved",
    "posted",
    "cover_image_url",
    "posted_at",
    "message_id"
]


class BobCopywriter:
    """Агент для генерации постов в стиле Bob 2.0"""
    
    def __init__(self):
        self.logger = setup_logger("BobCopywriter", "copywriter.log")
        self.sheets_client = get_sheets_client()
        self.llm_client = get_llm_client()
        
        # Загружаем системный промт
        self.system_prompt = self._load_system_prompt()
        
        self.logger.info("Bob Copywriter инициализирован")
    
    def _load_system_prompt(self) -> str:
        """Загружает системный промт из файла"""
        prompt_path = Path("prompts/bob_2_0.md")
        
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        
        # Fallback промт если файл не найден
        return """Ты — Bob 2.0, провокационный IT-блогер.
Структура поста: ХУК → БОЛЬ → ИНТРИГА → CTA → ПЕТЛЯ
Длина: 600-800 символов. Используй эмодзи 🔥💀🚀"""
    
    def _build_user_prompt(self, trend: Dict) -> str:
        """
        Строит пользовательский промт на основе тренда.
        
        Args:
            trend: Словарь тренда {title, description, news: [...]}
        
        Returns:
            Промт для генерации поста
        """
        title = trend.get("title", "AI Trend")
        description = trend.get("description", "")
        news_items = trend.get("news", [])
        
        # Формируем список новостей для контекста
        news_context = "\n".join([
            f"- {item.get('title', '')}"
            for item in news_items[:5]
        ])
        
        return f"""
Тренд: {title}

Описание: {description}

Новости по теме:
{news_context}

Задача: Напиши провокационный пост для Telegram (600-800 символов) по этому тренду.
Используй структуру: ХУК → БОЛЬ → ИНТРИГА → CTA → ПЕТЛЯ
Добавь агрессивные эмодзи и FOMO-триггеры.
"""
    
    def generate_post(self, trend: Dict) -> Optional[str]:
        """
        Генерирует пост для одного тренда.
        
        Args:
            trend: Словарь тренда
        
        Returns:
            Сгенерированный пост или None
        """
        user_prompt = self._build_user_prompt(trend)
        
        self.logger.info(f"Генерация поста для тренда: {trend.get('title')}")
        
        post = self.llm_client.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=800,
            temperature=0.8
        )
        
        if post:
            # Проверяем длину
            if len(post) < 600:
                self.logger.warning(f"Пост слишком короткий ({len(post)} символов)")
            elif len(post) > 800:
                self.logger.warning(f"Пост слишком длинный ({len(post)} символов)")
            else:
                self.logger.info(f"Пост готов ({len(post)} символов)")
        
        return post
    
    def generate_posts(self, trends: List[Dict], num_posts: int = 4) -> List[Dict]:
        """
        Генерирует посты для трендов.
        
        Args:
            trends: Список трендов
            num_posts: Количество постов (4 из 5 трендов, 1 запасной)
        
        Returns:
            Список постов [{trend, post_text}]
        """
        posts = []
        
        # Берём TOP-N трендов
        selected_trends = trends[:num_posts]
        
        for trend in selected_trends:
            post_text = self.generate_post(trend)
            
            if post_text:
                posts.append({
                    "trend": trend.get("title", ""),
                    "post_text": post_text,
                    "trend_data": trend  # Сохраняем для обложек
                })
                self.logger.info(f"Пост создан для: {trend.get('title')}")
            else:
                self.logger.warning(f"Не удалось создать пост для: {trend.get('title')}")
        
        self.logger.info(f"Создано постов: {len(posts)}/{len(selected_trends)}")
        
        return posts
    
    def save_to_sheets(self, posts: List[Dict]) -> int:
        """
        Сохраняет посты в Google Sheets Texts.
        
        Args:
            posts: Список постов
        
        Returns:
            Количество сохранённых записей
        """
        saved_count = 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for post in posts:
            values = [
                now,  # date
                post["trend"],  # trend
                post["post_text"],  # post_text
                "draft",  # status
                "N",  # approved
                "N",  # posted
                "",  # cover_image_url
                "",  # posted_at
                ""  # message_id
            ]
            
            if self.sheets_client.append_to_sheet(
                "Texts",
                values,
                headers=TEXTS_HEADERS
            ):
                saved_count += 1
        
        self.logger.info(f"Сохранено в Texts: {saved_count}/{len(posts)}")
        
        return saved_count
    
    def run(self, trends: List[Dict]) -> int:
        """
        Запускает полный пайплайн генерации постов.
        
        Args:
            trends: Список трендов из Trend Selector
        
        Returns:
            Количество сохранённых постов
        """
        self.logger.info("=== Запуск Bob Copywriter ===")
        
        if not trends:
            self.logger.warning("Нет трендов для генерации")
            return 0
        
        # Генерируем посты (4 из 5 трендов)
        posts = self.generate_posts(trends, num_posts=4)
        
        if not posts:
            self.logger.error("Не удалось создать ни одного поста")
            return 0
        
        # Сохраняем в Google Sheets
        saved = self.save_to_sheets(posts)
        
        return saved


def run_copywriter(trends: List[Dict] = None) -> int:
    """
    Точка входа для запуска агента.
    
    Args:
        trends: Список трендов (опционально, если None — загрузит из trends.md)
    
    Returns:
        Количество сохранённых постов
    """
    copywriter = BobCopywriter()
    
    # Если тренды не переданы, пробуем загрузить
    if trends is None:
        from agents.trend_selector import TrendSelector
        selector = TrendSelector()
        trends = selector.run()
    
    return copywriter.run(trends)


if __name__ == "__main__":
    count = run_copywriter()
    print(f"Bob Copywriter завершил работу. Сохранено постов: {count}")
