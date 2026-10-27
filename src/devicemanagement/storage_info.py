"""Display hardware capacity in the decimal units used for device models."""


def format_device_capacity(capacity):
    if not isinstance(capacity, (int, float)) or capacity <= 0:
        return ""
    gigabytes = capacity / 1_000_000_000
    model_sizes = (8, 16, 32, 64, 128, 256, 512, 1000, 2000, 4000)
    nearest = min(model_sizes, key=lambda size: abs(size - gigabytes))
    if abs(nearest - gigabytes) / nearest <= 0.08:
        return f"{nearest // 1000} TB" if nearest >= 1000 else f"{nearest} GB"
    return f"{gigabytes / 1000:.2g} TB" if gigabytes >= 1000 else f"{gigabytes:.0f} GB"
