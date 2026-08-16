from __future__ import annotations

import ctypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

user32.FindWindowW.restype = ctypes.c_void_p
user32.FindWindowExW.restype = ctypes.c_void_p
user32.GetWindowThreadProcessId.restype = ctypes.c_ulong
user32.InvalidateRect.restype = ctypes.c_bool
user32.SendMessageW.restype = ctypes.c_ssize_t
user32.SendMessageW.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint,
    ctypes.c_void_p,
    ctypes.c_void_p,
]

kernel32.OpenProcess.restype = ctypes.c_void_p
kernel32.VirtualAllocEx.restype = ctypes.c_void_p
kernel32.VirtualAllocEx.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.c_ulong,
    ctypes.c_ulong,
]
kernel32.ReadProcessMemory.restype = ctypes.c_bool
kernel32.WriteProcessMemory.restype = ctypes.c_bool
kernel32.VirtualFreeEx.restype = ctypes.c_bool
kernel32.CloseHandle.restype = ctypes.c_bool

# VM_OPERATION | VM_READ | VM_WRITE | QUERY_INFORMATION
PROCESS_ACCESS = 0x0438
MEM_COMMIT_RESERVE = 0x3000
MEM_RELEASE = 0x8000
PAGE_READWRITE = 0x04

LVM_GETITEMCOUNT = 0x1004
LVM_GETITEMPOS = 0x1010
LVM_GETITEMTEXTW = 0x1073
LVM_SETITEMPOS32 = 0x1031
LVIF_TEXT = 0x0001

TEXT_MAX = 260
POINT_SIZE = 8


class DesktopUnavailable(RuntimeError):
    """The desktop icon list could not be reached."""


class LVITEM(ctypes.Structure):
    """Win32 LVITEMW. The layout has to match explorer's 64-bit build exactly,
    so pszText is a void pointer rather than a string type."""

    _fields_ = [
        ("mask", ctypes.c_uint),
        ("iItem", ctypes.c_int),
        ("iSubItem", ctypes.c_int),
        ("state", ctypes.c_uint),
        ("stateMask", ctypes.c_uint),
        ("pszText", ctypes.c_void_p),
        ("cchTextMax", ctypes.c_int),
        ("iImage", ctypes.c_int),
        ("lParam", ctypes.c_ssize_t),
        ("iIndent", ctypes.c_int),
        ("iGroupId", ctypes.c_int),
        ("cColumns", ctypes.c_uint),
        ("puColumns", ctypes.c_void_p),
        ("piColFmt", ctypes.c_void_p),
        ("iGroup", ctypes.c_int),
    ]


def _find_listview():
    """Return the handle of the SysListView32 holding the desktop icons."""
    progman = user32.FindWindowW("Progman", None)
    defview = user32.FindWindowExW(progman, None, "SHELLDLL_DefView", None)
    listview = user32.FindWindowExW(defview, None, "SysListView32", None)
    if listview:
        return listview

    worker = None
    while True:
        worker = user32.FindWindowExW(None, worker, "WorkerW", None)
        if not worker:
            return None
        defview = user32.FindWindowExW(worker, None, "SHELLDLL_DefView", None)
        if defview:
            listview = user32.FindWindowExW(defview, None, "SysListView32", None)
            if listview:
                return listview


def _open_explorer(listview):
    """Open the explorer.exe process that owns *listview*."""
    pid = ctypes.c_ulong(0)
    user32.GetWindowThreadProcessId(listview, ctypes.byref(pid))

    process = kernel32.OpenProcess(PROCESS_ACCESS, False, pid.value)
    if not process:
        raise DesktopUnavailable(
            f"Could not open explorer.exe (error {ctypes.GetLastError()}). "
            "Try running Resti as Administrator."
        )
    return process


