import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFontMetrics
import qtawesome as qta
from configparser import ConfigParser
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QSize
import qtawesome as qta
from configparser import ConfigParser
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QSize
#from areas import HAControlUIRoom

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
    
color = config_object["colors"]["sensor_chart"]
available = config_object["colors"]["available"]
unavailable = config_object["colors"]["unavailable"]
background_slider = config_object["colors"]["elements_bg"]
border_bg = config_object["colors"]["elements_border"]

custom_rooms_colors = dict(config_object["custom_rooms_colors"])
default_color = custom_rooms_colors.get("default", "mdi:help-circle")

custom_rooms_icons = dict(config_object["custom_rooms_icons"])
default_icon = custom_rooms_icons.get("default", "mdi:help-circle")

custom_rooms_json = dict(config_object["custom_rooms_json"])
default_json = custom_rooms_json.get("default", "dummy.json")


class SensorRoomCard(QWidget):

    ha_state_signal = pyqtSignal(dict)

    def __init__(
        self,
        eid,
        etype,
        itype,
        name,
        ha_client,
        TYPE_OBJECT_NAME_MAP,
        on_tile_click=None,
        on_icon_click=None
    ):
        super().__init__()

        self.eid = eid
        self.ha = ha_client
        self.itype = itype

        self.setFixedHeight(130)
        self.setAutoFillBackground(True)
        self.setObjectName(TYPE_OBJECT_NAME_MAP.get(etype, "not_set"))

        for key in custom_rooms_json:
            if key in self.itype:
                json_file = custom_rooms_json[key]
                break
        
        self.json_file = json_file 
        
        r, g, b = map(int, unavailable.split(","))  
        self.unavailable_color = QColor(r, g, b)
        self.unavailable_color_rgb = f"rgb({r},{g},{b})"

        r, g, b = map(int, available.split(","))  
        self.available_color = QColor(r, g, b)
        self.available_color_rgb = f"rgb({r},{g},{b})"

        r, g, b = map(int, available.split(","))  
        self.available_color = QColor(r, g, b)
        self.available_color_rgba = f"rgba({r},{g},{b}, 150)"
        
        
        r, g, b = map(int, border_bg.split(","))  
        self.border_bg = QColor(r, g, b)
        self.border_bg_rgb = f"rgb({r},{g},{b})"

        self.color_border = f"rgba({color}, 210)"
        self.color_background = f"rgba({color}, 20)"
        
        self.color_icon = f"rgba({color}, 250)"
        self.color_background = f"rgba({color}, 20)"
        
        
        if on_tile_click:
            self.mousePressEvent = lambda e: on_tile_click(eid, etype, itype)

        self._build_ui(name, etype, itype, on_icon_click)


        self.ha_state_signal.connect(self._update_gui)

        self.ha.register(self)

    def _build_ui(self, name, etype, itype, on_icon_click):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.frame = QWidget()
        self.frame.setObjectName("light")
        self.frame.setAutoFillBackground(True)
        self.frame.setAttribute(Qt.WA_TransparentForMouseEvents, False)


        main = QVBoxLayout(self.frame)
        main.setContentsMargins(0, 0, 0, 0)

        self.ico_button = QPushButton()
        self.ico_button.clicked.connect(self.run_room)

        color = default_color
        for key in custom_rooms_colors:
            if key in self.itype:
                color = custom_rooms_colors[key]

                break


        r, g, b = map(int, color.split(","))  
        self.icon_color = QColor(r, g, b)  

        
        r, g, b = map(int, color.split(","))  
        self.border_rgba = f"rgba({r},{g},{b}, 100)"

        r, g, b = map(int, color.split(","))  
        self.background_rgba = f"rgba({r},{g},{b}, 50)"
        

        
        icon_name = default_icon
        
        for key in custom_rooms_icons:
            if key in self.itype:
                icon_name = custom_rooms_icons[key]
                break
                
        icon_color = self.icon_color
        
        
        self.ico_button.setIcon(qta.icon(icon_name, color=icon_color, scale_factor=0.7))
        self.ico_button.setIconSize(QSize(60, 50))

        
        self.name_label = QLabel(name)
        self.name_label.setStyleSheet(f"background:  transparent; color: {self.available_color_rgb}; border: 0px solid rgba(0,94,126, 250);")
        metrics = QFontMetrics(self.name_label.font())
        self.name_label.setText(metrics.elidedText(name, Qt.ElideRight, 250))

        self.value_label = QLabel("...")
        self.value_label.setStyleSheet(f"background:  transparent; color: {self.available_color_rgba}; font-size: 16px; border: 0px solid rgba(0,94,126, 250);")


        main.addStretch()
        main.addWidget(self.name_label, alignment=Qt.AlignHCenter)
        main.addWidget(self.ico_button, alignment=Qt.AlignHCenter)
        main.addWidget(self.value_label, alignment=Qt.AlignHCenter)
        main.addStretch()

        outer.addWidget(self.frame)


    def on_ha_state(self, eid, state_obj):
        if eid != self.eid:
            return

        self.ha_state_signal.emit(state_obj)

    def _update_gui(self, state_obj):
        state = state_obj.get("state", "")
        print(state)
        # wartość
        try:
            val = float(state)
            if "." in str(state):
                val = round(val, 1)
            self.value_label.setText(str(val))
        except Exception:
            if state == "unavailable":
                state ="Niedostepny"
                self.frame.setProperty("quality", "unavailable")
                self.ico_button.setStyleSheet("background: #121217; color: #64d0e9; border: 1px solid rgba(0,94,126, 250);")
                self.frame.style().unpolish(self.frame)
                self.frame.style().polish(self.frame)
                self.frame.update()
            
            
            self.value_label.setText(str(state))



            self.frame.setStyleSheet(f"background: {self.background_rgba};  border: 1px solid {self.border_rgba}; border-radius: 10px;")
            self.ico_button.setStyleSheet(f"background: #121217; color: #64d0e9; border: 1px solid {self.border_rgba}; border-radius: 10px;")
            self.ico_button.setFixedWidth(54)
                
                
                
        self.frame.style().unpolish(self.frame)
        self.frame.style().polish(self.frame)
        self.frame.update()

    def run_room(self):
        print(self.json_file)
      #  self.room_window = HAControlUIRoom(json_path=self.json_file)
      #  self.room_window.show()
      #  self.room_window.raise_()
      #  self.room_window.activateWindow()
        print(f"ico_button clicked! eid={self.eid}")
    # tutaj możesz umieścić logikę, którą chcesz uruchomić

