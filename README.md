# Xplora® Watch Version 2

Xplora® Watch Version 2 integration for Home Assistant

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Ludy87&repository=xplora_watch&category=integration)\
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge&logo=home-assistant)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Ludy87/xplora_watch?style=for-the-badge&logo=github)](https://github.com/Ludy87/xplora_watch/releases)
![GitHub Release Date](https://img.shields.io/github/release-date/Ludy87/xplora_watch?style=for-the-badge&logo=github)
[![GitHub license](https://img.shields.io/github/license/Ludy87/xplora_watch?style=for-the-badge&logo=github)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Ludy87/xplora_watch?style=for-the-badge&logo=github)](https://github.com/Ludy87/xplora_watch/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/Ludy87/xplora_watch?style=for-the-badge&logo=github)](https://github.com/Ludy87/xplora_watch/issues)\
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge&logo=code%20style-black)](https://github.com/psf/black)\
![Github All Releases](https://img.shields.io/github/downloads/Ludy87/xplora_watch/total.svg?style=for-the-badge&logo=GitHub)\
[![Validate with hassfest and HACS](https://github.com/Ludy87/xplora_watch/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/Ludy87/xplora_watch/actions/workflows/hassfest.yaml)
![Code Grade](https://api.codiga.io/project/35996/status/svg)
![Code Quality Score](https://api.codiga.io/project/35996/score/svg)

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/ludy87)

[![✨ Wishlist from Amazon ✨](https://www.astra-g.org/wp-content/uploads/2022/09/amazon_wish.png)](https://smile.amazon.de/registry/wishlist/2MX8QK8VE9MV1)

---
![Xplora® Watch Version 2](https://github.com/home-assistant/brands/blob/master/custom_integrations/xplora_watch/logo@2x.png?raw=true)

## Features

**IMPORTANCE: Of a service is activated by automation, the sensors will no longer be updated. Therefore, activate the `xplora_watch.see` service with a corresponding interval.**

| Features                                                                                             | Type           |
| ---------------------------------------------------------------------------------------------------- | -------------- |
| Battery                                                                                              | Sensor         |
| Watch-Xcoin                                                                                          | Sensor         |
| Watch Step per Day                                                                                   | Sensor         |
| Watch Online state                                                                                   | Binary Sensor  |
| Watch is in Safezone                                                                                 | Binary Sensor  |
| charging state                                                                                       | Binary Sensor  |
| Watch silent(s)                                                                                      | Switch         |
| Watch alarm(s)                                                                                       | Switch         |
| [Send Message](https://github.com/Ludy87/xplora_watch#send-message)                                  | Notify         |
| [Send Message Service](https://github.com/Ludy87/xplora_watch#send-message-via-service-v203)         | Service        |
| [Read Messages from Account](https://github.com/Ludy87/xplora_watch#read-messages-from-account-v240) | Service        |
| [Delete Messages from App](https://github.com/Ludy87/xplora_watch#delete-messages-from-app-v260)     | Service        |
| [Manually update](https://github.com/Ludy87/xplora_watch#manually-update-v208--v209)                 | Service        |
| turn off Watch                                                                                       | Service        |
| Watch Tracking                                                                                       | Device Tracker |
| Watch Show Safezone(s)                                                                               | Device Tracker |
---

## Installation

### MANUAL INSTALLATION

Copy the xplora_watch [last Releae](https://github.com/Ludy87/xplora_watch/releases) folder and all of its contents into your Home Assistant's custom_components folder. This folder is usually inside your /config folder. If you are running Hass.io, use SAMBA to copy the folder over. If you are running Home Assistant Supervised, the custom_components folder might be located at /usr/share/hassio/homeassistant. You may need to create the custom_components folder and then copy the localtuya folder and all of its contents into it. Alternatively, you can install localtuya through HACS by adding this repository.

### INSTALLATION mit HACS

1. Ensure that [HACS](https://hacs.xyz/) is installed.
2. Search for and install the "**Xplora® Watch Integration**" integration. [![GitHub release (latest by date)](https://img.shields.io/github/v/release/Ludy87/xplora_watch)](https://github.com/Ludy87/xplora_watch/releases)
3. [Configuration for the "Xplora® Watch Version 2" integration is now performed via a config flow as opposed to yaml configuration file.](https://github.com/Ludy87/xplora_watch#basis-configuration)

---

## Basis Configuration

1. Go to HACS -> Integrations -> Click "+"
2. Search for "Xplora® Watch" repository and add to HACS
3. Restart Home Assistant when it says to.
4. In Home Assistant, go to Configuration -> Integrations -> Click "+ Add Integration"
5. Search for "Xplora® Watch" and follow the instructions to setup.

Xplora® should now appear as a card under the HA Integrations page with "Configure" selection available at the bottom of the card.

| add in Version 2.2.0                                                                          | add in Version 2                                                                                        |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| ![signin image](https://raw.githubusercontent.com/Ludy87/xplora_watch/main/images/signin.png) | ![integration image](https://raw.githubusercontent.com/Ludy87/xplora_watch/main/images/integration.png) |

---

## Downloaded from voice messages, Videos and Images (v2.7.0)

- All voice messages, videos and images are stored in `config/www/{voice|video|image|}`. [#152](https://github.com/Ludy87/xplora_watch/discussions/152)
  - The voice message will be downloaded as amr and converted to mp3.
  - Videos as mp4
  - Images as jpeg
- updated [Markdown Card Sample](https://raw.githubusercontent.com/Ludy87/xplora_watch/main/samples/markdown-card-read-messages.md) [#155](https://github.com/Ludy87/xplora_watch/issues/155)

---

## Delete Messages from App (v2.6.0)

- new service added - delete only app message
- chats: add ```delete_flag```  `1` = message is deleted
- updated [Markdown Card Sample](https://raw.githubusercontent.com/Ludy87/xplora_watch/main/samples/markdown-card-read-messages.md)
- add Emoji
  - M1001 = "😄"
  - M1002 = "😏"
  - M1003 = "😘"
  - M1004 = "😅"
  - M1005 = "😂"
  - M1006 = "😭"
  - M1007 = "😍"
  - M1008 = "😎"
  - M1009 = "😜"
  - M1010 = "😳"
  - M1011 = "🥱"
  - M1012 = "👏"
  - M1013 = "😡"
  - M1014 = "👍"
  - M1015 = "😏"
  - M1016 = "😓"
  - M1017 = "🍧"
  - M1018 = "😮"
  - M1019 = "M1019"
  - M1020 = "🎁"
  - M1021 = "M1021"
  - M1022 = "☺️"
  - M1023 = "M1023"
  - M1024 = "🌹"

---

## Read Messages from Account (v2.4.0)

- A new (message) sensor has been added, default: disabled
- new service added, (message) sensor will be updated
- change Number of Messages option find in "Configure"
- [Markdown Card Sample](https://raw.githubusercontent.com/Ludy87/xplora_watch/main/samples/markdown-card-read-messages.md) (updated v2.6.0)
- [Automation Sample](https://raw.githubusercontent.com/Ludy87/xplora_watch/main/samples/automation-read-messages.yaml)

![markdown sample](https://raw.githubusercontent.com/Ludy87/xplora_watch/main/images/markdown_sample.png)

---

## Multilanguage (v2.1.0)

- DE
- EN

---

## Manually update (v2.0.8 & v2.0.9)

Manually update all information from your watch

![manually_refresh image](https://raw.githubusercontent.com/Ludy87/xplora_watch/main/images/manually_refresh.png)

---

## Change Friendly Name (v2.0.7)

Set Friendly Name
Please note that this can also change the entry_id!

Rule format: ```watchID=New Name``` Notice the equals sign

![friendly_name image](https://raw.githubusercontent.com/Ludy87/xplora_watch/main/images/friendly_name.png)

---

## Send Message

Set Target with the WatchID for the receiver watch

![notify image](https://raw.githubusercontent.com/Ludy87/xplora_watch/main/images/notify.png)

---

## Send Message via Service (v2.0.3)

![message_service image](https://raw.githubusercontent.com/Ludy87/xplora_watch/main/images/message_service.png)

---

## [🏳 Supported Countries 🏳](https://github.com/Ludy87/xplora_watch/wiki/Countries)

---

## Debug

```yaml
logger:
  logs:
    custom_components.xplora_watch: debug
```

---

## [Workaround for getting logged out of the Xplora® App on your phone](https://github.com/Ludy87/xplora_watch/issues/24)

---

<!-- START ./CHANGELOG.md -->
## Changelog

### [v2] - 2022-09-18

<!-- END ./CHANGELOG.md -->
