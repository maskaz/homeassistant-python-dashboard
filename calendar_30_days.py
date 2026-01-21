import sys
import os
import requests
import calendar
from datetime import date, timedelta
from dateutil import parser
from configparser import ConfigParser

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton
)
from PyQt5.QtCore import Qt

# ------------------------ QSS ------------------------
def get_style_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "styles.qss")

def load_stylesheet():
    with open(get_style_path(), "r", encoding="utf-8") as f:
        return f.read()

def get_config_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, "config.ini")

# Wczytywanie pliku konfiguracyjnego
config_path = get_config_path()
config_object = ConfigParser()
config_object.read(config_path)

if "ha" not in config_object:
    print("no [ha] inside config2.ini!")
    sys.exit(1)
    
config = config_object["ha"]
HA_TOKEN = config["ha_token"]
HA_URL = config["ha_ip"]
config_2 = config_object["settings"]
screen_settings = config_2["screen"]



HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json"
}

# ------------------------ POBIERANIE WYDARZEŃ ------------------------
def pobierz_wydarzenia_miesiac(eid):
    url = f"{HA_URL}/api/states/{eid}"
    events_by_day = {}

    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code != 200:
            return events_by_day

        data = r.json()
        events = data.get("attributes", {}).get("events", [])
        print(events)

        for ev in events:
            start_str = ev.get("start")
            end_str = ev.get("end")
            if not start_str or not end_str:
                continue

            start_dt = parser.isoparse(start_str)
            end_dt = parser.isoparse(end_str)
            if end_dt < start_dt:
                end_dt = start_dt

            current_day = start_dt.date()
            last_day = end_dt.date()

            while current_day <= last_day:
                hour_str = start_dt.strftime("%H:%M") if current_day == start_dt.date() else "00:00"
                events_by_day.setdefault(current_day, []).append({
                    "hour": hour_str,
                    "title": ev.get("summary", ""),
                    "desc": ev.get("description", "")
                })
                current_day += timedelta(days=1)

        return events_by_day

    except Exception as e:
        print("Błąd pobierania wydarzeń:", e)
        return {}

# ------------------------ WIDGET DNIA ------------------------
DNI_TYG = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]



class DayWidget(QWidget):
    def __init__(self, day_date, events=None, is_today=False, today=None):
        super().__init__()

        events = events or []
        today = today or date.today()

        # Styl dla dnia
        if is_today and events:
            self.setObjectName("calendar_day_today_event")
        elif is_today:
            self.setObjectName("calendar_day_today")
        elif events:
            self.setObjectName("calendar_day_event")
        else:
            self.setObjectName("calendar_day")
        self.setAttribute(Qt.WA_StyledBackground, True)

        # Główny layout pionowy
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(5)

        # Numer dnia + dzień tygodnia + ile dni do wydarzenia
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)
        
        # Liczba dni do wydarzenia
        delta_days = (day_date - today).days
        if delta_days == 0:
           delta_text = ", Today!"
        elif delta_days >= 0:
           delta_text = f", in {delta_days} days" 
        else:
           delta_text = "(past)"


        dd = str(day_date.day)
        mm = str(day_date.month)
        d_m = f"{dd}/{mm}"
        lbl_day = QLabel(d_m)
        lbl_day.setObjectName("calendar_day_number")
        lbl_day.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        dni = DNI_TYG[day_date.weekday()]
        dni_dni = f"{dni}{delta_text}"
        lbl_weekday = QLabel(dni_dni)
        lbl_weekday.setObjectName("calendar_weekday")
        lbl_weekday.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        header_layout.addWidget(lbl_day)
        header_layout.addWidget(lbl_weekday)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Każde wydarzenie w osobnym QWidget
        for ev in events:
            ev_widget = QWidget()
            ev_widget.setObjectName("calendar_event_widget")
            ev_widget.setAttribute(Qt.WA_StyledBackground, True)
            ev_widget.setFixedHeight(70)  # stała wysokość dla każdego wydarzenia

            ev_layout = QHBoxLayout(ev_widget)
            ev_layout.setContentsMargins(2, 10, 12, 10)
            ev_layout.setSpacing(5)

            lbl_hour = QLabel(f"{ev['hour']} ")
            lbl_hour.setObjectName("calendar_event_hour")
            lbl_hour.setFixedWidth(80)
            lbl_hour.setFixedHeight(50)
            lbl_hour.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            lbl_title = QLabel(f"{ev['title']}")
            lbl_title.setObjectName("calendar_event_title")
            lbl_title.setFixedHeight(70)
            lbl_title.setWordWrap(True)
            lbl_title.setAlignment(Qt.AlignLeft | Qt.AlignTop)

            lbl_desc = QLabel(f"{ev['desc']}")
            lbl_desc.setObjectName("calendar_event_title")
            lbl_desc.setFixedHeight(70)
            lbl_desc.setWordWrap(True)
            lbl_desc.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            
            ev_layout.addWidget(lbl_hour)
            ev_layout.addWidget(lbl_title)
            ev_layout.addWidget(lbl_desc)
            ev_layout.addStretch()

            main_layout.addWidget(ev_widget)



# ------------------------ OKNO GŁÓWNE ------------------------
class CalendarMonth(QMainWindow):
    def __init__(self, eid):
        super().__init__()
        self.eid = eid
        global screen_settings
        self.setWindowTitle("Calendar")
        self.setGeometry(100, 100, 768, 1024)
        self.setObjectName("calendar_main")

        if screen_settings == "full":
            self.setWindowFlag(Qt.FramelessWindowHint)
            self.showFullScreen()
            print("full screen")
        else:
            print("no full screen")
            
        self.stylesheet = load_stylesheet()
        self.setStyleSheet(self.stylesheet)
        
        self.today = date.today()
        self.events = pobierz_wydarzenia_miesiac(self.eid)

        central = QWidget()
        central.setObjectName("calendar_central")
        central.setAttribute(Qt.WA_StyledBackground, True)
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        header = QLabel(self.today.strftime("%d/%m/%Y - %A"))
        header.setAlignment(Qt.AlignCenter)
        header.setObjectName("calendar_header")
        main_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)

        scroll_content = QWidget()
        scroll_content.setObjectName("calendar_scroll_content")
        scroll_content.setAttribute(Qt.WA_StyledBackground, True)

        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll_layout.setSpacing(14)

        # Pokazujemy tylko dni z wydarzeniami
        start_date = self.today
        end_date = self.today + timedelta(days=60)

        for d, events in sorted(self.events.items()):
            if d < start_date or d > end_date:
                continue

            scroll_layout.addWidget(
                DayWidget(
                    day_date=d,
                    events=events,
                    is_today=(d == self.today),
                    today=self.today
                )
            )

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)

        btn_close = QPushButton("Zamknij")
        btn_close.setObjectName("close_button")
        btn_close.setFixedHeight(48)
        btn_close.clicked.connect(self.close)
        main_layout.addWidget(btn_close)

# ------------------------ START ------------------------
#if __name__ == "__main__":
#    app = QApplication(sys.argv)

#    try:
#        app.setStyleSheet(load_stylesheet())
#    except Exception as e:
#        print("Nie można wczytać QSS:", e)

#    win = CalendarMonth()
#    win.show()
#    sys.exit(app.exec_())

