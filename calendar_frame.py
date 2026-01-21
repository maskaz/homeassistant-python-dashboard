import os
import sys
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QSizePolicy, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
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
    
color = config_object["colors"]["sensor_chart"]
available = config_object["colors"]["available"]
unavailable = config_object["colors"]["unavailable"]
background_slider = config_object["colors"]["elements_bg"]
border_bg = config_object["colors"]["elements_border"]

icons_by_type = dict(config_object["icons_by_itype"])
default_icon = icons_by_type.get("default", "mdi:help-circle")




class SensorCalendar(QWidget):
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
        self.etype = etype
        self.itype = itype
        self.ha = ha_client
        self.setFixedHeight(60)
        self.setAutoFillBackground(True)
        self.setObjectName(TYPE_OBJECT_NAME_MAP.get(etype, "not_set"))
   
        
        r, g, b = map(int, unavailable.split(","))  
        self.unavailable_color = QColor(r, g, b)
        
        r, g, b = map(int, available.split(","))  
        self.available_color = QColor(r, g, b)
 
        r, g, b = map(int, background_slider.split(","))  
        self.background_slider = QColor(r, g, b)
        
        r, g, b = map(int, border_bg.split(","))  
        self.border_bg = QColor(r, g, b)


        
        
        if on_tile_click:
            print(self.eid)
            self.mousePressEvent = lambda e: on_tile_click(self.eid, self.etype, self.itype)
        else:
            self.mousePressEvent = lambda e: None  

        self._build_ui(name, etype, itype, on_icon_click)


        self.ha.register(self)

    def _build_ui(self, name, etype, itype, on_icon_click):
        outer_layout = QHBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        frame = QWidget()
        frame.setAutoFillBackground(True)
        frame.setObjectName("entity_frame")
        main_h = QHBoxLayout(frame)
        main_h.setContentsMargins(10, 5, 10, 10)
        main_h.setSpacing(10)

        self.ico_button = QPushButton()
        self.ico_button.setObjectName("ico_button")
        self.ico_button.setFixedSize(50, 50)
        
        icon_name = default_icon
        
        for key in icons_by_type:
            if key in self.itype:
                icon_name = icons_by_type[key]
                break
        icon_color = self.available_color
        self.ico_button.setIcon(qta.icon(icon_name, color=icon_color, scale_factor=0.7))
        self.ico_button.setIconSize(QSize(40, 40))

        if on_icon_click:
            self.ico_button.clicked.connect(
                lambda: on_icon_click(self.eid, self.etype, self.itype, name)
            )
        main_h.addWidget(self.ico_button)

        right_col = QVBoxLayout()
        right_col.setSpacing(5)
        right_col.setAlignment(Qt.AlignTop)

        # NAZWA
        self.name_label = QLabel(name)
        self.name_label.setObjectName("names")
        self.name_label.setFixedHeight(20)
        metrics = QFontMetrics(self.name_label.font())
        self.name_label.setText(metrics.elidedText(name, Qt.ElideRight, 250))
        right_col.addWidget(self.name_label)

        self.value_label = QLabel("...")
        self.value_label.setObjectName("sensor_chart_label")
        self.value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        right_col.addWidget(self.value_label)

        right_col.addStretch()
        main_h.addLayout(right_col)
        outer_layout.addWidget(frame)
        self.setLayout(outer_layout)

    def on_ha_state(self, eid, state_obj):
        if eid != self.eid:
            return
        print(state_obj)
        state = state_obj.get("state", "")
        attrs = state_obj.get("attributes", {})

        # jeśli to sensor liczbowy
        if state == "unavailable":
           self.ico_button.setProperty("unavailable", "unavailable")                
        else:
           self.ico_button.setObjectName("ico_button")        
        try:
            state_val = "Next 30 days"
            self.value_label.setText(str(state_val))
        except:
            # dla sensorów binarnych / tekstowych
            state_lower = str(state).lower()

