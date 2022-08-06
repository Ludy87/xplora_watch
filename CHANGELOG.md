## [v1.0.43] - 2022-08-06

### Fixed

- 🐛 Fix Steps sensor (Step counter) #43

---

## [v1.0.42] - 2022-08-03

<details>

### Added

- 🌱 add error message

</details>

---

## [v1.0.40 + v1.0.41] - 2022-05-28

<details>

### Added

- 🏗️ Steps sensor (Step counter) #37

### Fixed

- 🐛 Fix sensor: clear dummy ```wuid```

</details>

---

## [v1.0.39] - 2022-05-27

<details>

### Fixed

- 🐛 Fix device_tracker: ```rad``` default ```-1```

### Changed

- 🌱 bump pyxplora_api to 2.0.93

</details>

---

## [v1.0.38] - 2022-05-22

<details>

### Changed

- 🌱 bump pyxplora_api to 2.0.92

</details>

---

## [v1.0.37] - 2022-05-20

<details>

### Fixed

- 🐛 Fix #35

### Changed

- 🌱 bump pyxplora_api to 2.0.91

</details>

---

## [v1.0.36] - 2022-05-15

<details>

### Fixed

- 🐛 Fix #35

### Changed

- 🌱 bump pyxplora_api to 2.0.90
- 🗑️ clean up

</details>

---

## [v1.0.35] - 2022-05-07

<details>

### Fixed

- 🐛 Fix keyerror

### Changed

- 🌱 homeassistant 2022.5.2
- 🗑️ clean up

</details>

---

## [v1.0.34] - 2022-05-03

<details>

### Fixed

- 🐛 Fix sendText Bug

</details>

---

## [v1.0.33] - 2022-05-01

<details>

### Added

- 🏗️ resolved [#29](https://github.com/Ludy87/xplora_watch/issues/29) tracking device

</details>

---

## [v1.0.31 + v1.0.32] - 2022-04-30

<details>

### Fixed

- 🐛 Fix empty address

### Changed

- 🌱 homeassistant 2022.4.7

### Added

- 🏷️ add types

</details>

---

## [v1.0.30] - 2022-04-17

<details>

### Changed

- 🎨 Black Code Formatter

</details>

---

## [v0.0.29] - 2022-04-10

<details>

### Changed

- 🏷️ type `lat` and `lng` | `<str>` to `<float>`
- remove `*_async` (new Lib version)
- remove `await` without async function
- rename `ids` to `watch_ids`
- renmae `id` to `watch_id`

</details>

---

## [v0.0.28] - 2022-04-02

<details>

### Fixed

- 🎨 better error detection

</details>

---

## [v0.0.27] - 2022-03-26

<details>

### Fixed

- OpenCage: Server disconnected

</details>

---

## [v0.0.26] - 2022-03-20

<details>

### Changed

- API-Lib

</details>

---

## [v0.0.25] - 2022-03-19

<details>

### Added

- OpenCage Geocoding API

### Fixed

- #11

### Changed

- `child_no` to `watch_ids`

</details>

---

## [v0.0.24] - 2022-03-15

<details>

### Changed

- var name
- Api-Lib-Version
- obsolet import removed

</details>

---

## [v0.0.23] - 2022-03-11

<details>

### Added

- Lint with flake8

### Changed

- Entities
- Api-Lib-Version
- obsolet import removed

</details>

---

## [v0.0.22] - 2022-02-28

<details>

### Changed

- distance calculation (Meter)

</details>

---

## [v0.0.21] - 2022-02-27

<details>

### Changed

- var name

### Added

- Device Track last Time
- toggle switch Device Track [#15](https://github.com/Ludy87/xplora_watch/issues/15)

**Please add helper toggle with Name `Xplora Tracker Switch` Entity-ID `input_boolean.xplora_tracker_switch`**
</details>

---

## [v0.0.20] - 2022-02-17

<details>

### Changed

- Api-Lib-Version

</details>

---

## [v0.0.18 + v0.0.19] - 2022-02-14

<details>

### Fixed

- Device Tracker state `not_home` | `home` #12

### Changed

- obsolet import removed

</details>

---

## [v0.0.17] - 2022-02-11

<details>

### Fixed

- state error
- two init notify
- device tracker init error - no def

### Changed

- var name api -> controller
- obsolet import removed

</details>

---

## [v0.0.15-Beta + v0.0.16-Beta] - 2022-02-09

<details>

### Fixed

- Notify send error

### Changed

- hacs & homeassistant version

### Added

- multi watch profil

</details>

---

## [v0.0.14] - 2022-01-23

<details>

### Changed

- cleanup

### Added

- Icon Silent/Alarm

</details>

---

## [v0.0.13] - 2022-01-21

<details>

### Changed

- cleanup

### Fixed

- frozen state

</details>

---

## [v0.0.12] - 2022-01-20

<details>

### Added

- Watch Tracker Name

</details>

---

## [v0.0.11] - 2022-01-19

<details>

### Added

- Watch Safezone GPS - `DeviceTracker`
- Profil image Watch Tracker

### Changed

- variable

</details>

---

## [v0.0.10] - 2022-01-18

<details>

### Added

- Track Watch - `DeviceTracker`

</details>

---

## [v0.0.9] - 2022-01-08

<details>

### Added

- Watch alarm(s) - `Switch`

</details>

---

## [v0.0.8] - 2022-01-08

<details>

### Fixed

- frozen state

</details>

---

## [v0.0.7] - 2022-01-06

<details>

### Added

- Watch is safe - `BinarySensor`
- Watch charging - `BinarySensor`
- Watch silent(s) - `Switch`

### Changed

- `sync` to `async`

### Fixed

- timer control reload Entity
- wrong declaration (`sensors` to `types`)

</details>
