# Xplora® Watch

Home Assistant Sensoren for Xplora® Watch

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Ludy87/xplora_watch)](https://github.com/Ludy87/xplora_watch/releases)
![GitHub Release Date](https://img.shields.io/github/release-date/Ludy87/xplora_watch)
[![GitHub](https://img.shields.io/github/license/Ludy87/xplora_watch)](LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/Ludy87/xplora_watch)](https://github.com/Ludy87/xplora_watch/issues)
[![Validate](https://github.com/Ludy87/xplora_watch/actions/workflows/validate.yaml/badge.svg)](https://github.com/Ludy87/xplora_watch/actions/workflows/validate.yaml)

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

1. In deinem `config/custom_components` Ordner, einen Ordner mit dem Namen `xplora_watch` erstellen
2. Downloade [last Releae](https://github.com/Ludy87/xplora_watch/releases) und speichere sie in `config/custom_components/xplora_watch` ab

### INSTALLATION mit HACS

1. [HACS](https://hacs.xyz/) ist installier?
2. füge ein `Benutzerdefinierte Repositories` hinzu, als Kategorie `Integration`
3. installier __Xplora® Watch Integration__ [![GitHub release (latest by date)](https://img.shields.io/github/v/release/Ludy87/xplora_watch)](https://github.com/Ludy87/xplora_watch/releases)
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
    - "alarms"
    - "dt_watch"
  safezones: "show"
  scan_interval: 300
  tracker_scan_interval: 60
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
## [Changelog](https://github.com/Ludy87/xplora_watch/blob/main/CHANGELOG.md)

<!-- START ./CHANGELOG.md -->
# Change Log

## [v0.0.12] - 2022-01-20

### Added
- Watch Tracker Name

---
## [v0.0.11] - 2022-01-19

### Added
- Watch Safezone GPS - `DeviceTracker`
- Profil image Watch Tracker

### Changed
- variable

---
## [v0.0.10] - 2022-01-18

### Added
- Track Watch - `DeviceTracker`

---
## [v0.0.9] - 2022-01-08

### Added
- Watch alarm(s) - `Switch`

---

## [v0.0.8] - 2022-01-08

### Fixed
- frozen state

---
## [v0.0.7] - 2022-01-06

### Added
- Watch is safe - `BinarySensor`
- Watch charging - `BinarySensor`
- Watch silent(s) - `Switch`

### Changed
- `sync` to `async`

### Fixed
- timer control reload Entity
- wrong declaration (`sensors` to `types`)

<!-- END ./CHANGELOG.md -->
