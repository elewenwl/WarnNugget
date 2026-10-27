"""Small device capability checks based on Apple's product identifiers."""

_DYNAMIC_ISLAND_MODELS = frozenset({
    "iPhone15,2", "iPhone15,3", "iPhone15,4", "iPhone15,5",
    "iPhone16,1", "iPhone16,2",
    "iPhone17,1", "iPhone17,2", "iPhone17,3", "iPhone17,4",
    "iPhone18,1", "iPhone18,2", "iPhone18,3", "iPhone18,4",
})


_CAMERA_CONTROL_MODELS = frozenset({
    "iPhone17,1", "iPhone17,2", "iPhone17,3", "iPhone17,4",
    "iPhone18,1", "iPhone18,2", "iPhone18,3", "iPhone18,4",
    "iPhone19,2", "iPhone19,3", "iPhone19,7",
})


_ACTION_BUTTON_MODELS = _CAMERA_CONTROL_MODELS | frozenset({
    "iPhone16,1", "iPhone16,2", "iPhone17,5", "iPhone18,5",
})


def has_action_button(model: str) -> bool:
    """Return whether a known iPhone product type has an Action Button."""
    return str(model or "").strip() in _ACTION_BUTTON_MODELS


def has_camera_control(model: str) -> bool:
    """Return whether a known iPhone product type has physical Camera Control."""
    return str(model or "").strip() in _CAMERA_CONTROL_MODELS


def has_dynamic_island(model: str) -> bool:
    """Return whether a known iPhone product type has Dynamic Island hardware."""
    return str(model or "").strip() in _DYNAMIC_ISLAND_MODELS


def device_os_name(model: str) -> str:
    return "iPadOS" if str(model or "").startswith("iPad") else "iOS"


def device_kind(model: str) -> str:
    return "iPad" if str(model or "").startswith("iPad") else "iPhone"


def device_os_text(text: str, model: str) -> str:
    return text.replace("iOS", "iPadOS") if device_os_name(model) == "iPadOS" else text


def device_text(text: str, model: str) -> str:
    text = device_os_text(text, model)
    return text.replace("iPhone", "iPad") if device_kind(model) == "iPad" else text


def has_home_button(model: str) -> bool:
    """Recognize physical Home buttons; unknown product identifiers fail closed."""
    return str(model or "").strip() in {
        "iPhone8,1", "iPhone8,2", "iPhone8,4", "iPhone9,1", "iPhone9,2",
        "iPhone9,3", "iPhone9,4", "iPhone10,1", "iPhone10,2", "iPhone10,4", "iPhone10,5",
        "iPhone12,8", "iPhone14,6", "iPad5,1", "iPad5,2", "iPad5,3", "iPad5,4",
        "iPad6,3", "iPad6,4", "iPad6,7", "iPad6,8", "iPad6,11", "iPad6,12",
        "iPad7,1", "iPad7,2", "iPad7,3", "iPad7,4", "iPad7,5", "iPad7,6",
        "iPad7,11", "iPad7,12", "iPad11,1", "iPad11,2", "iPad11,3", "iPad11,4",
        "iPad11,6", "iPad11,7", "iPad12,1", "iPad12,2",
    }


def has_always_on_display(model: str) -> bool:
    """Recognize known Always-On display hardware; unknown models fail closed."""
    return str(model or "").strip() in {
        "iPhone15,2", "iPhone15,3", "iPhone16,1", "iPhone16,2",
        "iPhone17,1", "iPhone17,2", "iPhone18,1", "iPhone18,2", "iPhone18,3", "iPhone18,4",
        "iPhone19,2", "iPhone19,3", "iPhone19,7",
    }


def has_apple_intelligence(model: str) -> bool:
    """iPhone 15 Pro / Pro Max and subsequent iPhone hardware generations."""
    import re
    match = re.fullmatch(r"iPhone(\d+),(\d+)", str(model or "").strip())
    if match is None:
        return False
    generation, variant = map(int, match.groups())
    return (generation == 16 and variant in (1, 2)) or (generation >= 17 and variant > 0)
