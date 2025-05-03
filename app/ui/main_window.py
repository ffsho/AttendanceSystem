from PyQt6.QtWidgets import (QMainWindow, QWidget, QTabWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
import cv2
from ..core.face_recognition import FaceRecognizer
from ..core.database import DatabaseManager
from datetime import datetime
from .registration import RegistrationWidget
from .statistics import StatisticsWidget
from .system_participants import SystemParticipantsWidget
from .export import ExportWidget



class MainWindow(QMainWindow):
    update_table_signal = pyqtSignal()
    
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.face_recognizer = FaceRecognizer(db)
        self.tracking_active = False
        self.init_ui()
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        
        # Связываем сигналы
        self.update_table_signal.connect(self.update_attendance_table)
        self.update_attendance_table()

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

        # Вкладка "Статистика"
        self.statistics_tab = StatisticsWidget(self.db)
        self.tabs.addTab(self.statistics_tab, "Статистика")

        # Вкладка "Участники системы"
        self.users_tab = SystemParticipantsWidget(self.db)
        self.tabs.addTab(self.users_tab, "Участники системы")

        # Вкладка "Экспорт"
        self.export_tab = ExportWidget(self.db)
        self.tabs.addTab(self.export_tab, "Экспорт")

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
        self.attendance_table.setHorizontalHeaderLabels(["ФИО", "Группа", "Время/Дата"])
        self.attendance_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.attendance_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.attendance_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        main_layout.addLayout(left_panel, stretch=2)
        main_layout.addWidget(self.attendance_table, stretch=1)


    def toggle_tracking(self):
        self.tracking_active = not self.tracking_active
        if self.tracking_active:
            # Используем новый атрибут known_embeddings
            if not self.face_recognizer.known_embeddings:
                QMessageBox.warning(self, "Внимание", "Нет зарегистрированных пользователей!")
                self.tracking_active = False
                return
            
            # Пересоздаем объект камеры при каждом запуске
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                QMessageBox.critical(self, "Ошибка", "Камера недоступна!")
                self.tracking_active = False
                return
            
            self.tracking_btn.setText("Остановить отслеживание")
            self.timer.start(100)  # 100 мс для снижения нагрузки
        else:
            self.tracking_btn.setText("Начать отслеживание")
            self.timer.stop()
            if self.cap.isOpened():
                self.cap.release()
            self.video_label.clear()
            self.video_label.setText("Нажмите 'Начать отслеживание' для активации")
    
    def update_frame(self):
        """Обновление кадра с распознаванием лиц"""
        ret, frame = self.cap.read()
        if ret:
            # Распознавание лиц и получение результатов
            processed_frame, recognized_users = self.face_recognizer.process_frame(frame)

            # Обновление таблицы при обнаружении
            if recognized_users:
                self.update_table_signal.emit()

            # Конвертация для отображения в Qt
            rgb_image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(q_img).scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
            ))

    def update_attendance_table(self):
        """Обновление таблицы посещаемости"""
        try:
            # Получаем данные из БД
            records = self.db.get_today_attendance()

            # Устанавливаем правильное количество строк и столбцов
            self.attendance_table.setRowCount(len(records))
            self.attendance_table.setColumnCount(4)  # Добавлен 4-й столбец

            # Обновляем заголовки
            self.attendance_table.setHorizontalHeaderLabels(["ФИО", "Группа", "Время", "Дата"])

            # Обрабатываем каждую запись
            for row_idx, (fullname, group_name, timestamps) in enumerate(records):
                # Устанавливаем значения по умолчанию
                time_str = "N/A"
                date_str = "N/A"
                group = group_name or "N/A"  # Обработка None

                if timestamps:
                    # Очищаем и парсим временные метки
                    clean_timestamps = timestamps.strip(', ')
                    timestamp_list = [ts.strip() for ts in clean_timestamps.split(',') if ts.strip()]

                    if timestamp_list:
                        last_time = max(timestamp_list)
                        try:
                            dt = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
                            date_str = dt.strftime("%d.%m.%Y")
                            time_str = dt.strftime("%H:%M")
                        except Exception as e:
                            print(f"Ошибка парсинга времени: {e}")

                # Явно создаем элементы таблицы
                self.attendance_table.setItem(row_idx, 0, QTableWidgetItem(str(fullname)))
                self.attendance_table.setItem(row_idx, 1, QTableWidgetItem(str(group)))
                self.attendance_table.setItem(row_idx, 2, QTableWidgetItem(str(time_str)))
                self.attendance_table.setItem(row_idx, 3, QTableWidgetItem(str(date_str)))

        except Exception as e:
            print(f"Ошибка при обновлении таблицы: {e}")
            # Очищаем таблицу при ошибках
            self.attendance_table.setRowCount(0)



    def handle_registration_complete(self):
        """Обновление данных после регистрации"""
        self.face_recognizer.load_known_faces()
        self.face_recognizer.last_detected_user = None  # Сброс кэша
        self.update_attendance_table()
        self.update_table_signal.emit()
        self.video_label.repaint()


    def closeEvent(self, event):
        """Освобождение ресурсов при закрытии окна"""
        if self.cap.isOpened():
            self.cap.release()
        event.accept()