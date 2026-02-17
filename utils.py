"""Утилиты для логирования"""

import logging
from pathlib import Path
from config import get_log_level, get_log_to_file


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    Создаёт настроенный логгер для агента.
    
    Args:
        name: Имя логгера (обычно имя агента)
        log_file: Путь к файлу лога (опционально)
    
    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    
    # Очищаем существующие обработчики
    logger.handlers.clear()
    
    # Уровень логирования из конфига
    log_level = get_log_level()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Формат сообщений
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файловый обработчик (если указано и разрешено в конфиге)
    if log_file and get_log_to_file():
        log_path = Path("logs") / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
