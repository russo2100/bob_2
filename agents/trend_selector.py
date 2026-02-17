"""Агент 3: Trend Selector

Анализирует новости из NewsRaw, кластеризует по темам
и выбирает TOP-5 трендов для генерации постов.
"""

from typing import List, Dict, Tuple
from collections import defaultdict
from datetime import datetime
import re

from utils import setup_logger
from storage.google_sheets import get_sheets_client


# Ключевые слова для кластеризации по темам
TOPIC_KEYWORDS = {
    "AI Models": ["gpt", "model", "llm", "transformer", "diffusion", "claude", "gemini", "llama"],
    "AI Agents": ["agent", "autonomous", "workflow", "automation", "copilot", "assistant"],
    "AI Regulation": ["regulation", "policy", "law", "eu ai act", "safety", "governance"],
    "AI Business": ["investment", "funding", "acquisition", "valuation", "revenue", "market"],
    "AI Research": ["paper", "research", "benchmark", "accuracy", "performance", "state-of-the-art"],
    "AI Hardware": ["gpu", "tpu", "chip", "nvidia", "amd", "intel", "hardware", "compute"],
    "AI Open Source": ["open source", "github", "hugging face", "release", "library", "framework"],
    "AI Ethics": ["bias", "ethics", "fairness", "privacy", "misuse", "dangerous"],
}

# Бренды с высоким приоритетом (хайп)
HIGH_PRIORITY_BRANDS = ["OpenAI", "Google", "Anthropic", "Meta", "Microsoft", "NVIDIA"]


