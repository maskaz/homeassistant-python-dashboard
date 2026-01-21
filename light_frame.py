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
from popup_temp import show_temp_palette_popup
from popup_temp_color import show_temp_color_palette_popup

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
    
color = config_object["colors"]["light"]
available = config_object["colors"]["available"]
unavailable = config_object["colors"]["unavailable"]
background_slider = config_object["colors"]["slider_background"]
border_bg = config_object["colors"]["slider_border"]

background_frame = config_object["colors"]["backgrounds"]
border_frame = config_object["colors"]["borders"]
icons_background = config_object["colors"]["icons_background"]


icon_on = config_object["icons"]["light_on"]
icon_off = config_object["icons"]["light_off"]
icon_un =config_object["icons"]["unavailable"]
icons_by_type = dict(config_object["icons_by_itype"])
default_icon = icons_by_type.get("default", "mdi:help-circle")



class LightFrame(QWidget):
    ha_state_signal = pyqtSignal(dict)

    def __init__(self, eid, etype, itype, name, ha_client,
                 TYPE_OBJECT_NAME_MAP,
                 on_icon_click=None, on_frame_click=None):
        super().__init__()
        self.eid = eid
        self.etype = etype
        self.itype = itype
        self.ha = ha_client
        self.on_frame_click = on_frame_click
        self.debounce_timers = {}
        self.name = name

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
        self.background_slider_rgba = f"rgba({r},{g},{b}, 250)"
        
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
            self.ico_button.clicked.connect(
                lambda: on_icon_click(self.eid, self.etype, self.itype, self.name)
            )
        frame_layout.addWidget(self.ico_button, alignment=Qt.AlignVCenter)

        base_slider = Slider(self.frame)

        base_slider.setMinimum(0)
        base_slider.setMaximum(100)
        base_slider.setSingleStep(1)
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
        state = state_obj.get("state")
        attrs = state_obj.get("attributes", {})
        ha_brightness = 0 if state == "off" else int(attrs.get("brightness", 0) or 0)
        ui_value = int(round((ha_brightness / 255) * 100)) if ha_brightness else 0



        if ui_value != 0 or state != "off":
            self.frame.setStyleSheet(f"background: {self.background_color_rgba};  border: 1px solid {self.border_color_rgba}; border-radius: 10px;")
            self.ico_button.setStyleSheet(f"background: {self.icons_background_rgba}; border-width: 0px")
            if self.itype == "light" or self.itype == "temp" or self.itype == "temp_color":
               icon_name = self.icon_on
            else:
               for key in icons_by_type:
                  if key in self.itype:
                      icon_name = icons_by_type[key]

            icon_color = self.slider_color
           
        elif state == "unavailable":
            self.frame.setStyleSheet(f"background: {self.unavailable_color_rgba};  border: 1px solid {self.border_bg_rgba}; border-radius: 10px;")
            self.ico_button.setStyleSheet(f"background: {self.unavailable_color_rgba}; border-width: 0px")
            icon_name = self.icon_un
            icon_color = self.unavailable_color
            
        else:
            self.frame.setStyleSheet(f"background: {self.background_frame_rgba};  border: 1px solid {self.border_bg_rgba}; border-radius: 10px;")
            self.ico_button.setStyleSheet(f"background: {self.icons_background_rgba}; border-width: 0px")
            if self.itype == "light" or self.itype == "temp" or self.itype == "temp_color":
               icon_name = self.icon_off
            else:
               for key in icons_by_type:
                  if key in self.itype:
                      icon_name = icons_by_type[key]
                      
            icon_color = self.available_color

        self.frame.style().unpolish(self.frame)
        self.frame.style().polish(self.frame)
        self.frame.update()
        self.ico_button.style().unpolish(self.ico_button)
        self.ico_button.style().polish(self.ico_button)
        self.ico_button.setIcon(qta.icon(icon_name, color=icon_color, scale_factor=0.7))
        self.ico_button.update()

        self.slider.blockSignals(True)
        self.slider.setValue(ui_value)
        self.slider.blockSignals(False)
        self.slider.update()

    def slider_released(self, value):
        slider = self.sender()
        eid = slider.entity_id
        ui_value = value
        brightness = int(round((ui_value / 100) * 255))


        if eid in self.debounce_timers:
            self.debounce_timers[eid].stop()

        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.send_slider_value(brightness))
        self.debounce_timers[eid] = timer
        timer.start(300)

    def send_slider_value(self, brightness):
        if brightness == 0:
            self.ha.call_service("light", "turn_off", self.eid)
        else:
            self.ha.call_service("light", "turn_on", self.eid, {"brightness": brightness})


    def toggle_light(self, eid):
        state_obj = self.ha.entity_states.get(eid)
        if not state_obj:
            print(f"No HA status for {eid}")
            return
        current_state = state_obj.get("state")
        if current_state == "off":
            # włącz na ostatnią jasność
            self.ha.call_service("light", "turn_on", eid)
        else:
            # wyłącz
            self.ha.call_service("light", "turn_off", eid)
            
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return
        clicked_widget = self.childAt(event.pos())
        if clicked_widget in (self.slider, self.ico_button):
            super().mousePressEvent(event)
            return
        self.toggle_light(self.eid)
        super().mousePressEvent(event)

            
