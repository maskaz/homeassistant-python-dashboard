from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

def get_style_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, "styles.qss")


def load_stylesheet():
    with open(get_style_path(), "r") as file:
        return file.read()
        
def create_restart_tile(parent):

    frame = QWidget()
    frame.setFixedHeight(40)
    frame.setObjectName("entity_frame")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(5)

    self.stylesheet = load_stylesheet()
    self.setStyleSheet(self.stylesheet)


    restart_btn = QPushButton()
    restart_btn.setObjectName("close_button")
    layout.addWidget(restart_btn)

    restart_btn.clicked.connect(lambda: parent.ha.connect())

    return frame, update_tile

