from PyQt6.QtWidgets import QApplication
from app.core.database import DatabaseManager
from app.ui.main_window import MainWindow
import sys

def main():
    app = QApplication(sys.argv)
    db = DatabaseManager("educational")
    window = MainWindow(db)
    # load_styles(app)
    window.show()
    sys.exit(app.exec())

def load_styles(app: QApplication):
    try:
        with open("app/styles/SpyBot.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Ошибка загрузки стилей: {e}")


if __name__ == "__main__":
    main()