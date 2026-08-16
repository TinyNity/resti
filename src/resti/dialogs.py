from __future__ import annotations
import customtkinter as ctk
from resti import theme

class Dialog(ctk.CTkToplevel):
    """A centred, modal dialog with an accent rule along the top edge."""

    accent = theme.ACCENT

    def __init__(self, parent, title: str, width: int, height: int) -> None:
        super().__init__(parent)
        self.title(title)
        self.configure(fg_color=theme.SURFACE)
        self.resizable(False, False)
        self.grab_set()
        self.attributes("-topmost", True)
        self._result = None

        # Realise the widget first, otherwise the parent geometry read below
        # returns the placeholder 1x1 size and the dialog lands in the corner.
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        ctk.CTkFrame(self, height=2, fg_color=self.accent, corner_radius=0).pack(
            fill="x", side="top"
        )

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind("<Escape>", lambda event: self.cancel())

    def body(self, padding: tuple[int, int]) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=padding)
        return frame

    def button_row(self) -> ctk.CTkFrame:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=16)
        row.grid_columnconfigure((0, 1), weight=1)
        return row

    def add_cancel(self, row: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            row,
            text="Cancel",
            height=34,
            corner_radius=theme.RADIUS_SMALL,
            fg_color=theme.CARD,
            hover_color=theme.BORDER,
            text_color=theme.TEXT_MUTED,
            font=theme.FONT_BUTTON,
            command=self.cancel,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

    def close(self, result=None) -> None:
        self._result = result
        self.grab_release()
        self.destroy()

    def cancel(self) -> None:
        self.close(None)

    def show(self):
        """Block until the dialog is dismissed, then return its result."""
        self.wait_window()
        return self._result


class AskString(Dialog):
    """Prompt for a single line of text."""

    def __init__(self, parent, title: str, prompt: str, initial: str = "") -> None:
        super().__init__(parent, title, width=380, height=185)
        self.bind("<Return>", lambda event: self._accept())

        body = self.body(padding=(16, 0))
        ctk.CTkLabel(
            body, text=prompt, font=theme.FONT_BODY, text_color=theme.TEXT, anchor="w"
        ).pack(fill="x", pady=(0, 10))

        self._entry = ctk.CTkEntry(
            body,
            fg_color=theme.CARD,
            border_color=theme.BORDER,
            border_width=1,
            text_color=theme.TEXT,
            font=theme.FONT_BODY,
            height=36,
            corner_radius=theme.RADIUS_SMALL,
        )
        self._entry.insert(0, initial)
        self._entry.select_range(0, "end")
        self._entry.pack(fill="x")
        self._entry.focus()

        row = self.button_row()
        self.add_cancel(row)
        ctk.CTkButton(
            row,
            text="OK",
            height=34,
            corner_radius=theme.RADIUS_SMALL,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.BACKGROUND,
            font=theme.FONT_BUTTON_BOLD,
            command=self._accept,
        ).grid(row=0, column=1, sticky="ew")

    def _accept(self) -> None:
        self.close(self._entry.get().strip() or None)


class Confirm(Dialog):
    """Ask for confirmation before something destructive."""

    def __init__(self, parent, title: str, message: str) -> None:
        super().__init__(parent, title, width=360, height=165)

        body = self.body(padding=(18, 0))
        ctk.CTkLabel(
            body,
            text=message,
            font=theme.FONT_BODY,
            text_color=theme.TEXT,
            wraplength=310,
            justify="left",
        ).pack(anchor="w")

        row = self.button_row()
        self.add_cancel(row)
        ctk.CTkButton(
            row,
            text="Delete",
            height=34,
            corner_radius=theme.RADIUS_SMALL,
            fg_color=theme.DANGER_MUTED,
            hover_color=theme.DANGER,
            text_color=theme.TEXT,
            font=theme.FONT_BUTTON_BOLD,
            command=lambda: self.close(True),
        ).grid(row=0, column=1, sticky="ew")


class Error(Dialog):
    """Report a failure the user needs to act on."""

    accent = theme.DANGER

    def __init__(self, parent, title: str, message: str) -> None:
        super().__init__(parent, title, width=380, height=165)

        body = self.body(padding=(18, 0))
        ctk.CTkLabel(
            body,
            text=message,
            font=theme.FONT_BODY,
            text_color=theme.DANGER,
            wraplength=330,
            justify="left",
        ).pack(anchor="w")

        ctk.CTkButton(
            self,
            text="OK",
            height=34,
            corner_radius=theme.RADIUS_SMALL,
            fg_color=theme.CARD,
            hover_color=theme.BORDER,
            text_color=theme.TEXT,
            font=theme.FONT_BUTTON,
            command=self.cancel,
        ).pack(fill="x", padx=24, pady=16)


def ask_string(parent, title: str, prompt: str, initial: str = "") -> str | None:
    return AskString(parent, title, prompt, initial).show()


def confirm(parent, title: str, message: str) -> bool:
    return bool(Confirm(parent, title, message).show())


def error(parent, title: str, message: str) -> None:
    Error(parent, title, message).show()
