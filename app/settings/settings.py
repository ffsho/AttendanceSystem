import configparser
from pathlib import Path
from ..core.paths import SETTINGS_FILE, DEFAULT_SETTINGS_FILE



class SettingsManager:

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.set_default_settings()
        self.load_settings()


    def load_settings(self):
        """Загрузка настроек из файла."""
        if SETTINGS_FILE.exists():
            self.config.read(SETTINGS_FILE)
        else:
            self.config.read(DEFAULT_SETTINGS_FILE)


    def load_default_settings(self):
        """Закгрузка настроек 'по умолчанию'"""
        self.config.read(DEFAULT_SETTINGS_FILE)


    def save_settings(self):
        """Сохранение настроек в файл."""
        with open(SETTINGS_FILE, 'w') as f:
            self.config.write(f)


    def get_setting(self, key: str):
        """Получение конкретной настройки."""
        return self.config['Settings'].get(key, '1')


    def update_setting(self, key: str, value: str):
        """Обновление конкретной настройки."""
        self.config.set('Settings', f'{key}', f'{value}')
        self.save_settings()


    def set_default_settings(self):
        if not DEFAULT_SETTINGS_FILE.exists():
            with open(DEFAULT_SETTINGS_FILE, 'w') as file:
                if not self.config.has_section('Settings'):
                    self.config.add_section('Settings')
                    self.config.set('Settings', 'max_faces', '10')
                    self.config.set('Settings', 'institution', 'Educational')
                    self.config.write(file)