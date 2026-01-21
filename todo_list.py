import sys
import os
import json
from websocket import create_connection
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton,
    QLineEdit, QMessageBox, QSizePolicy, QMenu
)
from PyQt5.QtCore import Qt
from configparser import ConfigParser


# ---------------- CONFIG ----------------
def get_config_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "config.ini")

config = ConfigParser()
config.read(get_config_path())

HA_TOKEN = config["ha"]["ha_token"]
HA_WS_URL = config["ha"]["ha_ip_ws"]

screen_settings = config["settings"]["screen"]



# ---------------- STYLE ----------------
def get_style_path():
    base = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    return os.path.join(base, "styles.qss")

def load_stylesheet():
    with open(get_style_path(), "r", encoding="utf-8") as f:
        return f.read()

# ---------------- HA HELPERS ----------------
def auth(ws):
    ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
    while json.loads(ws.recv()).get("type") != "auth_ok":
        pass

def pobierz_todo_needs_action():
    ws = create_connection(HA_WS_URL)
    auth(ws)
    ws.send(json.dumps({
        "type": "call_service",
        "domain": "todo",
        "service": "get_items",
        "target": {"entity_id": TODO_ENTITY},
        "return_response": True,
        "id": 1
    }))
    result = json.loads(ws.recv())
    ws.close()
    items = result["result"]["response"][TODO_ENTITY]["items"]
    return [i["summary"] for i in items if i["status"] == "needs_action"]

def dodaj_todo(summary):
    if not summary.strip():
        return False
    ws = create_connection(HA_WS_URL)
    auth(ws)
    ws.send(json.dumps({
        "type": "call_service",
        "domain": "todo",
        "service": "add_item",
        "target": {"entity_id": TODO_ENTITY},
        "service_data": {"item": summary},
        "id": 1
    }))
    result = json.loads(ws.recv())
    ws.close()
    return result.get("success", False)

def usun_todo(summary):
    ws = create_connection(HA_WS_URL)
    auth(ws)
    ws.send(json.dumps({
        "type": "call_service",
        "domain": "todo",
        "service": "remove_item",
        "target": {"entity_id": TODO_ENTITY},
        "service_data": {"item": summary},
        "id": 1
    }))
    result = json.loads(ws.recv())
    ws.close()
    return result.get("success", False)

