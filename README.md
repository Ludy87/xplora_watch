# Xplora® Watch

Home Assistant Sensors for Xplora® Watch

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Ludy87/xplora_watch)](https://github.com/Ludy87/xplora_watch/releases)
![GitHub Release Date](https://img.shields.io/github/release-date/Ludy87/xplora_watch)
[![GitHub](https://img.shields.io/github/license/Ludy87/xplora_watch)](LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/Ludy87/xplora_watch)](https://github.com/Ludy87/xplora_watch/issues)
[![Validate with hassfest and HACS](https://github.com/Ludy87/xplora_watch/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/Ludy87/xplora_watch/actions/workflows/hassfest.yaml)

![Xplora® Watch](https://github.com/home-assistant/brands/blob/master/custom_integrations/xplora_watch/logo@2x.png?raw=true)

## Features

Features | Type
---|---
Battery | Sensor
Watch-Xcoin | Sensor
Watch Online state | Binary Sensor
Watch is safe | Binary Sensor
Watch charging | Binary Sensor
Watch silent(s) | Switch
Watch alarm(s) | Switch
Send Message | Notify
Watch Tracking | Device Tracker
Watch Show Safezone | Device Tracker

---
## Installation

### MANUAL INSTALLATION

Copy the xplora_watch [last Releae](https://github.com/Ludy87/xplora_watch/releases) folder and all of its contents into your Home Assistant's custom_components folder. This folder is usually inside your /config folder. If you are running Hass.io, use SAMBA to copy the folder over. If you are running Home Assistant Supervised, the custom_components folder might be located at /usr/share/hassio/homeassistant. You may need to create the custom_components folder and then copy the localtuya folder and all of its contents into it Alternatively, you can install localtuya through HACS by adding this repository.

### INSTALLATION mit HACS

1. Ensure that [HACS](https://hacs.xyz/) is installed.
2. Search for and install the "__Xplora® Watch Integration__" integration. [![GitHub release (latest by date)](https://img.shields.io/github/v/release/Ludy87/xplora_watch)](https://github.com/Ludy87/xplora_watch/releases)
3. [Add a `xplora_watch` entry to your `configuration.yaml`.](https://github.com/Ludy87/xplora_watch#basis-configuration)
4. Restart Home Assistant.

---
## Basis Configuration

1. Add entry to your `configuration.yaml`

### <u>Small Settings</u>
```yaml
xplora_watch:
  country_code: "+49"
  phonenumber: "123456789"
  password: "password"
  userlang: "de-DE"
  timezone: "Europe/Berlin"
  types:
    - "battery"
    - "xcoin"
    - "state"
    - "safezone"
    - "charging"
    - "silents"
    - "alarms"
    - "dt_watch"
  safezones: "show" # optional
  scan_interval: 180 # default sec - optional
  tracker_scan_interval: 60 # default sec - optional
```
---
### <u>Optional Settings</u>

for [OpenCage Geocoding API](https://opencagedata.com/) address searching
```yaml
  opencage: API_KEY # optional
```
You have more watches and you will one watch integridad? Select this one with ```child_phonenumber``` or ```watch_id```. The safety way is ```child_phonenumber```

```yaml
  child_phonenumber: # optional & ignored if 'watch_id' is set
    - "9876543210"
    - "5678901234"
```
If ```watch_id``` is set, ```child_phonenumber``` is ignored. Errors can occur.
```yaml
  watch_id: # optional
    - 012328123d123f5e775e5e3346739732
```
---
### <u>Full Settings</u>
```yaml
xplora_watch:
  country_code: "+49"
  phonenumber: "123456789"
  password: "password"
  userlang: "de-DE"
  timezone: "Europe/Berlin"
  opencage: API_KEY # optional
  child_phonenumber: # optional & ignored if 'watch_id' is set
    - "9876543210"
    - "5678901234"
  watch_id: # optional
    - 012328123d123f5e775e5e3346739732
  types:
    - "battery"
    - "xcoin"
    - "state"
    - "safezone"
    - "charging"
    - "silents"
    - "alarms"
    - "dt_watch"
  safezones: "show" # optional
  scan_interval: 180 # default sec - optional
  tracker_scan_interval: 60 # default sec - optional
```
2. Restart Home Assistant
3. Check `Home Assistant » Developer Tools » States`

---
## Notify configuration

1. Add entry Notification to your `configuration.yaml`
```yaml
notify:
  - platform: xplora_watch
    name: "XPlora"
```
2. Restart Home Assistant
3. Check `Home Assistant » Developer Tools » States`

![notify image](./images/notify.png)

---
## Tracking Setting

1. define if wrong status (`not_home`|`home`)
```yaml
zone:
  - name: Home
    latitude: '' # your lat
    longitude: '' # your lng
```

---
## 🏳 Supported Countries 🏳

<!-- START ./countries.md -->
<!-- END ./countries.md -->

---
# Debug

```yaml
logger:
  logs:
    custom_components.xplora_watch: debug
```

---
## [Changelog](https://github.com/Ludy87/xplora_watch/blob/main/CHANGELOG.md)

<!-- START ./CHANGELOG.md -->
<!-- END ./CHANGELOG.md -->
