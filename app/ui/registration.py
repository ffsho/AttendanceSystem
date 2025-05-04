from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                            QPushButton, QFormLayout, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from ..core.face_recognition import FaceRecognizer
from ..core.database import DatabaseManager
import cv2



class RegistrationWidget(QWidget):

    registration_complete = pyqtSignal()

    def __init__(self, db: DatabaseManager, face_recognizer: FaceRecognizer):
        """
        Инициализация вкладки "Регистрация"
        :param db: Объект DatabaseManager для работы с базой данных
        """

        super().__init__()
        self.db = db
        self.face_recognizer = face_recognizer
        self.current_user_id = None
        self.init_ui()


    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout = QVBoxLayout(self)

        # Форма ввода данных
        self.form = QFormLayout()
        
        self.inputs = {
            'lastname': QLineEdit(),
            'firstname': QLineEdit(),
            'patronymic': QLineEdit(),
            'faculty': QLineEdit(),
            'group': QLineEdit()
        }

        # Добавление полей в форму
        self.form.addRow("Фамилия:", self.inputs['lastname'])
        self.form.addRow("Имя:", self.inputs['firstname'])
        self.form.addRow("Отчество:", self.inputs['patronymic'])
        self.form.addRow("Факультет:", self.inputs['faculty'])
        self.form.addRow("Группа:", self.inputs['group'])

        # Кнопки
        self.btn_register = QPushButton("Зарегистрировать")
        self.btn_register.clicked.connect(self.start_registration)
        # main_layout.addLayout(self.form)
        # main_layout.addWidget(self.btn_register, alignment=Qt.AlignmentFlag.AlignCenter)

        container = QWidget()
        container.setObjectName("registration_container")
        container_layout = QVBoxLayout(container)
        container_layout.addLayout(self.form)
        container_layout.addWidget(self.btn_register, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)


    def start_registration(self):
        """Запуск процесса регистрации"""
        user_data = {
            'lastname': self.inputs['lastname'].text().strip(),
            'firstname': self.inputs['firstname'].text().strip(),
            'patronymic': self.inputs['patronymic'].text().strip(),
            'faculty': self.inputs['faculty'].text().strip(),
            'group': self.inputs['group'].text().strip()
        }

        if not all(user_data.values()):
            QMessageBox.critical(self, "Ошибка", "Все поля обязательны для заполнения!")
            return

        # Сохранение в БД
        user_id = self.db.add_user(user_data)
        if user_id == -1:
            QMessageBox.critical(self, "Ошибка", "Ошибка сохранения в базу данных!")
            return

        # Захват образцов лица
        if self.capture_face_samples(user_id):
            self.clear_form()
            self.db.add_attendance_record(user_id)
            self.registration_complete.emit()
            QMessageBox.information(self, "Успех", 
                "Пользователь успешно зарегистрирован!\nЛицо добавлено в систему.")
        else:
            self.db.delete_user(user_id)
            QMessageBox.critical(self, "Ошибка", 
                "Не удалось захватить изображения лица!")


    def capture_face_samples(self, user_id: int) -> bool:
        return self.face_recognizer.register_new_user(user_id=user_id, num_samples=10)


    def clear_form(self):
        """Очистка полей формы"""
        for field in self.inputs.values():
            field.clear()