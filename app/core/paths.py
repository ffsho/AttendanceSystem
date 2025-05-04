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
MODELS_DIR = DATA_DIR / "models"

# Пути к данным
DB_DIR = DATA_DIR / "db"
ATTENDANCE_REPORTS_DIR = DATA_DIR / "reports"
FACES_DATA_DIR = DATA_DIR / "faces"
FACES_IMG_DIR = FACES_DATA_DIR / "images"

# Файлы
DB_FILE = DB_DIR / "attendance.db"

# Стили
STYLES_DIR = ROOT_DIR / "app" / "styles"

def verify_paths():
    """Проверка и создание необходимой структуры директорий"""
    required_dirs = [
        DB_DIR,
        ATTENDANCE_REPORTS_DIR,
        FACES_IMG_DIR,
        MODELS_DIR
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