# Xplora® Watch

Home Assistant Sensoren für die Xplora® Watch

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

## [Changelog](https://github.com/Ludy87/xplora_watch/blob/main/CHANGELOG.md)