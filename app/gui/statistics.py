from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                            QPushButton, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QDate
from ..core.database import DatabaseManager




class StatisticsWidget(QWidget):

    def __init__(self, db: DatabaseManager):
        """
        Инициализация влкдки "Статистика"
        :param db: Объект DatabaseManager для работы с базой данных
        """
        
        super().__init__()
        self.db = db
        self.institution_type = db.institution_type
        self.init_ui()
        

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Панель управления поиском
        search_layout = QHBoxLayout()
        
        if self.institution_type == 'Educational':
            # Поле ввода
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Введите ФИО, группу или дату (ДД.ММ.ГГГГ)")
            # Кнопки поиска
            self.btn_text = QPushButton("Поиск по ФИО/группе")
            self.btn_date = QPushButton("Поиск по дате")

        elif self.institution_type == 'Enterprise':
            # Поле ввода
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Введите ФИО, должности или дату (ДД.ММ.ГГГГ)")
            # Кнопки поиска
            self.btn_text = QPushButton("Поиск по ФИО/должности")
            self.btn_date = QPushButton("Поиск по дате")

        
        # Настройка кнопок
        self.btn_text.clicked.connect(self.search_by_text)
        self.btn_date.clicked.connect(self.search_by_date)
        
        # Добавление элементов
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_text)
        search_layout.addWidget(self.btn_date)
        
        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)

        if self.institution_type == 'Educational':
            self.results_table.setHorizontalHeaderLabels(["ФИО", "Группа", "Дата", "Время"])
        elif self.institution_type == 'Enterprise':
            self.results_table.setHorizontalHeaderLabels(["ФИО", "Должность", "Дата", "Время"])
        
        # Настройка ширины столбцов
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Компоновка
        layout.addLayout(search_layout)
        layout.addWidget(self.results_table)
        
        # Загрузка начальных данных
        self.load_last_30_days()
        

    def search_by_text(self):
        """Поиск по ФИО или группе"""
        search_text = self.search_input.text().strip()
        if not search_text:
            self.load_last_30_days()
            return
            
        records = self.db.get_attendance_by_search(search_text)
        self.display_results(records)
        

    def search_by_date(self):
        """Поиск по дате"""
        date_input = self.search_input.text().strip()
        if not date_input:
            self.load_last_30_days()
            return
            
        try:
            records = self.db.get_attendance_by_date(date_input)
            self.display_results(records)
        except ValueError as e:
            print(f"Ошибка даты: {str(e)}")
            

    def load_last_30_days(self):
        """Загрузка данных за последние 30 дней"""
        end_date = QDate.currentDate().toString("yyyy-MM-dd")
        start_date = QDate.currentDate().addDays(-30).toString("yyyy-MM-dd")
        records = self.db.get_attendance(start_date, end_date)
        self.display_results(records)
        
        
    def display_results(self, records):
        """Отображение результатов"""
        self.results_table.setRowCount(0)
        
        for user_id, fullname, times in records:
            for entry in times.split(';'):
                entry = entry.strip()
                if not entry:
                    continue
                    
                row = self.results_table.rowCount()
                self.results_table.insertRow(row)
                
                try:
                    dt = datetime.strptime(entry, "%d.%m.%Y %H:%M")
                    date_str = dt.strftime("%d.%m.%Y")
                    time_str = dt.strftime("%H:%M")
                except:
                    date_str = time_str = "N/A"
                
                # Таблица
                self.results_table.setItem(row, 0, QTableWidgetItem(fullname))
                if self.institution_type == 'Educational':
                    group = self.db.get_user_group(user_id)
                    self.results_table.setItem(row, 1, QTableWidgetItem(group))
                elif self.institution_type == 'Enterprise':
                    position = self.db.get_user_position(user_id)
                    self.results_table.setItem(row, 1, QTableWidgetItem(position))
                self.results_table.setItem(row, 2, QTableWidgetItem(date_str))
                self.results_table.setItem(row, 3, QTableWidgetItem(time_str))