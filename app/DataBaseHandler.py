import sqlite3
from datetime import date
from typing import List, Tuple

class DatabaseManager:
    def __init__(self, db_path: str, institution_type: str):
        self.conn = sqlite3.connect(db_path)
        self.institution_type = institution_type
        self._create_tables()
        
    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()