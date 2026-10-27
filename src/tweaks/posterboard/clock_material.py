"""Modify the material archive embedded in a PosterKit title style."""
import math
import plistlib


def set_clock_material(data, changes):
    archive = plistlib.loads(data)
    if archive.get("$archiver") != "NSKeyedArchiver":
        raise ValueError("Expected a keyed clock archive")
    objects = archive["$objects"]

    def resolve(value):
        return objects[value.data] if isinstance(value, plistlib.UID) else value

    root = resolve(archive["$top"]["root"])
    if "titleContentStyle" not in root:
        raise ValueError("This wallpaper has no titleContentStyle archive")
    raw = resolve(root["titleContentStyle"])
    if not isinstance(raw, bytes):
        raise ValueError("Unsupported titleContentStyle representation")
    nested = plistlib.loads(raw)
    if nested.get("$archiver") != "NSKeyedArchiver":
        raise ValueError("Expected a keyed clock material archive")
    nested_objects = nested["$objects"]
    style = nested_objects[nested["$top"]["root"].data]
    style_class = nested_objects[style["$class"].data]
    if style_class.get("$classname") != "PRPosterContentVibrantMaterialStyle":
        raise ValueError("This wallpaper does not use PRPosterContentVibrantMaterialStyle")
    for key, value in changes.items():
        if key not in ("frostLevel", "preferredMaterialType") or key not in style:
            raise ValueError(f"Unsupported clock material field: {key}")
        if key == "frostLevel":
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("Clock frost level must be between 0 and 1")
            value = float(value)
        elif type(value) is not int or value < 0:
            raise ValueError("Clock material type must be a nonnegative integer")
        if isinstance(style[key], plistlib.UID):
            style[key] = plistlib.UID(len(nested_objects))
            nested_objects.append(value)
        else:
            style[key] = value
    inner = plistlib.dumps(nested, fmt=plistlib.FMT_BINARY, sort_keys=False)
    if plistlib.loads(inner) != nested:
        raise ValueError("Clock material serialization failed")
    if isinstance(root["titleContentStyle"], plistlib.UID):
        root["titleContentStyle"] = plistlib.UID(len(objects))
        objects.append(inner)
    else:
        root["titleContentStyle"] = inner
    output = plistlib.dumps(archive, fmt=plistlib.FMT_BINARY, sort_keys=False)
    if plistlib.loads(output) != archive:
        raise ValueError("Clock archive serialization failed")
    return output
