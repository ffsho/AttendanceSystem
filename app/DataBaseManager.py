import sqlite3
from datetime import date
from typing import List, Tuple
from pathlib import Path
from .definitions import DB_FILE


class DatabaseManager:
    def __init__(self, institution_type: str):
        self.conn = sqlite3.connect(DB_FILE)
        self.institution_type = institution_type
        self._create_tables()
        
    def _create_tables(self):
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

        # Таблица посещаемости
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                date DATE GENERATED ALWAYS AS (DATE(timestamp)) VIRTUAL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        # Индексы для ускорения выборок
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_user ON attendance(user_id)')
        self.conn.commit()

    def add_user(self, user_data: dict):
        cursor = self.conn.cursor()
        
        if self.institution_type == 'educational':
            cursor.execute('''
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
            cursor.execute('''
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
            
        self.conn.commit()
        return cursor.lastrowid

    def get_all_users(self) -> List[Tuple]:
        cursor = self.conn.cursor()
        
        if self.institution_type == 'educational':
            cursor.execute('''
                SELECT 
                    id, 
                    lastname, 
                    firstname, 
                    patronymic, 
                    faculty, 
                    group_name 
                FROM users 
                WHERE user_type = 'student'
            ''')
        else:
            cursor.execute('''
                SELECT 
                    id, 
                    lastname, 
                    firstname, 
                    patronymic, 
                    position, 
                    hire_date, 
                    birth_date 
                FROM users 
                WHERE user_type = 'employee'
            ''')
            
        return cursor.fetchall()

    def delete_user(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        self.conn.commit()
    
    def add_attendance_record(self, user_id: int):
        """Добавление записи о посещении"""
        self.cursor.execute('''
            INSERT INTO attendance (user_id) 
            VALUES (?)
        ''', (user_id,))
        self.conn.commit()

    def get_attendance(self, start_date: str, end_date: str) -> list:
        """Получение посещаемости за период"""
        self.cursor.execute('''
            SELECT 
                a.date,
                u.lastname,
                u.firstname,
                COUNT(a.id) AS visits,
                GROUP_CONCAT(TIME(a.timestamp), ', ') AS times
            FROM attendance a
            JOIN users u ON u.id = a.user_id
            WHERE a.date BETWEEN ? AND ?
            GROUP BY a.date, u.id
            ORDER BY a.date DESC
        ''', (start_date, end_date))
        return self.cursor.fetchall()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()