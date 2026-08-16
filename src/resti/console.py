import ctypes
import sys

RESET = "\033[0m"
RED = "\033[31m"
DIM = "\033[2m"

STD_ERROR_HANDLE = -12
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004


def enable_colour() -> None:
    """Ask the Windows console to interpret ANSI escapes (Windows 10 1511+)."""
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(STD_ERROR_HANDLE)
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(
                handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            )
    except (AttributeError, OSError):
        pass


def _paint(colour: str, text: str) -> str:
    stream = sys.stderr
    if stream is not None and getattr(stream, "isatty", bool)():
        return f"{colour}{text}{RESET}"
    return text


def _write(line: str) -> None:
    if sys.stderr is not None:
        print(line, file=sys.stderr)


def error(message: str) -> None:
    _write(f"{_paint(RED, '[error]')} {message}")


def hint(message: str) -> None:
    _write(_paint(DIM, f"        {message}"))
