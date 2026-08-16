"""
Plain color constants only 
"""

BACKGROUND = "#09090f"
SURFACE = "#111118"
CARD = "#16161f"
BORDER = "#232334"

ACCENT = "#7c6af7"
ACCENT_HOVER = "#9d8fff"
SUCCESS = "#4fd1c5"
DANGER = "#f56565"
DANGER_MUTED = "#7a2020"

TEXT = "#e2e8f0"
TEXT_MUTED = "#94a3b8"
TEXT_FAINT = "#475569"

UI = "Segoe UI"
MONO = "Cascadia Mono"

FONT_TITLE = (UI, 14, "bold")
FONT_EMPTY = (UI, 14)
FONT_BODY = (UI, 11)
FONT_ITEM = (UI, 11, "bold")
FONT_META = (UI, 12)
FONT_BUTTON = (UI, 10)
FONT_BUTTON_BOLD = (UI, 10, "bold")
FONT_CHIP = (UI, 9, "bold")
FONT_COUNTER = (MONO, 12)

RADIUS = 8
RADIUS_SMALL = 6


def blend(start: str, end: str, amount: float) -> str:
    """Mix two ``#rrggbb`` colours, *amount* running 0.0 (start) to 1.0 (end)."""
    channels = (
        round(
            int(start[i : i + 2], 16)
            + (int(end[i : i + 2], 16) - int(start[i : i + 2], 16)) * amount
        )
        for i in (1, 3, 5)
    )
    return "#" + "".join(f"{channel:02x}" for channel in channels)
