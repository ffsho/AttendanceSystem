from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                            QPushButton, QTableWidget, QTableWidgetItem, 
                            QLabel, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from ..core.database import DatabaseManager



class StatisticsWidget(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Поисковая строка
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по фамилии, группе или дате (ДД.ММ.ГГГГ)")
        self.search_input.returnPressed.connect(self.search_attendance)
        
        search_btn = QPushButton("Поиск")
        search_btn.clicked.connect(self.search_attendance)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        
        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["ФИО", "Группа", "Дата", "Время"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        
        # Добавляем элементы в основной layout
        layout.addLayout(search_layout)
        layout.addWidget(self.results_table)
        
        # Загружаем все данные при инициализации
        self.load_all_attendance()
        
    def search_attendance(self):
        """Выполняет поиск по введенному запросу"""
        search_text = self.search_input.text().strip()
        
        if not search_text:
            self.load_all_attendance()
            return
            
        # Пробуем распарсить дату
        try:
            date_obj = QDate.fromString(search_text, "dd.MM.yyyy")
            if date_obj.isValid():
                date_str = date_obj.toString("yyyy-MM-dd")
                records = self.db.get_attendance_by_date(date_str)
                self.display_results(records)
                return
        except:
            pass
            
        # Если не дата, ищем по фамилии или группе
        records = self.db.get_attendance_by_search(search_text.lower())
        self.display_results(records)
        
    def load_all_attendance(self):
        """Загружает все записи посещаемости"""
        # Получаем записи за последние 30 дней
        end_date = QDate.currentDate().toString("yyyy-MM-dd")
        start_date = QDate.currentDate().addDays(-30).toString("yyyy-MM-dd")
        records = self.db.get_attendance(start_date, end_date)
        self.display_results(records)
        
    def display_results(self, records):
        """Отображает результаты в таблице"""
        self.results_table.setRowCount(len(records))
        
        for row_idx, (user_id, fullname, times) in enumerate(records):
            # Разбиваем строку с временами на отдельные записи
            time_entries = [t.strip() for t in times.split(';') if t.strip()]
            
            # Для каждой записи создаем отдельную строку в таблице
            for entry_idx, time_entry in enumerate(time_entries):
                if entry_idx > 0:
                    self.results_table.insertRow(row_idx + entry_idx)
                
                try:
                    dt = datetime.strptime(time_entry, "%d.%m.%Y %H:%M")
                    date_str = dt.strftime("%d.%m.%Y")
                    time_str = dt.strftime("%H:%M")
                except:
                    date_str = "N/A"
                    time_str = "N/A"
                
                # Получаем группу пользователя (нужно добавить этот метод в DatabaseManager)
                group = self.db.get_user_group(user_id)
                
                self.results_table.setItem(row_idx + entry_idx, 0, QTableWidgetItem(fullname))
                self.results_table.setItem(row_idx + entry_idx, 1, QTableWidgetItem(group))
                self.results_table.setItem(row_idx + entry_idx, 2, QTableWidgetItem(date_str))
                self.results_table.setItem(row_idx + entry_idx, 3, QTableWidgetItem(time_str))