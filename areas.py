import sys
import os
import json
import threading
import websocket
import os.path
import time
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFontMetrics, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QGridLayout, QGraphicsDropShadowEffect,
    QSlider, QPushButton, QHBoxLayout, QScrollArea, QGroupBox, QScroller, QStyleOptionSlider, QDesktopWidget, QComboBox, QFrame
)
from PyQt5.QtGui import QMouseEvent
from PyQt5 import QtWidgets, uic
from configparser import ConfigParser
from sensor_graph_loading import show_sensor_graph  
from PyQt5.QtGui import QColor
from slider_tweak import Slider
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
     
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QGraphicsOpacityEffect, QProgressBar
from PyQt5.QtCore import QPropertyAnimation
from qtwidgets import PaletteGrid, PaletteHorizontal, PaletteVertical
from PyQt5.QtWidgets import QTabBar, QStackedWidget, QMainWindow, QTabWidget

from functools import partial
from qtwidgets import Toggle

from light_frame import LightFrame
from fan_frame import FanFrame
from cover_frame import CoverFrame
from number_slider_frame import NumberSliderFrame
from thermostat_frame import ThermostatFrame
from sensor_chart_frame import SensorChartFrame
from sensor_frame import SensorFrame
from select_frame import SelectFrame
from connection_frame import create_ha_connection_tile

from sensor_status import SensorStatus
from popup_temp import show_temp_palette_popup
from popup_temp_color import show_temp_color_palette_popup
from switch_frame import SwitchFrame
from weather_frame import create_pogoda_frame
from room_frame import SensorRoomCard
from todo_frame import SensorTodo
from calendar_frame import SensorCalendar
from todo_list import TodoListWindow
from calendar_30_days import CalendarMonth
import qtawesome as qta

def get_config_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "config.ini")


config_path = get_config_path()
config_object = ConfigParser()
config_object.read(config_path)

if "ha" not in config_object:
    print("no [ha] inside config.ini!")
    sys.exit(1)


HA_TOKEN = config_object["ha"]["ha_token"]
HA_WS_URL = config_object["ha"]["ha_ip_ws"]
screen_settings = config_object["settings"]["screen"]
columns = config_object["settings"]["columns"]
                    
def get_json_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, filename)
    
def load_entity_groups_from_file(json_path):
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
            return data  
    except FileNotFoundError:
        print(f"file {json_path} not found")
        return {}

def get_style_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, "styles.qss")


def load_stylesheet():
    with open(get_style_path(), "r") as file:
        return file.read()

def load_colors_from_qss():
    classpath = get_slider_style_path()
    colors = {}
    with open(path, "r") as f:
         for line in f:
             if ":" in line:
                 key, value = line.strip().strip(";").split(":")
                 colors[key.strip()] = value.strip()
         return colors

