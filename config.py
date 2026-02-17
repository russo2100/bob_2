"""Конфигурация проекта и загрузка переменных окружения"""

from dotenv import load_dotenv
from pathlib import Path
import os


def load_env():
    """Загружает .env файл из корня проекта"""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Пробуем загрузить .env.example как fallback
        env_example_path = Path(__file__).parent / ".env.example"
        if env_example_path.exists():
            load_dotenv(env_example_path)


def get_env(key: str, default: str = None, required: bool = False) -> str:
    """
    Получает переменную окружения.
    
    Args:
        key: Имя переменной
        default: Значение по умолчанию
        required: Если True, выбрасывает ошибку при отсутствии
    
    Returns:
        Значение переменной или default/None
    """
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


def get_env_list(key: str, separator: str = ",") -> list:
    """
    Получает список из переменной окружения (разделённый separator).
    
    Args:
        key: Имя переменной
        separator: Разделитель значений
    
    Returns:
        Список значений
    """
    value = get_env(key, "")
    if not value:
        return []
    return [item.strip() for item in value.split(separator)]


def get_env_int(key: str, default: int = 0) -> int:
    """
    Получает целочисленное значение из переменной окружения.
    
    Args:
        key: Имя переменной
        default: Значение по умолчанию
    
    Returns:
        Целочисленное значение
    """
    value = get_env(key, str(default))
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Получает булево значение из переменной окружения.
    
    Args:
        key: Имя переменной
        default: Значение по умолчанию
    
    Returns:
        Булево значение
    """
    value = get_env(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


# =========================================
# OpenRouter конфигурация
# =========================================

def get_openrouter_api_key() -> str:
    """Получает API ключ OpenRouter"""
    return get_env("OPENROUTER_API_KEY", required=True)


def get_model_for_task(task: str) -> str:
    """
    Получает модель для конкретной задачи.
    
    Args:
        task: Название задачи (rss, sonar, trend, copywriter, cover)
    
    Returns:
        Название модели
    """
    task_to_env = {
        "rss": "RSS_MODEL_NAME",
        "sonar": "SONAR_MODEL_NAME",
        "trend": "TREND_MODEL_NAME",
        "copywriter": "COPYWRITER_MODEL_NAME",
        "cover": "COVER_MODEL_NAME",
        "image": "IMAGE_MODEL_NAME"
    }
    
    env_key = task_to_env.get(task, "COPYWRITER_MODEL_NAME")
    return get_env(env_key, "openai/gpt-4o-mini")


# =========================================
# Google API конфигурация
# =========================================

def get_google_credentials_path() -> str:
    """Получает путь к credentials.json"""
    return get_env("GOOGLE_CREDENTIALS_PATH", "credentials.json")


def get_google_service_account_email() -> str:
    """Получает email сервисного аккаунта"""
    return get_env("GOOGLE_SERVICE_ACCOUNT_EMAIL", "")


def get_google_delegated_email() -> str:
    """Получает email для делегирования (ваш личный email)"""
    return get_env("GOOGLE_DELEGATED_EMAIL", "")


def get_google_spreadsheet_id() -> str:
    """Получает ID Google Таблицы"""
    return get_env("GOOGLE_SPREADSHEET_ID", required=True)


def get_google_drive_folder_id() -> str:
    """Получает ID папки на Google Диске"""
    return get_env("GOOGLE_DRIVE_FOLDER_ID", "")


# =========================================
# Telegram конфигурация
# =========================================

def get_telegram_bot_token() -> str:
    """Получает токен Telegram бота"""
    return get_env("TELEGRAM_BOT_TOKEN", "")


def get_telegram_channel_id() -> str:
    """Получает ID Telegram канала"""
    return get_env("TELEGRAM_CHANNEL_ID", "")


# =========================================
# Логирование конфигурация
# =========================================

def get_log_level() -> str:
    """Получает уровень логирования"""
    return get_env("LOG_LEVEL", "INFO")


def get_log_to_file() -> bool:
    """Проверяет нужно ли сохранять логи в файлы"""
    return get_env_bool("LOG_TO_FILE", True)


# =========================================
# Планировщик конфигурация
# =========================================

def get_scheduler_timezone() -> str:
    """Получает часовой пояс для планировщика"""
    return get_env("SCHEDULER_TIMEZONE", "Europe/Samara")


def get_daily_run_hour() -> int:
    """Получает час ежедневного запуска"""
    return get_env_int("DAILY_RUN_HOUR", 9)


def get_daily_run_minute() -> int:
    """Получает минуты ежедневного запуска"""
    return get_env_int("DAILY_RUN_MINUTE", 30)


# =========================================
# Дополнительные настройки
# =========================================

def get_top_trends_count() -> int:
    """Получает количество трендов для выбора"""
    return get_env_int("TOP_TRENDS_COUNT", 5)


def get_posts_count() -> int:
    """Получает количество постов для генерации"""
    return get_env_int("POSTS_COUNT", 4)


def get_max_post_length() -> int:
    """Получает максимальную длину поста"""
    return get_env_int("MAX_POST_LENGTH", 800)


def get_min_post_length() -> int:
    """Получает минимальную длину поста"""
    return get_env_int("MIN_POST_LENGTH", 600)


def get_default_post_status() -> str:
    """Получает статус по умолчанию для новых постов"""
    return get_env("DEFAULT_POST_STATUS", "draft")


def get_auto_approve_posts() -> bool:
    """Проверяет нужно ли автоматически одобрять посты"""
    return get_env_bool("AUTO_APPROVE_POSTES", False)


def get_image_size() -> str:
    """Получает размер изображений для генерации"""
    return get_env("IMAGE_SIZE", "1080x1080")
