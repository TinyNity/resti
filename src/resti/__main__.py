"""Entry point for ``py -m resti`` and for the PyInstaller build."""

import sys

from resti import console, dpi


def main() -> int:
    console.enable_colour()

    # Checked before importing anything that touches the app, because desktop.py
    # binds to user32/kernel32 at import time and would fail with an opaque
    # AttributeError anywhere else.
    if sys.platform != "win32":
        console.error("Resti runs on Windows only.")
        console.hint("It reads icon positions out of the Windows desktop shell.")
        return 1

    # Both Tk and customtkinter sample the process DPI mode when they are first
    # imported, so this has to come before either of them is loaded.
    dpi.enable()

    try:
        from resti.app import App
    except ImportError as exc:
        console.error(f"A required package is missing: {exc.name or exc}")
        console.hint("Install it with: py -m pip install customtkinter")
        return 1

    App().mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