class HAWebSocketClient:
    def __init__(self, on_state_update, on_disconnected=None):
        self.ws = None
        self.authenticated = False
        self.connected = False
        self.msg_id = 1
        self.entity_states = {}
        self.on_state_update = on_state_update
        self.on_disconnected = on_disconnected
        self._observers = []


    def register(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)
        if hasattr(observer, "eid") and observer.eid in self.entity_states:
            observer.on_ha_state(observer.eid, self.entity_states[observer.eid])

    def notify_observers(self, eid, state_obj):
        for observer in self._observers:
            if hasattr(observer, "on_ha_state"):
                observer.on_ha_state(eid, state_obj)

    def connect(self):
        def run():
            self.ws = websocket.WebSocketApp(
                HA_WS_URL,
                on_open=self.on_open,
                on_message=self.on_message,
                on_close=self.on_close,
                on_error=self.on_error
            )
            self.ws.run_forever()
        threading.Thread(target=run, daemon=True).start()

    def send(self, payload):
        if self.connected:
            try:
                self.ws.send(json.dumps(payload))
            except Exception as e:
                print(f"error sending: {e}")

    def next_id(self):
        self.msg_id += 1
        return self.msg_id

    def on_open(self, ws):
        self.connected = True
        print("Connected")
        self.send({"type": "auth", "access_token": HA_TOKEN})

    def on_message(self, ws, message):
        try:
            msg = json.loads(message)
        except json.JSONDecodeError:
            print("invalid JSON:", message)
            return

        if msg["type"] == "auth_ok":
            self.authenticated = True
            self.subscribe_events()
            self.get_initial_states()

        elif msg["type"] == "event":
            entity_id = msg["event"]["data"]["entity_id"]
            new_state = msg["event"]["data"]["new_state"]
            self.entity_states[entity_id] = new_state
            self.on_state_update(entity_id, new_state)
            self.notify_observers(entity_id, new_state)

        elif msg["type"] == "result":
            if not msg.get("success"):
                print(f"res. error: {msg.get('error')}")
                return

            result = msg.get("result")
            if result is None:
                return

            if isinstance(result, dict) and "entity_id" in result:
                eid = result["entity_id"]
                self.entity_states[eid] = result
                self.on_state_update(eid, result)
                self.notify_observers(eid, result)

            elif isinstance(result, list):
                for state in result:
                    eid = state.get("entity_id")
                    if eid:
                        self.entity_states[eid] = state
                        self.on_state_update(eid, state)
                        self.notify_observers(eid, state)

    def disconnect(self):
        if self.ws:
            try:
                self.ws.close()
                print("WebSocket has been closed")
            except Exception as e:
                print(f"Error when closing: {e}")
        self.connected = False
        self.authenticated = False

    def on_close(self, ws, *args):
        self.connected = False
        print("websocket closed")
        if self.on_disconnected:
            self.on_disconnected()

    def on_error(self, ws, error):
        self.connected = False
        print(f"error websocket: {error}")
        if self.on_disconnected:
            self.on_disconnected()

    def subscribe_events(self):
        self.send({
            "id": self.next_id(),
            "type": "subscribe_events",
            "event_type": "state_changed"
        })

    def get_initial_states(self):
        self.send({
            "id": self.next_id(),
            "type": "get_states"
        })

    def call_service(self, domain, service, entity_id, data=None):
        if data is None:
            data = {}
        data["entity_id"] = entity_id
        self.send({
            "id": self.next_id(),
            "type": "call_service",
            "domain": domain,
            "service": service,
            "service_data": data
        })

    def try_reconnect(self):
        if not self.connected:
            print("Connecting...")
            self.connect()


