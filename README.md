# Face Recognition Attendance System

![GitHub](https://img.shields.io/github/license/yourusername/face-attendance-system)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

Система для автоматизированного учета посещаемости с использованием распознавания лиц. Поддерживает образовательные учреждения и предприятия.

## 📌 Особенности
- Регистрация пользователей с захватом изображений через веб-камеру
- Автоматическая фиксация времени входа/выхода
- Экспорт данных в Excel
- Адаптивный графический интерфейс (PyQt6)
- Поддержка двух типов учреждений: Educational и Enterprise

## 🚀 Быстрый старт

### Требования
- Python 3.10+
- Веб-камера
- 4 ГБ+ оперативной памяти

### Установка
```bash
git clone https://github.com/ffsho/AttendanceSystem.git
cd AttendanceSystem
pip install -r requirements.txt
```
Запуск
```bash
python main.py
```

🗂 Структура проекта
```bash
.
├── app/
│   ├── core/                  # Ядро системы
│   │   ├── database.py        # Менеджер БД (SQLite)
│   │   ├── face_recognition.py # Распознавание лиц (InsightFace)
│   │   └── paths.py           # Управление путями
│   ├── data/                  # Хранилище данных
│   │   ├── db/                # Базы данных
│   │   └── faces/             # Изображения пользователей
│   ├── settings/              # Конфигурация
│   ├── styles/                # Стили интерфейса
│   └── ui/                    # Графический интерфейс
├── requirements.txt           # Зависимости
└── main.py                    # Точка входа
```
## 🏗 Архитектурная схема

```plaintext
┌──────────────────────┐       ┌───────────────────┐
│       UI Layer       │       │   Core Services   │
│ (PyQt6 Widgets)      │◄─────►│                   │
│ - MainWindow         │       │ - FaceRecognizer  │
│ - Registration       │       │ - DatabaseManager │
│ - Export             │       │ - PathsManager    │
└──────────▲───────────┘       └────────▲──────────┘
           │                            │
           │                      ┌─────▼─────┐
           │                      │  Data     │
           │                      │  Storage  │
           │                      │ - SQLite  │
           │                      │ - Images  │
           │                      └───────────┘
           │
┌──────────┴───────────┐
│   Configuration      │
│ - settings.ini       │
│ - style.qss          │
└──────────────────────┘
```
🛠 Ключевые компоненты
База данных (app/core/database.py)

    DatabaseManager: Центральный класс для работы с SQLite

        Автоматическое создание таблиц

        CRUD операции для пользователей и посещений

        Каскадное удаление данных
        
1. Модели данных
Таблица users (Educational)
```sql

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lastname TEXT NOT NULL,
    firstname TEXT NOT NULL,
    patronymic TEXT,
    faculty TEXT,
    group_name TEXT
)
```
Таблица users (Enterprise)
```sql
CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lastname TEXT COLLATE NOCASE NOT NULL,
                    firstname TEXT COLLATE NOCASE NOT NULL,
                    patronymic TEXT COLLATE NOCASE,
                    position TEXT,
                    hire_date DATE,
                    birth_date DATE
                )
```
Таблица attendance
```sql

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

2. Сервисный слой

|Сервис	         | Ответственность                    | Методы                               |
| -------------- | ---------------------------------- | ------------------------------------ |
|DatabaseManage  | Управление SQLite-базами	          |  add_user(), get_attendance()        |
|FaceRecognizer	 | Распознавание лиц через InsightFace|	process_frame(), register_new_user() |
|PathsManager	 | Управление файловой структурой	  |  verify_paths()                      |
|SettingsManager | Работа с INI-конфигами	          |  load_settings(), update_setting()   |


Face Recognition Widget (core/face_recognition.py)
```python

class FaceRecognizer:
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, list]:
        """Обработка кадра с аннотациями"""
        faces = self.model.get(frame)
        for face in faces[:self.max_faces]:
            bbox = face.bbox.astype(int)
            similarity, user_id = self._recognize_face(face.embedding)
            self._draw_annotation(frame, bbox, similarity, user_id)
Распознавание лиц (app/core/face_recognition.py)
```
    FaceRecognizer:

        Реализация модели InsightFace

        Поддержка GPU/CPU

        Порог распознавания: 0.5 (настраивается)

Интерфейс (app/ui/)

    5 основных вкладок:

        🏠 Главная: Видеопоток с аннотациями

        📝 Регистрация: Форма добавления пользователей

        📊 Статистика: Фильтры по дате/тексту

        👥 Участники: Управление пользователями

        📤 Экспорт: Генерация XLSX-отчетов

📖 Примеры использования
Регистрация нового пользователя

    Перейдите на вкладку "Регистрация"

    Заполните обязательные поля

    Нажмите "Зарегистрировать"

    Дождитесь захвата 10 образцов лица
Регистрация
![registration](https://github.com/user-attachments/assets/97cc6beb-6b48-48b1-96e7-712f82f6db0b)
Распознавание
![recognition](https://github.com/user-attachments/assets/d057bf5f-ebcf-4e95-96da-6e97a29dffd3)
⚙️ Настройки

Файл app/settings/settings.ini:
ini

[Settings]
max_faces = 5

institution = Educational

❗ Обработка ошибок
Типовые сценарии

    Ошибка камеры

```python

if not cap.isOpened():
    QMessageBox.critical("Камера недоступна!")
```
    Ошибка БД

```python

except sqlite3.Error as e:
    print(f"SQL Error: {e}")
    self.conn.rollback()
```
    Ошибка распознавания

```python

if not self.known_embeddings:
    QMessageBox.warning("Нет зарегистрированных пользователей!")
```
