from PyQt6.QtWidgets import (QMainWindow, QWidget, QTabWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QMessageBox, QMenuBar, QApplication)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QAction, QIcon
import cv2
from ..core.face_recognition import FaceRecognizer
from ..core.database import DatabaseManager
from datetime import datetime
from .registration import RegistrationWidget
from .statistics import StatisticsWidget
from .system_participants import SystemParticipantsWidget
from .export import ExportWidget
from .settings import SettingsDialog
from ..settings.settings import SettingsManager
EXIT_CODE_REBOOT = 1001



class MainWindow(QMainWindow):

    update_table_signal = pyqtSignal()
    

    def __init__(self, settings_manager: SettingsManager):
        """
        Инициализация главного окна
        :param settings_manager: Объект SettingsManager для работы с конфигурационными файлами
        """

        super().__init__()
        self.settings_manager = settings_manager
        self.settings_manager.load_settings()
        self.institution_type = settings_manager.get_setting('institution')
        self.db = DatabaseManager(settings_manager.get_setting('institution'))
        self.restart_required = False
        self.tracking_active = False
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.face_recognizer = FaceRecognizer(self.db, self.settings_manager)
        self.init_ui()

        # Связывание сигналов
        self.update_table_signal.connect(self.update_attendance_table)
        self.update_attendance_table()


    def init_ui(self):
        # Настройки окна
        self.setWindowTitle("Система учета посещаемости")
        self.setGeometry(100, 100, 1200, 600)

        # Меню
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        # 'Настройки'
        settings = QAction("Настройки", self)
        menu_bar.addAction(settings)
        settings.triggered.connect(self.open_settings)

        # Виджет вкладок
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
        
        if self.institution_type == 'Educational':
            self.attendance_table.setHorizontalHeaderLabels(["ФИО", "Группа", "Время/Дата"])
        elif self.institution_type == 'Enterprise':
            self.attendance_table.setHorizontalHeaderLabels(["ФИО", "Должность", "Время/Дата"])

        self.attendance_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.attendance_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.attendance_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        main_layout.addLayout(left_panel, stretch=2)
        main_layout.addWidget(self.attendance_table, stretch=1)


    def toggle_tracking(self):
        """
        Запуск/остановка режима отслеживание и поиска лиц
        """
        self.tracking_active = not self.tracking_active
        
        if self.tracking_active:
        
            if not self.face_recognizer.known_embeddings:
                QMessageBox.warning(self, "Внимание", "Нет зарегистрированных пользователей!")
                self.tracking_active = False
                return

            self.cap = cv2.VideoCapture(0)
        
            if not self.cap.isOpened():
                QMessageBox.critical(self, "Ошибка", "Камера недоступна!")
                self.tracking_active = False
                return

            self.tracking_btn.setText("Остановить отслеживание")
            self.timer.start(100)  # 100 мс
        
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
            # Получение записей о текущей посещаемости из БД
            records = self.db.get_today_attendance()

            self.attendance_table.setRowCount(len(records))
            self.attendance_table.setColumnCount(4)


            if self.institution_type == 'Educational':
                self.attendance_table.setHorizontalHeaderLabels(["ФИО", "Группа", "Время", "Дата"])
            elif self.institution_type == 'Enterprise':
                self.attendance_table.setHorizontalHeaderLabels(["ФИО", "Должность", "Время", "Дата"])


            # Обработка записей
            for row_idx, (fullname, group_position, timestamps) in enumerate(records):
                # Значения по умолчанию
                time_str = "N/A"
                date_str = "N/A"
                group = group_position or "N/A"

                if timestamps:
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

                self.attendance_table.setItem(row_idx, 0, QTableWidgetItem(str(fullname)))
                self.attendance_table.setItem(row_idx, 1, QTableWidgetItem(str(group)))
                self.attendance_table.setItem(row_idx, 2, QTableWidgetItem(str(time_str)))
                self.attendance_table.setItem(row_idx, 3, QTableWidgetItem(str(date_str)))

        except Exception as e:
            print(f"Ошибка при обновлении таблицы: {e}")
            self.attendance_table.setRowCount(0)


    def handle_registration_complete(self):
        """Обновление данных после регистрации"""
        self.face_recognizer.load_known_faces()
        self.face_recognizer.last_detected_user = None  # Сброс кэша
        self.update_attendance_table()
        self.update_table_signal.emit()
        self.video_label.repaint()


    def open_settings(self):
        """Открытие настроек"""
        settings_dialog = SettingsDialog(self.settings_manager, parent=self)
        settings_dialog.settings_updated.connect(self.update_settings) 
        settings_dialog.exec()
    
    
    def update_settings(self, new_settings):
        """Обработчик обновленных настроек"""
        print("Обновленные настройки:", new_settings)
        
        self.max_faces = new_settings['max_faces']
        if self.institution_type != new_settings['institution']:
            self.institution_type = new_settings['institution']
            self.recreate_db()
            self.restart_required = True
            self.close()
            
        self.recreate_face_recognizer()


    def recreate_db(self):
        """Пересоздание объекта DatabaseManager с обновленными настройками"""
        if hasattr(self, "db"):
            del self.db
        
        self.db = DatabaseManager(self.settings_manager.get_setting('institution'))


    def recreate_face_recognizer(self):
        """Пересоздание объекта FaceRecognizer с обновленными настройками"""
        if hasattr(self, "face_recognizer"):
            del self.face_recognizer

        self.face_recognizer = FaceRecognizer(self.db, self.settings_manager)
        self.face_recognizer.load_known_faces()


    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        if self.cap.isOpened():
            self.cap.release()

        # Для перезапуска
        if self.restart_required:
            QApplication.exit(EXIT_CODE_REBOOT)
        
        event.accept()