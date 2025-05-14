from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QSpinBox, 
    QDialogButtonBox, QComboBox
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal
from ..core.paths import STYLES_DIR
from ..settings.settings import SettingsManager


class SettingsDialog(QDialog):

    settings_updated = pyqtSignal(dict)


    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки системы")
        self.setWindowIcon(QIcon(f'{STYLES_DIR}/icons/gear.png'))
        self.init_ui()
        self.settings_manager = settings_manager
        self.load_settings()


    def init_ui(self):
        layout = QVBoxLayout(self)

        # Настройка количества распознаваемых лиц
        self.faces_spin = QSpinBox()
        self.faces_spin.setRange(1, 25)
        self.faces_spin.setPrefix("Макс. лиц: ")
        layout.addWidget(QLabel("Количество одновременно распознаваемых лиц:"))
        layout.addWidget(self.faces_spin)

        # Выбор учреждения
        self.institution = QComboBox()
        self.institution.addItems(["Educational", "Enterprise"])
        layout.addWidget(QLabel("Тип учреждения:"))
        layout.addWidget(self.institution)

        # Выбор на чем будет работать модель CPU/GPU
        self.execution_provider = QComboBox()
        self.execution_provider.addItems(["CPU", "GPU"])
        layout.addWidget(QLabel("На чем будет запускаться модель?:"))
        layout.addWidget(self.execution_provider)

        # Кнопки управления
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.save_settings)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)


    def load_settings(self):
        """Загрузка текущих настроек"""
        self.faces_spin.setValue(int(self.settings_manager.get_setting('max_faces')))
        self.institution.setCurrentText(self.settings_manager.get_setting('institution'))
        self.execution_provider.setCurrentText(self.settings_manager.get_setting('execution_provider'))

    def save_settings(self):
        """Сохранение настроек и отправка сигнала"""
        new_settings = {
            'max_faces': self.faces_spin.value(),
            'institution' : self.institution.currentText(),
            'execution_provider' : self.execution_provider.currentText()
        }

        self.settings_manager.update_setting('max_faces', new_settings.get('max_faces'))
        self.settings_manager.update_setting('institution', new_settings.get('institution'))
        self.settings_manager.update_setting('execution_provider', new_settings.get('execution_provider'))
        self.settings_manager.save_settings()
        self.settings_updated.emit(new_settings)
        self.accept()