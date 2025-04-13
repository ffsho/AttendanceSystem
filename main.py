from app.definitions import DB_FILE, FACES_IMG_DIR
from app.DataBaseManager import DatabaseManager
import argparse


def main():
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["edu", "ent"], required=True)
    args = parser.parse_args()

    # Инициализация БД
    institution_type = "educational" if args.type == "edu" else "enterprise"
    db = DatabaseManager(institution_type)
    
    print(f"Система готова к работе! Тип учреждения: {institution_type}")


if __name__ == "__main__":
    main()