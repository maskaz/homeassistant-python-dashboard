# homeassistant-python-dashboard

## Description

Python Dashboard was created for low performance single-board computer (like Raspberry Pi 3). 
Goal is to have Home Assistant control dashboard without heavyweight Web Browser usage.

So clean from dust old RPI with a touchscreen, install code and have fun.

## Installation:

# Install needed python libraries

    sudo apt update
    sudo apt install python3 python3-pip python3-ven
    
    python3 -m venv myenv
    
    source myenv/bin/activate
    
    pip install websocket-client
    pip install PyQt5
    pip install numpy
    pip install requests
    pip install pyqtgraph
    pip install QtPy
    pip install qtwidgets
    pip install QtAwesome
    pip install python-dateutil

# Clone repo

## Configuration:

###   Edit config.ini file
      Input your HA instance IP 
      
      ha_token -  set long_lived_access_token
      ha_ip - set ip for RestApi (http://ip:8123)
      ha_ip_ws - set ip for Websocket (ws://ip:8123/api/websocket)


      screen = full (this option is mainly for development purposes, for non fullscreen mode, put anything beside "full")columns = 2
      columns = 4  (how many columns should be show, depends on screen resolution, vertical or horizontal rotation of a screen)

###   Widgets. Edit example.json file
   First is name of area (example: Bedroom)

    Connection status:
       Button/label for connection status to HA .
       When connection will lost, it will be turn to red button, click will force reconnection.
       
       {"entity_id": " ", "name": " ", "widget_type": "ha_connection",  "info_type": "label"}      
       
     Label:
     
       {"entity_id": " ", "name": "Lights", "widget_type": "label",  "info_type": "label"}   - Label with name of widget group
       
     Light (light controler with slider):
     
       {"entity_id": "light.bedroom_lamp", "name": "Bedroom Light", "widget_type": "light",  "info_type": "temp_color"}

       Extra config. 
          "info_type":
              temp_color - for light with color and temprature control (popup under light icon)
              temp - for light with only temperature control option    (popup under light icon)
              light - for light without color and temperature control options
       
     Switch:
     
       {"entity_id": "switch.floor_lamp", "name": "Floor lamp", "widget_type": "switch",  "info_type": "switch"}

       
     Cover (roller blinds, covers, etc):
       
       {"entity_id": "cover.bedroom", "name": "Covers", "widget_type": "cover",  "info_type": "cover"}

    
     Fan:

        {"entity_id": "fan.ceiling_fan", "name": "Ceiling fan", "widget_type": "fan",  "info_type": "fan"}

     Number slider: (enteties that needs numeric input):
     
        {"entity_id": "number.fan", "name": "Number fan", "widget_type": "number_slider",  "info_type": "0.500.50"}

       Configure for (info_type) number entity:  minvalue.maxvalue.step

     Thermostat

        {"entity_id": "climate.bedroom_thermostat", "name": "Bedroom thermostat", "widget_type": "thermostat",  "info_type": "thermostat"}

     Sensor with chart:

       {"entity_id": "sensor.bedrrom_temp", "name": "Temperature", "widget_type": "sensor_chart",  "info_type": "temperature"}

        Configuration of "info_type" will change icon of sensor, values:
           temperature = mdi6.temperature-celsius
           humidity = mdi6.water-percent
           power = mdi6.lightning-bolt
           door = mdi6.door
           window = mdi6.window-closed-variant
           motion = mdi6.motion-sensor
           dishwasher = mdi6.dishwasher
           brightness = mdi6.brightness-percent
           audio = mdi6.speaker
           list = mdi6.list-box-outline
           dust = mdi6.weather-dust
           co2 = mdi6.molecule-co2
           organic = mdi6.flower-pollen-outline
           air_quality = mdi6.scent
           bell = mdi6.bell-outline
           entryphone = mdi6.microwave
           bathroom = mdi6.shower-head

       Additional info_types and coresponding icons can be added to colors_icons.ini file under [icons_by_itype] config

     To do list:

       {"entity_id": "todo.shopping_card", "name": "Shoping", "widget_type": "todo",  "info_type": "todo"},

         This widget will show number of tasks on "To do" list. Tasks can be added and removed form list. Additional window showing after click of widget

     Calendar:    

       {"entity_id": "sensor.listofevents", "name": "Calendar", "widget_type": "calendar",  "info_type": "calendar"}

         This widget will open list of events from calendar. 
         To work this widget needs additional template added to your Home Assistant configuration.yaml:


        !! remember about commas after each  "{"entity_id":(...)" line, but last one cannot have it !!
        Save json file

        
Calendar template:

template:
  - trigger:
      - platform: time_pattern
        minutes: /1
      - platform: homeassistant
        event: start
    action:
    - action: calendar.get_events
      target:
        entity_id: 
            - calendar.name_of_your_existing_calendar
      data:
        duration:
          days: 90
      response_variable: calendar_events
    sensor:
      - name: Listofevents
        unique_id: listofevents
        state:   "{{ calendar_events['calendar.name_of_your_existing_calendar'].events | count() }}"
        attributes:
             events: "{{ calendar_events['calendar.name_of_your_existing_calendar'].events  }}"





###   Run
      python3 areas.py example.json

        
Additional features in a future, first one: main screen with weather.
