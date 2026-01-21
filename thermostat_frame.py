import os
import sys
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
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
    
color = config_object["colors"]["thermostat"]
available = config_object["colors"]["available"]
unavailable = config_object["colors"]["unavailable"]
background_slider = config_object["colors"]["elements_bg"]
border_bg = config_object["colors"]["elements_border"]

icon_on = config_object["icons"]["thermostat_on"]
icon_off = config_object["icons"]["thermostat_off"]
icon_un =config_object["icons"]["unavailable"]
arrow_up =  config_object["icons"]["arrow_up"]
arrow_down = config_object["icons"]["arrow_down"]

class ThermostatFrame(QWidget):
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
        self.debounce_timers = {}

        self.setAutoFillBackground(True)
        self.setObjectName(TYPE_OBJECT_NAME_MAP.get(etype, "not_set"))
        self.setFixedHeight(80)

        r, g, b = map(int, color.split(","))  
        self.thermostat_color = QColor(r, g, b)  
        self.thermostat_color_rgb = f"rgb({r},{g},{b})"
        
        r, g, b = map(int, unavailable.split(","))  
        self.unavailable_color = QColor(r, g, b)
        self.unavailable_color_rgb = f"rgb({r},{g},{b})"

        
        r, g, b = map(int, available.split(","))  
        self.available_color = QColor(r, g, b)
        self.available_color_rgb = f"rgb({r},{g},{b})"
 
        
        r, g, b = map(int, border_bg.split(","))  
        self.border_bg = QColor(r, g, b)
        self.border_bg_rgb = f"rgb({r},{g},{b})"
        
        self.icon_on = icon_on
        self.icon_off = icon_off
        self.icon_un = icon_un
        self.arrow_up =  arrow_up
        self.arrow_down = arrow_down
        
        if on_tile_click:
            self.mousePressEvent = lambda e: on_tile_click(eid, etype, itype)

        self._build_ui(name, etype, itype,  on_icon_click)

        self.ha.register(self)

        self.on_ha_state(self.eid, self.ha.entity_states.get(self.eid, {}))

    def _build_ui(self, name, etype, itype, on_icon_click):
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)


        frame = QWidget()
        frame.setAutoFillBackground(True)
        frame.setObjectName("entity_frame")
        main_h = QHBoxLayout(frame)
        main_h.setContentsMargins(10, 5, 10, 10)
        main_h.setSpacing(10)
        main_h.setAlignment(Qt.AlignLeft)

        self.ico_button = QPushButton()
        self.ico_button.setObjectName("ico_button")
        self.ico_button.setFixedSize(50, 50)
        icon_name = self.icon_on
        icon_color = self.thermostat_color
        self.ico_button.setIcon(qta.icon(icon_name, color=icon_color, scale_factor=0.7))
        self.ico_button.setIconSize(QSize(40, 40))
        self.ico_button.clicked.connect(lambda: on_icon_click(self.eid, etype, itype, name))
        main_h.addWidget(self.ico_button)


        right_col = QVBoxLayout()
        right_col.setSpacing(5)
        right_col.setAlignment(Qt.AlignTop)


        self.name_label = QLabel(name)
        self.name_label.setObjectName("names")
        self.name_label.setFixedHeight(20)
        metrics = QFontMetrics(self.name_label.font())
        self.name_label.setText(metrics.elidedText(name, Qt.ElideRight, 250))
        right_col.addWidget(self.name_label)


        content_box = QHBoxLayout()
        content_box.setContentsMargins(0,0,0,0)
        content_box.setSpacing(10)
        right_col.addLayout(content_box)

        # kolory przycisków
 #       thermostat_bg_color = f"rgb({elements_color})"
 #       thermostat_bg_active_color = f"rgb({thermostat_color})"
 #       sw_border_font_color_up = f"rgb({elements_color_up})"
 #       sw_border_font_color_down = f"rgb({elements_color_down})"

        self.btn_minus = QPushButton("󰧗")
        self.btn_minus.setObjectName("thermostat_button")
        self.btn_minus.setFixedSize(60,40)
        self.btn_minus.setStyleSheet(f"""
            QPushButton {{
                background-color: #191919;
                color: #ffffff;
                border-color: #000000;
            }}
            QPushButton:pressed, QPushButton:checked {{
                background-color: #45a3d5;
                color: #ffffff;
                border-color: #000000;
            }}
        """)
        content_box.addWidget(self.btn_minus)

        self.value_label = QLabel("...")
        self.value_label.setAlignment(Qt.AlignLeft)
        self.value_label.setFixedHeight(40)
        self.value_label.setFixedWidth(80)
        self.value_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.thermostat_color_rgb};
                border: 2px solid {self.border_bg_rgb};
                color: {self.available_color_rgb};
                font-size: 16px;
                text-align:right;
                border-radius: 4px;
                padding: 8px 16px;
            }}
        """)




        content_box.addWidget(self.value_label)

        self.btn_plus = QPushButton("󰧝")
        self.btn_plus.setObjectName("thermostat_button")
        self.btn_plus.setFixedSize(60,40)
        self.btn_plus.setStyleSheet(f"""
            QPushButton {{
                background-color: #191919;
                color: #ffffff;
                border-color: #000000;
            }}
            QPushButton:pressed, QPushButton:checked {{
                background-color: #cf4c45;
                color: #ffffff;
                border-color: #000000;
            }}
        """)
        content_box.addWidget(self.btn_plus)

        self.btn_minus.clicked.connect(lambda _, eid=self.eid: self.adjust_number_value_thermostat_debounce(eid, -1))
        self.btn_plus.clicked.connect(lambda _, eid=self.eid: self.adjust_number_value_thermostat_debounce(eid, 1))

        right_col.addStretch()
        main_h.addLayout(right_col)
        outer_layout.addWidget(frame)


    def adjust_number_value_thermostat_debounce(self, eid, step_value):
        if eid in self.debounce_timers:
            self.debounce_timers[eid].stop()
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda eid=eid, step_value=step_value: self.adjust_number_value_thermostat(eid, step_value))
        self.debounce_timers[eid] = timer
        timer.start(300)


    def adjust_number_value_thermostat(self, eid, tempe):
        state_obj = self.ha.entity_states.get(eid)
        if not state_obj:
            print(f"No state of {eid}")
            return

        attrs = state_obj.get("attributes", {})
        try:
            current = int(attrs.get("temperature", 0))
            step = float(attrs.get("step", 1))
            min_ = float(attrs.get("min", 15))
            max_ = float(attrs.get("max", 30))
        except (ValueError, TypeError) as e:
            print(f"Entity attr error {eid}: {e}")
            return

        new_value = current + tempe * step
        new_value = max(min_, min(max_, new_value))

        self.ha.call_service(
            domain="climate",
            service="set_temperature",
            entity_id=eid,
            data={"temperature": new_value}
        )

    def on_ha_state(self, eid, state_obj):
        if eid != self.eid:
            return
        attrs = state_obj.get("attributes", {})
        temperature = attrs.get("temperature")
        if temperature is not None:
            self.value_label.setText(str(temperature))

