# Xplora® Watch

Home Assistant Sensorenfür die Xplora® Watch

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Ludy87/xplora_watch)](https://github.com/Ludy87/xplora_watch/releases)
![GitHub Release Date](https://img.shields.io/github/release-date/Ludy87/xplora_watch)
[![GitHub](https://img.shields.io/github/license/Ludy87/xplora_watch)](LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/Ludy87/xplora_watch)](https://github.com/Ludy87/xplora_watch/issues)

## Features
  - Battery-Sensor
  - Watch-Xcoin-Sensor

## Installation

---

### MANUAL INSTALLATION

1. In deinem `config/custom_components` Ordner, einen Ordner mit dem Namen `xplora_watch` erstellen
2. Downloade [last Releae](https://github.com/Ludy87/xplora_watch/releases) und speichere sie in `config/custom_components/xplora_watch` ab

### INSTALLATION mit HACS

1. [HACS](https://hacs.xyz/) ist installier?
2. füge ein `Benutzerdefinierte Repositories` hinzu, als Kategorie `Integration`
3. installier __Xplora-Watch Integration__ [![GitHub release (latest by date)](https://img.shields.io/github/v/release/Ludy87/xplora_watch)](https://github.com/Ludy87/xplora_watch/releases)
4. Restart Home Assistant


## Basis Konfiguration

1. Füge den Sensor in die `configuration.yaml` ein
```yaml
xplora_watch:
  country_code: "+49"
  phonenumber: "123456789"
  password: "password"
  userlang: "de-DE"
  timezone: "Europe/Berlin"
  sensors: 
    - "battery"
    - "xcoin"
  scan_interval: 300
```
2. Restart Home Assistant
3. Check `Home Assistant » Developer Tools » States`

## Supported Countries

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
