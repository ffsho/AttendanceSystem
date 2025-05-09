from pathlib import Path
import sys


# Базовые пути
try:
    # Определение корневой директории проекта
    ROOT_DIR = Path(__file__).resolve().parents[2]
    if not ROOT_DIR.exists():
        raise FileNotFoundError("Корневая директория проекта не найдена")
except Exception as e:
    print(f"FATAL ERROR: {str(e)}")
    sys.exit(1)


# Основные директории
DATA_DIR = ROOT_DIR / "app" / "data"

# Пути к данным
DB_DIR = DATA_DIR / "db"
ATTENDANCE_REPORTS_DIR = DATA_DIR / "reports"
FACES_DATA_DIR = DATA_DIR / "faces"
FACES_DATA_DIR_EDUCATIONAL = FACES_DATA_DIR / "educational"
FACES_DATA_DIR_ENTERPRISE = FACES_DATA_DIR / "enterprise"
FACES_IMG_DIR_EDUCATIONAL = FACES_DATA_DIR_EDUCATIONAL / "images"
FACES_IMG_DIR_ENTERPRISE = FACES_DATA_DIR_ENTERPRISE / "images"

# Базы данных
DB_EDUCATIONAL = DB_DIR / "educational.db"
DB_ENTERPRISE = DB_DIR / "enterprise.db"

# Настройки .ini
SETTINGS_FILE = ROOT_DIR / "app" / "settings" / "settings.ini"
DEFAULT_SETTINGS_FILE = ROOT_DIR / "app" / "settings" / "default_settings.ini"

# Стили
STYLES_DIR = ROOT_DIR / "app" / "styles"

def verify_paths():
    """Проверка и создание необходимой структуры директорий"""
    required_dirs = [
        DB_DIR,
        ATTENDANCE_REPORTS_DIR,
        FACES_IMG_DIR_EDUCATIONAL,
        FACES_IMG_DIR_ENTERPRISE
    ]
    
    # Создание директорий
    for directory in required_dirs:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Невозможно создать директорию {directory}: {str(e)}")
            sys.exit(1)

# Выполнение проверок при импорте
verify_paths()