import sys
import math
import os
import numpy as np
from datetime import datetime, timedelta
import requests
from configparser import ConfigParser

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QSizePolicy, QProgressBar
from PyQt5.QtCore import QTimer, Qt
from PyQt5 import QtWidgets
from PyQt5.QtGui import QFont
import pyqtgraph as pg

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
    print("no config.ini!")
    sys.exit(1)


HA_TOKEN = config_object["ha"]["ha_token"]
HA_URL = config_object["ha"]["ha_ip"]
screen_settings = config_object["settings"]["screen"]

def load_stylesheet(path):
    with open(path, "r") as file:
        return file.read()

class VerticalAxis(pg.AxisItem):
    def __init__(self, orientation='bottom'):
        super().__init__(orientation=orientation)
        self._angle = -90
        self._height_updated = False

    def tickStrings(self, values, scale, spacing):
        return [datetime.fromtimestamp(value).strftime("%H:%M") for value in values]

    def drawPicture(self, p, axisSpec, tickSpecs, textSpecs):
        super().drawPicture(p, axisSpec, tickSpecs, [])
        font = QFont("Arial", 10)
        p.setFont(font)
        p.setPen(self.pen())
        max_width = 0
        self._angle = self._angle % -180
        for rect, flags, text in textSpecs:
            p.save()
            p.translate(rect.center())
            p.rotate(self._angle)
            p.translate(-rect.center())
            x_offset = math.ceil(math.fabs(math.sin(math.radians(self._angle)) * rect.width()))
            if self._angle < 0:
                x_offset = -x_offset
            p.translate(x_offset / 2, 0)
            p.drawText(rect, flags, text)
            p.restore()
            offset = math.fabs(x_offset)
            max_width = offset if max_width < offset else max_width
        if not self._height_updated:
            self.setHeight(self.height() + max_width)
            self._height_updated = True

def get_sensor_history(sensor_id):
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }

    meta_url = f"{HA_URL}/api/states/{sensor_id}"
    meta_response = requests.get(meta_url, headers=headers)
    if meta_response.status_code != 200:
        raise Exception(f"Metadata error: {meta_response.status_code}")
    meta_data = meta_response.json()

    is_binary = sensor_id.startswith("binary_sensor.") or meta_data.get("attributes", {}).get("device_class") in ["window", "door", "opening"]

    now_utc = datetime.utcnow()
    now = now_utc + timedelta(hours=2)
    start = now - timedelta(hours=4)
    start_iso = start.isoformat()
    end_iso = now.isoformat()

    url = f"{HA_URL}/api/history/period/{start_iso}?end_time={end_iso}&filter_entity_id={sensor_id}&significant_changes=true"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"error: {response.status_code} – {response.text}")

    data = response.json()
    timestamps, values = [], []

    for entry in data[0]:
        try:
            timestamp = datetime.fromisoformat(entry['last_updated'].replace('Z', '+00:00'))
            state_str = entry['state'].lower()

            if is_binary:
                state_map = {"on": 1, "off": 0, "open": 1, "closed": 0}
                if state_str in state_map:
                    value = state_map[state_str]
                else:
                    continue
            else:
                value = float(entry['state'])

            timestamps.append(timestamp)
            values.append(value)
        except (ValueError, KeyError):
            continue
    return timestamps, values, is_binary

class SensorChartWindow(QtWidgets.QMainWindow):
    def __init__(self, sensor_id):
        super().__init__()
        global screen_settings
        self.setWindowTitle(f"History: {sensor_id}")
        self.setGeometry(100, 100, 768, 1024)
        if screen_settings == "full":
            self.setWindowFlag(Qt.FramelessWindowHint)
            self.showFullScreen()
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.setStyleSheet(load_stylesheet("styles.qss"))

        self.sensor_id = sensor_id
        self.progress_value = 0


        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)


        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 12px; padding: 5px;")
        self.layout.addWidget(self.info_label)
        self.info_label.setFixedHeight(50)


        self.loader_widget = QWidget(self.central_widget)
        loader_layout = QVBoxLayout(self.loader_widget)
        loader_layout.setAlignment(Qt.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedSize(200, 20)
        loader_layout.addWidget(self.progress_bar)

        self.layout.addWidget(self.loader_widget)


        self.plot_widget = pg.PlotWidget(axisItems={'bottom': VerticalAxis(orientation='bottom')})
        self.plot_widget.setBackground('#141a28')
        self.plot_widget.hide()
        self.layout.addWidget(self.plot_widget)


        self.close_btn = QPushButton("Close")
        self.close_btn.setObjectName("close_button")
        self.close_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.close_btn.setFixedHeight(60)
        self.close_btn.clicked.connect(self.close)
        self.layout.addWidget(self.close_btn)


        self.progress_timer = QTimer()
        self.progress_timer.setInterval(5)
        self.progress_timer.timeout.connect(self._update_progress)
        self.progress_timer.start()

        QTimer.singleShot(0, self.refresh_data)

    def _update_progress(self):
        self.progress_value += 1
        self.progress_bar.setValue(self.progress_value)

        if self.progress_value >= 100:
            self.progress_timer.stop()
            self.loader_widget.hide()
            self.plot_widget.show()

    def refresh_data(self):
        try:
            self.timestamps, self.values, self.is_binary = get_sensor_history(self.sensor_id)
        except Exception as e:
            print(f"error: {e}")
            self.timestamps, self.values, self.is_binary = [], [], False
        self.update_plot()

    def update_plot(self):
        self.plot = self.plot_widget.getPlotItem()
        self.plot.clear()
        self.plot.showGrid(x=True, y=True)

        if not self.timestamps or not self.values:
            self.info_label.setText("No data to show")
            return

        x = np.array([ts.timestamp() for ts in self.timestamps], dtype=float)
        y = np.array(self.values, dtype=float)

        if self.is_binary:
            if len(x) > 1:
                delta = x[-1] - x[-2]
            else:
                delta = 60
            x_extended = np.append(x, x[-1] + delta)
            self.plot.plot(x_extended, y, stepMode=True, fillLevel=0,
                           brush=(0, 128, 255, 100), pen=pg.mkPen(color='#2287b3', width=2))
            ticks = [(0, "OFF"), (1, "ON")]
            self.plot.getAxis('left').setTicks([ticks])
            self.plot.setYRange(-0.1, 1.1)
        else:
            self.plot.plot(x, y, pen=pg.mkPen(color='#e38d08', width=2))

        max_ticks = 10
        total_points = len(self.timestamps)
        if total_points <= max_ticks:
            ticks = [(ts.timestamp(), ts.strftime("%H:%M")) for ts in self.timestamps]
        else:
            step = max(1, total_points // max_ticks)
            ticks = [(ts.timestamp(), ts.strftime("%H:%M")) for i, ts in enumerate(self.timestamps) if i % step == 0]

        self.plot.getAxis('bottom').setTicks([ticks])

        now = datetime.now().strftime("%H:%M:%S")
        self.info_label.setText(f"{self.sensor_id} | Generated: {now}")


def show_sensor_graph(sensor_id: str):
    app = QApplication.instance()
    created_app = False

    if app is None:
        app = QApplication(sys.argv)
        created_app = True

    window = SensorChartWindow(sensor_id)
    window.show()

    if created_app:
        sys.exit(app.exec_())
    return window

