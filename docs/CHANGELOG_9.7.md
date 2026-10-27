# GoldenNugget Desktop 9.7

## General

- Dedicated Community Catalog page for presets and `.batter` templates.
- Community tweaks in templates: switches, sliders, text fields and choices.
- Catalog update indicators for imported presets and downloaded templates.
- Download size and SHA-256 checks for catalog templates.
- Community tweaks are included in the apply summary, risk assessment and Reset dialog.
- Add Disable Icon Shimmer (iOS 26.4+) and experimental Disable Icon Glass Outline tweaks.
- Add experimental SpringBoard RSSI indicator tweak.

## PosterBoard

- Legacy wallpaper conversion and bundle renaming now run only on iOS 27 and newer. iOS 26 keeps the original format.
- Hide the Convert switch on iOS 26 and update it when switching devices.
- Fix wallpaper delivery with encrypted protective backups.

## UI

- Restore first-run interface selection with Sidebar and Modern options.
- Replace interface preview SVGs with English screenshots and add Retina/HiDPI support.
- Hide the header Back button and home screen Apply button when Sidebar is enabled.
- Refresh shared controls, update the home screen logo and fix bundled contributor images.

## Fixes

- Improve media cache verification: check every recorded file and its exact size.
- Stop reporting success when tweak delivery or media restoration is incomplete.
- Fix media folder selection when restoring a cached backup.
- Handle expected device disconnections after the final reboot and retry the connection automatically.
- Block template file paths outside the extracted package and restrict offset expressions to arithmetic.
- Fix the About dialog crash and crashes caused by events targeting deleted widgets.
- Fix the iOS backup command-line tool and resource loading when launched outside the project folder.
- Remove unused code and improve macOS dependency packaging.

**Full Changelog**: https://github.com/GoldenNugget-Team/GoldenNugget/compare/9.6.2...9.7