class HAControlUIRoom(QMainWindow):
    def __init__(self, json_path=None):
        super().__init__()
        self.data = {}
        self.what_window = "normal_window"
        self.connection_timer = QTimer(self)
        self.connection_timer.timeout.connect(self.update_reconnect_button_status)
        self.connection_timer.start(1000)  
        self.columns = columns
        if json_path:
            full_path = get_json_path(json_path)
            self.data = load_entity_groups_from_file(full_path)
            

        global screen_settings
        self.setWindowTitle("HA")
        self.setGeometry(100, 100, 768, 1024)
        if screen_settings == "full":
            self.setWindowFlag(Qt.FramelessWindowHint)
            self.showFullScreen()
            print("full screen")
        else:
            print("no full screen")

        self.stylesheet = load_stylesheet()
        self.setStyleSheet(self.stylesheet)


        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0) 

        self.loader_widget = QWidget(self.central_widget)
        loader_layout = QVBoxLayout(self.loader_widget)
        loader_layout.setAlignment(Qt.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressbar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedSize(200, 20)
        loader_layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)

        self.main_layout.addWidget(self.loader_widget)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("scroll")
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setWidgetResizable(True)
        QScroller.grabGesture(self.scroll_area.viewport(), QScroller.LeftMouseButtonGesture)
        self.main_layout.addWidget(self.scroll_area)
        self.scroll_area.hide()

        self.container = QWidget()
        self.container.setObjectName("container")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.container)

        self.entity_widgets = {}
        self.entity_groups = self.data
        self.entity_info_types = {}
        self.entity_widget_types = {}

        self.ha = HAWebSocketClient(
            on_state_update=self.update_entity_state,
            on_disconnected=self.handle_disconnected
        )
        self.ha.connect()

        self.setup_widgets()

        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.timeout.connect(self.try_reconnect)

        self.debounce_timers = {}

        self.close_btn = QPushButton("Close")
        self.close_btn.setObjectName("close_button")
        self.close_btn.setFixedHeight(50)
        self.close_btn.clicked.connect(self.close_window)


        self.main_layout.addWidget(self.close_btn)

        self.connection_timer = QTimer(self)
        self.connection_timer.timeout.connect(self.update_reconnect_button_status)
        self.connection_timer.start(1000) 


        self.progress_value = 0
        self.timer = QTimer()
        self.timer.setInterval(6)  
        self.timer.timeout.connect(self._update_progress)
        self.timer.start()

    def _update_progress(self):
        self.progress_value += 1
        self.progress_bar.setValue(self.progress_value)

        if self.progress_value >= 100:
            self.timer.stop()
            self._show_main_ui()

    def _show_main_ui(self):
        self.loader_widget.hide()
        self.scroll_area.show()
        
    def close_window(self):
        self.reconnect_timer.stop()
        self.reconnect_timer.deleteLater()
        self.debounce_timers.clear()
        self.ha.ws.close() 
        self.ha = None
        self.close()
        
    def open_tab_window(self, index):
            json_file, widget_class = self.tabs_data[index]
            w = widget_class(json_file)
            w.show()
            self.tab_bar.setCurrentIndex(2);


    def send_selected_temp(self, eid, c):
        if c == "#ffffff": #1
           temp = 200
        elif c == "#ffebd9": #2
           temp = 230
        elif c == "#ffdbb9": #3
           temp = 260
        elif c == "#ffcc9c": #4
           temp = 290
        elif c == "#ffac5e": #5
           temp = 310
        elif c == "#ff9c3f": #6
           temp = 340
        elif c == "#ff8c21": #7
           temp = 370     
        elif c == "#ff7b00": #8
           temp = 400
        else:
           temp = 230        
        self.send_light_value_temp(eid, temp)
        
    def send_selected_color(self, eid, c):
        if c == "#ff8600": 
           hue = 40
        elif c == "#fffb00":
           hue = 60
        elif c == "#00ff25": 
           hue = 100
        elif c == "#00fff4": 
           hue = 180
        elif c == "#0200ff": 
           hue = 210
        elif c == "#8800ff": 
           hue = 240
        elif c == "#ff00eb": 
           hue = 284          
        elif c == "#ff0091": 
           hue = 310    
        elif c == "#ff0000": 
           hue = 330 
        else:
           hue = 330        
        self.send_light_value_hue(eid, hue)



    def setup_widgets(self):
        GROUP_MAP = {
"label": 1,
"light": 2,
"switch": 3,
"fan": 4,
"cover": 4,
"number_slider": 4,
"thermostat": 5,
"room_card": 6,
"sensor_chart": 7,
"sensor_frame": 7,
"todo": 8,
"calendar": 8,
"select": 10,
"ha_connection": 11,
             
             
        }

        TYPE_OBJECT_NAME_MAP = {

        }



        for group_name, entities in self.entity_groups.items():
            group_box = QGroupBox(group_name)
            if self.what_window == "window_with_weather":
               group_box.setObjectName("group_box_pogoda")            
            else:
               group_box.setObjectName("group_box")
            group_layout = QGridLayout()
            group_layout.setHorizontalSpacing(8)
            group_layout.setVerticalSpacing(8)
            group_box.setLayout(group_layout)
            
            row = 0
            col = 0
            print("self.columns")
            print(self.columns)
            max_cols = int(self.columns)
            prev_etype_group = None

            for entity in entities:
                eid = entity["entity_id"]
                etype = entity["widget_type"]
                itype = entity["info_type"]
                name = entity["name"]

                etype_group = GROUP_MAP.get(etype, -1)

                if prev_etype_group is not None and etype_group != prev_etype_group:
                    remaining = max_cols - col
                    if remaining > 0:
                        spacer = QWidget()
                        spacer.setObjectName("spacer")
                        group_layout.addWidget(spacer, row, col, 1, remaining)
                    col = 0
                    row += 1
                    count_current_type = 0
                    
                if etype == "label":
                    frame = QWidget()
                    frame_layout = QVBoxLayout(frame)
                    frame_layout.setContentsMargins(0, 0, 0, 0)
                    frame_layout.setSpacing(0)

                    name_label = QLabel(name)
                    name_label.setObjectName("section")  
                    name_label.setAlignment(Qt.AlignLeft)
                    frame_layout.addWidget(name_label)

                    frame.setObjectName("label")


                    group_layout.addWidget(frame, row, col, 1, 2)  

                    col += 2
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue
                    
                
                elif etype == "weather":
                    frame, info = create_pogoda_frame(
                        eid, etype, itype, name,
                        TYPE_OBJECT_NAME_MAP
                    )

                    self.entity_widget_types[info["eid"]] = info["etype"]
                    self.entity_info_types[(info["eid"], "state")] = info["itype"]
                    self.entity_widgets[(info["eid"], "state")] = info["state_widget"]
                    group_layout.addWidget(frame, row, col, 1, max_cols) 
                    frame.setObjectName("pogoda")
                    col += 2
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue
#-----------------------------------------------------------------------------

                elif etype == "light":
                    frame = LightFrame(
                            eid=eid,
                            etype=etype,
                            itype=itype,
                            name=name,
                            ha_client=self.ha,
                            TYPE_OBJECT_NAME_MAP=TYPE_OBJECT_NAME_MAP,
                            on_icon_click=self.frame_icon_clicked,
                            on_frame_click=self.frame_clicked
                        )

                    group_layout.addWidget(frame, row, col)


                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue
                    
