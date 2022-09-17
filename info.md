# Xplora® Watch Version 2

Home Assistant Sensors for Xplora® Watch Version 2

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge&logo=appveyor)](https://github.com/custom-components/hacs)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Ludy87/xplora_watch?style=for-the-badge&logo=appveyor)](https://github.com/Ludy87/xplora_watch/releases)
![GitHub Release Date](https://img.shields.io/github/release-date/Ludy87/xplora_watch)
[![GitHub](https://img.shields.io/github/license/Ludy87/xplora_watch?style=for-the-badge&logo=appveyor)](LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/Ludy87/xplora_watch?style=for-the-badge&logo=appveyor)](https://github.com/Ludy87/xplora_watch/issues)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge&logo=appveyor)](https://github.com/psf/black)

[![Validate with hassfest and HACS](https://github.com/Ludy87/xplora_watch/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/Ludy87/xplora_watch/actions/workflows/hassfest.yaml)

## Features

Features | Type
---|---
Battery | Sensor
Watch-Xcoin | Sensor
Watch Step per Day | Sensor
Watch Online state | Binary Sensor
Watch is in Safezone | Binary Sensor
charging state | Binary Sensor
Watch silent(s) | Switch
Watch alarm(s) | Switch
Send Message | Notify
Watch Tracking | Device Tracker
Watch Show Safezone(s) | Device Tracker
---

## Basis Configuration

Configuration for the "Xplora® Watch Version 2" integration is now performed via a config flow as opposed to yaml configuration file.

1. Go to HACS -> Integrations -> Click "+"
2. Search for "Xplora® Watch" repository and add to HACS
3. Restart Home Assistant when it says to.
4. In Home Assistant, go to Configuration -> Integrations -> Click "+ Add Integration"
5. Search for "Xplora® Watch" and follow the instructions to setup.

---

## [Changelog](https://github.com/Ludy87/xplora_watch/blob/main/CHANGELOG.md)