def _iter_icons(listview, process):
    """Yield ``(index, name, x, y)`` for every icon on the desktop."""
    count = user32.SendMessageW(listview, LVM_GETITEMCOUNT, None, None)
    item_size = ctypes.sizeof(LVITEM)
    copied = ctypes.c_size_t(0)

    remote_item = None
    remote_point = None
    try:
        remote_item = kernel32.VirtualAllocEx(
            process, None, item_size + TEXT_MAX * 2, MEM_COMMIT_RESERVE, PAGE_READWRITE
        )
        remote_point = kernel32.VirtualAllocEx(
            process, None, POINT_SIZE, MEM_COMMIT_RESERVE, PAGE_READWRITE
        )
        if not remote_item or not remote_point:
            raise DesktopUnavailable("Could not allocate memory in explorer.exe.")

        # The label buffer sits directly after the LVITEM in the same allocation.
        remote_text = remote_item + item_size

        for index in range(count):
            item = LVITEM()
            item.mask = LVIF_TEXT
            item.iItem = index
            item.iSubItem = 0
            item.pszText = remote_text
            item.cchTextMax = TEXT_MAX - 1

            raw = (ctypes.c_char * item_size).from_buffer_copy(item)
            kernel32.WriteProcessMemory(
                process, remote_item, raw, item_size, ctypes.byref(copied)
            )
            user32.SendMessageW(
                listview,
                LVM_GETITEMTEXTW,
                ctypes.c_void_p(index),
                ctypes.c_void_p(remote_item),
            )

            text = ctypes.create_string_buffer(TEXT_MAX * 2)
            kernel32.ReadProcessMemory(
                process, remote_text, text, TEXT_MAX * 2, ctypes.byref(copied)
            )
            # The buffer is not cleared between items, so cut at the first NUL
            # rather than stripping trailing ones — otherwise a short label keeps
            # the tail of the previous, longer one.
            name = text.raw.decode("utf-16-le").split("\x00")[0]

            user32.SendMessageW(
                listview,
                LVM_GETITEMPOS,
                ctypes.c_void_p(index),
                ctypes.c_void_p(remote_point),
            )
            point = ctypes.create_string_buffer(POINT_SIZE)
            kernel32.ReadProcessMemory(
                process, remote_point, point, POINT_SIZE, ctypes.byref(copied)
            )
            x = int.from_bytes(point.raw[:4], "little", signed=True)
            y = int.from_bytes(point.raw[4:], "little", signed=True)

            yield index, name, x, y
    finally:
        if remote_item:
            kernel32.VirtualFreeEx(process, remote_item, 0, MEM_RELEASE)
        if remote_point:
            kernel32.VirtualFreeEx(process, remote_point, 0, MEM_RELEASE)


def read_icons() -> list[dict]:
    """Return ``[{"name": str, "x": int, "y": int}, ...]`` for the current layout."""
    listview = _find_listview()
    if not listview:
        raise DesktopUnavailable("Desktop icon list not found.")

    process = _open_explorer(listview)
    try:
        return [
            {"name": name, "x": x, "y": y}
            for _, name, x, y in _iter_icons(listview, process)
        ]
    finally:
        kernel32.CloseHandle(process)


def restore_icons(targets: dict[str, tuple[int, int]]) -> int:
    """Move every icon named in *targets* back to its saved position.

    *targets* maps a lower-cased icon label to an ``(x, y)`` pair. Icons that are
    no longer on the desktop are skipped. Returns how many were moved.
    """
    listview = _find_listview()
    if not listview:
        raise DesktopUnavailable("Desktop icon list not found.")

    process = _open_explorer(listview)
    moved = 0
    copied = ctypes.c_size_t(0)
    remote_point = None
    try:
        remote_point = kernel32.VirtualAllocEx(
            process, None, POINT_SIZE, MEM_COMMIT_RESERVE, PAGE_READWRITE
        )
        if not remote_point:
            raise DesktopUnavailable("Could not allocate memory in explorer.exe.")

        for index, name, _, _ in _iter_icons(listview, process):
            position = targets.get(name.lower())
            if position is None:
                continue

            x, y = position
            # LVM_SETITEMPOS32 takes a POINT* in lParam, unlike LVM_SETITEMPOSITION
            # which packs the coordinates into the lParam itself and so is capped
            # at 16 bits per axis.
            point = ctypes.create_string_buffer(
                x.to_bytes(4, "little", signed=True)
                + y.to_bytes(4, "little", signed=True)
            )
            kernel32.WriteProcessMemory(
                process, remote_point, point, POINT_SIZE, ctypes.byref(copied)
            )
            user32.SendMessageW(
                listview,
                LVM_SETITEMPOS32,
                ctypes.c_void_p(index),
                ctypes.c_void_p(remote_point),
            )
            moved += 1

        user32.InvalidateRect(ctypes.c_void_p(listview), None, True)
    finally:
        if remote_point:
            kernel32.VirtualFreeEx(process, remote_point, 0, MEM_RELEASE)
        kernel32.CloseHandle(process)

    return moved
