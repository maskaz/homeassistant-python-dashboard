import os
import sys
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
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
    
color = config_object["colors"]["select"]
available = config_object["colors"]["available"]
unavailable = config_object["colors"]["unavailable"]
background_slider = config_object["colors"]["elements_bg"]
border_bg = config_object["colors"]["elements_border"]

icon_on = config_object["icons"]["select_on"]
icon_off = config_object["icons"]["select_off"]
icon_un =config_object["icons"]["unavailable"]

class SelectFrame(QWidget):
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

        self.setAutoFillBackground(True)
        self.setObjectName(TYPE_OBJECT_NAME_MAP.get(etype, "not_set"))
        self.setFixedHeight(80)

        r, g, b = map(int, color.split(","))  
        self.color = QColor(r, g, b)     
        
        r, g, b = map(int, unavailable.split(","))  
        self.unavailable_color = QColor(r, g, b)
        
        r, g, b = map(int, available.split(","))  
        self.available_color = QColor(r, g, b)
 
        r, g, b = map(int, background_slider.split(","))  
        self.background_slider = QColor(r, g, b)
        
        r, g, b = map(int, border_bg.split(","))  
        self.border_bg = QColor(r, g, b)

        self.icon_on = icon_on
        self.icon_off = icon_off
        self.icon_un = icon_un
        
        if on_tile_click:
            self.mousePressEvent = lambda e: on_tile_click(eid, etype, itype)

        self._build_ui(name, etype, itype, on_icon_click)

        # rejestracja w websocket
        self.ha.register(self)

        # pobranie stanu od razu po starcie
        self.on_ha_state(self.eid, self.ha.entity_states.get(self.eid, {}))

    def _build_ui(self, name, etype, itype, on_icon_click):
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # główny frame wewnątrz widgetu
        frame = QWidget()
        frame.setAutoFillBackground(True)
        frame.setObjectName("entity_frame")
        main_h = QHBoxLayout(frame)
        main_h.setContentsMargins(10, 10, 10, 10)
        main_h.setSpacing(10)

        # IKONA po lewej
        self.ico_button = QPushButton()
        self.ico_button.setObjectName("ico_button")
        self.ico_button.setFixedSize(50, 50)
        
        icon_color = self.color
        icon_name = self.icon_on
        self.ico_button.setIcon(qta.icon(icon_name, color=icon_color, scale_factor=0.7))
        self.ico_button.setIconSize(QSize(40, 40))
        
        if on_icon_click:
            self.ico_button.clicked.connect(lambda: on_icon_click(self.eid, etype, itype, name))
        main_h.addWidget(self.ico_button)

        # PRAWA KOLUMNA
        right_col = QVBoxLayout()
        right_col.setSpacing(5)
        right_col.setAlignment(Qt.AlignTop)

        # nazwa
        self.name_label = QLabel(name)
        self.name_label.setObjectName("names")
        self.name_label.setFixedHeight(20)
        metrics = QFontMetrics(self.name_label.font())
        self.name_label.setText(metrics.elidedText(name, Qt.ElideRight, 250))
        right_col.addWidget(self.name_label)

        # content box dla ComboBox
        content_box = QHBoxLayout()
        content_box.setContentsMargins(0, 0, 0, 0)
        content_box.setSpacing(10)
        right_col.addLayout(content_box)

        self.combo = QComboBox()
        self.combo.setFixedHeight(40) 
     #   self.combo.setObjectName("lista_combo")
        self.combo.entity_id = self.eid
        self.combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo.currentIndexChanged.connect(lambda index, c=self.combo: self.select_changed(self.eid, c))
        content_box.addWidget(self.combo)

        right_col.addStretch()
        main_h.addLayout(right_col)
        outer_layout.addWidget(frame)

    # --- aktualizacja stanu z HA ---
    def on_ha_state(self, eid, state_obj):
        if eid != self.eid:
            return

        state = state_obj.get("state")
        attrs = state_obj.get("attributes", {})
        options = attrs.get("options", [])

        combo = self.combo
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(options)
        if state in options:
            combo.setCurrentIndex(options.index(state))
        combo.blockSignals(False)

    def select_changed(self, eid, combo):
        new_value = combo.currentText()
        print(f"Change {eid} -> {new_value}")
        self.ha.call_service("select", "select_option", eid, {"option": new_value})
