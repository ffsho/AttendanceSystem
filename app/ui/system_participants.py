from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt
from ..core.database import DatabaseManager




class SystemParticipantsWidget(QWidget):
    
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.init_ui()
        self.load_users()


    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Панель поиска и управления
        control_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по ФИО или группе...")
        self.search_input.returnPressed.connect(self.search_users)
        
        self.search_btn = QPushButton("Поиск")
        self.search_btn.clicked.connect(self.search_users)
        
        self.delete_btn = QPushButton("Удалить выделенного")
        self.delete_btn.clicked.connect(self.delete_selected_user)
        
        control_layout.addWidget(self.search_input)
        control_layout.addWidget(self.search_btn)
        control_layout.addWidget(self.delete_btn)
        
        # Таблица пользователей
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Фамилия", "Имя", "Отчество", "Тип", 
            "Факультет", "Группа"
        ])
        
        # Настройка таблицы
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.users_table.verticalHeader().hide()
        
        layout.addLayout(control_layout)
        layout.addWidget(self.users_table)


    def load_users(self, search_query=None):
        try:
            users = self.db.get_all_users(search_query)
            self.users_table.setRowCount(len(users))
            
            for row_idx, user in enumerate(users):
                for col_idx, value in enumerate(user):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
                    # Для ID сделаем выравнивание по центру
                    if col_idx == 0:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    self.users_table.setItem(row_idx, col_idx, item)
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить пользователей: {str(e)}")


    def search_users(self):
        query = self.search_input.text().strip()
        self.load_users(query)


    def delete_selected_user(self):
        selected = self.users_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Внимание", "Выберите пользователя для удаления!")
            return
            
        try:
            user_id = int(self.users_table.item(selected[0].row(), 0).text())
            
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Вы уверены, что хотите удалить этого пользователя? Все связанные записи посещаемости также будут удалены!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.db.delete_user(user_id):
                    self.load_users()
                    
                    QMessageBox.information(self, "Успех", "Пользователь успешно удален!")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось удалить пользователя!")
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")