#--------------------------------------------------------------------------------------------------------- 

                elif etype == "switch":
                    frame = SwitchFrame(
                         eid=eid,
                         etype=etype,
                         itype=itype,
                         name=name,
                         ha_client=self.ha,
                         TYPE_OBJECT_NAME_MAP=TYPE_OBJECT_NAME_MAP,
                         on_frame_click=self.frame_clicked,
                         on_icon_click=self.frame_icon_clicked
                     )
                    group_layout.addWidget(frame, row, col)

                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue


#---------------------------------------------------------------------------------------

                elif etype == "fan":
                    frame = FanFrame(
                            eid=eid,
                            etype=etype,
                            itype=itype,
                            name=name,
                            ha_client=self.ha,
                            TYPE_OBJECT_NAME_MAP=TYPE_OBJECT_NAME_MAP,
                            on_icon_click=self.frame_icon_clicked,
                            on_frame_click=self.frame_clicked
                        )

                    group_layout.addWidget(frame, row, col)

                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue
#---------------------------------------------------------------------------------------

                elif etype == "cover":
                    frame = CoverFrame(
                                eid=eid,
                                etype=etype,
                                itype=itype,
                                name=name,
                                ha_client=self.ha,
                                TYPE_OBJECT_NAME_MAP=TYPE_OBJECT_NAME_MAP
                            )

                    group_layout.addWidget(frame, row, col)
                    col += 2
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue
#----------------------------------------------------------------------------------------------

                elif etype == "number_slider":
                    frame = NumberSliderFrame(
                             eid=eid,
                             etype=etype,
                             itype=itype,
                             name=name,
                             ha_client=self.ha,
                             TYPE_OBJECT_NAME_MAP=TYPE_OBJECT_NAME_MAP,
                             on_icon_click=self.frame_icon_clicked,
                             on_frame_click=self.frame_clicked
                         )

                    group_layout.addWidget(frame, row, col)
                    col += 2
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue
#------------------------------------------------------------------------------------

                elif etype == "thermostat":
                    frame = ThermostatFrame(
                            eid=eid,
                            etype=etype,
                            itype=itype,
                            name=name,
                            ha_client=self.ha,
                            TYPE_OBJECT_NAME_MAP=TYPE_OBJECT_NAME_MAP,
                            on_tile_click=self.frame_clicked,
                            on_icon_click=self.frame_icon_clicked
                        )

                    group_layout.addWidget(frame, row, col)
                    col += 2
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue
#------------------------------------------------------------------------------

                elif etype == "room_card":
                    frame = SensorRoomCard(
                        eid=eid,
                        etype=etype,
                        itype=itype,
                        name=name,
                        ha_client=self.ha,
                        TYPE_OBJECT_NAME_MAP=TYPE_OBJECT_NAME_MAP,
                        on_tile_click=self.frame_clicked,
                        on_icon_click=self.frame_icon_clicked
                        )

                    group_layout.addWidget(frame, row, col)

                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue
                    
#------------------------------------------------------------------------------

                elif etype == "sensor_chart":
                    frame = SensorChartFrame(
                        eid=eid,
                        etype=etype,
                        itype=itype,
                        name=name,
                        ha_client=self.ha,
                        TYPE_OBJECT_NAME_MAP=TYPE_OBJECT_NAME_MAP,
                        on_tile_click=self.frame_clicked,
                        on_icon_click=self.frame_icon_clicked
                        )

                    group_layout.addWidget(frame, row, col)

                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue


