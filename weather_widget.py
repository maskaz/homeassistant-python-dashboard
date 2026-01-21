import json
import os
import sys
import requests
from datetime import datetime, date, timedelta
from configparser import ConfigParser
from dateutil import parser
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap



today = datetime.now()
date_key = today.strftime("%d%m")

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
    print("no [ha] inside config2.ini!")
    sys.exit(1)

config = config_object["ha"]

HA_TOKEN = config["ha_token"]
HA_IP = config["ha_ip"]

headers = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}


what_weather = 1  





def pobierz_pogode_godzinowa():
    url = f"{HA_IP}/api/states/sensor.pogoda_godzinowa"
    try:
        response = requests.get(url, headers=headers)
        forecast_dict = {}
        if response.status_code == 200:
            data = response.json()
            attributes = data.get("attributes", {})
            forecast = attributes.get("forecast", [])
            for idx, day in enumerate(forecast[:10], start=1):
                dt = datetime.fromisoformat(day["datetime"])
                godz = dt.strftime("%H:%M:%S")
                forecast_dict[f"godzina_{idx}"] = {
                    "godzina": godz,
                    "conditions": day["condition"],
                    "temperatura": day["temperature"],
                    "wiatr": day["wind_speed"],
                    "zachmurzenie": day["cloud_coverage"],
                    "wilgotnosc": day["humidity"]
                    
                    
                }
        else:
            forecast_dict = {"godzina_1": {"godzina": "puste"}}
        return json.dumps(forecast_dict, ensure_ascii=False, indent=2)
    except Exception:
        forecast_dict = {"godzina_1": {"godzina": "puste"}}
        return json.dumps(forecast_dict, ensure_ascii=False, indent=2)


def pobierz_pogode_dzienna():
    url = f"{HA_IP}/api/states/sensor.pogoda_dzienna"
    try:
        response = requests.get(url, headers=headers)
        forecast_dict = {}
        if response.status_code == 200:
            data = response.json()
            attributes = data.get("attributes", {})
            forecast = attributes.get("forecast", [])
            for idx, day in enumerate(forecast[:7], start=1):
                dt = datetime.fromisoformat(day["datetime"])
                time_only = dt.strftime("%d/%m/%Y")
                match idx:
                    case 1: time_only = "today"
                    case 2: time_only = "tomorrow"
                    case 3: time_only = (date.today() + timedelta(days=idx-1)).strftime("%A")
                    case 4: time_only = (date.today() + timedelta(days=idx-1)).strftime("%A")
                    case 5: time_only = (date.today() + timedelta(days=idx-1)).strftime("%A")
                forecast_dict[f"dzien_{idx}"] = {
                    "data": time_only,
                    "conditions": day.get("condition", ""),
                    "temperatura_max": day.get("temperature", ""),
                    "temperatura_min": day.get("templow", ""),
                    "rainfall": day.get("precipitation", ""),
                    "direction_wiatru": day.get("wind_bearing", "")
                }
        return json.dumps(forecast_dict, ensure_ascii=False, indent=2)
    except Exception:
        return json.dumps({}, ensure_ascii=False, indent=2)


def pobierz_meteoalarm():
    url = f"{HA_IP}/api/states/binary_sensor.meteoalarm"
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code != 200:
            return ""
        data = r.json()
      #  print(data)
        poziom = data.get("attributes", {}).get("event", "")
        sam_poziom = poziom.split()[0]
        opis = data.get("attributes", {}).get("description", "")
        dane_alarmowe = (f"{sam_poziom}: {opis}")
        return dane_alarmowe
    except Exception as e:
        print("Błąd meteoalarm:", e)
        return ""

def pobierz_sensor_na_parapecie(eid):
    url = f"{HA_IP}/api/states/{eid}"

    try:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            state = 0
            return json.dumps({"temperatura": state}, ensure_ascii=False, indent=2)
       
        data = response.json()
        state = data.get("state", 0)
        return json.dumps({"temperatura": state}, ensure_ascii=False, indent=2)

    except Exception:
        state = 0
        return json.dumps({"temperatura": state}, ensure_ascii=False, indent=2)
        