# ---------------- TASK WIDGET ----------------
class TaskWidget(QWidget):
    def __init__(self, summary, parent_window):
        super().__init__()
        self.summary = summary
        self.parent_window = parent_window

        self.setObjectName("todo_object_widget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)

        lbl_title = QLabel(f"󰨕  {summary}")
        lbl_title.setObjectName("todo_object")
        lbl_title.setWordWrap(True)
        lbl_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(lbl_title)

        # PRZYCISK – KLIK = USUŃ (OD RAZU)
        btn_delete = QPushButton("󰅚")
        btn_delete.setFixedSize(40, 40)
        btn_delete.setObjectName("element_usun")
        btn_delete.clicked.connect(self.delete_item)
        layout.addWidget(btn_delete)

    def delete_item(self):
        if usun_todo(self.summary):
            self.parent_window.odswiez_liste()


# ---------------- ONSCREEN KEYBOARD ----------------
class OnScreenKeyboard(QWidget):
    def __init__(self, target, add_callback):
        super().__init__()
        self.target = target
        self.add_callback = add_callback

        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Pierwszy wiersz
        row1 = QHBoxLayout()
        for c in "1234567890":
            b = QPushButton(c)
            b.setObjectName("element_klawiatura")
            b.clicked.connect(lambda _, x=c: self.target.insert(x))
            row1.addWidget(b)
        layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        for c in "qwertyuiop":
            b = QPushButton(c)
            b.setObjectName("element_klawiatura")
            b.clicked.connect(lambda _, x=c: self.target.insert(x))
            row2.addWidget(b)
        layout.addLayout(row2)

        # Drugi wiersz
        row3 = QHBoxLayout()
        for c in "asdfghjkl":
            b = QPushButton(c)
            b.setObjectName("element_klawiatura")
            b.clicked.connect(lambda _, x=c: self.target.insert(x))
            row3.addWidget(b)
        layout.addLayout(row3)

        # Trzeci wiersz: zxcvbnm + BACKSPACE
        row4 = QHBoxLayout()
        for c in "zxcvbnm":
            b = QPushButton(c)
            b.setObjectName("element_klawiatura")
            b.clicked.connect(lambda _, x=c: self.target.insert(x))
            row4.addWidget(b)

        bk = QPushButton(" 󰧙 ")
        bk.setObjectName("element_klawiatura")
        bk.clicked.connect(lambda: self.target.setText(self.target.text()[:-1]))
        row4.addWidget(bk)
        layout.addLayout(row4)

        # Ostatni wiersz: SPACJA + DODAJ
        row5 = QHBoxLayout()

        sp = QPushButton("󱊔")
        sp.setObjectName("element_klawiatura")
        sp.clicked.connect(lambda: self.target.insert(" "))
        row5.addWidget(sp)

        add = QPushButton("󰿶")
        add.setObjectName("element_klawiatura")
        add.setFixedWidth(100)
        add.clicked.connect(self.add_callback)
        row5.addWidget(add)

        layout.addLayout(row5)



# ---------------- MAIN WINDOW ----------------
class TodoListWindow(QMainWindow):
    def __init__(self, eid):
        super().__init__()


        global TODO_ENTITY
        TODO_ENTITY = eid
        global screen_settings
        self.setWindowTitle(f"{eid}")
        self.setGeometry(100, 100, 768, 1024)
        if screen_settings == "full":
            self.setWindowFlag(Qt.FramelessWindowHint)
            self.showFullScreen()
            print("full screen")
        else:
            print("no full screen")
        self.setStyleSheet(load_stylesheet())            

        self.eid = eid
        print(eid)
        central = QWidget()
        central.setObjectName("calendar_central")
        central.setAttribute(Qt.WA_StyledBackground, True)
        self.setCentralWidget(central)

        self.layout = QVBoxLayout(central)

        header = QLabel("Za.kupy")
        header.setAlignment(Qt.AlignCenter)
        header.setObjectName("calendar_header")
        self.layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout.addWidget(self.scroll)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll.setWidget(self.scroll_content)

        self.input = QLineEdit()
        self.input.setObjectName("wpisz")
        self.layout.addWidget(self.input)
     #   self.input.hide()

        self.keyboard = OnScreenKeyboard(self.input, self.dodaj)
        self.layout.addWidget(self.keyboard)
     #   self.keyboard.hide()


        lbl_gap = QLabel(" ")
        lbl_gap.setObjectName("todo_object")
        lbl_gap.setWordWrap(True)
        lbl_gap.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.layout.addWidget(lbl_gap)
        
     #   toggle = QPushButton("Pokaż / Ukryj klawiaturę")
    #    toggle.clicked.connect(self.toggle_keyboard)
    #    self.layout.addWidget(toggle)

        btn_close = QPushButton("Zamknij")
        btn_close.setObjectName("close_button")
        btn_close.setFixedHeight(48)
        btn_close.clicked.connect(self.close)
        self.layout.addWidget(btn_close)

        self.odswiez_liste()

    def toggle_keyboard(self):
        v = not self.keyboard.isVisible()
        self.keyboard.setVisible(v)
        self.input.setVisible(v)
        self.btn_add.setVisible(v)

    def odswiez_liste(self):
        while self.scroll_layout.count():
            w = self.scroll_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        for t in pobierz_todo_needs_action():
            self.scroll_layout.addWidget(TaskWidget(t, self))
        self.scroll_layout.addStretch()

    def dodaj(self):
        if dodaj_todo(self.input.text()):
            self.input.clear()
            self.odswiez_liste()

