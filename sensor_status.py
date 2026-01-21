from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QSizePolicy, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFontMetrics
from datetime import datetime, timedelta
from configparser import ConfigParser
import sys
import os

def get_config_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "config2.ini")

# Wczytywanie pliku konfiguracyjnego
config_path = get_config_path()
config_object = ConfigParser()
config_object.read(config_path)


class SensorStatus(QWidget):
    ha_state_signal = pyqtSignal(dict)  # 🔥 sygnał do wątku GUI

    def __init__(
        self,
        eid,
        etype,
        itype,
        name,
        ha_client,
        TYPE_OBJECT_NAME_MAP,
        COLOR_MAP,
        ICON_MAP,
        on_tile_click=None,
        on_icon_click=None
    ):
        super().__init__()
        self.eid = eid
        self.etype = etype
        self.itype = itype
        self.ha = ha_client
        self.on_tile_click = on_tile_click

        
        self.setAutoFillBackground(True)
        self.setObjectName(TYPE_OBJECT_NAME_MAP.get(etype, "not_set"))

        self._build_ui(name, etype, itype, on_icon_click)

        self.ha_state_signal.connect(self._update_gui)

        self.ha.register(self)

    def _build_ui(self, name, etype, itype, on_icon_click):
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.frame = QWidget()
        self.frame.setFixedHeight(70)
        self.frame.setAutoFillBackground(True)
        self.frame.setObjectName("light")
        main_h = QHBoxLayout(self.frame)
        main_h.setContentsMargins(10, 10, 10, 10)
        main_h.setSpacing(10)

        # IKONA
        self.ico_button = QPushButton(ICON_MAP.get(itype, "󰞱"))
        self.ico_button.setObjectName("ico_button")
        self.ico_button.setFixedSize(50, 50)
        if on_icon_click:
            self.ico_button.clicked.connect(lambda: on_icon_click(self.eid, etype, itype, name))
        main_h.addWidget(self.ico_button)

        # PRAWA KOLUMNA
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

        # BOX WARTOŚCI
        content_box = QHBoxLayout()
        content_box.setSpacing(10)

        self.value_label = QLabel("...")
        self.value_label.setObjectName("sensor_chart_label")
        self.value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        content_box.addWidget(self.value_label)

        self.value_zmiana = QLabel("...")
        self.value_zmiana.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.value_zmiana.setContentsMargins(0, 0, 0, 0)
        self.value_zmiana.setAlignment(Qt.AlignBottom)
        self.value_zmiana.setObjectName("sensor_chart_label_small")
        content_box.addWidget(self.value_zmiana, alignment=Qt.AlignRight)

        right_col.addLayout(content_box)
        right_col.addStretch()
        main_h.addLayout(right_col)
        outer_layout.addWidget(self.frame)
        self.setLayout(outer_layout)

    # WEJŚCIE Z HA (dowolny wątek)
    def on_ha_state(self, eid, state_obj):
        if eid != self.eid:
            return
        self.ha_state_signal.emit(state_obj)

    # GUI THREAD
    def _update_gui(self, state_obj):
        state = state_obj.get("state", "")
        attrs = state_obj.get("attributes", {})
        zmiana = state_obj.get("last_changed", "")
        dt = datetime.fromisoformat(zmiana)
        dt_plus_one = dt + timedelta(hours=1)
        kiedy_zmiana = dt_plus_one.strftime("%H:%M")

        # liczbowy sensor
        try:
            state_val = float(state)
            if "." in str(state):
                state_val = round(state_val, 1)
            self.value_label.setText(str(state_val))
            self.value_zmiana.setText(f"Zmiana: {kiedy_zmiana}")
        except:
            # dla sensorów binarnych / tekstowych
            display = state  

            if "door" in self.itype or "window" in self.itype:
                self.value_zmiana.setText(f"Zmiana: {kiedy_zmiana}")
                if state == "on":
                    display = "Otwarte"
                    self.value_label.setStyleSheet(f"background-color: transparent; color: #ffffff; font-size: 22px;")
                    self.frame.setProperty("quality", "bad")
                    self.ico_button.setText("󰠜")
                    
                elif state == "Nieznany":
                    display = "Nieznany"
                    self.value_label.setStyleSheet(f"background-color: transparent; color: #ffffff; font-size: 22px;")
                    self.frame.setProperty("quality", "no_sensor")
                    self.ico_button.setText("󰅘")
                else:
                    display = "Zamknięte"
                    self.value_label.setStyleSheet(f"background-color: transparent; color: #ffffff; font-size: 22px;")
                    self.frame.setProperty("quality", "good")
                    self.ico_button.setText("󱂯")

                self.frame.style().unpolish(self.frame)
                self.frame.style().polish(self.frame)
                self.frame.update()
        
            elif "dzwonek" in self.itype:
                self.value_zmiana.setText(" ")
                if state == "on":
                    display = "Dzwoni"
                    self.value_label.setStyleSheet(f"background-color: transparent; color: #ffffff; font-size: 22px;")
                    self.frame.setProperty("quality", "bad")
                    self.ico_button.setText("󰂞")
                    
                elif state == "unknown":
                    display = "Nieznany"
                    self.value_label.setStyleSheet(f"background-color: transparent; color: #ffffff; font-size: 22px;")
                    self.frame.setProperty("quality", "no_sensor")
                    self.ico_button.setText("󰅘")
                    
                else:
                    display = "Oczekiwanie"
                    self.value_label.setStyleSheet(f"background-color: transparent; color: #ffffff; font-size: 22px;")
                    self.frame.setProperty("quality", "good")
                    self.ico_button.setText("󱑂")

                self.frame.style().unpolish(self.frame)
                self.frame.style().polish(self.frame)
                self.frame.update()
                
            elif "domofon" in self.itype:
                print("domofon")
                print(state)
                self.value_zmiana.setText(" ")
                if state == "Dzwoni" or state == "Bledny kod":
                    self.value_label.setStyleSheet(f"background-color: transparent; color: #ffffff; font-size: 22px;")
                    self.frame.setProperty("quality", "bad")
                    self.ico_button.setText("󰂞")
                    
                elif state == "Otwarcie drzwi":
                    self.value_label.setStyleSheet(f"background-color: transparent; color: #ffffff; font-size: 22px;")
                    self.frame.setProperty("quality", "good")
                    self.ico_button.setText("󰠜")
                    
                elif state == "unknown":
                    display = "Nieznany"
                    self.value_label.setStyleSheet(f"background-color: transparent; color: #ffffff; font-size: 22px;")
                    self.frame.setProperty("quality", "no_sensor")
                    self.ico_button.setText("󰅘")
                    
                else:
                    display = "Oczekiwanie"
                    self.value_label.setStyleSheet(f"background-color: transparent; color: #ffffff; font-size: 22px;")
                    self.frame.setProperty("quality", "good")
                    self.ico_button.setText("󱑂")

                    
                self.frame.style().unpolish(self.frame)
                self.frame.style().polish(self.frame)
                self.frame.update()                    
                    
                    
                    
            elif "obecnosc" in self.itype:
                self.value_zmiana.setText(" ")
                if state == "on":
                    display = "Zajęta"
                    self.value_label.setStyleSheet(f"background-color: transparent; color: #ffffff; font-size: 22px;")
                    self.frame.setProperty("info", "red")
                    self.ico_button.setText("󰅚")
                    
                elif state == "unknown":
                    display = "Nieznany"
                    self.value_label.setStyleSheet(f"background-color: transparent; color: #ffffff; font-size: 22px;")
                    self.frame.setProperty("info", "no_sensor")
                    self.ico_button.setText("󰅘")
                    
                else:
                    display = "Wolna"
                    self.value_label.setStyleSheet(f"background-color: transparent; color: #ffffff; font-size: 22px;")
                    self.frame.setProperty("info", "green")
                    self.ico_button.setText("󰄰")


                self.frame.style().unpolish(self.frame)
                self.frame.style().polish(self.frame)
                self.frame.update()
                
            elif "kamera" in self.itype:
                self.value_zmiana.setText(" ")
                if state == "on":
                    display = "Wyłączona"
                    self.value_label.setStyleSheet(f"background-color: transparent; color: {sensor_room_color_green};")
                    self.ico_button.setText("󱜷")
                    self.ico_button.setProperty("ico_camera", "off")

                    self.ico_button.style().unpolish(self.ico_button)
                    self.ico_button.style().polish(self.ico_button)
                    self.ico_button.update()
        
                else:
                    display = "Włączona"
                    self.value_label.setStyleSheet(f"background-color: transparent; color: {sensor_room_color_orange};")
                    self.ico_button.setText("󰖠")
                    self.ico_button.setProperty("ico_camera", "on")

                    self.ico_button.style().unpolish(self.ico_button)
                    self.ico_button.style().polish(self.ico_button)
                    self.ico_button.update()

            self.value_label.setText(str(display))

    # KLIK W TŁO KAFELKA
    def mousePressEvent(self, event):
        clicked_widget = self.childAt(event.pos())
        if self.on_tile_click and clicked_widget not in (self.ico_button,):
            self.on_tile_click(self.eid, self.etype, self.itype)
        super().mousePressEvent(event)