class TrendSelector:
    """Агент для выбора трендов из новостей"""
    
    def __init__(self):
        self.logger = setup_logger("TrendSelector", "trend_selector.log")
        self.sheets_client = get_sheets_client()
    
    def _classify_topic(self, text: str) -> str:
        """
        Классифицирует текст по темам.
        
        Args:
            text: Текст новости
        
        Returns:
            Название темы
        """
        text_lower = text.lower()
        
        for topic, keywords in TOPIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return topic
        
        return "AI General"  # Тема по умолчанию
    
    def _calculate_score(
        self,
        cluster: List[Dict],
        topic: str
    ) -> float:
        """
        Рассчитывает score для кластера трендов.
        
        Формула: частота + бренд_бонус + новизна
        
        Args:
            cluster: Список новостей в кластере
            topic: Название темы
        
        Returns:
            Score тренда
        """
        # Частота упоминаний (вес 1.0)
        frequency_score = len(cluster)
        
        # Бренд бонус (вес 2.0)
        brand_score = 0
        for news in cluster:
            brand = news.get("brand", "")
            if brand and brand in HIGH_PRIORITY_BRANDS:
                brand_score += 2
        
        # Новизна (вес 0.5) - свежие новости важнее
        recency_score = 0
        now = datetime.now()
        for news in cluster:
            try:
                pub_date = datetime.strptime(news.get("published_at", ""), "%Y-%m-%d %H:%M:%S")
                hours_diff = (now - pub_date).total_seconds() / 3600
                # Чем свежее, тем выше score (максимум 1.0)
                recency_score += max(0, 1 - hours_diff / 24) * 0.5
            except (ValueError, TypeError):
                recency_score += 0.25  # Среднее значение если дата не распознана
        
        total_score = frequency_score + brand_score + recency_score
        self.logger.debug(f"Topic '{topic}': freq={frequency_score}, brand={brand_score}, recency={recency_score:.2f}, total={total_score:.2f}")
        
        return total_score
    
    def _generate_description(self, cluster: List[Dict], topic: str) -> str:
        """
        Генерирует описание тренда на основе новостей в кластере.
        
        Args:
            cluster: Список новостей
            topic: Название темы
        
        Returns:
            Описание тренда (2-3 предложения)
        """
        # Берём самые свежие заголовки
        titles = [news.get("title", "") for news in cluster[:3]]
        
        # Извлекаем бренды
        brands = set()
        for news in cluster:
            brand = news.get("brand", "")
            if brand:
                brands.add(brand)
        
        # Формируем описание
        brands_str = ", ".join(brands) if brands else "Various companies"
        count = len(cluster)
        
        description = f"{topic}: {count} новостей от {brands_str}. Ключевые события: {'; '.join(titles[:2])}"
        
        return description[:300]  # Ограничиваем длину
    
    def cluster_news(self, records: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Кластеризует новости по темам.
        
        Args:
            records: Список новостей из NewsRaw
        
        Returns:
            Словарь {topic: [news_records]}
        """
        clusters = defaultdict(list)
        
        for record in records:
            # Объединяем title и summary для классификации
            text = f"{record.get('title', '')} {record.get('summary', '')}"
            topic = self._classify_topic(text)
            clusters[topic].append(record)
        
        self.logger.info(f"Сформировано кластеров: {len(clusters)}")
        for topic, news in clusters.items():
            self.logger.info(f"  {topic}: {len(news)} новостей")
        
        return dict(clusters)
    
    def select_top_trends(
        self,
        clusters: Dict[str, List[Dict]],
        top_n: int = 5
    ) -> List[Dict]:
        """
        Выбирает TOP-N трендов по score.
        
        Args:
            clusters: Словарь кластеров
            top_n: Количество трендов для выбора
        
        Returns:
            Список трендов [{title, description, score, count}]
        """
        trends = []
        
        for topic, cluster in clusters.items():
            score = self._calculate_score(cluster, topic)
            description = self._generate_description(cluster, topic)
            
            trends.append({
                "title": topic,
                "description": description,
                "score": score,
                "count": len(cluster),
                "news": cluster  # Сохраняем для копирайтера
            })
        
        # Сортируем по score (убывание)
        trends.sort(key=lambda x: x["score"], reverse=True)
        
        top_trends = trends[:top_n]
        self.logger.info(f"Выбрано TOP-{top_n} трендов")
        
        return top_trends
    
    def generate_trends_md(self, trends: List[Dict], output_path: str = "trends.md") -> str:
        """
        Генерирует trends.md файл.
        
        Args:
            trends: Список трендов
            output_path: Путь для сохранения
        
        Returns:
            Содержимое файла
        """
        lines = [
            "# 🔥 TOP-5 AI Trends",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ]
        
        for i, trend in enumerate(trends, 1):
            lines.append(f"## {i}. {trend['title']}")
            lines.append("")
            lines.append(f"**Score:** {trend['score']:.1f} | **News:** {trend['count']}")
            lines.append("")
            lines.append(f"{trend['description']}")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        content = "\n".join(lines)
        
        # Сохраняем файл
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.logger.info(f"Сохранён {output_path}")
        
        return content
    
    def run(self) -> List[Dict]:
        """
        Запускает полный пайплайн выбора трендов.
        
        Returns:
            Список TOP-5 трендов
        """
        self.logger.info("=== Запуск Trend Selector ===")
        
        # Читаем новости за сегодня
        records = self.sheets_client.get_today_records("NewsRaw", "date")
        self.logger.info(f"Прочитано записей за сегодня: {len(records)}")
        
        if not records:
            self.logger.warning("Нет записей за сегодня")
            return []
        
        # Кластеризуем
        clusters = self.cluster_news(records)
        
        # Выбираем TOP-5
        top_trends = self.select_top_trends(clusters, top_n=5)
        
        # Генерируем trends.md
        if top_trends:
            self.generate_trends_md(top_trends)
        
        return top_trends


def run_trend_selector() -> List[Dict]:
    """Точка входа для запуска агента"""
    selector = TrendSelector()
    return selector.run()


if __name__ == "__main__":
    trends = run_trend_selector()
    print(f"Trend Selector завершил работу. Выбрано трендов: {len(trends)}")
    for i, trend in enumerate(trends, 1):
        print(f"  {i}. {trend['title']} (score: {trend['score']:.1f})")