#------------------------------------------------------------------------------

                elif etype == "sensor_frame":
                    frame = SensorFrame(
                        eid=eid,
                        etype=etype,
                        itype=itype,
                        name=name,
                        ha_client=self.ha,
                        TYPE_OBJECT_NAME_MAP=TYPE_OBJECT_NAME_MAP,
                        on_tile_click=self.frame_clicked,
                        on_icon_click=self.frame_icon_clicked
                        )

                    group_layout.addWidget(frame, row, col)

                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue

#-------------------------------------------------------------------------


                elif etype == "todo":
                    frame = SensorTodo(
                        eid=eid,
                        etype=etype,
                        itype=itype,
                        name=name,
                        ha_client=self.ha,
                        TYPE_OBJECT_NAME_MAP=TYPE_OBJECT_NAME_MAP,
                        on_tile_click=self.frame_clicked,
                        on_icon_click=self.frame_icon_clicked
                        )

                    group_layout.addWidget(frame, row, col)

                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue

#-------------------------------------------------------------------------



                elif etype == "calendar":
                    frame = SensorCalendar(
                        eid=eid,
                        etype=etype,
                        itype=itype,
                        name=name,
                        ha_client=self.ha,
                        TYPE_OBJECT_NAME_MAP=TYPE_OBJECT_NAME_MAP,
                        on_tile_click=self.frame_clicked,
                        on_icon_click=self.frame_icon_clicked
                        )

                    group_layout.addWidget(frame, row, col)

                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue
                    



#-------------------------------------------------------------------------

                elif etype == "select":
                    frame = SelectFrame(
                                eid=eid,
                                etype=etype,
                                itype=itype,
                                name=name,
                                ha_client=self.ha,
                                TYPE_OBJECT_NAME_MAP=TYPE_OBJECT_NAME_MAP,
                                on_tile_click=self.frame_clicked,
                                on_icon_click=self.frame_icon_clicked
                            )


                    group_layout.addWidget(frame, row, col)

                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue

#-------------------------------------------------------------------------------------

                elif etype == "ha_connection":
                    frame = QWidget()
                    frame_layout = QVBoxLayout(frame)
                    frame_layout.setContentsMargins(0, 0, 0, 0)
                    frame_layout.setSpacing(0)
                    reconnect_btn = QPushButton("Połącz ponownie")
                    frame_layout.addWidget(reconnect_btn)

                    reconnect_btn.clicked.connect(lambda: self.window().reconnect_ha_tiles())

                    frame.setObjectName("ha_connection")

                    group_layout.addWidget(frame, row, col, 1, max_cols)
                    col += 2
                    if col >= max_cols:
                        col = 0
                        row += 1

                    self.entity_widgets[("ha_connection", "reconnect_btn")] = reconnect_btn
                    prev_etype_group = etype_group
                    continue

#----------------------------------------------------------------------------

                elif etype == "restart":
                    if col != 0:
                       row += 1
                       col = 0
                    frame = QWidget()
                    frame_layout = QVBoxLayout(frame)
                    frame_layout.setContentsMargins(0, 0, 0, 0)
                    frame_layout.setSpacing(0)

                    restart_btn = QPushButton("Restart OS")
                    restart_btn.setObjectName("close_button")
                    frame_layout.addWidget(restart_btn)

                    restart_btn.clicked.connect(lambda: self.window().restart_rpi())


                    group_layout.addWidget(frame, row, col, 1, 2)
                    col += 2
                    if col >= max_cols:
                        col = 0
                        row += 1

                    prev_etype_group = etype_group
                    continue

    
#-----------------------------------------------------------------------------

                else:
                    frame = QWidget()
                    frame.setObjectName("default")

                group_layout.addWidget(frame, row, col)

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

                prev_etype_group = etype_group


            if col != 0:
                remaining = max_cols - col
                for i in range(remaining):
                    spacer = QWidget()
                    spacer.setObjectName("spacer")
                    group_layout.addWidget(spacer, row, col + i)
                    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            group_layout.setRowStretch(row + 1, 1)  
            self.container_layout.addWidget(group_box)


    def update_entity_state(self, eid, state_obj):
        etype = self.entity_widget_types.get(eid, "")
        itype = self.entity_info_types.get((eid, "brightness"), "")

        state = state_obj.get("state")
        attrs = state_obj.get("attributes", {})

