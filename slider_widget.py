from PyQt5.QtGui import QColor, QFont
from qtpy.QtCore import Signal, Qt, QRect
from qtpy.QtGui import QPainter, QFontMetrics, QPen, QBrush
from qtpy.QtWidgets import QWidget

# -----------------------------
# Slider (Twój oryginalny)
# -----------------------------
class Slider(QWidget):
    valueChanged = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Basic params
        self._min = 0
        self._max = 10
        self._value = 0.0
        self._is_float = False
        self._decimals = 1

        self._thousands_separator = ""
        self._decimal_separator = "."
        self._prefix = ""
        self._suffix = " "

        self._show_value = True
        self._text_color = QColor("#000000")
        self._background_color = QColor("#D6D6D6")
        self._accent_color = QColor("#0078D7")
        self._border_color = QColor("#D1CFD3")
        self._border_radius = 10  # Domyślne zaokrąglenie

        self._font = self.font()  # używa domyślnego fontu QWidget/Qt
        self._font_metrics = QFontMetrics(self._font)


        self._single_step = 0
        self._page_step = 0

        self._keyboard_enabled = True
        self._wheel_enabled = True

        self._dragging = False

        self._accent_pen = QPen(self._accent_color, 1)
        self._text_pen = QPen(self._text_color)

        self.setFocusPolicy(Qt.ClickFocus)
        self.setAutoFillBackground(False)

        self._value_text_pos = "bottom_left"
        self._value_text_offset = (5, -7)

    # -----------------------------
    # Gradient helpers
    # -----------------------------
    def _lighter_color(self, color, factor=1.6):
        c = QColor(color)
        return c.lighter(int(factor * 100))

    def _value_color(self):
        ratio = (self._value - self._min) / max(1, self.range())
        light = self._lighter_color(self._accent_color, 0.6)
        orig = self._accent_color

        r = light.red() + (orig.red() - light.red()) * ratio
        g = light.green() + (orig.green() - light.green()) * ratio
        b = light.blue() + (orig.blue() - light.blue()) * ratio

        return QColor(int(r), int(g), int(b))

    # -----------------------------
    # Events
    # -----------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._update_value_from_pos(event.pos().x())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._update_value_from_pos(event.pos().x())

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._update_value_from_pos(event.pos().x())

    def wheelEvent(self, event):
        if not self._wheel_enabled:
            return

        delta = event.angleDelta().y()
        step = self._single_step if self._single_step else self.range() * 0.01

        if delta > 0:
            self.setValue(self._value + step)
        else:
            self.setValue(self._value - step)

    def keyPressEvent(self, event):
        if not self._keyboard_enabled:
            return

        key = event.key()
        step = self._single_step if self._single_step else self.range() * 0.01
        page = self._page_step if self._page_step else self.range() * 0.05

        if key == Qt.Key_Home:
            self.setValue(self._min)
        elif key == Qt.Key_End:
            self.setValue(self._max)
        elif key in (Qt.Key_Right, Qt.Key_Up):
            self.setValue(self._value + step)
        elif key in (Qt.Key_Left, Qt.Key_Down):
            self.setValue(self._value - step)
        elif key == Qt.Key_PageUp:
            self.setValue(self._value + page)
        elif key == Qt.Key_PageDown:
            self.setValue(self._value - page)

    # -----------------------------
    # Painting
    # -----------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self._font)

        radius = min(self._border_radius, self.height() // 2)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self._background_color))
        painter.drawRoundedRect(self.rect(), radius, radius)

        pos_x = self._value_to_pos(self._value)
        if pos_x > 0:
            color = self._value_color()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            filled_rect = QRect(0, 1, pos_x, self.height() - 2)
            painter.drawRoundedRect(filled_rect, radius, radius)

        border_pen = QPen(self._border_color, 2)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(
            self.rect().adjusted(1, 1, -1, -1),
            radius,
            radius
        )

        if self._show_value:
            text = self.getValueFormatted()
            w = self._font_metrics.horizontalAdvance(text)
            h = self._font_metrics.height()

            if self._value_text_pos == "bottom_left":
                text_x = 5 + self._value_text_offset[0]
                text_y = self.height() - 5 + self._value_text_offset[1]
            elif self._value_text_pos == "top_left":
                text_x = 5 + self._value_text_offset[0]
                text_y = h + self._value_text_offset[1]
            elif self._value_text_pos == "center":
                text_x = (self.width() - w) // 2 + self._value_text_offset[0]
                text_y = (self.height() + h) // 2 + self._value_text_offset[1]
            elif self._value_text_pos == "custom":
                text_x, text_y = self._value_text_offset

            painter.setPen(self._text_pen)
            painter.drawText(text_x, text_y, text)

    # -----------------------------
    # Helpers
    # -----------------------------
    def _update_value_from_pos(self, pos_x):
        value = self._pos_to_value(pos_x)
        if self._single_step:
            step = self._single_step
            value = round((value - self._min) / step) * step + self._min
        self.setValue(value)

    def _pos_to_value(self, pos):
        pos = max(0, min(pos, self.width()))
        return self._min + (pos / max(1, self.width())) * self.range()

    def _value_to_pos(self, value):
        return int((value - self._min) / self.range() * (self.width() - 2))

    def range(self):
        return self._max - self._min

    # -----------------------------
    # Value API
    # -----------------------------
    def setValue(self, value):
        value = max(self._min, min(value, self._max))
        rounded = round(value, self._decimals) if self._is_float else int(value)
        prev = round(self._value, self._decimals) if self._is_float else int(self._value)

        self._value = value
        if rounded != prev:
            self.valueChanged.emit(rounded)
        self.update()

    def getValue(self):
        return round(self._value, self._decimals) if self._is_float else int(self._value)

    def getValueFormatted(self):
        if self._is_float:
            fmt = f"{{:,.{self._decimals}f}}"
            text = fmt.format(self.getValue())
        else:
            text = f"{int(self.getValue()):,}"
        text = text.replace(",", "TEMP").replace(".", self._decimal_separator)
        text = text.replace("TEMP", self._thousands_separator)
        return f"{self._prefix}{text}{self._suffix}"

    # -----------------------------
    # Compatibility API
    # -----------------------------
    def setMinimum(self, v):
        self._min = v
        if self._max < self._min:
            self._max = self._min
        self.setValue(self._value)

    def getMinimum(self):
        return self._min

    def setMaximum(self, v):
        self._max = v
        if self._min > self._max:
            self._min = self._max
        self.setValue(self._value)

    def getMaximum(self):
        return self._max

    def setRange(self, mn, mx):
        self._min = mn
        self._max = mx
        self.setValue(self._value)

    # -----------------------------
    # Other setters
    # -----------------------------
    def setFloat(self, flag):
        self._is_float = flag
        self.update()

    def setDecimals(self, dec):
        self._decimals = dec
        self.update()

    def setPrefix(self, s):
        self._prefix = s
        self.update()

    def setSuffix(self, s):
        self._suffix = s
        self.update()

    def showValue(self, on):
        self._show_value = on
        self.update()

    def setTextColor(self, c):
        self._text_color = c
        self._text_pen = QPen(c)
        self.update()

    def setBackgroundColor(self, c):
        self._background_color = c
        self.update()

    def setAccentColor(self, c):
        self._accent_color = c
        self._accent_pen = QPen(c, 1)
        self.update()

    def setBorderColor(self, c):
        self._border_color = c
        self.update()

    def setBorderRadius(self, r):
        self._border_radius = r
        self.update()

    def setFont(self, font):
        self._font = font
        self._font_metrics = QFontMetrics(font)
        self.update()

    def setSingleStep(self, s):
        self._single_step = s

    def setPageStep(self, s):
        self._page_step = s

    def setKeyboardInputEnabled(self, on):
        self._keyboard_enabled = on

    def setMouseWheelInputEnabled(self, on):
        self._wheel_enabled = on


# -----------------------------
# Slider Factory (Twój oryginalny)
# -----------------------------
def create_slider(parent, min_val, max_val, eid, slot, step, height=40, radius=5):
    slider = Slider(parent)
    slider.setMinimum(min_val)
    slider.setMaximum(max_val)
    slider.setSingleStep(step)
    slider.setFixedHeight(height)
    slider.setBorderRadius(radius)
    slider.showValue(True)
    slider.setBackgroundColor(QColor('#29282e')) 
    
    slider.entity_id = eid
    if slot:
        slider.valueChanged.connect(slot)

    font = QFont()
    font.setPointSize(10)
    font.setBold(False)
    slider.setFont(font)

    return slider

