from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QSpinBox, 
    QDialogButtonBox, QComboBox
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal
from ..core.paths import STYLES_DIR



class SettingsDialog(QDialog):

    settings_updated = pyqtSignal(dict)


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки системы")
        self.setWindowIcon(QIcon(f'{STYLES_DIR}/icons/gear.png'))
        self.init_ui()
        self.load_settings()


    def init_ui(self):
        layout = QVBoxLayout(self)

        # Настройка количества распознаваемых лиц
        self.faces_spin = QSpinBox()
        self.faces_spin.setRange(1, 25)
        self.faces_spin.setPrefix("Макс. лиц: ")
        layout.addWidget(QLabel("Количество одновременно распознаваемых лиц:"))
        layout.addWidget(self.faces_spin)


        self.institution = QComboBox()
        self.institution.addItems(["Educational", "Enterprise"])
        layout.addWidget(self.institution)

        # Кнопки управления
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.save_settings)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)


    def load_settings(self):
        """Загрузка текущих настроек (пример с QSettings)"""
        self.faces_spin.setValue(1)


    def save_settings(self):
        """Сохранение настроек и отправка сигнала"""
        new_settings = {
            'max_faces': self.faces_spin.value(),
            'institution' : self.institution.currentText()
        }
        self.settings_updated.emit(new_settings)
        self.accept()