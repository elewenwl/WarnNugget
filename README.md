# WarNugget

> **Yet another Nugget fork, but this one is mine.**  
> A modified version of GoldenNugget for animated wallpapers and system tweaks on iOS.  
> Built for iOS 26.2+ (including experimental support for iOS 27).

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/elewenwl/WarNugget?style=for-the-badge)](https://github.com/elewenwl/WarNugget/releases)
[![GitHub license](https://img.shields.io/github/license/elewenwl/WarNugget?style=for-the-badge)](https://github.com/elewenwl/WarNugget/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://python.org)

---

## What is this?

**WarNugget** is a fork of GoldenNugget, renamed and repurposed by me (`elewenwl`).  
The main goal is to provide a user-friendly interface for installing animated wallpapers (PosterBoard) and other tweaks, **without turning your device into a brick**.

> ⚠️ **WARNING:** This is a fork. I am not responsible for any bootloops, data loss, or other issues with your iPhone. You proceed at your own risk.  
> **Always make a backup before applying anything!**

---

## Features

- **PosterBoard (Tendies)**: Import and install animated wallpapers (`.tendies`).
- **Tweaks & Daemons**: Manage system tweaks (powered by the original GoldenNugget engine).
- **Safety Mechanism**: The app warns you when an iOS 27 device is connected.
- **Custom UI**: Renamed windows, custom credits, and links.

---

## Installation (Build from Source)

Since this is a Python project, you'll need Python and its dependencies.

```bash
# 1. Clone the repository
git clone https://github.com/elewenwl/WarNugget.git
cd WarNugget

# 2. Install dependencies (a virtual environment is recommended)
pip install -r requirements.txt

# 3. Run the app
python main_app.py
On Windows, you also need iTunes (or Apple Devices) installed and the Apple Mobile Device Service running.

Compatibility
                                   Feature	iOS 26.2 – 26.4                          iOS 27.0
PosterBoard (Animated Wallpapers)	✅ Supported	                                    ⚠️ Experimental
Tweaks (General)	                ✅ Supported	                                    ⚠️ Limited
Daemons                          	✅ Supported	                                    ⚠️ Limited
Status Bar Modifications	        ✅ Supported	                                    ❌ Not supported
Passcode Themes                 	✅ Supported	                                    ❌ Not supported
Note: iOS 27 support relies on a protective backup-and-restore workaround. Apple's patch means the process can trigger a bootloop if it fails. Use with extreme caution.

Screenshots
(Insert your screenshots here. Example: ![Main Window](docs/screenshot.png))

Credits
This project would not exist without the work of these people:

GoldenNugget Team (awesomenull, leminlimez, and others) — for the original code and engine.

leminlimez — for the original Nugget.

The community — for testing and feedback.

Links
My GitHub: elewenwl

Original GoldenNugget: GitHub

License
Distributed under the original project's license (GoldenNugget).
If the original license is not specified, consider it "AS IS", without any warranties.

WarNugget
Очередной форк Nugget, но этот — мой.
Модификация GoldenNugget для работы с анимированными обоями и системными твиками на iOS.
Сделано для iOS 26.2+ (включая экспериментальную поддержку iOS 27).

https://img.shields.io/github/v/release/elewenwl/WarNugget?style=for-the-badge
https://img.shields.io/github/license/elewenwl/WarNugget?style=for-the-badge
https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python

Что это?
WarNugget — это форк проекта GoldenNugget, переработанный и переименованный мной (elewenwl).
Основная задача — дать пользователям удобный интерфейс для установки анимированных обоев (PosterBoard) и других твиков, не превращая устройство в кирпич.

⚠️ ВНИМАНИЕ: Это форк. Я не несу ответственности за возможные блокировки загрузки, потерю данных или другие проблемы с вашим iPhone. Все действия выполняются на ваш страх и риск.
Всегда делайте резервную копию перед применением!

Возможности
PosterBoard (Tendies): Импорт и установка анимированных обоев (.tendies).

Tweaks & Daemons: Управление системными твиками (через оригинальный движок GoldenNugget).

Защитный механизм: При подключении устройства программа предупреждает об опасности на iOS 27.

Кастомный интерфейс: Переименованные окна, свои авторы и ссылки.
