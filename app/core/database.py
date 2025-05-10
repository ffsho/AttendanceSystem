import shutil
import sqlite3
from datetime import datetime
from typing import List, Tuple
from pathlib import Path
import pytz
from .paths import DB_EDUCATIONAL, DB_ENTERPRISE, FACES_IMG_DIR_EDUCATIONAL, FACES_IMG_DIR_ENTERPRISE

TIMEZONE = pytz.timezone('Asia/Yekaterinburg')




class DatabaseManager:

    def __init__(self, institution_type: str):
        """
        Инициализация класса для работы с базой данных с использованием sqlite3
        :param institution_type=Educational или Enterprise
        """
        self.institution_type = institution_type
        if self.institution_type == 'Educational':
            self.conn = sqlite3.connect(DB_EDUCATIONAL)
        
        elif self.institution_type == 'Enterprise':
            self.conn = sqlite3.connect(DB_ENTERPRISE)

        else:
            raise ValueError("Недопустимый тип учреждения. Допустимые значения: 'Educational', 'Enterprise'")

        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        self._create_tables()


    def _create_tables(self):
        """Создание таблиц с полями, для конкретного учреждения"""
        if self.institution_type == 'Educational':
            self._create_tables_educational()

        elif self.institution_type == 'Enterprise':
            self._create_tables_enterprise()


    def _create_tables_enterprise(self):
        """Создание таблиц для Enterprise"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lastname TEXT COLLATE NOCASE NOT NULL,
                    firstname TEXT COLLATE NOCASE NOT NULL,
                    patronymic TEXT COLLATE NOCASE,
                    position TEXT,
                    hire_date DATE,
                    birth_date DATE
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

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
            print(f"Ошибка при создании таблиц [Enterprise]: {e}")
            self.conn.rollback()


    def _create_tables_educational(self):
        """Создание таблиц для Educational"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lastname TEXT COLLATE NOCASE NOT NULL,
                    firstname TEXT COLLATE NOCASE NOT NULL,
                    patronymic TEXT COLLATE NOCASE,
                    faculty TEXT,
                    group_name TEXT COLLATE NOCASE
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

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
            print(f"Ошибка при создании таблиц [Educational]: {e}")
            self.conn.rollback()


    def add_attendance_record(self, user_id: int):
        """Добавление записи о посещении с текущим временем в SQL"""
        try:
            self.cursor.execute('''
                INSERT INTO attendance (user_id, timestamp)
                VALUES (?, datetime('now', 'localtime'))
            ''', (user_id,))
            self.conn.commit()

        except sqlite3.Error as e:
            print(f"Ошибка с добавлением записи о посещении: {e}")
            self.conn.rollback()


    def add_user(self, user_data: dict) -> int:
        """Добавление нового пользователя"""
        if self.institution_type == 'Educational':
            return self._add_user_educational(user_data)
        
        elif self.institution_type == 'Enterprise':
            return self._add_user_enterprise(user_data)


    def _add_user_enterprise(self, user_data: dict) -> int:
        """Добавление нового пользователя в Enterprise"""
        try:
            self.cursor.execute('''
                INSERT INTO users 
                (lastname, firstname, patronymic, position, hire_date, birth_date)
                VALUES (?, ?, ?, ?, ?, ?)
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
            print(f"Ошибка c добавлением нового пользователя в таблицу [Enterprise] {e}")
            self.conn.rollback()
            return -1


    def _add_user_educational(self, user_data: dict) -> int:
        """Добавление нового пользователя в Educational"""
        try:
            self.cursor.execute('''
                INSERT INTO users 
                (lastname, firstname, patronymic, faculty, group_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_data['lastname'],
                user_data['firstname'],
                user_data.get('patronymic', ''),
                user_data['faculty'],
                user_data['group']
            ))
                    
            user_id = self.cursor.lastrowid
            self.conn.commit()
            return user_id
        
        except sqlite3.Error as e:
            print(f"Ошибка с добавлением нового пользователя в таблицу [Educational]: {e}")
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
                        strftime('%d.%m.%Y %H:%M', datetime(timestamp)),
                        '; '
                    ) AS times
                FROM attendance a
                JOIN users u ON a.user_id = u.id
                WHERE date(timestamp) BETWEEN ? AND ?
                GROUP BY u.id
                ORDER BY timestamp DESC
            ''', (start_date, end_date))
            return self.cursor.fetchall()
        
        except sqlite3.Error as e:
            print(f"Ошибка с полученим посещаемости: {e}")
            return []


    def get_today_attendance(self) -> List[Tuple]:
        """Получение посещаемости за текущий день"""
        if self.institution_type == 'Educational':
            return self._get_today_attendance_educational()
        
        elif self.institution_type == 'Enterprise':
            return self._get_today_attendance_enterprise()


    def _get_today_attendance_enterprise(self) -> List[Tuple]:
        """Получение посещаемости за текущий день [Enterprise]"""
        try:
            self.cursor.execute('''
                SELECT 
                    u.lastname || ' ' || u.firstname || ' ' || u.patronymic AS full_name, u.position, 
                    GROUP_CONCAT(a.timestamp, ', ') AS timestamps
                FROM users u 
                JOIN attendance a ON u.id = a.user_id
                WHERE DATE(a.timestamp) = DATE(datetime('now', 'localtime'))
                GROUP BY u.id;
            ''')
            return self.cursor.fetchall()
        
        except sqlite3.Error as e:
            print(f"Ошибка с полученим посещаемости за текущий день [Enterprise]: {e}")
            return []


    def _get_today_attendance_educational(self) -> List[Tuple]:
        """Получение посещаемости за текущий день [Educational]"""
        try:
            self.cursor.execute('''
                SELECT 
                    u.lastname || ' ' || u.firstname || ' ' || u.patronymic AS full_name, 
                    u.group_name, 
                    GROUP_CONCAT(a.timestamp, ', ') AS timestamps
                FROM users u 
                JOIN attendance a ON u.id = a.user_id
                WHERE DATE(a.timestamp) = DATE(datetime('now', 'localtime'))
                GROUP BY u.id;
            ''')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Ошибка с полученим посещаемости за текущий день [Educational]: {e}")
            return []
        

    def has_attendance_today(self, user_id: int) -> bool:
        """Проверка, есть ли сегодняшняя запись о посещении для пользователя"""
        try:
            self.cursor.execute('''
                SELECT COUNT(*) FROM attendance
                WHERE user_id = ? AND DATE(timestamp) = DATE(datetime('now', 'localtime'))
            ''', (user_id,))
            count = self.cursor.fetchone()[0]
            return count > 0
        
        except sqlite3.Error as e:
            print(f"Ошибка проверки посещаемости пользователя: {e}")
            return False
        

    def delete_attendance_record(self, record_id: int):
        """Удаление записи о посещении по ID"""
        try:
            self.cursor.execute('''
                DELETE FROM attendance 
                WHERE id = ?
            ''', (record_id,))
            if self.cursor.rowcount > 0:
                self.conn.commit()
                print(f"Запись с ID {record_id} успешно удалена.")
            else:
                print(f"Запись с ID {record_id} не найдена.")
        except sqlite3.Error as e:
            print(f"Ошибка при удалении записи о посещении: {e}")
            self.conn.rollback()

    
    def get_attendance_by_date(self, date_input: str) -> List[Tuple]:
        """Поиск записей о посещених по частичной дате (день, день.месяц, день.месяц.год)"""
        try:
            parts = date_input.split(".")
            day, month, year = None, None, None

            if len(parts) == 1:
                day = parts[0].zfill(2)
            elif len(parts) == 2:
                day, month = parts
                day = day.zfill(2)
                month = month.zfill(2)
            elif len(parts) == 3:
                day, month, year = parts
                day = day.zfill(2)
                month = month.zfill(2)
            else:
                raise ValueError("Некорректный формат даты")

            conditions = []
            params = []
            if day:
                conditions.append("strftime('%d', a.timestamp) = ?")
                params.append(day)
            if month:
                conditions.append("strftime('%m', a.timestamp) = ?")
                params.append(month)
            if year:
                conditions.append("strftime('%Y', a.timestamp) = ?")
                params.append(year)

            if not conditions:
                raise ValueError("Не указана дата")

            query = f'''
                SELECT
                    u.id,
                    u.lastname || ' ' || u.firstname || COALESCE(' ' || u.patronymic, '') AS fullname,
                    GROUP_CONCAT(
                        strftime('%d.%m.%Y %H:%M', a.timestamp),
                        '; '
                    ) AS times
                FROM attendance a
                JOIN users u ON a.user_id = u.id
                WHERE {' AND '.join(conditions)}
                GROUP BY u.id
                ORDER BY a.timestamp DESC
            '''

            self.cursor.execute(query, params)
            return self.cursor.fetchall()

        except ValueError as ve:
            print(f"Ошибка: {ve}")
            return []
        except sqlite3.Error as e:
            print(f"Ошибка при поиске по дате: {e}")
            return []


    def get_attendance_by_search(self, search_text):
        """Поиск записей о посещених по фамилии, имени, отчеству, группе, позиции"""
        if self.institution_type == 'Educational':
            return self._get_attendance_by_search_educational(search_text)
        
        elif self.institution_type == 'Enterprise':
            return self._get_attendance_by_search_enterprise(search_text)
    

    def _get_attendance_by_search_enterprise(self, search_text):
        """Поиск записей о посещених по фамилии, имени, отчеству или группе [Enterprise]"""
        try:
            search_param = f"%{search_text}%"
            self.cursor.execute('''
                SELECT
                    u.id,
                    u.lastname || ' ' || u.firstname || COALESCE(' ' || u.patronymic, '') AS fullname,
                    GROUP_CONCAT(
                        strftime('%d.%m.%Y %H:%M', datetime(a.timestamp)), '; ') AS times
                FROM attendance a
                JOIN users u ON a.user_id = u.id
                WHERE 
                    u.lastname LIKE ? 
                    OR u.firstname LIKE ?
                    OR u.patronymic LIKE ?
                    OR u.position LIKE ?
                GROUP BY u.id
                ORDER BY a.timestamp DESC
            ''', (search_param, search_param, search_param, search_param))
            return self.cursor.fetchall()
        
        except sqlite3.Error as e:
            print(f"Ошибка при поиске [Enterprise]: {e}")
            return []


    def _get_attendance_by_search_educational(self, search_text):
        """Поиск записей о посещених по фамилии, имени, отчеству или группе [Educational]"""
        try:
            search_param = f"%{search_text}%"
            self.cursor.execute('''
                SELECT
                    u.id,
                    u.lastname || ' ' || u.firstname || COALESCE(' ' || u.patronymic, '') AS fullname,
                    GROUP_CONCAT(
                        strftime('%d.%m.%Y %H:%M', datetime(a.timestamp)), '; ') AS times
                FROM attendance a
                JOIN users u ON a.user_id = u.id
                WHERE 
                    u.lastname LIKE ? 
                    OR u.firstname LIKE ?
                    OR u.patronymic LIKE ?
                    OR u.group_name LIKE ?
                GROUP BY u.id
                ORDER BY a.timestamp DESC
            ''', (search_param, search_param, search_param, search_param))
            return self.cursor.fetchall()
        
        except sqlite3.Error as e:
            print(f"Ошибка при поиске [Educational]: {e}")
            return []
    

    def get_all_users(self, search_query=None):
        """Получение всех пользователей с возможностью поиска"""
        if self.institution_type == 'Educational':
            return self._get_all_users_educational(search_query)
        
        elif self.institution_type == 'Enterprise':
            return self._get_all_users_enterprise(search_query)
        

    def _get_all_users_enterprise(self, search_query=None):
        """Получение всех пользователей с возможностью поиска [Enterprise]"""
        try:
            if search_query:
                search_param = f"%{search_query}%"
                self.cursor.execute('''
                    SELECT 
                        id, lastname, firstname, patronymic, position, hire_date, birth_date
                    FROM users
                    WHERE 
                        lastname LIKE ? OR
                        firstname LIKE ? OR
                        patronymic LIKE ? OR
                        position LIKE ?
                    ORDER BY lastname, firstname
                ''', (search_param, search_param, search_param, search_param))
            else:
                self.cursor.execute('''
                    SELECT 
                        id, lastname, firstname, patronymic, position, hire_date, birth_date
                    FROM users
                    ORDER BY lastname, firstname
                ''')
            return self.cursor.fetchall()
        
        except sqlite3.Error as e:
            print(f"Ошибка при поиске зарегистрированных пользователей [Enterprise]: {e}")
            return []


    def _get_all_users_educational(self, search_query=None):
        """Получение всех пользователей с возможностью поиска [Educational]"""
        try:
            if search_query:
                search_param = f"%{search_query}%"
                self.cursor.execute('''
                    SELECT 
                        id, lastname, firstname, patronymic, faculty, group_name
                    FROM users
                    WHERE 
                        lastname LIKE ? OR
                        firstname LIKE ? OR
                        patronymic LIKE ? OR
                        group_name LIKE ?
                    ORDER BY lastname, firstname
                ''', (search_param, search_param, search_param, search_param))
            else:
                self.cursor.execute('''
                    SELECT 
                        id, lastname, firstname, patronymic, faculty, group_name
                    FROM users
                    ORDER BY lastname, firstname
                ''')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Ошибка при поиске зарегистрированных пользователей: {e}")
            return []
        
        
    def get_user_position(self, user_id):
        """Поиск должности сотрудника по id"""
        try:
            self.cursor.execute('''
                SELECT position FROM users WHERE id = ?
            ''', (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else "N/A"
        
        except sqlite3.Error as e:
            print(f"Ошибка при получении должности сотрудника: {e}")
            return "N/A"


    def get_user_group(self, user_id):
        """Поиск группы пользователя по id"""
        try:
            self.cursor.execute('''
                SELECT group_name FROM users WHERE id = ?
            ''', (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else "N/A"
        
        except sqlite3.Error as e:
            print(f"Ошибка при получении группы пользователя: {e}")
            return "N/A"


    def delete_user(self, user_id: int) -> bool:
        """Удаление пользователя по ID"""
        try:
            self.cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            self.conn.commit()

            if self.cursor.rowcount > 0:
                
                if self.institution_type == 'Educational':
                    user_folder = FACES_IMG_DIR_EDUCATIONAL / str(user_id)
                elif self.institution_type == 'Enterprise':
                    user_folder = FACES_IMG_DIR_ENTERPRISE / str(user_id)

                if user_folder.exists():
                    shutil.rmtree(user_folder)
                self.conn.commit()
                return True

            return False

        except sqlite3.Error as e:
            print(f"Ошибка при удалении пользователя: {e}")
            self.conn.rollback()
            return False


    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()