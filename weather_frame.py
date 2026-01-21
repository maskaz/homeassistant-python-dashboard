from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizePolicy
from weather_widget import Pogoda


def create_pogoda_frame(eid, etype, itype, name,
                        TYPE_OBJECT_NAME_MAP):
    frame = QWidget()
    frame.setObjectName("pogoda_frame")


    main_h = QHBoxLayout(frame)
    main_h.setContentsMargins(10, 10, 10, 10)
    main_h.setSpacing(10)

    # Dodajemy widget Pogoda
    pogoda_widget = Pogoda(eid)
    pogoda_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    main_h.addWidget(pogoda_widget)


    info = {
        "eid": eid,
        "etype": etype,
        "itype": itype,
        "state_widget": pogoda_widget
    }
    return frame, info

