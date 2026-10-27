"""Editor metadata for existing PosterKit fields, not device support claims."""

CLOCK_FONT_IDENTIFIERS=tuple('PRTimeFontIdentifier'+suffix for suffix in (
    'NewYork','NewYorkAlpha','NewYorkHeavy','November','NovemberCondensed','October',
    'PrivateSystemRoundedHeavy','PrivateSystemSoftHeavy','PrivateSystemStencilHeavy',
    'Rail','Rounded','SFArabic','SFArabicRounded','SFCondensed','SFHebrew','SFHebrewRounded',
    'SFPro','SFRounded','Slab','Soft','SoftLight','Stencil',
))


def number_limits(path, default):
    if path in ('clockOpacity','titleContentStyle.frostLevel','contentsLuminence') or path.startswith('customizationConfiguration._tintColorStyle.'):
        return 0,1,.01
    if path=='timeFontConfiguration.weight':
        return 0,1000,1
    if type(default) is int:
        return 0,100000,1
    return -100000,100000,.001


POSTER_PRESETS={
    'Still wallpaper': {'Rendering:depthEffectDisabled':True,'Rendering:motionEffectsDisabled':True},
    'Compact clock': {'Clock:permanentCompactTimeEnabled':True},
    'Non-compact clock': {'Clock:permanentCompactTimeEnabled':False},
}
