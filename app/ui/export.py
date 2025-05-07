from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QDateEdit, QLabel, QFileDialog, QMessageBox, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import QDate
from datetime import datetime
import pandas as pd
import sqlite3
from ..core.database import DatabaseManager



class ExportWidget(QWidget):

    def __init__(self, db: DatabaseManager):
        """
        Инициализация вкладки "Экспорт"
        :param db: Объект DatabaseManager для работы с базой данных 
        """
        super().__init__()
        self.db = db
        self.institution_type = db.institution_type
        self.init_ui()


    def init_ui(self):
        layout = QVBoxLayout(self)

        # Выбор диапазона дат
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("С:"))
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("По:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Загрузить данные")
        self.load_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(self.load_btn)
        
        self.export_btn = QPushButton("Экспорт в Excel")
        self.export_btn.clicked.connect(self.export_to_excel)
        self.export_btn.setEnabled(False)
        btn_layout.addWidget(self.export_btn)
        
        # Таблица для предпросмотра
        self.preview_table = QTableWidget()

        if self.institution_type == 'Educational':
            self.preview_table.setColumnCount(4)
            self.preview_table.setHorizontalHeaderLabels(["ФИО", "Группа", "Дата", "Время"])
        elif self.institution_type == 'Enterprise':
            self.preview_table.setColumnCount(4)
            self.preview_table.setHorizontalHeaderLabels(["ФИО", "Должность", "Дата", "Время"])

        self.preview_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        # Компоновка
        layout.addLayout(date_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(self.preview_table)


    def load_data(self):
        """Загрузка данных для предпросмотра"""
        try:
            start = self.start_date.date().toString("yyyy-MM-dd")
            end = self.end_date.date().toString("yyyy-MM-dd")
            
            records = self.db.get_attendance(start, end)
            if not records:
                QMessageBox.warning(self, "Нет данных", "За выбранный период записи отсутствуют.")
                return
            
            self.display_preview(records)
            self.export_btn.setEnabled(True)
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка БД", f"Ошибка загрузки данных:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Неизвестная ошибка:\n{str(e)}")


    def display_preview(self, records):
        """Отображение данных для предпросмотра"""
        self.preview_table.setRowCount(0)
        
        for user_id, fullname, times in records:
            for entry in times.split(';'):
                entry = entry.strip()
                if not entry:
                    continue
                
                row = self.preview_table.rowCount()
                self.preview_table.insertRow(row)
                
                try:
                    dt = datetime.strptime(entry, "%d.%m.%Y %H:%M")
                    date_str = dt.strftime("%d.%m.%Y")
                    time_str = dt.strftime("%H:%M")
                except ValueError:
                    date_str = "Ошибка даты"
                    time_str = "Ошибка времени"
                
                self.preview_table.setItem(row, 0, QTableWidgetItem(fullname))
                if self.institution_type == 'Educational':
                    group = self.db.get_user_group(user_id) or "N/A"
                    self.preview_table.setItem(row, 1, QTableWidgetItem(group))
                elif self.institution_type == 'Enterprise':
                    position = self.db.get_user_position(user_id) or "N/A"
                    self.preview_table.setItem(row, 1, QTableWidgetItem(position))
                self.preview_table.setItem(row, 2, QTableWidgetItem(date_str))
                self.preview_table.setItem(row, 3, QTableWidgetItem(time_str))


    def export_to_excel(self):
        """Экспорт данных в Excel"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить как",
                f"Посещаемость_{self.start_date.date().toString('dd-MM-yyyy')}_{self.end_date.date().toString('dd-MM-yyyy')}.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                return
                
            start = self.start_date.date().toString("yyyy-MM-dd")
            end = self.end_date.date().toString("yyyy-MM-dd")
            records = self.db.get_attendance(start, end)
            
            # Формирование DataFrame
            data = []
            for user_id, fullname, times in records:

                if self.institution_type == 'Educational':
                    group = self.db.get_user_group(user_id) or "N/A"
                elif self.institution_type == 'Enterprise':
                    position = self.db.get_user_position(user_id) or "N/A"

                for entry in times.split(';'):
                    entry = entry.strip()
                    if entry:
                        try:
                            dt = datetime.strptime(entry, "%d.%m.%Y %H:%M")
                            if self.institution_type == 'Educational':
                                data.append({
                                    "ФИО": fullname,
                                    "Группа": group,
                                    "Дата": dt.strftime("%d.%m.%Y"),
                                    "Время": dt.strftime("%H:%M")
                                })
                            elif self.institution_type == 'Enterprise':
                                data.append({
                                    "ФИО": fullname,
                                    "Должность": position,
                                    "Дата": dt.strftime("%d.%m.%Y"),
                                    "Время": dt.strftime("%H:%M")
                                })
                        except ValueError:
                            continue
            
            if not data:
                QMessageBox.warning(self, "Нет данных", "Нет данных для экспорта.")
                return
                
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            QMessageBox.information(
                self, 
                "Экспорт завершен", 
                f"Данные успешно экспортированы в файл:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Ошибка экспорта", 
                f"Не удалось выполнить экспорт:\n{str(e)}"
            )