"""
AI Content Pipeline v1.0 — Orchestrator

Главный скрипт для последовательного запуска агентов 1-6.
Поддерживает запуск по расписанию (APScheduler) и разовый запуск.

Использование:
    python main.py              # Разовый запуск всех агентов
    python main.py --schedule   # Запуск с планировщиком (daily 09:30 UTC+4)
"""

import sys
import argparse
from datetime import datetime
from typing import Dict, Any, Optional
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import load_env
from utils import setup_logger
from agents.rss_collector import run_rss_collector
from agents.sonar_scanner import run_sonar_scanner
from agents.trend_selector import run_trend_selector
from agents.copywriter import run_copywriter
from agents.cover_generator import run_cover_generator
from agents.publisher import run_publisher


# Время запуска по UTC+4 (Europe/Samara)
SCHEDULER_TIMEZONE = "Europe/Samara"
DAILY_RUN_HOUR = 9
DAILY_RUN_MINUTE = 30


class Orchestrator:
    """Оркестратор для управления пайплайном агентов"""
    
    def __init__(self):
        load_env()
        self.logger = setup_logger("Orchestrator", "orchestrator.log")
        
        # Статистика выполнения
        self.stats: Dict[str, Any] = {
            "started_at": None,
            "finished_at": None,
            "agents": {},
            "errors": []
        }
        
        self.logger.info("Orchestrator инициализирован")
    
    def _run_agent(self, name: str, func, *args, **kwargs) -> Any:
        """
        Запускает агента с логированием и обработкой ошибок.
        
        Args:
            name: Название агента
            func: Функция для запуска
            *args, **kwargs: Аргументы для функции
        
        Returns:
            Результат выполнения или None при ошибке
        """
        self.logger.info(f"▶️ Запуск агента: {name}")
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.stats["agents"][name] = {
                "status": "success",
                "result": result,
                "duration_sec": duration,
                "started_at": start_time.isoformat(),
                "finished_at": end_time.isoformat()
            }
            
            self.logger.info(f"✅ Агент {name} завершён за {duration:.2f}с")
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.stats["agents"][name] = {
                "status": "error",
                "error": error_msg,
                "duration_sec": duration,
                "started_at": start_time.isoformat(),
                "finished_at": end_time.isoformat()
            }
            self.stats["errors"].append({"agent": name, "error": error_msg})
            
            self.logger.error(f"❌ Агент {name} завершился с ошибкой: {e}")
            
            # Graceful degradation — продолжаем выполнение
            return None
    
    def run_pipeline(self) -> Dict[str, Any]:
        """
        Запускает полный пайплайн агентов 1-6.
        
        Последовательность:
        1. RSS Collector → NewsRaw
        2. Sonar Scanner → NewsRaw
        3. Trend Selector → trends.md
        4. Bob Copywriter → Texts (drafts)
        5. Cover Generator → data/*.png + Texts updated
        6. Publisher → Telegram (только approved)
        
        Returns:
            Статистика выполнения
        """
        self.logger.info("=" * 60)
        self.logger.info("🚀 Запуск AI Content Pipeline")
        self.logger.info("=" * 60)
        
        self.stats["started_at"] = datetime.now().isoformat()
        
        # Агент 1: RSS Collector
        rss_count = self._run_agent("RSS Collector", run_rss_collector)
        
        # Агент 2: Sonar Scanner
        sonar_count = self._run_agent("Sonar Scanner", run_sonar_scanner)
        
        # Агент 3: Trend Selector
        trends = self._run_agent("Trend Selector", run_trend_selector)
        
        # Агент 4: Bob Copywriter (нужны тренды)
        posts_count = self._run_agent("Bob Copywriter", run_copywriter, trends)
        
        # Агент 5: Cover Generator
        covers_count = self._run_agent("Cover Generator", run_cover_generator)
        
        # Агент 6: Publisher (публикует только approved)
        publish_stats = self._run_agent("Publisher", run_publisher)
        
        self.stats["finished_at"] = datetime.now().isoformat()
        
        # Итоговый отчёт
        self._print_summary()
        
        return self.stats
    
    def _print_summary(self):
        """Печатает итоговый отчёт о выполнении"""
        self.logger.info("=" * 60)
        self.logger.info("📊 Итоговый отчёт")
        self.logger.info("=" * 60)
        
        # Собираем результаты
        rss_result = self.stats["agents"].get("RSS Collector", {})
        sonar_result = self.stats["agents"].get("Sonar Scanner", {})
        trends_result = self.stats["agents"].get("Trend Selector", {})
        posts_result = self.stats["agents"].get("Bob Copywriter", {})
        covers_result = self.stats["agents"].get("Cover Generator", {})
        publish_result = self.stats["agents"].get("Publisher", {})
        
        # Формируем сводку
        summary = [
            f"📰 RSS Collector: {rss_result.get('result', 0)} новостей",
            f"🔍 Sonar Scanner: {sonar_result.get('result', 0)} событий",
            f"📈 Trend Selector: {len(trends_result.get('result', []))} трендов",
            f"✍️ Bob Copywriter: {posts_result.get('result', 0)} постов",
            f"🎨 Cover Generator: {covers_result.get('result', 0)} обложек",
        ]
        
        # Публикация
        pub_result = publish_result.get('result', {})
        if pub_result:
            summary.append(
                f"📢 Publisher: {pub_result.get('published', 0)} опубликовано, "
                f"{pub_result.get('failed', 0)} ошибок"
            )
        
        for line in summary:
            self.logger.info(line)
        
        # Ошибки
        if self.stats["errors"]:
            self.logger.warning(f"⚠️ Ошибок: {len(self.stats['errors'])}")
            for err in self.stats["errors"]:
                self.logger.warning(f"  - {err['agent']}: {err['error']}")
        
        # Длительность
        try:
            start = datetime.fromisoformat(self.stats["started_at"])
            finish = datetime.fromisoformat(self.stats["finished_at"])
            total_duration = (finish - start).total_seconds()
            self.logger.info(f"⏱️ Общая длительность: {total_duration:.2f}с")
        except:
            pass
        
        self.logger.info("=" * 60)


