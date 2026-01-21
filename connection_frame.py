from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

def create_ha_connection_tile(parent):
    """
    Tworzy kafelek połączenia HA z przyciskiem reconnect.
    parent - instancja HAControlUIobszar (żeby lambda mogła użyć parent.ha.connect())
    """
    frame = QWidget()
    frame.setFixedHeight(40)
    frame.setObjectName("ha_connection_tile")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(5)

    status_label = QLabel("Łączenie...")
    status_label.setAlignment(Qt.AlignCenter)
    status_label.setObjectName("ha_status_label")
    layout.addWidget(status_label)

    reconnect_btn = QPushButton("Połącz ponownie")
    reconnect_btn.setObjectName("ha_reconnect_button")
    layout.addWidget(reconnect_btn)

    # Lambda do ponownego połączenia
    reconnect_btn.clicked.connect(lambda: parent.ha.connect())

    # Funkcja aktualizująca stan kafelka
    def update_tile():
        if parent.ha.connected:
            status_label.setText("Połączono ✅")
        else:
            status_label.setText("Rozłączono ❌")

    # Zwracamy widget i funkcję aktualizacji
    return frame, update_tile

