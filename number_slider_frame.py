import os
import sys
from PyQt5.QtWidgets import QWidget, QPushButton, QSizePolicy, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QFont, QFontMetrics
from slider_widget import Slider
import qtawesome as qta
from configparser import ConfigParser
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QSize

def get_config_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, "colors_icons.ini")

config_path = get_config_path()
config_object = ConfigParser()
config_object.read(config_path)

if "colors" not in config_object:
    print("No Colors file")
    sys.exit(1)
    
color = config_object["colors"]["number_slider"]
available = config_object["colors"]["available"]
unavailable = config_object["colors"]["unavailable"]
background_slider = config_object["colors"]["slider_background"]
border_bg = config_object["colors"]["slider_border"]

background_frame = config_object["colors"]["backgrounds"]
border_frame = config_object["colors"]["borders"]
icons_background = config_object["colors"]["icons_background"]

icon_on = config_object["icons"]["number_slider_on"]
icon_off = config_object["icons"]["number_slider_off"]
icon_un =config_object["icons"]["unavailable"]

class NumberSliderFrame(QWidget):
    ha_state_signal = pyqtSignal(dict)  

    def __init__(
        self,
        eid,
        etype,
        itype,
        name,
        ha_client,
        TYPE_OBJECT_NAME_MAP,
        on_icon_click=None,
        on_frame_click=None
    ):
        super().__init__()
        self.eid = eid
        self.etype = etype
        self.itype = itype
        self.name = name
        self.ha = ha_client
        self.on_frame_click = on_frame_click
        self.debounce_timers = {}

        self.setFixedHeight(70)
        self.setObjectName(TYPE_OBJECT_NAME_MAP.get(etype, "not_set"))

        r, g, b = map(int, color.split(","))  
        self.slider_color = QColor(r, g, b)     
        self.background_color_rgba = f"rgba({r},{g},{b}, 40)"
        self.border_color_rgba = f"rgba({r},{g},{b}, 60)"
        
        
        r, g, b = map(int, unavailable.split(","))  
        self.unavailable_color = QColor(r, g, b)
        self.unavailable_color_rgba = f"rgba({r},{g},{b}, 250)"
        
        r, g, b = map(int, available.split(","))  
        self.available_color = QColor(r, g, b)
 
        r, g, b = map(int, background_slider.split(","))  
        self.background_slider = QColor(r, g, b)
        
        r, g, b = map(int, border_bg.split(","))  
        self.border_bg = QColor(r, g, b)
        
        r, g, b = map(int, background_frame.split(","))
        self.background_frame_rgba = f"rgba({r},{g},{b}, 250)"

        r, g, b = map(int, border_frame.split(","))
        self.border_bg_rgba = f"rgba({r},{g},{b}, 250)"

        r, g, b = map(int, icons_background.split(","))
        self.icons_background_rgba = f"rgba({r},{g},{b}, 250)"
        
        self.icon_on = icon_on
        self.icon_off = icon_off
        self.icon_un = icon_un
        
        self.frame = QWidget()
        self.frame.setObjectName("entity_frame")
        self.frame.setAutoFillBackground(True)

        frame_layout = QHBoxLayout(self.frame)
        frame_layout.setContentsMargins(10, 0, 5, 0)
        frame_layout.setSpacing(10)

        self.ico_button = QPushButton()
        self.ico_button.setFixedSize(50, 50)
        self.ico_button.setObjectName("ico_button")
        self.ico_button.setIconSize(QSize(40, 40))
        if on_icon_click:
            self.ico_button.clicked.connect(lambda: on_icon_click(self.eid, self.etype, self.itype, self.name))
        frame_layout.addWidget(self.ico_button, alignment=Qt.AlignVCenter)


        base_slider = Slider(self.frame)

        print("DDDDDDDDDDDDDDDDDDDDDDDDD")
        print(itype)
        min_speed, max_speed, step_set = map(int, itype.split("."))
        base_slider.setMinimum(min_speed)
        base_slider.setMaximum(max_speed)
        base_slider.setSingleStep(step_set)
        base_slider.valueChanged.connect(self.slider_released)
        base_slider.entity_id = self.eid
        base_slider.setFixedHeight(40)         
        base_slider.setBorderRadius(5)          
        base_slider.showValue(True)
        base_slider.setBackgroundColor(self.background_slider)
        base_slider.setAccentColor(self.slider_color)
        base_slider.setBorderColor(self.border_bg)
        base_slider.setTextColor(self.available_color)
        base_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        base_slider.setFixedHeight(60)

        orig_class = base_slider.__class__
        class SliderWithName(orig_class):
            def paintEvent(slider_self, event):
                orig_class.paintEvent(slider_self, event)
                painter = QPainter(slider_self)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QColor('#ffffff'))
                font = slider_self.font()
                painter.setFont(font)
                metrics = QFontMetrics(font)
                text_height = metrics.height()
                x = 8
                y = (slider_self.height() + text_height) // 4 + 5
                painter.drawText(x, y, name)

        base_slider.__class__ = SliderWithName
        self.slider = base_slider
        frame_layout.addWidget(self.slider)

        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        outer_layout.addWidget(self.frame)
        self.setLayout(outer_layout)


        self.ha_state_signal.connect(self._update_gui)
        self.ha.register(self)


    def on_ha_state(self, eid, state_obj):
        if eid != self.eid:
            return
        self.ha_state_signal.emit(state_obj)

    def _update_gui(self, state_obj):
        try:
            value = int(float(state_obj.get("state", 0)))
            available_state = state_obj.get("state")
            print(available_state)
        except Exception:
            value = 0
            available_state = state_obj.get("state")
            print(available_state)
        
        if value != 0:
            self.frame.setStyleSheet(f"background: {self.background_color_rgba};  border: 1px solid {self.border_color_rgba}; border-radius: 10px;")
            self.ico_button.setStyleSheet(f"background: {self.icons_background_rgba}; border-width: 0px")
            icon_name = self.icon_on
            icon_color = self.slider_color
            
        elif value == 0  and available_state != "unavailable":
            self.frame.setStyleSheet(f"background: {self.background_frame_rgba};  border: 1px solid {self.border_bg_rgba}; border-radius: 10px;")
            self.ico_button.setStyleSheet(f"background: {self.icons_background_rgba}; border-width: 0px")
            icon_name = self.icon_off
            icon_color = self.available_color
            
        else:
            self.frame.setStyleSheet(f"background: {self.unavailable_color_rgba};  border: 1px solid {self.border_bg_rgba}; border-radius: 10px;")
            self.ico_button.setStyleSheet(f"background: {self.unavailable_color_rgba}; border-width: 0px")
            icon_name = self.icon_un
            icon_color = self.unavailable_color
            
            
        self.frame.style().unpolish(self.frame)
        self.frame.style().polish(self.frame)
        self.frame.update()
        self.ico_button.style().unpolish(self.ico_button)
        self.ico_button.style().polish(self.ico_button)
        self.ico_button.setIcon(qta.icon(icon_name, color=icon_color, scale_factor=0.7))
        self.ico_button.update()
        
            
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        self.slider.update()


    def slider_released(self, value):
        slider = self.sender()
        eid = slider.entity_id
        position = value

        if eid in self.debounce_timers:
            self.debounce_timers[eid].stop()

        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda eid=eid, value=position: self.send_number_slider_value(eid, value))
        self.debounce_timers[eid] = timer
        timer.start(100)

    def send_number_slider_value(self, eid, value):
        self.ha.call_service("number", "set_value", eid, {"value": value})
        if eid in self.debounce_timers:
            del self.debounce_timers[eid]


    def mousePressEvent(self, event):
        clicked_widget = self.childAt(event.pos())
        if self.on_frame_click and clicked_widget not in (self.slider, self.ico_button):
            self.on_frame_click(self.eid, self.etype, self.itype)
        super().mousePressEvent(event)

