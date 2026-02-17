"""Утилиты для работы с локальной файловой системой"""

from pathlib import Path
from typing import Optional, List
import json

from utils import setup_logger


logger = setup_logger("LocalFS", "local_fs.log")


def read_file(filepath: str, encoding: str = "utf-8") -> Optional[str]:
    """
    Читает файл и возвращает содержимое.
    
    Args:
        filepath: Путь к файлу
        encoding: Кодировка
    
    Returns:
        Содержимое файла или None
    """
    try:
        path = Path(filepath)
        if not path.exists():
            logger.warning(f"Файл не найден: {filepath}")
            return None
        
        with open(path, "r", encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Ошибка чтения файла {filepath}: {e}")
        return None


def write_file(filepath: str, content: str, encoding: str = "utf-8") -> bool:
    """
    Записывает содержимое в файл.
    
    Args:
        filepath: Путь к файлу
        content: Содержимое
        encoding: Кодировка
    
    Returns:
        True если успешно
    """
    try:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        
        logger.info(f"Файл записан: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Ошибка записи файла {filepath}: {e}")
        return False


def read_json(filepath: str) -> Optional[dict]:
    """
    Читает JSON файл.
    
    Args:
        filepath: Путь к файлу
    
    Returns:
        Словарь или None
    """
    try:
        content = read_file(filepath)
        if content:
            return json.loads(content)
        return None
    except Exception as e:
        logger.error(f"Ошибка чтения JSON {filepath}: {e}")
        return None


def write_json(filepath: str, data: dict, indent: int = 2) -> bool:
    """
    Записывает словарь в JSON файл.
    
    Args:
        filepath: Путь к файлу
        data: Данные для записи
        indent: Отступ для форматирования
    
    Returns:
        True если успешно
    """
    try:
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        return write_file(filepath, content)
    except Exception as e:
        logger.error(f"Ошибка записи JSON {filepath}: {e}")
        return False


def list_files(directory: str, pattern: str = "*") -> List[str]:
    """
    Возвращает список файлов в директории по паттерну.
    
    Args:
        directory: Путь к директории
        pattern: Глоб-паттерн (например, "*.png")
    
    Returns:
        Список путей к файлам
    """
    try:
        path = Path(directory)
        if not path.exists():
            return []
        
        return [str(f) for f in path.glob(pattern)]
    except Exception as e:
        logger.error(f"Ошибка списка файлов в {directory}: {e}")
        return []


def file_exists(filepath: str) -> bool:
    """
    Проверяет существование файла.
    
    Args:
        filepath: Путь к файлу
    
    Returns:
        True если файл существует
    """
    return Path(filepath).exists()


def get_filename_without_extension(filepath: str) -> str:
    """
    Получает имя файла без расширения.
    
    Args:
        filepath: Путь к файлу
    
    Returns:
        Имя файла без расширения
    """
    return Path(filepath).stem


def ensure_directory(directory: str) -> bool:
    """
    Создаёт директорию если не существует.
    
    Args:
        directory: Путь к директории
    
    Returns:
        True если успешно
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Ошибка создания директории {directory}: {e}")
        return False
