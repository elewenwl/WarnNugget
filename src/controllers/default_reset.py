from collections import defaultdict

from src.tweaks.basic_plist_locations import FileLocation
from src.tweaks.registry import SPECS, Section
from src.tweaks.tweak_classes import BasicPlistTweak, suspend_tweak_notifications
from src.tweaks.tweak_loader import _build_spec
from src.utils.pages import Page
from src.utils.preference_reset import PreferenceKeyReset

PAGE_SECTIONS = {Page.Springboard: Section.SPRINGBOARD,
                 Page.InternalOptions: Section.INTERNAL,
                 Page.LiquidGlass: Section.LIQUID_GLASS}


def remaining_reset_entries(entries, pages):
    sections = {PAGE_SECTIONS[page] for page in pages if page in PAGE_SECTIONS}
    specs = {spec.id.name: spec for spec in SPECS}
    return {name: entry for name, entry in entries.items()
            if not ((name.startswith('Daemons/') and Page.Daemons in pages)
                    or (name.startswith('StatusBar') and Page.StatusBar in pages)
                    or (name in specs and specs[name].section in sections
                        and isinstance(_build_spec(specs[name]), BasicPlistTweak)))}


def preference_reset_plan(entries, pages):
    if entries is None:
        if Page.Daemons in pages or any(page in PAGE_SECTIONS for page in pages):
            raise ValueError('No applied-selection record is available for this device and iOS version.')
        return {}
    selected = {PAGE_SECTIONS[page] for page in pages if page in PAGE_SECTIONS}
    paths = defaultdict(set)
    specs = {spec.id.name: spec for spec in SPECS}
    for name, entry in entries.items():
        if name.startswith('Daemons/'):
            if Page.Daemons in pages:
                paths[FileLocation.disabledDaemons].add((name[len('Daemons/'):],))
            continue
        spec = specs.get(name)
        if spec is None or spec.section not in selected:
            continue
        tweak = _build_spec(spec)
        if not isinstance(tweak, BasicPlistTweak):
            # Eligibility archives and PosterKit have separate reset mechanisms.
            continue
        with suspend_tweak_notifications():
            tweak.set_value(entry['value'])
            payloads = tweak.apply_tweak({})
        for location, values in payloads.items():
            if location == FileLocation.featureflags:
                for domain, flags in values.items():
                    paths[location].update((domain, flag, field)
                                           for flag, fields in flags.items() for field in fields)
            else:
                paths[location].update((key,) for key in values)
    return {location: PreferenceKeyReset(keys) for location, keys in paths.items()}