class KlikalnyWidget(QWidget):
    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.callback = callback

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.callback()
            
class Pogoda(QWidget):
    weather_icons_lokalizacja = os.path.join(os.path.dirname(__file__), "weather_icons")

    weather_icons = {
    "sunny": "sunny.png",
    "partlycloudy": "partial_cloud.png",
    "cloudy": "cloudy.png",
    "rainy": "rainy.png",
    "pouring": "pouring.png",
    "snowy": "snowy.png",
    "fog": "fog.png",
    "clear-night": "clear-night.png",
    "lightning": "lightning.png",
    "lightning-rainy": "lightning-rainy.png",
    "windy": "windy.png",
    "windy-variant": "windy.png",
    "snowy-rainy": "snowy-rainy.png",
    "hail": "hail.png",
    "exceptional": "exceptional.png",
    }

    tlum = {
        "sunny": "Słonecznie",
        "partlycloudy": "Częściowe zachmurzenie",
        "cloudy": "Pochmurno",
        "rainy": "Deszczowo",
        "pouring": "Ulewa",
        "snowy": "Śnieżnie",
        "fog": "Mgła",
        "clear-night": "Noc - czyste niebo",
        "lightning": "Burza",
        "lightning-rainy": "Burza z deszczem",
        "windy": "Wietrznie",
        "windy-variant": "Wietrznie z chmurami",
        "snowy-rainy": "Deszcz ze śniegiem",
        "hail": "Grad",
        "exceptional": "Wyjątkowe conditions"
    }


    def __init__(self, eid=None, parent=None):
        super().__init__(parent)
        self.eid = eid

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)


        
        

        self.left_box = QVBoxLayout()
        self.left_box.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.left_box)

        self.more_weather_widget = KlikalnyWidget(self._toggle_weather)


        self.more_weather_box = QHBoxLayout(self.more_weather_widget)
        self.more_weather_box.setContentsMargins(0, 10, 0, 5)
        self.more_weather_box.setSpacing(0)

        self.main_layout.addWidget(self.more_weather_widget)
        

        self.refresh()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(10000)


        
    def _set_png_icon(self, label: QLabel, warunek: str, size: int):
        filename = self.weather_icons.get(warunek)
        if not filename:
            label.clear()
            return

        path = os.path.join(self.weather_icons_lokalizacja, filename)
        if not os.path.exists(path):
            label.clear()
            return
        label.setFixedSize(size, size)
        pix = QPixmap(path).scaled(
            size,
            size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        label.setPixmap(pix)
        label.setAlignment(Qt.AlignCenter)
        
        
    def refresh(self):
        if what_weather == 1:
            self._show_main_weather()
        else:
            self._show_main_weather()
        self._show_change_weather()

        self._clock_update()

   
    
    
    def _clock_update(self):
        now = datetime.now().strftime("%H:%M  %d.%m.%Y")
        if hasattr(self, "lbl_clock"):
            self.lbl_clock.setText(now)

    # ------------------------------------------------------------

    def _show_main_weather(self):
        for box in [self.left_box]:
            while box.count():
                item = box.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        data_godz = json.loads(pobierz_pogode_godzinowa())
        data_dzien = json.loads(pobierz_pogode_dzienna())
        data_sensor = json.loads(pobierz_sensor_na_parapecie(self.eid))
        temp_zew = godz = data_sensor.get("temperatura")
        if isinstance(temp_zew, float):
           temp_zew = float(temp_zew)
           temp_zew = (round(temp_zew,1))
        else:
            temp_zew = str(temp_zew)


        godz = data_godz.get("godzina_2", {}).get("godzina", "")
        war = data_godz.get("godzina_2", {}).get("conditions", "")
        temp = data_godz.get("godzina_2", {}).get("temperatura", "")
        wia = data_godz.get("godzina_2", {}).get("wiatr", "")
        chmury = data_godz.get("godzina_2", {}).get("zachmurzenie", "")
        

        first_day = data_dzien.get("dzien_1", {})
        data_str = first_day.get("data", "")
        war_dzien = first_day.get("conditions", "")
        temp_max = first_day.get("temperatura_max", "")
        temp_min = first_day.get("temperatura_min", "")
        deszcz = first_day.get("rainfall", "")
        wiatr_direction = first_day.get("direction_wiatru", "")
        wiatr_direction = int(wiatr_direction)
        print(wiatr_direction)


        direction_arrow_ = {
    **{i: "󰧇" for i in range(0, 45)},
    **{i: "󰧅" for i in range(45, 90)},
    **{i: "󰧂" for i in range(90, 135)},
    **{i: "󰦹" for i in range(135, 180)},
    **{i: "󰦿" for i in range(180, 225)},
    **{i: "󰦷" for i in range(225, 270)},
    **{i: "󰧀" for i in range(270, 315)},
    **{i: "󰧃" for i in range(315, 360)},
}


        arrow_ = direction_arrow_.get(wiatr_direction, "?")  
        print(f"direction {wiatr_direction}°: {arrow_}")

        main_widget = KlikalnyWidget(self._show_change_weather)
        main_widget.setFixedHeight(80)
        main_widget.setObjectName("en_weather_widget")
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        lbl_i = QLabel()
        self._set_png_icon(lbl_i, war, 80)
        lbl_i.setObjectName("en_weather_icon_big")
        lbl_i.setAlignment(Qt.AlignCenter)
        lbl_i.setFixedWidth(130)
        lbl_i.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(lbl_i)

        right_widget = QWidget()
        right_widget.setObjectName("en_weather_col")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        clock_row = QWidget()
        clock_row.setObjectName("en_weather_col")
        clock_layout = QHBoxLayout(clock_row)
        clock_layout.setContentsMargins(0, 0, 0, 0)
        clock_layout.setSpacing(0)

        lbl_temp_side_clock = QLabel(f"{temp_zew}°C")
        lbl_temp_side_clock.setObjectName("en_weather_big_value")
        lbl_temp_side_clock.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.lbl_clock = QLabel()
        self.lbl_clock.setContentsMargins(0,0,0,0)
        self.lbl_clock.setObjectName("en_weather_big_date")
        self.lbl_clock.setAlignment(Qt.AlignRight | Qt.AlignVCenter)


        clock_layout.addWidget(lbl_temp_side_clock)
        clock_layout.addStretch()
        clock_layout.addWidget(self.lbl_clock)
        right_layout.addWidget(clock_row)
    
        row1 = QWidget()
        row1.setObjectName("en_weather_col")
        row1_layout = QHBoxLayout(row1)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(0)
        
        conditions = self.tlum.get(war, "")
        lbl_conditions = QLabel(f"Net temp: {temp}°C")  
        lbl_conditions.setObjectName("en_weather_small_info")
        lbl_conditions.setAlignment(Qt.AlignLeft)

        lbl_rainfall = QLabel(f"Speed: {wia} km/h | direction: {arrow_}")
        lbl_rainfall.setObjectName("en_weather_small_info")
        lbl_rainfall.setAlignment(Qt.AlignRight)

        row1_layout.addWidget(lbl_conditions)
        row1_layout.addStretch()
        row1_layout.addWidget(lbl_rainfall)

        row2 = QWidget()
        row2.setObjectName("en_weather_col")
        row2_layout = QHBoxLayout(row2)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(10)

        lbl_temp_min = QLabel(f"Min {temp_min}°C")
        lbl_temp_min.setObjectName("en_weather_temp_min")
        lbl_temp_min.setAlignment(Qt.AlignLeft)

        lbl_temp_max = QLabel(f"Max {temp_max}°C")
        lbl_temp_max.setObjectName("en_weather_temp_max")
        lbl_temp_max.setAlignment(Qt.AlignLeft)

        row2_layout.addWidget(lbl_temp_min)
        row2_layout.addWidget(lbl_temp_max)


        lbl_temp_day = QLabel(f"{conditions} | Clouds:  {chmury}% | Percip:  {deszcz} mm")
        lbl_temp_day.setObjectName("en_weather_small_info")
        lbl_temp_day.setAlignment(Qt.AlignRight)

        row2_layout.addStretch()
        row2_layout.addWidget(lbl_temp_day)

        right_layout.addWidget(row2)
        right_layout.addWidget(row1)
        main_layout.addWidget(right_widget)
        self.left_box.addWidget(main_widget)

    def _show_change_weather(self):
        if not hasattr(self, "more_weather_box"):
            return

        while self.more_weather_box.count():
            item = self.more_weather_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # --- PRZYCISK JAKO PIERWSZA KOLUMNA ---

    
        if what_weather == 1:
            self._wyswietl_pogode_godzinowa()
        else:
            self._wyswietl_pogode_dzienna()

    def _toggle_weather(self):
        global what_weather
        what_weather = 2 if what_weather == 1 else 1
        self._show_change_weather()

    # ------------------------------------------------------------
    def _wyswietl_pogode_godzinowa(self):
        data = json.loads(pobierz_pogode_godzinowa())
        weather_left_height = 90


        
        for i in range(2, 7):
            blok = data.get(f"godzina_{i}", {})
            godz = blok.get("godzina", "")
            war = blok.get("conditions", "")
         #   print(war)
            temp = blok.get("temperatura", "")

            kol = QWidget()
            kol.setFixedHeight(weather_left_height)
            if i < 6:
               kol.setObjectName("en_weather_widget_col")
            else:
               kol.setObjectName("en_weather_widget")
            lay = QVBoxLayout(kol)
            lay.setContentsMargins(0, 0, 1, 0)
            lay.setSpacing(0)

            lbl_g = QLabel(godz)
            lbl_g.setObjectName("en_weather_hour")
            lbl_g.setAlignment(Qt.AlignHCenter)
            lbl_g.setFixedHeight(20)
            
            lbl_i = QLabel()
            self._set_png_icon(lbl_i, war, 40)
            lbl_i.setObjectName("en_weather_icon")
            lbl_i.setFixedWidth(74)
            lbl_i.setAlignment(Qt.AlignHCenter)
            lbl_i.setFixedHeight(44) 
            

            lbl_t = QLabel(f"{temp}°C")
            lbl_t.setObjectName("en_weather_temp")
            lbl_t.setAlignment(Qt.AlignHCenter)

            for lbl in [lbl_g, lbl_i, lbl_t]:
        #    for lbl in [lbl_g, lbl_i, lbl_w, lbl_t]:
                lay.addWidget(lbl, alignment=Qt.AlignHCenter | Qt.AlignVCenter)

            self.more_weather_box.addWidget(kol)



    def _wyswietl_pogode_dzienna(self):
        data = json.loads(pobierz_pogode_dzienna())
        weather_left_height = 90

        for i in range(1, 6):
            blok = data.get(f"dzien_{i}", {})
            data_str = blok.get("data", "")
            war = blok.get("conditions", "")
            temp_max = blok.get("temperatura_max", "")
            temp_min = blok.get("temperatura_min", "")

            kol = QWidget()
            kol.setFixedHeight(weather_left_height)
            if i < 5:
               kol.setObjectName("en_weather_widget_col")
            else:
               kol.setObjectName("en_weather_widget")
            lay = QVBoxLayout(kol)
            lay.setContentsMargins(0, 0, 1, 0)
            lay.setSpacing(0)

            lbl_data = QLabel(data_str)
            lbl_data.setObjectName("en_weather_hour")
            lbl_data.setAlignment(Qt.AlignHCenter)
            lbl_data.setFixedHeight(20) 
            
            lbl_i = QLabel()
            self._set_png_icon(lbl_i, war, 40)
            lbl_i.setFixedWidth(74)
            lbl_i.setObjectName("en_weather_icon")
            lbl_i.setAlignment(Qt.AlignHCenter)
            lbl_i.setFixedHeight(44) 
            

            lbl_t = QLabel(f"{temp_min}°C / {temp_max}°C")
            lbl_t.setObjectName("en_weather_temp")
            lbl_t.setAlignment(Qt.AlignHCenter)

            for lbl in [lbl_data, lbl_i, lbl_t]:
       #     for lbl in [lbl_data, lbl_i, lbl_w, lbl_t]:
                lay.addWidget(lbl, alignment=Qt.AlignHCenter | Qt.AlignVCenter)

            self.more_weather_box.addWidget(kol)


 


