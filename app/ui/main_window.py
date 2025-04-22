from PyQt6.QtWidgets import (QMainWindow, QWidget, QTabWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTableWidget, 
                            QTableWidgetItem)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
import cv2
from ..core.face_recognition import FaceRecognizer
from ..core.database import DatabaseManager
from datetime import datetime
from .registration import RegistrationWidget

class MainWindow(QMainWindow):
    update_table_signal = pyqtSignal()
    
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.face_recognizer = FaceRecognizer(db)
        self.tracking_active = False
        self.init_ui()
        self.init_camera()
        
        # Связываем сигналы
        self.update_table_signal.connect(self.update_attendance_table)

    def init_ui(self):
        self.setWindowTitle("Система учета посещаемости")
        self.setGeometry(100, 100, 1200, 600)
        
        # Создаем виджет вкладок
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Вкладка "Главная"
        self.main_tab = QWidget()
        self.tabs.addTab(self.main_tab, "Главная")

        # Вкладка "Регистрация"
        self.registration_tab = RegistrationWidget(self.db, self.face_recognizer)
        self.registration_tab.registration_complete.connect(self.handle_registration_complete)
        self.tabs.addTab(self.registration_tab, "Регистрация")
        # Компоновка главной вкладки
        main_layout = QHBoxLayout(self.main_tab)
        
        # Левая панель: камера и управление
        left_panel = QVBoxLayout()
        
        # Область для видео
        self.video_label = QLabel("Нажмите 'Начать отслеживание' для активации")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("border: 2px solid gray;")
        self.video_label.setMinimumSize(640, 480)
        
        # Кнопка управления отслеживанием
        self.tracking_btn = QPushButton("Начать отслеживание")
        self.tracking_btn.clicked.connect(self.toggle_tracking)
        
        left_panel.addWidget(self.video_label)
        left_panel.addWidget(self.tracking_btn)
        
        # Правая панель: таблица посещаемости
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(3)
        self.attendance_table.setHorizontalHeaderLabels(["ФИО", "Время", "Дата"])
        self.attendance_table.horizontalHeader().setStretchLastSection(True)
        
        main_layout.addLayout(left_panel, stretch=2)
        main_layout.addWidget(self.attendance_table, stretch=1)

    def init_camera(self):
        """Инициализация камеры через OpenCV"""
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

    def toggle_tracking(self):
        """Переключение режима отслеживания"""
        self.tracking_active = not self.tracking_active
        if self.tracking_active:
            self.timer.start(30)
            self.tracking_btn.setText("Остановить отслеживание")
            self.video_label.setText("Идет обработка видео...")
        else:
            self.timer.stop()
            self.tracking_btn.setText("Начать отслеживание")
            self.video_label.setText("Нажмите 'Начать отслеживание' для активации")

    def update_frame(self):
        """Обновление кадра с распознаванием лиц"""
        ret, frame = self.cap.read()
        if ret and self.tracking_active:
            # Распознавание лиц через FaceRecognizer
            processed_frame = self.face_recognizer.process_frame(frame)
            
            # Обновление таблицы при обнаружении
            if self.face_recognizer.last_detection:
                self.update_table_signal.emit()
            
            # Конвертация для отображения в Qt
            rgb_image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(q_img).scaled(
                self.video_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio
            ))

    def update_attendance_table(self):
        """Обновление таблицы посещаемости"""
        today = datetime.now().strftime("%Y-%m-%d")
        records = self.db.get_attendance(today, today)
        
        self.attendance_table.setRowCount(len(records))
        for row_idx, (user_id, fullname, timestamps) in enumerate(records):
            if timestamps:
                last_time = max(timestamps.split(', '))
                try:
                    dt = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
                    date_str = dt.strftime("%d.%m.%Y")
                    time_str = dt.strftime("%H:%M")
                except:
                    date_str = "N/A"
                    time_str = "N/A"
            else:
                date_str = "N/A"
                time_str = "N/A"
            
            self.attendance_table.setItem(row_idx, 0, QTableWidgetItem(fullname))
            self.attendance_table.setItem(row_idx, 1, QTableWidgetItem(time_str))
            self.attendance_table.setItem(row_idx, 2, QTableWidgetItem(date_str))
    
    def handle_registration_complete(self):
        """Обновление данных после регистрации"""
        self.face_recognizer.load_known_faces()
        self.update_attendance_table()

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.cap.isOpened():
            self.timer.stop()
            self.cap.release()
        event.accept()