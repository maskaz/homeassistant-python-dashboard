from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication, QDesktopWidget
from PyQt5.QtCore import Qt
from functools import partial
import sys
import os


def get_style_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, "styles.qss")


def load_stylesheet():
    with open(get_style_path(), "r") as file:
        return file.read()
        
def show_temp_color_palette_popup(parent, eid, itype, name, entity_states, send_selected_temp, send_selected_color, entity_info_types):

    # półprzezroczysta warstwa
    dim_widget = QWidget(parent)
    dim_widget.setStyleSheet("background-color: rgba(0, 0, 0, 190);")
    dim_widget.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    dim_widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)
    dim_widget.setGeometry(QApplication.desktop().geometry())
    dim_widget.show()

    popup = QWidget(parent)
    vbox_layout = QVBoxLayout(popup)
    stylesheet = load_stylesheet()
    popup.setStyleSheet(stylesheet)
    popup.setObjectName("popup")
    popup.setWindowFlag(Qt.FramelessWindowHint)
    popup.setWindowFlag(Qt.WindowStaysOnTopHint)

    lala = entity_states.get(eid, {}).get("attributes", {})
    entity_info_types[(eid, "temp_color")] = itype

    # --- Etykieta temperatury ---
    label_temp = QLabel(f"{name}: Temperature")
    label_temp.setObjectName("names_popups")
    label_temp.setAlignment(Qt.AlignCenter)
    vbox_layout.addWidget(label_temp, Qt.AlignCenter)

    temp_colors = ['#ffffff', '#ffebd9', '#ffdbb9', '#ffcc9c', '#ffac5e', '#ff9c3f', '#ff8c21', '#ff7b00']
    temp_layout = QHBoxLayout()
    for color in temp_colors:
        btn = QPushButton()
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: none;
                border-radius: 2px;
            }}
            QPushButton:pressed {{
                background-color: rgb(17, 17, 17);
                border: 1px solid #ffffff;
                border-radius: 2px;
            }}
        """)
        btn.setFixedSize(50, 50)
        btn.clicked.connect(partial(send_selected_temp, eid, color))
        temp_layout.addWidget(btn)
    vbox_layout.addLayout(temp_layout)

    # --- Etykieta koloru ---
    label_color = QLabel(f"{name}: Color")
    label_color.setObjectName("names_popups")
    label_color.setAlignment(Qt.AlignCenter)
    vbox_layout.addWidget(label_color)

    color_colors = ['#fffb00', '#00ff25', '#00fff4', '#0200ff', '#8800ff', '#ff00eb', '#ff0091', '#ff0000']
    color_layout = QHBoxLayout()
    for color in color_colors:
        btn = QPushButton()
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: none;
                border-radius: 2px;
            }}
            QPushButton:pressed {{
                background-color: rgb(17, 17, 17);
                border: 1px solid #ffffff;
                border-radius: 2px;
            }}
        """)
        btn.setFixedSize(50, 50)
        btn.clicked.connect(partial(send_selected_color, eid, color))
        color_layout.addWidget(btn)
    vbox_layout.addLayout(color_layout)

    spacer = QWidget()
    spacer.setObjectName("spacer")
    vbox_layout.addWidget(spacer)

    btn_close = QPushButton("Close")
    btn_close.setObjectName("close_button")
    btn_close.clicked.connect(lambda: (popup.close(), dim_widget.close()))
    vbox_layout.addWidget(btn_close)

    popup.setLayout(vbox_layout)
    popup.resize(600, 260)

    screen_geometry = QDesktopWidget().availableGeometry()
    x = (screen_geometry.width() - popup.width()) // 2
    y = (screen_geometry.height() - popup.height()) // 2
    popup.move(x, y)
    popup.show()

    return popup, dim_widget

