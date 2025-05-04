from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                            QPushButton, QFormLayout, QMessageBox, QSizePolicy, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from ..core.face_recognition import FaceRecognizer
from ..core.database import DatabaseManager



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
            'faculty': QComboBox(),
            'group': QComboBox()
        }

        faculties = ["Математический факультет"]
        groups = ["МТ-101", "МТ-102", "МТ-201", "МТ-202", "МТ-301", "МТ-302", "МТ-401", 
                  "МП-101", "МП-102", "МП-103", "МП-201", "МП-202", "МП-203", "МП-301", "МП-302", "МП-401", "МП-402", 
                  "МН-101", "МН-102", "МН-201", "МН-202", "МН-301", "МН-401", 
                  "МК-101", "МК-102", "МК-201", "МК-202", "МК-301", "МК-302", "МК-401", "МК-402", "МК-501", ]
        
        self.inputs['faculty'].addItems(faculties)
        self.inputs['group'].addItems(groups)

        # Добавление полей в форму
        self.form.addRow(self.inputs['lastname'])
        self.inputs['lastname'].setPlaceholderText("Фамилия")
        self.form.addRow(self.inputs['firstname'])
        self.inputs['firstname'].setPlaceholderText("Имя")
        self.form.addRow(self.inputs['patronymic'])
        self.inputs['patronymic'].setPlaceholderText("Отчество")
        self.form.addRow(self.inputs['faculty'])
        self.form.addRow(self.inputs['group'])
    

        # Кнопки
        self.btn_register = QPushButton("Зарегистрировать")
        self.btn_register.clicked.connect(self.start_registration)
        self.btn_register.setObjectName("btn_register")

        container = QWidget()
        container.setObjectName("registration_container")
        container_layout = QVBoxLayout(container)
        container_layout.addLayout(self.form)
        container_layout.addWidget(self.btn_register, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)

        for label in [self.form.itemAt(i).widget() for i in range(self.form.rowCount())]:
            if isinstance(label, QLabel):
                label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)


    def start_registration(self):
        """Запуск процесса регистрации"""
        user_data = {
            'lastname': self.inputs['lastname'].text().strip(),
            'firstname': self.inputs['firstname'].text().strip(),
            'patronymic': self.inputs['patronymic'].text().strip(),
            'faculty': self.inputs['faculty'].currentText().strip(),
            'group': self.inputs['group'].currentText().strip()
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