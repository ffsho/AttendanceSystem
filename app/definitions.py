from pathlib import Path

# Базовые пути
ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "app"

# Пути к данным
DB_DIR = APP_DIR / "db"
ATTENDANCE_DIR = APP_DIR / "Attendance"
FACES_DATA_DIR = APP_DIR / "faces_data"
FACES_IMG_DIR = FACES_DATA_DIR / "faces"

# Файлы базы данных
DB_FILE = DB_DIR / "attendance.db"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov"}

# Пути к моделям ML
MODELS_DIR = ROOT_DIR / "models"
FACE_DETECTION_MODEL = MODELS_DIR / "haarcascade_frontalface_default.xml"

# Создание директорий при необходимости
required_dirs = [DB_DIR, ATTENDANCE_DIR, FACES_IMG_DIR]
for directory in required_dirs:
    directory.mkdir(parents=True, exist_ok=True)