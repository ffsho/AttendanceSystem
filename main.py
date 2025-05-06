from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase, QFont
from app.core.database import DatabaseManager
from app.ui.main_window import MainWindow
import sys
from app.core.paths import STYLES_DIR

def main():
    app = QApplication(sys.argv)
    db = DatabaseManager("Educational")
    window = MainWindow(db)
    load_styles(app)
    window.show()
    sys.exit(app.exec())

def load_styles(app: QApplication):
    try:
        with open(f"{STYLES_DIR}/style.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
            font_id = QFontDatabase.addApplicationFont(f"{STYLES_DIR}/fonts/Montserrat-Regular.ttf")
            font_family = QFontDatabase.applicationFontFamilies(font_id)
            app.setFont(QFont(font_family[0]))
    except Exception as e:
        print(f"Ошибка загрузки стилей: {e}")



if __name__ == "__main__":
    main()