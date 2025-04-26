from PyQt6.QtWidgets import QApplication
from app.core.database import DatabaseManager
from app.ui.main_window import MainWindow
import sys

def main():
    app = QApplication(sys.argv)
    db = DatabaseManager("educational")  # или "enterprise"
    window = MainWindow(db)
    db.delete_attendance_record(2)
    window.show()
    sys.exit(app.exec())




if __name__ == "__main__":
    main()