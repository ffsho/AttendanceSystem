from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase, QFont
from app.gui.main_window import MainWindow
import sys
from app.core.paths import STYLES_DIR
from app.settings.settings import SettingsManager


def main():

    EXIT_CODE_REBOOT = 1001
    app = QApplication(sys.argv)

    while True:    
        settings_manager = SettingsManager()
        window = MainWindow(settings_manager)
        load_styles(app)
        window.show()

        exit_code = app.exec()
        if exit_code != EXIT_CODE_REBOOT:
            break

    sys.exit(exit_code)


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