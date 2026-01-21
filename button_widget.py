from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QFont

class ToggleButton(QCheckBox):
    toggled = pyqtSignal(bool)

    def __init__(
        self,
        width,
        bg_off,
        bg_on,
        btn_off,
        btn_on,
        border_bg,
        border_btn_off,
        border_btn_on,
        border_width,
        checked,
        text_on,
        text_off,
        text_color_off,
        text_color_on,
        on_toggle=None   # dodałem obsługę on_toggle
    ):
        super().__init__()
        self.setFixedSize(width, 42)
        self.setCursor(Qt.PointingHandCursor)

        self.bg_off = bg_off
        self.bg_on = bg_on
        self.btn_off = btn_off
        self.btn_on = btn_on

        self.border_bg = border_bg
        self.border_btn_off = border_btn_off
        self.border_btn_on = border_btn_on
        self.border_width = border_width

        self.text_on = text_on
        self.text_off = text_off
        self.text_color_off = text_color_off
        self.text_color_on = text_color_on

        self._circle_position = 9

        self.stateChanged.connect(self._update_position)
        self.stateChanged.connect(lambda v: self.toggled.emit(bool(v)))

        if on_toggle:
            self.toggled.connect(on_toggle)

        # ustawienie początkowego stanu
        self.setChecked(checked)
        self._update_position(self.isChecked())

    def _update_position(self, value):
        self._circle_position = self.width() - 48 if value else 4
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # ---- TŁO PRZYCISKU ----
        p.setBrush(QColor(self.bg_on if self.isChecked() else self.bg_off))
        pen_bg = QPen(QColor(self.border_bg))
        pen_bg.setWidth(self.border_width)
        p.setPen(pen_bg)
        p.drawRoundedRect(self.rect(), 8, 8)

        # ---- KÓŁKO PRZYCISKU ----
        rect = self._circle_position, 3, 46, 36
        p.setBrush(QColor(self.btn_on if self.isChecked() else self.btn_off))
        pen_btn = QPen(QColor(self.border_btn_on if self.isChecked() else self.border_btn_off))
        pen_btn.setWidth(self.border_width)
        p.setPen(pen_btn)
        p.drawRoundedRect(*rect, 4, 4)

        # ---- TEKST ON/OFF NA KÓŁKU ----
        text_color = self.text_color_on if self.isChecked() else self.text_color_off
        p.setPen(QColor(text_color))
        font = QFont()
        font.setBold(True)
        p.setFont(font)
        x, y, w, h = rect
        text = self.text_on if self.isChecked() else self.text_off
        p.drawText(x, y, w, h, Qt.AlignCenter, text)

    def mousePressEvent(self, event):
        self.setChecked(not self.isChecked())  # przełącz stan przy kliknięciu
        super().mousePressEvent(event)

