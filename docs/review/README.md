# Interface and tweak refresh

The added tweak controls are listed in [added-tweaks.csv](added-tweaks.csv), including their keys, destinations, types, version gates and warnings. A successful preference write does not establish that iOS reads the key or produces the intended effect.

This branch keeps the current upstream daemon definitions and launchd label groups unchanged. Additional daemon controls from #67 are excluded pending further device testing. Existing daemon controls retain the updated categories, search and favorites UI.

The vendored awesomeUI files and generated resources_rc.py remain unchanged. Feature PNGs are loaded from the existing packaged src/qt data directory, with embedded resources as a fallback.

The original interface was exercised by the contributor on iPhone 12 and iPhone 15 Pro Max. Offline regressions cover this rebased branch; they are not a substitute for device verification of every added preference. The PR remains a draft pending that validation.

Upstream reconnect handling from 9.7.1 is retained verbatim in `_wait_for_device`, including transient usbmux and re-pairing errors. The added Find My UI wait and AFC media handling are separate paths.
