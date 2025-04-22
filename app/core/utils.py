from datetime import datetime, timedelta
import pandas as pd
from app.core.definitions import ATTENDANCE_DIR
from app.core.database import DatabaseManager



def export_attendance_to_excel(db: DatabaseManager, days: int = 30):
    """Экспорт посещаемости в Excel"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    data = db.get_attendance(start_date, end_date)
    
    df = pd.DataFrame(data, columns=[
        'Дата',
        'Фамилия',
        'Имя',
        'Количество посещений',
        'Время посещений'
    ])
    
    filename = ATTENDANCE_DIR / f"attendance_report_{start_date}_to_{end_date}.xlsx"
    df.to_excel(filename, index=False)
    return filename

def get_todays_attendance(db: DatabaseManager) -> pd.DataFrame:
    """Получение посещаемости за сегодня"""
    today = datetime.now().strftime("%Y-%m-%d")
    data = db.get_attendance(today, today)
    
    return pd.DataFrame(data, columns=[
        'Дата',
        'Фамилия',
        'Имя',
        'Посещений',
        'Время'
    ])