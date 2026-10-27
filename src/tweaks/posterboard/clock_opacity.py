"""Preserve both keyed color representations while changing clock opacity."""
import math
import plistlib


def set_clock_opacity(data, alpha):
    if type(alpha) not in (float, int) or not math.isfinite(alpha) or not 0 <= alpha <= 1:
        raise ValueError("Clock opacity must be between 0 and 1.")
    alpha = float(alpha)

    def open_archive(raw):
        archive = plistlib.loads(raw)
        if archive.get("$archiver") != "NSKeyedArchiver":
            raise ValueError("Expected a keyed clock/color archive")
        objects = archive["$objects"]

        def resolve(value):
            if isinstance(value, plistlib.UID):
                return objects[value.data]
            return value

        def assign(obj, key, value):
            if isinstance(obj[key], plistlib.UID):
                obj[key] = plistlib.UID(len(objects))
                objects.append(value)
            else:
                obj[key] = value

        return archive, resolve(archive["$top"]["root"]), resolve, assign

    def edit_color(color, resolve, assign):
        if not isinstance(color, dict) or "UIAlpha" not in color:
            raise ValueError("The device clock color has no supported UIAlpha field")
        if type(resolve(color["UIAlpha"])) not in (int, float):
            raise ValueError("Unsupported clock alpha representation")
        assign(color, "UIAlpha", alpha)
        if "NSWhite" in color:
            white = resolve(color["NSWhite"])
            if type(white) not in (str, bytes):
                raise ValueError("Unsupported NSWhite representation")
            text = white.decode("ascii") if isinstance(white, bytes) else white
            components = text.split()
            if len(components) != 2:
                raise ValueError("Expected white and alpha components in NSWhite")
            updated = components[0] + " " + format(alpha, ".17g")
            assign(color, "NSWhite", updated.encode("ascii") if isinstance(white, bytes) else updated)

    archive, root, resolve, assign = open_archive(data)
    title = resolve(root["titleColor"])
    edit_color(resolve(title["color"]), resolve, assign)
    has_color_data = "colorData" in title and resolve(title["colorData"]) != "$null"
    if has_color_data:
        wrapper = resolve(title["colorData"])
        if not isinstance(wrapper, dict) or "NS.data" not in wrapper:
            raise ValueError("Unsupported clock colorData representation")
        nested, color, nested_resolve, nested_assign = open_archive(resolve(wrapper["NS.data"]))
        edit_color(color, nested_resolve, nested_assign)
        inner = plistlib.dumps(nested, fmt=plistlib.FMT_BINARY, sort_keys=False)
        assign(wrapper, "NS.data", inner)
    output = plistlib.dumps(archive, fmt=plistlib.FMT_BINARY, sort_keys=False)

    _, verified_root, verified_resolve, _ = open_archive(output)
    verified_title = verified_resolve(verified_root["titleColor"])
    outer_color = verified_resolve(verified_title["color"])
    if verified_resolve(outer_color["UIAlpha"]) != alpha:
        raise ValueError("Clock opacity archive verification failed")
    if has_color_data:
        _, inner_color, inner_resolve, _ = open_archive(
            verified_resolve(verified_resolve(verified_title["colorData"])["NS.data"]))
        if inner_resolve(inner_color["UIAlpha"]) != alpha:
            raise ValueError("Nested clock opacity archive verification failed")
    return output