def create_scheduler() -> BlockingScheduler:
    """
    Создаёт планировщик для ежедневного запуска.
    
    Returns:
    BlockingScheduler
    """
    scheduler = BlockingScheduler(timezone=pytz.timezone(SCHEDULER_TIMEZONE))
    
    # Запуск каждый день в 09:30 UTC+4
    trigger = CronTrigger(
        hour=DAILY_RUN_HOUR,
        minute=DAILY_RUN_MINUTE,
        timezone=SCHEDULER_TIMEZONE
    )
    
    scheduler.add_job(
        run_pipeline_wrapper,
        trigger=trigger,
        id="daily_pipeline",
        name="Daily AI Content Pipeline",
        replace_existing=True
    )
    
    return scheduler


def run_pipeline_wrapper():
    """Обёртка для запуска пайплайна (для планировщика)"""
    orchestrator = Orchestrator()
    return orchestrator.run_pipeline()


def main():
    """Точка входа"""
    parser = argparse.ArgumentParser(
        description="AI Content Pipeline — Мультиагентная система генерации контента"
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Запустить с планировщиком (daily 09:30 UTC+4)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Тестовый запуск (проверка соединения)"
    )
    
    args = parser.parse_args()
    
    if args.test:
        # Тестовый запуск
        print("🔧 Тестовый запуск AI Content Pipeline")
        print("-" * 40)
        
        try:
            from storage.google_sheets import get_sheets_client
            print("✅ Google Sheets Client: OK")
        except Exception as e:
            print(f"❌ Google Sheets Client: {e}")
        
        try:
            from storage.telegram_client import get_telegram_client
            client = get_telegram_client()
            if client.test_connection():
                print("✅ Telegram Bot: OK")
            else:
                print("❌ Telegram Bot: Connection failed")
        except Exception as e:
            print(f"❌ Telegram Bot: {e}")
        
        print("-" * 40)
        print("Тест завершён")
        return
    
    if args.schedule:
        # Запуск с планировщиком
        print(f"⏰ Запуск планировщика (ежедневно в {DAILY_RUN_HOUR}:{DAILY_RUN_MINUTE:02d} UTC+4)")
        
        scheduler = create_scheduler()
        
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("\n👋 Планировщик остановлен")
    else:
        # Разовый запуск
        orchestrator = Orchestrator()
        orchestrator.run_pipeline()


if __name__ == "__main__":
    main()
