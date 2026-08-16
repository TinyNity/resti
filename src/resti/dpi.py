"""Process-wide DPI awareness."""
import ctypes

PROCESS_PER_MONITOR_DPI_AWARE = 2
def enable() -> None:
    """Opt the process into per-monitor DPI scaling.

    Windows locks the DPI mode the first time a process draws anything, so this
    has to run before Tk or customtkinter are imported. Falls back to the older
    system-wide call on Windows 8 and earlier, and does nothing if neither is
    available.
    """
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
        return
    except (AttributeError, OSError):
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass