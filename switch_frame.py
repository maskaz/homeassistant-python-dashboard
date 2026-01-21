import sys
import os
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from button_widget import ToggleButton
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
    
color = config_object["colors"]["switch"]
available = config_object["colors"]["available"]
unavailable = config_object["colors"]["unavailable"]
background_slider = config_object["colors"]["slider_background"]
border_bg = config_object["colors"]["slider_border"]

background_frame = config_object["colors"]["backgrounds"]
border_frame = config_object["colors"]["borders"]
icons_background = config_object["colors"]["icons_background"]

icon_on = config_object["icons"]["switch_on"]
icon_off = config_object["icons"]["switch_off"]
icon_un =config_object["icons"]["unavailable"]


class SwitchFrame(QWidget):
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
        self.ha = ha_client
        self.on_frame_click = on_frame_click

        self.setFixedHeight(80)
        self.setAutoFillBackground(True)
        self.setObjectName(TYPE_OBJECT_NAME_MAP.get(etype, "not_set"))

        r, g, b = map(int, color.split(","))  
        self.switch_color = QColor(r, g, b)     
        self.background_color_rgba = f"rgba({r},{g},{b}, 40)"
        self.border_color_rgba = f"rgba({r},{g},{b}, 60)"
        
        r, g, b = map(int, color.split(","))  
        self.switch_color_frame_on = QColor(r, g, b, 20) 
        
        r, g, b = map(int, unavailable.split(","))  
        self.unavailable_color = QColor(r, g, b)
        self.unavailable_color_rgba = f"rgba({r},{g},{b}, 60)"
        
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
        
        self._build_ui(name, etype, itype, on_icon_click)
        self.ha_state_signal.connect(self._update_gui)

        r, g, b = map(int, icons_background.split(","))
        self.icons_background_rgba = f"rgba({r},{g},{b}, 250)"

        self.ha.register(self)


    def _build_ui(self, name, etype, itype, on_icon_click):
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.frame = QWidget()
        self.frame.setAutoFillBackground(True)
        self.frame.setObjectName("entity_frame")
        main_h = QHBoxLayout(self.frame)
        main_h.setContentsMargins(10, 5, 10, 10)
        main_h.setSpacing(10)
        main_h.setAlignment(Qt.AlignLeft)

        # IKONA
        self.ico_button = QPushButton()
        self.ico_button.setFixedSize(50, 50)
        self.ico_button.setObjectName("ico_button")
        self.ico_button.setIconSize(QSize(40, 40))
        if on_icon_click:
            self.ico_button.clicked.connect(lambda: on_icon_click(self.eid, etype, itype, name))
        main_h.addWidget(self.ico_button)

        # PRAWA KOLUMNA
        right_col = QVBoxLayout()
        right_col.setSpacing(5)
        right_col.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.name_label = QLabel(name)
        self.name_label.setObjectName("names")
        self.name_label.setFixedHeight(20)
        right_col.addWidget(self.name_label)


        self.switch_button = ToggleButton(
    width=100,
    bg_off=self.background_slider,
    bg_on=self.background_slider,
    btn_off=self.background_slider,
    btn_on=self.switch_color_frame_on,
    border_bg=self.border_bg,
    border_btn_off=self.available_color,
    border_btn_on=self.switch_color,
    border_width=2,
    checked=False,
    text_on="ON",
    text_off="OFF",
    text_color_off=self.available_color,
    text_color_on=self.switch_color,
    on_toggle=self._on_switch_clicked
)

        right_col.addWidget(self.switch_button)

        main_h.addLayout(right_col)
        outer_layout.addWidget(self.frame)
        self.setLayout(outer_layout)

    # ---- EVENT Z HA (dowolny wątek) ----
    def on_ha_state(self, eid, state_obj):
        if eid != self.eid:
            return
        self.ha_state_signal.emit(state_obj) 

    # ---- GUI THREAD ----
    def _update_gui(self, state_obj):
        state = state_obj.get("state", "off")
        checked = state != "off"

        if checked:
           self.frame.setStyleSheet(f"background: {self.background_color_rgba};  border: 1px solid {self.border_color_rgba}; border-radius: 10px;")
           self.ico_button.setStyleSheet(f"background: {self.icons_background_rgba}; border-width: 0px")
           self.name_label.setStyleSheet(f"background: transparent; border: 0px solid transparent; border-radius: 0px;")
           icon_name = self.icon_on
           icon_color = self.switch_color
           
        elif state == "unavailable":
            self.frame.setStyleSheet(f"background: {self.unavailable_color_rgba};  border: 1px solid {self.border_bg_rgba}; border-radius: 10px;")
            self.ico_button.setStyleSheet(f"background: {self.unavailable_color_rgba}; border-width: 0px")
            self.name_label.setStyleSheet(f"background: transparent; border: 0px solid transparent; border-radius: 0px;")
            icon_name = self.icon_un
            icon_color = self.unavailable_color
            
        else:
           self.frame.setStyleSheet(f"background: {self.background_frame_rgba};  border: 1px solid {self.border_bg_rgba}; border-radius: 10px;")
           self.ico_button.setStyleSheet(f"background: {self.icons_background_rgba}; border-width: 0px")
           self.name_label.setStyleSheet(f"background: transparent; border: 0px solid transparent; border-radius: 0px;")
           icon_name = self.icon_off
           icon_color = self.available_color


        self.switch_button.blockSignals(True)
        self.switch_button.setChecked(checked)
        self.switch_button._update_position(checked)  
        self.switch_button.update()                   
        self.switch_button.blockSignals(False)


        self.frame.style().unpolish(self.frame)
        self.frame.style().polish(self.frame)
        self.frame.update()
        self.ico_button.style().unpolish(self.ico_button)
        self.ico_button.style().polish(self.ico_button)
        self.ico_button.setIcon(qta.icon(icon_name, color=icon_color, scale_factor=0.7))
        self.ico_button.update()


    def _on_switch_clicked(self):
        self.toggle_switch(self.eid)


    def toggle_switch(self, eid):
        service = "toggle" 
        self.ha.call_service("switch", service, eid)


    def mousePressEvent(self, event):
        clicked_widget = self.childAt(event.pos())

    # nie reaguj jeśli kliknięto switch lub ikonę
        if clicked_widget in (self.switch_button, self.ico_button):
            return

    # toggle switch
        self.toggle_switch(self.eid)

        super().mousePressEvent(event)

