
import datetime
import pytz
from app.core.database import DatabaseManager
import os




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


    print("--------------------")

    
test_timezone()