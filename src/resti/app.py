"""The Resti main window."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime

import customtkinter as ctk

from resti import dialogs, theme
from resti.desktop import read_icons, restore_icons
from resti.storage import Snapshot, SnapshotStore

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

WINDOW_WIDTH = 520
WINDOW_HEIGHT = 620
STATUS_RESET_MS = 4000


class SnapshotRow(ctk.CTkFrame):
    """One saved layout, with its restore / rename / delete actions."""

    def __init__(self, parent, snapshot: Snapshot, on_select, on_restore, on_rename, on_delete):
        super().__init__(parent, fg_color=theme.CARD, corner_radius=theme.RADIUS)
        self.name = snapshot.name
        self._on_select = on_select
        self.grid_columnconfigure(0, weight=1)

        # A plain tk.Frame, because place() only accepts the negative height
        # offset used by set_selected() on a classic Tk widget.
        self._marker = tk.Frame(self, width=4, bg=theme.ACCENT)
        self._marker.place_forget()

        details = ctk.CTkFrame(self, fg_color="transparent")
        details.grid(row=0, column=0, sticky="ew", padx=(14, 8), pady=10)
        details.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            details,
            text=snapshot.name,
            font=theme.FONT_ITEM,
            text_color=theme.TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            details,
            text=f"{snapshot.icon_count} icons  ·  {snapshot.date}",
            font=theme.FONT_META,
            text_color=theme.TEXT_FAINT,
            anchor="w",
        ).grid(row=1, column=0, sticky="ew")

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=1, padx=(0, 10), pady=8)

        buttons = (
            ("RESTORE", theme.ACCENT, theme.ACCENT_HOVER, theme.BACKGROUND, on_restore),
            ("RENAME", theme.SURFACE, theme.BORDER, theme.TEXT_MUTED, on_rename),
            ("DELETE", theme.DANGER_MUTED, theme.DANGER, theme.TEXT, on_delete),
        )
        for column, (label, fill, hover, text, command) in enumerate(buttons):
            ctk.CTkButton(
                actions,
                text=label,
                width=72,
                height=28,
                corner_radius=theme.RADIUS_SMALL,
                font=theme.FONT_CHIP,
                fg_color=fill,
                hover_color=hover,
                text_color=text,
                command=lambda action=command: action(self.name),
            ).grid(row=0, column=column, padx=(0, 4) if column < 2 else 0)

        for widget in (self, details):
            widget.bind("<Button-1>", lambda event: self._on_select(self.name))

    def set_selected(self, selected: bool) -> None:
        if selected:
            self.configure(fg_color=theme.blend(theme.CARD, theme.ACCENT, 0.12))
            self._marker.place(x=0, y=4, relheight=1.0, height=-8)
        else:
            self.configure(fg_color=theme.CARD)
            self._marker.place_forget()


class App(ctk.CTk):
    """Main window: the snapshot list, a status line and the save action."""

    def __init__(self, store: SnapshotStore | None = None) -> None:
        super().__init__()
        self.title("Resti")
        self.configure(fg_color=theme.BACKGROUND)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(480, 480)
        # Start invisible so the window can be positioned before it is seen.
        self.attributes("-alpha", 0.0)

        self.store = store if store is not None else SnapshotStore()
        self._rows: dict[str, SnapshotRow] = {}

        self._build()
        self._refresh()
        self._centre()
        self._apply_window_icon()
        self._fade_in(0.0)

    # Layout

    def _build(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        listing = ctk.CTkFrame(self, fg_color="transparent")
        listing.grid(row=0, column=0, sticky="nsew", padx=24, pady=12)
        listing.grid_rowconfigure(1, weight=1)
        listing.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(listing, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ctk.CTkLabel(
            header, text="SNAPSHOTS", font=theme.FONT_TITLE, text_color=theme.TEXT_FAINT
        ).pack(side="left")
        self._counter = ctk.CTkLabel(
            header, text="", font=theme.FONT_COUNTER, text_color=theme.TEXT_FAINT
        )
        self._counter.pack(side="right")

        self._list = ctk.CTkScrollableFrame(
            listing,
            fg_color=theme.SURFACE,
            scrollbar_button_color=theme.BORDER,
            scrollbar_button_hover_color=theme.TEXT_FAINT,
            corner_radius=10,
        )
        self._list.grid(row=1, column=0, sticky="nsew")
        self._list.grid_columnconfigure(0, weight=1)

        self._placeholder = ctk.CTkLabel(
            self._list,
            text="No snapshots yet.\nClick 'Save Current Layout' to create one.",
            font=theme.FONT_EMPTY,
            text_color=theme.TEXT_FAINT,
            justify="center",
        )

        ctk.CTkFrame(self, height=1, fg_color=theme.BORDER).grid(
            row=1, column=0, sticky="ew", padx=24
        )

        self._status = ctk.CTkLabel(
            self,
            text="Ready.",
            font=theme.FONT_META,
            text_color=theme.TEXT_FAINT,
            anchor="w",
        )
        self._status.grid(row=2, column=0, sticky="ew", padx=26, pady=(4, 2))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=24, pady=(4, 20))
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(
            footer,
            text="SAVE CURRENT LAYOUT",
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.BACKGROUND,
            font=theme.FONT_BUTTON_BOLD,
            height=42,
            corner_radius=theme.RADIUS,
            command=self.save_layout,
        ).grid(row=0, column=0, sticky="ew")

    def _centre(self) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth() - WINDOW_WIDTH) // 2
        y = (self.winfo_screenheight() - WINDOW_HEIGHT) // 2
        self.geometry(f"+{x}+{y}")

    def _fade_in(self, alpha: float) -> None:
        alpha = min(1.0, alpha + 0.08)
        self.attributes("-alpha", alpha)
        if alpha < 1.0:
            self.after(12, self._fade_in, alpha)

    def _apply_window_icon(self) -> None:
        """Draw a violet dot to use as the window icon.

        Tk otherwise shows its own feather, and a PhotoImage built at runtime
        avoids shipping a second icon file alongside the .ico used by the exe.
        """
        size = 32
        centre = size / 2
        radius = centre - 1
        rows = []
        for y in range(size):
            row = []
            for x in range(size):
                distance = ((x - centre + 0.5) ** 2 + (y - centre + 0.5) ** 2) ** 0.5
                if distance < radius:
                    row.append(
                        theme.blend(theme.ACCENT, "#ffffff", 1.0 - distance / radius)
                    )
                else:
                    row.append(theme.BACKGROUND)
            rows.append("{" + " ".join(row) + "}")

        try:
            image = tk.PhotoImage(width=size, height=size)
            image.put(" ".join(rows))
            self.iconphoto(True, image)
        except tk.TclError:
            return
        # Tk keeps only a weak reference to the image, so without this the icon
        # is collected and the window silently falls back to the feather.
        self._icon_image = image

    # Snapshot list

    def _refresh(self) -> None:
        for row in self._rows.values():
            row.destroy()
        self._rows.clear()

        snapshots = self.store.newest_first()
        if not snapshots:
            self._placeholder.grid(row=0, column=0, pady=30)
        else:
            self._placeholder.grid_remove()
            for index, snapshot in enumerate(snapshots):
                row = SnapshotRow(
                    self._list,
                    snapshot,
                    on_select=self._select,
                    on_restore=self.restore_layout,
                    on_rename=self.rename_snapshot,
                    on_delete=self.delete_snapshot,
                )
                row.grid(row=index, column=0, sticky="ew", padx=4, pady=3)
                self._rows[snapshot.name] = row

        total = len(self.store)
        self._counter.configure(text=f"{total} saved" if total else "")

    def _select(self, name: str) -> None:
        for row_name, row in self._rows.items():
            row.set_selected(row_name == name)

    def _report(self, message: str, colour: str = theme.TEXT_FAINT) -> None:
        self._status.configure(text=message, text_color=colour)
        self.after(
            STATUS_RESET_MS,
            lambda: self._status.configure(text_color=theme.TEXT_FAINT),
        )

    # Actions

    def save_layout(self) -> None:
        name = dialogs.ask_string(
            self,
            "Save Snapshot",
            "Name for this layout:",
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        if not name:
            return

        try:
            snapshot = self.store.add(name, read_icons())
        except Exception as exc:
            dialogs.error(self, "Error", str(exc))
            return

        self._refresh()
        self._report(
            f"✓  Saved '{snapshot.name}' — {snapshot.icon_count} icons.", theme.SUCCESS
        )

    def restore_layout(self, name: str) -> None:
        targets = self.store[name].targets
        try:
            moved = restore_icons(targets)
        except Exception as exc:
            dialogs.error(self, "Error", str(exc))
            return

        self._report(
            f"✓  Restored '{name}' — {moved}/{len(targets)} icons.", theme.SUCCESS
        )

    def rename_snapshot(self, name: str) -> None:
        new_name = dialogs.ask_string(self, "Rename", "New name:", name)
        if not new_name or new_name == name:
            return

        self.store.rename(name, new_name)
        self._refresh()
        self._report(f"Renamed '{name}' → '{new_name}'.")

    def delete_snapshot(self, name: str) -> None:
        if not dialogs.confirm(self, "Delete", f"Delete '{name}'?"):
            return

        self.store.delete(name)
        self._refresh()
        self._report(f"Deleted '{name}'.")
