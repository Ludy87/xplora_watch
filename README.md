# Xplora® Watch

Home Assistant Sensorenfür die Xplora® Watch

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Ludy87/xplora_watch)](https://github.com/Ludy87/xplora_watch/releases)
![GitHub Release Date](https://img.shields.io/github/release-date/Ludy87/xplora_watch)
[![GitHub](https://img.shields.io/github/license/Ludy87/xplora_watch)](LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/Ludy87/xplora_watch)](https://github.com/Ludy87/xplora_watch/issues)
[![Validate](https://github.com/Ludy87/xplora_watch/actions/workflows/validate.yaml/badge.svg)](https://github.com/Ludy87/xplora_watch/actions/workflows/validate.yaml)

## Features

Features | Type
---|---
Battery | Sensor
Watch-Xcoin | Sensor
Watch Online state | BinarySensor
Watch is safe | BinarySensor
Watch charging | BinarySensor
Watch silent(s) | Switch
send Message | Notify

---
## Installation

### MANUAL INSTALLATION

1. In deinem `config/custom_components` Ordner, einen Ordner mit dem Namen `xplora_watch` erstellen
2. Downloade [last Releae](https://github.com/Ludy87/xplora_watch/releases) und speichere sie in `config/custom_components/xplora_watch` ab

### INSTALLATION mit HACS

1. [HACS](https://hacs.xyz/) ist installier?
2. füge ein `Benutzerdefinierte Repositories` hinzu, als Kategorie `Integration`
3. installier __Xplora-Watch Integration__ [![GitHub release (latest by date)](https://img.shields.io/github/v/release/Ludy87/xplora_watch)](https://github.com/Ludy87/xplora_watch/releases)
4. Restart Home Assistant

---
## Basis Configuration

1. Füge in die `configuration.yaml` ein
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
  scan_interval: 300
```
2. Restart Home Assistant
3. Check `Home Assistant » Developer Tools » States`

---
## Notify configuration

1. Füge die Notification in die `configuration.yaml` ein
```yaml
notify:
  - platform: xplora_watch
    name: "XPlora"
```
2. Restart Home Assistant
3. Check `Home Assistant » Developer Tools » States`

---
## 🏳 Supported Countries 🏳

<!-- START ./countries.md -->
| country name | country code |
|--------------|--------------|
| United Kingdom | 44 |
| Spain | 34 |
| Germany | 49 |
| Norway | 47 |
| Sweden | 46 |
| Finland | 358 |
| France | 33 |
| Italy | 39 |
| Switzerland | 41 |
| Austria | 43 |

<!-- END ./countries.md -->

---
# Debug

```yaml
logger:
  logs:
    custom_components.xplora_watch: debug
```

---
## [Changelog](https://github.com/Ludy87/xplora_watch/CHANGELOG.md)

<!-- START ./CHANGELOG.md -->
<!-- END ./CHANGELOG.md -->