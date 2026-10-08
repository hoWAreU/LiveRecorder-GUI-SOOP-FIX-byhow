"""Select SOOP's named source streams without assuming playlist positions."""

import re


_KNOWN_HEIGHTS = {
    "original": 1080,
    "hd4k": 720,
    "hd": 540,
    "sd": 360,
    "ld": 240,
}
_REQUESTED_HEIGHTS = {
    "2K": 1440,
    "1080P": 1080,
    "720P": 720,
    "540P": 540,
    "360P": 360,
    "240P": 240,
    "UHD": 720,
    "HD": 540,
    "SD": 360,
    "LD": 240,
    "超清": 720,
    "高清": 540,
    "标清": 360,
    "標清": 360,
    "流畅": 240,
    "流暢": 240,
}


def preset_height(preset: dict) -> int:
    label = str(preset.get("label", ""))
    match = re.search(r"(?<!\d)(\d{3,4})\s*p\b", label, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return _KNOWN_HEIGHTS.get(str(preset.get("name", "")).lower(), 0)


def ordered_presets(presets: list[dict], requested_quality: str) -> list[dict]:
    """Prefer the requested height; use the nearest lower source if absent."""
    available = [
        preset for preset in presets
        if isinstance(preset, dict) and preset.get("name")
        and str(preset["name"]).lower() != "auto" and preset_height(preset)
    ]
    target = _REQUESTED_HEIGHTS.get(str(requested_quality).upper())
    if target is None:
        return sorted(available, key=preset_height, reverse=True)
    lower = sorted((p for p in available if preset_height(p) <= target),
                   key=preset_height, reverse=True)
    higher = sorted((p for p in available if preset_height(p) > target),
                    key=preset_height)
    return lower + higher
