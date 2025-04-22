import sqlite3
from datetime import datetime
from typing import List, Tuple
from pathlib import Path
import pytz
from .definitions import DB_FILE

TIMEZONE = pytz.timezone('Asia/Yekaterinburg')

class DatabaseManager:
    def __init__(self, institution_type: str):
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        self.institution_type = institution_type
        self._create_tables()

    def _create_tables(self):
        """Создание таблиц с корректной структурой"""
        try:
            # Таблица пользователей
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lastname TEXT NOT NULL,
                    firstname TEXT NOT NULL,
                    patronymic TEXT,
                    user_type TEXT CHECK(user_type IN ('student', 'employee')),
                    faculty TEXT,
                    group_name TEXT,
                    position TEXT,
                    hire_date DATE,
                    birth_date DATE
                )
            ''')

            # Таблица посещаемости с временем в UTC
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

            # Оптимизирующие индексы
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_attendance_user 
                ON attendance(user_id)
            ''')
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_attendance_time 
                ON attendance(timestamp)
            ''')

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()

    def _get_current_time(self) -> str:
        """Возвращает текущее время в формате ISO 8601 с часовым поясом"""
        return datetime.now(TIMEZONE).isoformat()

    def add_attendance_record(self, user_id: int):
        """Добавление записи о посещении с валидацией"""
        try:
            current_time = self._get_current_time()
            self.cursor.execute('''
                INSERT INTO attendance (user_id, timestamp)
                VALUES (?, ?)
            ''', (user_id, current_time))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error adding attendance: {e}")
            self.conn.rollback()

    def add_user(self, user_data: dict) -> int:
        """Добавление нового пользователя с транзакцией"""
        try:
            if self.institution_type == 'educational':
                self.cursor.execute('''
                    INSERT INTO users 
                    (lastname, firstname, patronymic, user_type, faculty, group_name)
                    VALUES (?, ?, ?, 'student', ?, ?)
                ''', (
                    user_data['lastname'],
                    user_data['firstname'],
                    user_data.get('patronymic', ''),
                    user_data['faculty'],
                    user_data['group']
                ))
            else:
                self.cursor.execute('''
                    INSERT INTO users 
                    (lastname, firstname, patronymic, user_type, position, hire_date, birth_date)
                    VALUES (?, ?, ?, 'employee', ?, ?, ?)
                ''', (
                    user_data['lastname'],
                    user_data['firstname'],
                    user_data.get('patronymic', ''),
                    user_data['position'],
                    user_data['hire_date'],
                    user_data['birth_date']
                ))
            
            user_id = self.cursor.lastrowid
            self.conn.commit()
            return user_id
        except sqlite3.Error as e:
            print(f"Error adding user: {e}")
            self.conn.rollback()
            return -1

    def get_attendance(self, start_date: str, end_date: str) -> List[Tuple]:
        """Получение посещаемости с преобразованием времени"""
        try:
            self.cursor.execute('''
                SELECT 
                    u.id,
                    u.lastname || ' ' || u.firstname || COALESCE(' ' || u.patronymic, '') AS fullname,
                    GROUP_CONCAT(
                        strftime('%d.%m.%Y %H:%M', 
                        datetime(timestamp, 'localtime')
                    , '; ') AS times
                FROM attendance a
                JOIN users u ON a.user_id = u.id
                WHERE date(timestamp) BETWEEN ? AND ?
                GROUP BY u.id
                ORDER BY timestamp DESC
            ''', (start_date, end_date))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching attendance: {e}")
            return []

    def get_all_users(self) -> List[Tuple]:
        """Получение всех пользователей с фильтрацией по типу"""
        try:
            if self.institution_type == 'educational':
                self.cursor.execute('''
                    SELECT id, lastname, firstname, patronymic 
                    FROM users 
                    WHERE user_type = 'student'
                ''')
            else:
                self.cursor.execute('''
                    SELECT id, lastname, firstname, patronymic 
                    FROM users 
                    WHERE user_type = 'employee'
                ''')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching users: {e}")
            return []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()