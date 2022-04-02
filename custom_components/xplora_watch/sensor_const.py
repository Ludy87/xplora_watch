"""Xplora® Watch Sensor const"""

ICON_BATTERY = [
    "mdi:battery",
    "mdi:battery-90",
    "mdi:battery-80",
    "mdi:battery-70",
    "mdi:battery-60",
    "mdi:battery-50",
    "mdi:battery-40",
    "mdi:battery-30",
    "mdi:battery-20",
    "mdi:battery-10",
    "mdi:battery-alert",
    "mdi:battery-charging-100",
    "mdi:battery-charging-90",
    "mdi:battery-charging-80",
    "mdi:battery-charging-70",
    "mdi:battery-charging-60",
    "mdi:battery-charging-50",
    "mdi:battery-charging-40",
    "mdi:battery-charging-30",
    "mdi:battery-charging-20",
    "mdi:battery-charging-10",
]


def bat(_battery, _isCharging) -> str:
    _icon = "mdi:battery-unknown"
    if _battery > 90:
        _icon = ICON_BATTERY[0]
    elif _battery > 80:
        _icon = ICON_BATTERY[1]
    elif _battery > 70:
        _icon = ICON_BATTERY[2]
    elif _battery > 60:
        _icon = ICON_BATTERY[3]
    elif _battery > 50:
        _icon = ICON_BATTERY[4]
    elif _battery > 40:
        _icon = ICON_BATTERY[5]
    elif _battery > 30:
        _icon = ICON_BATTERY[6]
    elif _battery > 20:
        _icon = ICON_BATTERY[7]
    elif _battery > 10:
        _icon = ICON_BATTERY[8]
    elif _battery > 5:
        _icon = ICON_BATTERY[9]
    elif _battery > 0:
        _icon = ICON_BATTERY[10]
    if _battery == 100 and _isCharging:
        _icon = ICON_BATTERY[11]
    elif _battery >= 90 and _isCharging:
        _icon = ICON_BATTERY[12]
    elif _battery >= 80 and _isCharging:
        _icon = ICON_BATTERY[13]
    elif _battery >= 70 and _isCharging:
        _icon = ICON_BATTERY[14]
    elif _battery >= 60 and _isCharging:
        _icon = ICON_BATTERY[15]
    elif _battery >= 50 and _isCharging:
        _icon = ICON_BATTERY[16]
    elif _battery >= 40 and _isCharging:
        _icon = ICON_BATTERY[17]
    elif _battery >= 30 and _isCharging:
        _icon = ICON_BATTERY[18]
    elif _battery >= 20 and _isCharging:
        _icon = ICON_BATTERY[19]
    elif _battery >= 10 and _isCharging:
        _icon = ICON_BATTERY[20]
    return _icon
