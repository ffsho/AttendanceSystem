
import datetime
import pytz
from app.core.database import DatabaseManager
import os


os.environ['TZ'] = 'Asia/Yekaterinburg'


# Тестовая функция
def test_timezone():
    db = DatabaseManager('educational')
    user_id = db.add_user({
        'lastname': 'Test',
        'firstname': 'User',
        'faculty': 'Test',
        'group': 'TEST-01'
    })
    
    db.add_attendance_record(user_id)
    
    # Проверка последней записи
    db.cursor.execute("SELECT timestamp FROM attendance ORDER BY id DESC LIMIT 1")
    record = db.cursor.fetchone()
    print(f"Время в базе: {record[0]}")
    print(f"Локальное время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(datetime.datetime.now())

    print("--------------------")

    timezone = pytz.timezone('Asia/Yekaterinburg')
    now = datetime.datetime.now(tz = timezone).strftime('%Y-%m-%d %H:%M:%S')
    print(now)
test_timezone()