#------------------------------------------------------------------------
          
 
        if etype == "number":
            label = self.entity_widgets.get((eid, "label"))
            if label:
                try:
                    
                    label.setText(f"{float(state):.0f}")
                    print(label.setText(f"{float(state):.0f}"))
                except:
                    label.setText(str(state))



        temp_widget = self.entity_widgets.get((eid, "temp"))
        hue_widget = self.entity_widgets.get((eid, "hue"))




    def update_reconnect_button_status(self):
        reconnect_btn = self.entity_widgets.get(("ha_connection", "reconnect_btn"))
        if not reconnect_btn:
            return
        if self.ha.connected: 
            print("Connected")
            reconnect_btn = self.entity_widgets.get(("ha_connection", "reconnect_btn"))
            reconnect_btn.setStyleSheet("background-color: transparent ; color: white; border: 0px solid transparent;")
            reconnect_btn.setText("Connected")
        else:
            reconnect_btn = self.entity_widgets.get(("ha_connection", "reconnect_btn"))
            reconnect_btn.setStyleSheet("background-color: red ; color: white;")
            reconnect_btn.setText("Disconnected")
            print("Disconnected")


    def frame_clicked(self, eid, etype, itype):
        widget = self.entity_widgets.get(eid)
        if etype == "switch":
            self.toggle_switch(eid)  
        elif etype == "sensor_chart":
            self.toggle_sensor_chart(eid)
        elif etype == "more_info":
            self.toggle_sensor_chart(eid)
        elif etype == "light":
            self.toggle_light(eid)
        elif etype == "cover":
            self.toggle_cover(eid)
        elif etype == "todo":
            self.toggle_todo(eid) 
        elif etype == "calendar":
            self.toggle_calendar(eid)  
        else:
            print(eid)
       

    def frame_icon_clicked(self, eid, etype, itype, name):
        if etype == "light" and itype == "temp":
            show_temp_palette_popup(
                parent=self,
                eid=eid,
                itype=itype,
                name=name,
                entity_states=self.ha.entity_states,
                send_selected_temp=self.send_selected_temp,
                entity_info_types=self.entity_info_types,
            )

        elif etype == "light" and itype == "temp_color":
            show_temp_color_palette_popup(
                parent=self,
                eid=eid,
                itype=itype,
                name=name,
                entity_states=self.ha.entity_states,
                send_selected_temp=self.send_selected_temp,
                send_selected_color=self.send_selected_color,
                entity_info_types=self.entity_info_types
            )
            
        elif etype == "switch":
                self.toggle_switch(eid, True)
         

    def send_light_value_temp(self, eid, temp):
        self.ha.call_service("light", "turn_on", eid, {"color_temp": temp})
        if eid in self.debounce_timers:
          del self.debounce_timers[eid]
          
    def send_light_value_hue(self, eid, hue):
        self.ha.call_service("light", "turn_on", eid, {"hs_color": [hue, 100]})
        if eid in self.debounce_timers:
          del self.debounce_timers[eid]


    def restart_rpi(self):    
        print("reboot")
        os.system("sudo reboot")
        
    def toggle_sensor_chart(self, eid):
        if hasattr(self, "chart_window") and self.chart_window.isVisible():
            print("already open")
        else:
            self.chart_window = show_sensor_graph(eid)
            self.chart_window.show()
            self.chart_window.raise_()
            self.chart_window.activateWindow()

    def toggle_todo(self, eid):
        if hasattr(self, "todo") and self.todo.isVisible():
            print("already open")
        else:
            self.todo =  TodoListWindow(eid)
            self.todo.show()
            self.todo.raise_()
            self.todo.activateWindow()
 
    def toggle_calendar(self, eid):
        if hasattr(self, "todo") and self.todo.isVisible():
            print("already open")
        else:
            self.todo =  CalendarMonth(eid)
            self.todo.show()
            self.todo.raise_()
            self.todo.activateWindow()
            
    def handle_disconnected(self):
        if not self.reconnect_timer.isActive():
            print("another try after 10 sec")
            self.reconnect_timer.start(10000)

    def try_reconnect(self):
        if not self.ha.connected:
            print("reconnect")
            self.ha.connect()
        else:
            self.reconnect_timer.stop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    json_path = sys.argv[1]

    app = QApplication(sys.argv)
    window = HAControlUIRoom(json_path)
    window.show()
    sys.exit(app.exec_())
