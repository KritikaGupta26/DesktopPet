"""Water Panda: a tiny roaming reminder companion for Windows."""

from __future__ import annotations

import csv
import ctypes
import json
import math
import time
import os
import random
import signal
import shutil
import sqlite3
import subprocess
import sys
import textwrap
import queue
import threading
import traceback
from contextlib import closing
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk


ACTIVITY_LABELS = {
    "feed":"Feed bamboo", "walk":"Walk", "run":"Run", "jump":"Jump", "cursor_follow":"Follow cursor",
    "cursor_avoid":"Avoid cursor", "fetch":"Fetch", "log":"Play on log", "bamboo_hang":"Hang on bamboo",
    "kung_fu":"Kung fu", "wind_down":"Wind down",
    "sneeze":"Sneeze", "meditate":"Meditate", "sploot":"Sploot", "dance":"Dance",
    "forward_roll":"Somersault", "petting":"Petting", "bow":"Bow", "water":"Water reminder",
    "movement":"Movement break", "watch":"Personal reminder", "wave":"Wave", "groom":"Grooming",
    "peekaboo":"Peekaboo", "clap":"Clap", "blow_kiss":"Blow a kiss",
    "hiccup":"Hiccup", "victory":"Celebrate",
}
ACTIVITY_ALIASES = {
    "ear_rub":"groom", "wash_face":"groom", "belly_scratch":"groom",
    "yawn_stretch":"wind_down", "lazy_stretch":"wind_down", "sleep":"wind_down", "side_roll":"forward_roll", "eat_bamboo":"feed", "wiggle":"dance", "greeting":"wave", "snore_sleep":"wind_down",
    "sit_on_log":"log", "balance_on_log":"log", "bored_shuffle":"log", "sit_down":"sploot",
    "wake_up":"wind_down", "carry_bamboo":"feed", "water_offer":"water", "alternate_offer":"water",
    "drink_water":"water", "alternate_hoop":"movement", "hula_hoop":"movement",
    "chase_ball":"fetch", "catch_ball":"fetch", "happy_idle":"wave", "sad":"bow",
}
ROUTINE_ACTIVITIES = ("groom", "wind_down", "dance", "kung_fu", "peekaboo", "clap", "blow_kiss", "forward_roll", "log")
GENTLE_ACTIVITIES = ROUTINE_ACTIVITIES[:2]
GROOM_SEQUENCE = (("wash_face", 3.0), ("ear_rub", 3.0), ("belly_scratch", 3.0))
WIND_DOWN_SEQUENCE = (("yawn_stretch", 3.0), ("lazy_stretch", 3.0), ("sleep", 18.0), ("wake_up", 4.0))

def sequence_pose(sequence, elapsed: float) -> tuple[str, float]:
    remaining = max(0.0, elapsed)
    for key, duration in sequence:
        if remaining < duration:
            return key, remaining
        remaining -= duration
    return sequence[-1][0], sequence[-1][1]

def wind_down_pose(elapsed: float) -> tuple[str, float]:
    return sequence_pose(WIND_DOWN_SEQUENCE, elapsed)

def normalize_standing_sprite(sprite: Image.Image) -> Image.Image:
    # One scale for the entire idle row, with the same ground anchor as walking.
    enlarged = sprite.resize((625, 625), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (512, 512))
    canvas.alpha_composite(enlarged, ((512-625)//2, 489-round(489*625/512)))
    return canvas



APP_NAME = "WaterPuppy"
APP_VERSION = 25
REMINDER_MINUTES = 30
WATER_DECLINE_SECONDS = 8
WALK_FRAME_ORDER = (0, 1, 2, 4, 5, 6)
TRANSPARENT_COLOR = "#00ff01"
SMALL_WIDTH = 180
SMALL_HEIGHT = 184
PET_CENTER_Y = 94
PET_GROUND_Y = 169
PROMPT_WIDTH = 360
PROMPT_HEIGHT = 324
ACTIVE_TICK_MILLISECONDS = 80
IDLE_TICK_MILLISECONDS = 250
HIDDEN_TICK_MILLISECONDS = 1000

PALETTE = {
    "ink": "#332E48",
    "muted": "#746F86",
    "lavender": "#EEE8FF",
    "purple": "#8C72D8",
    "purple_dark": "#6651AF",
    "mint": "#DDF8EE",
    "teal": "#55BFA6",
    "cream": "#FFFCF6",
    "rose": "#FFE7EF",
    "sky": "#E3F4FF",
}

GLASS = {
    "window": "#111318",
    "rail": "#151820",
    "surface": "#1C2029",
    "surface_hover": "#272C37",
    "border": "#343A46",
    "text": "#F7F8FC",
    "muted": "#A7AFBF",
    "accent": "#7C6CF2",
    "accent_hover": "#9285FF",
    "aqua": "#67D8C2",
    "danger": "#FF8FA3",
}

PET_LABELS = {"panda": "Panda"}

COMMON_STATES = ("meditate_hd",) + tuple(f"feed_{i}" for i in range(4)) + tuple(f"offer_{i}" for i in range(8)) + tuple(f"hoop_{i}" for i in range(8)) + tuple(f"clock_{i}" for i in range(6)) + (
    "water_bring",
    "bow_hd",
    "water_reach",
    "idle_hd",
    "normal",
    "blink",
    "asking",
    "happy",
    "sad",
    "yawn_1",
    "yawn_2",
    "sleep",
    "wave",
    "nuzzle",
    "kungfu",
    "stretch",
    "somersault",
    "sneeze",
    "meditate",
    "sploot",
    "staff",
    "bow",
    "fetch_look",
    "fetch_chase",
    "fetch_carry",
    "fetch_offer",
    "walk_right_1",
    "walk_right_2",
    "walk_right_3",
    "walk_right_4",
    "walk_right_5",
    "walk_right_6",
    "walk_right_7",
    "walk_right_8",
    "walk_left_1",
    "walk_left_2",
    "walk_left_3",
    "walk_left_4",
    "walk_left_5",
    "walk_left_6",
    "walk_left_7",
    "walk_left_8",
    "run_right_1",
    "run_right_2",
    "run_right_3",
    "run_right_4",
    "run_left_1",
    "run_left_2",
    "run_left_3",
    "run_left_4",
    "bored_1",
    "bored_2",
    "bored_3",
    "bored_4",
    "bored_5",
    "bored_6",
    "bored_7",
    "bored_8",
    "hula_1",
    "hula_2",
    "watch",
    "water",
    "bored_walk_right_1",
    "bored_walk_right_2",
    "bored_walk_left_1",
    "bored_walk_left_2",
)

PET_ACTIONS = {
    "panda": ("action_bamboo", "action_hang"),
}

FREE_IDLE_MOODS = (
    "stretch",
    "somersault",
    "sneeze",
    "meditate",
    "sploot",
    "bow",
)

EDGE_ACTIONS = ("bored_edge",)

PET_CHATTER = {
    "panda": (
        "Sip, stretch, repeat.",
        "Bamboo break!",
        "You’re doing lovely.",
        "A little water magic?",
    ),
}

PET_REACTIONS = {
    "panda": ("So cozy!", "Panda hug!", "Hehe!"),
}

TIME_CHATTER = {
    "morning": (
        "Good morning, sunshine!",
        "Tiny morning stretch?",
        "Panda mode: awake-ish.",
    ),
    "afternoon": (
        "Panda productivity patrol!",
        "How are you doing, really?",
        "A tiny pause can help.",
    ),
    "evening": (
        "You did enough today.",
        "Soft evening panda vibes.",
        "Shoulders down, deep breath.",
    ),
    "late": (
        "Still here with you.",
        "Late-night panda shift!",
        "Be gentle with yourself.",
    ),
}

WATER_PROMPTS = (
    "Water moment!",
    "Tiny sip check!",
    "Hydration high-five?",
    "Did you have some water?",
)

MOVEMENT_PROMPTS = (
    ("Hula with Mochi", "Stand, circle your hips, and move for one minute"),
    ("Tiny hoop break", "Roll your shoulders and move with your panda"),
    ("Uncurl with me", "Hula, stretch, or walk for one playful minute"),
)


def pythonw_path() -> Path:
    executable = Path(sys.executable)
    candidate = executable.with_name("pythonw.exe")
    return candidate if candidate.exists() else executable


def enable_windows_dpi_awareness() -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


class StudioPageSwitcher:
    """Small navigation controller used instead of dated notebook tabs."""

    def __init__(self, pages: list[tk.Widget], buttons: list[tk.Button]) -> None:
        self.pages = pages
        self.buttons = buttons
        self.current = 0

    def winfo_exists(self) -> bool:
        return bool(self.pages and self.pages[0].winfo_exists())

    def select(self, index: int) -> None:
        if not 0 <= index < len(self.pages):
            return
        self.current = index
        self.pages[index].tkraise()
        for button_index, button in enumerate(self.buttons):
            selected = button_index == index
            button.configure(
                bg=GLASS["surface_hover"] if selected else GLASS["rail"],
                fg=GLASS["text"] if selected else GLASS["muted"],
                activebackground=GLASS["surface_hover"],
                activeforeground=GLASS["text"],
            )


class WindowsTray:
    """Dependency-free Windows notification-area icon and native menu."""

    WM_APP = 0x8000
    WM_TRAY = WM_APP + 41
    WM_COMMAND = 0x0111
    WM_DESTROY = 0x0002
    WM_CLOSE = 0x0010
    WM_LBUTTONDBLCLK = 0x0203
    WM_RBUTTONUP = 0x0205
    NIM_ADD = 0x00000000
    NIM_DELETE = 0x00000002
    NIF_MESSAGE = 0x00000001
    NIF_ICON = 0x00000002
    NIF_TIP = 0x00000004
    IMAGE_ICON = 1
    LR_LOADFROMFILE = 0x0010
    LR_DEFAULTSIZE = 0x0040
    MF_STRING = 0x0000
    MF_SEPARATOR = 0x0800
    TPM_RETURNCMD = 0x0100
    TPM_RIGHTBUTTON = 0x0002

    def __init__(self, icon_path: Path) -> None:
        self.icon_path = icon_path
        self.actions: queue.Queue[str] = queue.Queue()
        self.thread: threading.Thread | None = None
        self.hwnd = 0
        self.ready = threading.Event()
        self._wndproc = None
        self._nid = None
        self.roaming_enabled = True
        self.error = ""
        self.icon_added = False

    def start(self) -> None:
        if os.name != "nt" or self.thread is not None:
            return
        self.thread = threading.Thread(target=self._safe_message_loop, daemon=True)
        self.thread.start()
        self.ready.wait(timeout=2)

    def stop(self) -> None:
        if os.name != "nt" or not self.hwnd:
            return
        try:
            ctypes.windll.user32.PostMessageW(self.hwnd, self.WM_CLOSE, 0, 0)
        except (AttributeError, OSError):
            pass

    def get_action(self) -> str | None:
        try:
            return self.actions.get_nowait()
        except queue.Empty:
            return None

    def _safe_message_loop(self) -> None:
        try:
            self._message_loop()
        except Exception:
            self.error = traceback.format_exc()
            self.ready.set()

    def _message_loop(self) -> None:
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        shell32 = ctypes.windll.shell32
        kernel32 = ctypes.windll.kernel32
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        user32.CreatePopupMenu.restype = wintypes.HMENU
        user32.LoadImageW.restype = wintypes.HANDLE
        user32.LoadIconW.restype = wintypes.HICON
        user32.DefWindowProcW.restype = ctypes.c_ssize_t

        WNDPROC = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )

        class WNDCLASSW(ctypes.Structure):
            _fields_ = [
                ("style", wintypes.UINT),
                ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE),
                ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
            ]

        class NOTIFYICONDATAW(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("hWnd", wintypes.HWND),
                ("uID", wintypes.UINT),
                ("uFlags", wintypes.UINT),
                ("uCallbackMessage", wintypes.UINT),
                ("hIcon", wintypes.HICON),
                ("szTip", wintypes.WCHAR * 128),
                ("dwState", wintypes.DWORD),
                ("dwStateMask", wintypes.DWORD),
                ("szInfo", wintypes.WCHAR * 256),
                ("uTimeoutOrVersion", wintypes.UINT),
                ("szInfoTitle", wintypes.WCHAR * 64),
                ("dwInfoFlags", wintypes.DWORD),
                ("guidItem", ctypes.c_byte * 16),
                ("hBalloonIcon", wintypes.HICON),
            ]

        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
        user32.RegisterClassW.restype = wintypes.WORD
        user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
                                         ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                         wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes.c_void_p]
        user32.DefWindowProcW.argtypes = [wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
        user32.LoadImageW.argtypes = [wintypes.HINSTANCE,wintypes.LPCWSTR,wintypes.UINT,ctypes.c_int,ctypes.c_int,wintypes.UINT]
        user32.LoadIconW.argtypes = [wintypes.HINSTANCE,ctypes.c_void_p]
        user32.AppendMenuW.argtypes = [wintypes.HMENU,wintypes.UINT,ctypes.c_size_t,wintypes.LPCWSTR]
        user32.TrackPopupMenu.argtypes = [wintypes.HMENU,wintypes.UINT,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.HWND,ctypes.c_void_p]
        user32.TrackPopupMenu.restype = wintypes.UINT
        user32.DestroyMenu.argtypes = [wintypes.HMENU]
        user32.DestroyWindow.argtypes = [wintypes.HWND]
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
        user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG),wintypes.HWND,wintypes.UINT,wintypes.UINT]
        user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
        user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
        user32.DispatchMessageW.restype = ctypes.c_ssize_t
        user32.PostMessageW.argtypes = [wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
        shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD,ctypes.POINTER(NOTIFYICONDATAW)]
        shell32.Shell_NotifyIconW.restype = wintypes.BOOL

        command_map = {
            1001: "open",
            1002: "ask_water",
            1003: "toggle_roam",
            1005: "reminder",
            1006: "pause",
            1007: "resume",
            1008: "exit",
        }

        def show_menu(hwnd: int) -> None:
            menu = user32.CreatePopupMenu()
            user32.AppendMenuW(menu, self.MF_STRING, 1001, "Open Panda Home")
            user32.AppendMenuW(menu, self.MF_SEPARATOR, 0, None)
            roaming_label = "Disable roaming" if self.roaming_enabled else "Enable roaming"
            user32.AppendMenuW(menu, self.MF_STRING, 1003, roaming_label)
            user32.AppendMenuW(menu, self.MF_STRING, 1002, "Ask for water now")
            user32.AppendMenuW(menu, self.MF_STRING, 1006, "Pause water reminders for 1 hour")
            user32.AppendMenuW(menu, self.MF_STRING, 1007, "Resume water reminders")
            user32.AppendMenuW(menu, self.MF_STRING, 1005, "Add personal reminder")
            user32.AppendMenuW(menu, self.MF_SEPARATOR, 0, None)
            user32.AppendMenuW(menu, self.MF_STRING, 1008, "Exit Water Panda")
            point = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(point))
            user32.SetForegroundWindow(hwnd)
            selected = user32.TrackPopupMenu(
                menu,
                self.TPM_RETURNCMD | self.TPM_RIGHTBUTTON,
                point.x,
                point.y,
                0,
                hwnd,
                None,
            )
            user32.DestroyMenu(menu)
            action = command_map.get(int(selected))
            if action:
                self.actions.put(action)

        @WNDPROC
        def wndproc(hwnd, message, wparam, lparam):
            if message == self.WM_TRAY:
                event = int(lparam) & 0xFFFF
                if event == self.WM_LBUTTONDBLCLK:
                    self.actions.put("open")
                elif event == self.WM_RBUTTONUP:
                    show_menu(hwnd)
                return 0
            if message == self.WM_CLOSE:
                if self._nid is not None:
                    shell32.Shell_NotifyIconW(self.NIM_DELETE, ctypes.byref(self._nid))
                user32.DestroyWindow(hwnd)
                return 0
            if message == self.WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, message, wparam, lparam)

        self._wndproc = wndproc
        instance = kernel32.GetModuleHandleW(None)
        class_name = f"WaterPandaTray_{os.getpid()}"
        window_class = WNDCLASSW()
        window_class.lpfnWndProc = wndproc
        window_class.hInstance = instance
        window_class.lpszClassName = class_name
        user32.RegisterClassW(ctypes.byref(window_class))
        user32.CreateWindowExW.restype = wintypes.HWND
        hwnd = user32.CreateWindowExW(
            0, class_name, "Water Panda", 0, 0, 0, 0, 0,
            None, None, instance, None,
        )
        self.hwnd = int(hwnd or 0)
        if not self.hwnd:
            self.error = f"CreateWindowExW failed: {kernel32.GetLastError()}"
            self.ready.set()
            return

        icon = user32.LoadImageW(
            None,
            str(self.icon_path),
            self.IMAGE_ICON,
            0,
            0,
            self.LR_LOADFROMFILE | self.LR_DEFAULTSIZE,
        )
        if not icon:
            icon = user32.LoadIconW(None, 32512)
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = hwnd
        nid.uID = 1
        nid.uFlags = self.NIF_MESSAGE | self.NIF_ICON | self.NIF_TIP
        nid.uCallbackMessage = self.WM_TRAY
        nid.hIcon = icon
        nid.szTip = "Water Panda"
        self._nid = nid
        self.icon_added = bool(shell32.Shell_NotifyIconW(self.NIM_ADD, ctypes.byref(nid)))
        self.ready.set()

        message = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(message))
            user32.DispatchMessageW(ctypes.byref(message))


def set_startup(enabled: bool, script_path: Path) -> None:
    if os.name != "nt":
        return
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        key_path,
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        if enabled:
            command = (
                f'"{script_path}"'
                if script_path.suffix.lower() == ".exe"
                else f'"{pythonw_path()}" "{script_path}"'
            )
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass


def stop_installed_copy(install_dir: Path) -> None:
    pid_file = install_dir / "water_puppy.pid"
    if not pid_file.exists():
        return
    try:
        old_pid = int(pid_file.read_text(encoding="utf-8").strip())
        os.kill(old_pid, signal.SIGTERM)
    except (OSError, ValueError):
        pass
    try:
        pid_file.unlink(missing_ok=True)
    except OSError:
        pass


def ensure_single_instance(app_dir: Path) -> None:
    pid_file = app_dir / "water_puppy.pid"
    if not pid_file.exists():
        return
    try:
        existing_pid = int(pid_file.read_text(encoding="utf-8").strip())
        if existing_pid != os.getpid():
            os.kill(existing_pid, 0)
            messagebox.showinfo(
                "Water Panda",
                "Your Water Panda is already playing on the desktop.",
            )
            raise SystemExit
    except (OSError, ValueError):
        try:
            pid_file.unlink(missing_ok=True)
        except OSError:
            pass


def install_and_restart_if_needed() -> None:
    if os.name != "nt":
        return
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()
        set_startup(True, executable)
        for old_script in executable.parent.glob("Start_Water_*.pyw"):
            try:
                old_script.unlink()
            except OSError:
                pass
        return

    source_script = Path(__file__).resolve()
    install_dir = Path(os.environ["LOCALAPPDATA"]) / APP_NAME

    if source_script.parent == install_dir:
        set_startup(True, source_script)
        for pattern in ("Start_Water_Puppy.pyw", "Start_Water_Panda_v*.pyw"):
            for old_script in install_dir.glob(pattern):
                if old_script == source_script:
                    continue
                try:
                    old_script.unlink()
                except OSError:
                    pass
        return

    install_dir.mkdir(parents=True, exist_ok=True)
    version_stamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    installed_script = install_dir / (
        f"Start_Water_Panda_v{APP_VERSION}_{version_stamp}.pyw"
    )

    # Always install to a new filename. Windows may keep the previous Python
    # script locked briefly while its background process is closing.
    shutil.copy2(source_script, installed_script)
    installed_assets = install_dir / "assets"
    source_assets = source_script.parent / "assets"
    if installed_assets.exists():
        for obsolete_pattern in ("puppy_*.png", "penguin_*.png"):
            for obsolete_asset in installed_assets.glob(obsolete_pattern):
                try:
                    obsolete_asset.unlink()
                except OSError:
                    pass
        current_asset_names = {
            asset.name for asset in source_assets.iterdir() if asset.is_file()
        }
        for installed_asset in installed_assets.glob("panda_*.png"):
            if installed_asset.name not in current_asset_names:
                try:
                    installed_asset.unlink()
                except OSError:
                    pass
    shutil.copytree(
        source_assets,
        install_dir / "assets",
        dirs_exist_ok=True,
    )
    stop_installed_copy(install_dir)
    set_startup(True, installed_script)
    subprocess.Popen(
        [str(pythonw_path()), str(installed_script)],
        cwd=str(install_dir),
        close_fds=True,
    )
    messagebox.showinfo(
        "Water Panda",
        "Your Water Panda is ready.\n\n"
        "Click it for a little reaction, drag it anywhere, or "
        "double-click to open Panda Home.",
    )
    raise SystemExit


class WaterPet:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Water Panda")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=TRANSPARENT_COLOR)
        try:
            self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        except tk.TclError:
            pass

        self.canvas = tk.Canvas(
            self.root,
            width=SMALL_WIDTH,
            height=SMALL_HEIGHT,
            bg=TRANSPARENT_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.app_dir = (
            Path(sys.executable).resolve().parent
            if getattr(sys, "frozen", False)
            else Path(__file__).resolve().parent
        )
        data_dir = Path(os.environ.get("WATER_PANDA_DATA_DIR", str(self.app_dir)))
        data_dir.mkdir(parents=True, exist_ok=True)
        self.settings_path = data_dir / "settings.json"
        self.database_path = data_dir / "water_history.db"
        self.images = self._load_images()
        self._initialize_database()
        self.cache_date = datetime.now().date()
        self.today_total_cache = self._today_total()

        self.settings = self._load_settings()
        self.pat_count = int(self.settings["pat_count"])
        self.adopted_at = str(self.settings["adopted_at"])
        self.pet_type = tk.StringVar(value=self.settings["pet"])
        self.pet_name = tk.StringVar(value=self.settings["name"])
        self.roam_enabled = tk.BooleanVar(value=self.settings["wander"])
        self.sound_enabled = tk.BooleanVar(value=self.settings["sound"])
        self.hide_fullscreen = tk.BooleanVar(
            value=self.settings["hide_fullscreen"]
        )
        self.personality = tk.StringVar(value=self.settings["personality"])
        self.cursor_mode = tk.StringVar(value=self.settings["cursor_mode"])
        self.cursor_session_kind = ""
        self.cursor_session_until = None
        self.last_routine_key = ""
        self.cursor_games = tk.BooleanVar(value=self.settings["cursor_games"])
        self.sleep_enabled = tk.BooleanVar(value=self.settings["sleep_enabled"])
        self.roam_rest_seconds = tk.IntVar(value=self.settings["roam_rest_seconds"])
        self.sleep_after_minutes = tk.IntVar(value=self.settings["sleep_after_minutes"])
        self.yawn_after_seconds = tk.IntVar(value=self.settings["yawn_after_seconds"])
        self.auto_activity = tk.StringVar(value=self.settings["auto_activity"])
        self.hunger_enabled = tk.BooleanVar(value=self.settings["hunger_enabled"])
        self.hunger_minutes = tk.IntVar(value=self.settings["hunger_minutes"])
        self.hungry = False
        self.hunger_requested = False
        self.next_hunger = datetime.now() + timedelta(minutes=self.hunger_minutes.get())
        self.walk_frame_ms = tk.IntVar(value=self.settings["walk_frame_ms"])
        self.routine_enabled = {key: tk.BooleanVar(value=key in self.settings["routine_activities"]) for key in ROUTINE_ACTIVITIES}
        self.routine_index = 0
        self.activity_minutes = tk.IntVar(value=self.settings["activity_minutes"])
        self.next_idle_activity = datetime.now() + timedelta(minutes=self.activity_minutes.get())
        self.movement_enabled = tk.BooleanVar(
            value=self.settings["movement_enabled"]
        )
        self.movement_minutes = tk.IntVar(
            value=self.settings["movement_minutes"]
        )
        self.state = "normal"
        self.water_prompt_text = random.choice(WATER_PROMPTS)
        self.frame = 0
        self.prompt_visible = False
        self.happy_until: datetime | None = None
        self.sad_until: datetime | None = None
        self.next_reminder = datetime.now() + timedelta(
            minutes=REMINDER_MINUTES
        )
        self.last_logged_amount = 0
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.width = SMALL_WIDTH
        self.height = SMALL_HEIGHT
        self.pet_x = 0.0
        self.pet_y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self.walk_speed = 3.0
        self.walk_direction = "left"
        self.motion_mode = "idle"
        self.current_action: str | None = None
        self.pending_edge_action: str | None = None
        self.action_until: datetime | None = None
        self.action_started_at = datetime.now()
        self.dragging = False
        self.drag_moved = False
        self.drag_start_root = (0, 0)
        self.drag_samples: list[tuple[datetime, int, int]] = []
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.idle_until = datetime.now() + timedelta(seconds=2)
        self.chatter_until: datetime | None = None
        self.chatter_text = ""
        self.chatter_window: tk.Toplevel | None = None
        self.chatter_label: tk.Label | None = None
        self.chatter_canvas: tk.Canvas | None = None
        self.chatter_geometry = ""
        self.next_chatter = datetime.now() + timedelta(
            seconds=random.uniform(45, 95)
        )
        self.idle_mood = ""
        self.idle_mood_until: datetime | None = None
        self.idle_mood_started_at = datetime.now()
        self.action_sequence_stage = -1
        self.next_idle_mood = datetime.now() + timedelta(
            seconds=random.uniform(25, 55)
        )
        self.next_cursor_reaction = datetime.now() + timedelta(seconds=2)
        self.cursor_escape_until: datetime | None = None
        self.fetch_origin: tuple[float, float] | None = None
        self.fetch_pause_until: datetime | None = None
        self.inactivity_yawn_shown = False
        self.user_was_inactive = False
        self.system_idle_seconds_cache = 0.0
        self.last_system_idle_check = datetime.min
        self.hovering = False
        self.particles: list[dict[str, float | str]] = []
        self.reminders_paused_until: datetime | None = None
        self.next_movement_reminder = datetime.now() + timedelta(
            minutes=self.movement_minutes.get()
        )
        self.last_schedule_check = datetime.min
        self.last_fullscreen_check = datetime.min
        self.alert_window: tk.Toplevel | None = None
        self.alert_pet_label: tk.Label | None = None
        self.alert_icon_label: tk.Label | None = None
        self.active_alert_id: int | None = None
        self.active_alert_kind = ""
        self.alert_title = ""
        self.alert_subtitle = ""
        self.attention_started_at: datetime | None = None
        self.attention_stage = 0
        self.next_attention_nudge: datetime | None = None
        self.attention_sound_played = False
        self.reminder_tree: ttk.Treeview | None = None
        self.reminder_feedback_var = tk.StringVar()
        self.reminder_title_var = tk.StringVar()
        self.reminder_date_var = tk.StringVar()
        self.reminder_time_var = tk.StringVar(value="01:00 PM")
        self.date_display_to_iso: dict[str, str] = {}
        self.window_ledge_cache: list[tuple[int, int, int]] = []
        self.window_ledge_cache_at = datetime.min
        self.was_hidden_for_fullscreen = False
        self.history_window: tk.Toplevel | None = None
        self.daily_tree: ttk.Treeview | None = None
        self.entry_tree: ttk.Treeview | None = None
        self.today_label: ttk.Label | None = None
        self.summary_label: ttk.Label | None = None
        self.chart_canvas: tk.Canvas | None = None
        self.name_entry: ttk.Entry | None = None
        self.studio_notebook: ttk.Notebook | None = None
        self.memories_label: ttk.Label | None = None
        self.tray = WindowsTray(self.app_dir / "assets" / "panda.ico")
        self.tray.roaming_enabled = self.roam_enabled.get()

        self._place_bottom_right()
        self.root.after(60, self._apply_pet_window_style)
        self._build_menu()
        self._bind_events()
        self._write_pid()
        self.tray.start()
        self.root.after(500, self._poll_tray)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._tick()

    def _poll_tray(self) -> None:
        while True:
            action = self.tray.get_action()
            if action is None:
                break
            if action == "open":
                self.show_history()
            elif action == "ask_water":
                self.show_prompt()
            elif action == "toggle_roam":
                self.roam_enabled.set(not self.roam_enabled.get())
                self._toggle_roaming()
            elif action == "reminder":
                self.show_reminders()
            elif action == "pause":
                self.pause_reminders()
            elif action == "resume":
                self.resume_reminders()
            elif action == "exit":
                self.close()
                return
        try:
            self.root.after(500, self._poll_tray)
        except tk.TclError:
            pass

    def _quick_log_water(self, millilitres: int) -> None:
        self.prompt_visible = True
        self.record_water(millilitres)
        self._show_chatter(f"{millilitres} ml logged from the tray ✦", seconds=4)

    def _load_images(self) -> dict[str, dict[str, ImageTk.PhotoImage]]:
        assets = self.app_dir / "assets"
        loaded: dict[str, dict[str, ImageTk.PhotoImage]] = {}
        for pet in PET_LABELS:
            loaded[pet] = {}
            states = COMMON_STATES + PET_ACTIONS[pet]
            for state in states:
                with Image.open(assets / f"{pet}_{state}.png") as opened:
                    sprite = opened.convert("RGBA")
                sprite.thumbnail((172, 172), Image.Resampling.LANCZOS)
                canvas = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
                canvas.alpha_composite(
                    sprite,
                    ((180 - sprite.width) // 2, (180 - sprite.height) // 2),
                )
                # Windows color-key windows cannot display partial alpha:
                # Tk blends translucent fur with the green key, leaving a halo.
                # Keep opaque fur pixels and make the fringe fully transparent.
                canvas.putalpha(canvas.getchannel("A").point(
                    lambda alpha: 255 if alpha >= 128 else 0
                ))
                loaded[pet][state] = ImageTk.PhotoImage(canvas)
        with Image.open(assets / "panda_somersault.png") as opened:
            rolling = opened.convert("RGBA")
        rolling.thumbnail((132, 132), Image.Resampling.LANCZOS)
        for frame in range(16):
            sprite = rolling.rotate(-22.5 * frame, Image.Resampling.BICUBIC, expand=True)
            sprite.thumbnail((166, 166), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (180, 180))
            canvas.alpha_composite(sprite, ((180-sprite.width)//2, (180-sprite.height)//2))
            canvas.putalpha(canvas.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
            loaded["panda"][f"roll_{frame}"] = ImageTk.PhotoImage(canvas)
        self.pack_manifest = json.loads((assets / "sprite_collection_manifest.json").read_text(encoding="utf-8"))
        for key, metadata in self.pack_manifest.items():
            for i in range(metadata["frames"]):
                variants = (key, key + "_left") if key in ("walk", "run") else (key,)
                for variant in variants:
                    with Image.open(assets / f"pack_{variant}_{i}.png") as opened:
                        sprite = opened.convert("RGBA")
                    if key == "happy_idle":
                        sprite = normalize_standing_sprite(sprite)
                    sprite = sprite.resize((180,180), Image.Resampling.LANCZOS)
                    sprite.putalpha(sprite.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
                    loaded["panda"][f"pack_{variant}_{i}"] = ImageTk.PhotoImage(sprite)
        return loaded

    def _pack_image(self, key: str, elapsed: float = 0.0, index: int | None = None):
        metadata = self.pack_manifest[key]
        if index is None and metadata.get("frame_seconds"):
            timings = metadata["frame_seconds"]
            position = max(0,elapsed) % sum(timings) if metadata["mode"] == "loop" else max(0,elapsed)
            index = len(timings)-1
            accumulated = 0.0
            for frame,duration in enumerate(timings):
                accumulated += duration
                if position < accumulated:
                    index = frame
                    break
        if index is None:
            index = max(0, int(elapsed / metadata["seconds_per_frame"]))
            index = index % metadata["frames"] if metadata["mode"] == "loop" else min(metadata["frames"]-1,index)
        return self.images["panda"][f"pack_{key}_{index}"]

    def _image(self, state: str) -> ImageTk.PhotoImage:
        now = datetime.now()
        started = getattr(self, "idle_mood_started_at", now) if getattr(self,"idle_mood","") else getattr(self,"action_started_at",now)
        elapsed = max(0.0,(now-started).total_seconds())
        if state.startswith("packframe:"):
            _, key, index = state.split(":")
            return self._pack_image(key, index=int(index))
        if state.startswith(("walk_", "run_")):
            parts = state.split("_");key=parts[0]
            if key == "walk":
                # Use complete coordinated key poses, never assembled limb pieces.
                index=WALK_FRAME_ORDER[(int(parts[2])-1)%len(WALK_FRAME_ORDER)]
                variant="walk_left" if parts[1]=="left" else "walk"
                return self.images["panda"][f"pack_{variant}_{index}"]
            index = (int(parts[2]) - 1) % self.pack_manifest[key]["frames"]
            variant = key + "_left" if parts[1] == "left" else key
            return self.images["panda"][f"pack_{variant}_{index}"]
        for prefix,key in (("offer_","water_offer"),("hoop_","hula_hoop"),("clock_","watch")):
            if state.startswith(prefix):
                return self._pack_image(key,index=int(state.rsplit("_",1)[1]))
        aliases = {"normal":"happy_idle","blink":"happy_idle","happy":"victory","sad":"sad",
                   "asking":"cursor_follow","wave":"wave","nuzzle":"petting","kungfu":"kung_fu",
                   "bow":"bow","stretch":"lazy_stretch","sneeze":"sneeze","sploot":"sploot",
                   "yawn_1":"yawn_stretch","yawn_2":"yawn_stretch","sleep":"sleep","staff":"carry_bamboo",
                   "fetch_look":"fetch","fetch_chase":"chase_ball","fetch_carry":"fetch","fetch_offer":"catch_ball",
                   "somersault":"forward_roll"}
        if state in aliases:
            if state in ("normal","blink","sad"):elapsed=now.timestamp()
            return self._pack_image(aliases[state],elapsed)
        if state == "meditate":state="meditate_hd"
        return self.images[self.pet_type.get()][state]

    def _play_pack_animation(self, key: str) -> None:
        if self.prompt_visible or self.active_alert_kind or self.dragging or self.state == "sad":
            return
        canonical=ACTIVITY_ALIASES.get(key,key)
        if canonical != key or key in ("cursor_follow","cursor_avoid"):
            self._play_activity(canonical)
            return
        metadata = self.pack_manifest[key]
        if key in ("walk", "run"):
            self._test_walk_across_screen()
            if key == "run":
                self.walk_speed = 7.5
                self.motion_mode = "escaping"
                self.cursor_escape_until = datetime.now() + timedelta(seconds=8)
            return
        if metadata["edge_only"]:
            self._start_edge_activity("pack:" + key)
            left,top,right,bottom=self._screen_bounds()
            self.target_x=float(left if self.pet_x < (left+right)/2 else right-SMALL_WIDTH)
            self.target_y=max(top,min(self.pet_y,bottom-SMALL_HEIGHT-42))
            return
        seconds = max(4.0,metadata["frames"]*metadata["seconds_per_frame"]+1.0)
        self._play_test_animation("pack:" + key, seconds)

    def _play_activity(self, key: str) -> None:
        if self.prompt_visible or self.active_alert_kind or self.dragging or self.state == "sad":
            return
        if key == "wind_down":self._play_test_animation("wind_down",sum(duration for _,duration in WIND_DOWN_SEQUENCE))
        elif key == "groom":self._play_test_animation("groom",sum(duration for _,duration in GROOM_SEQUENCE))
        elif key == "feed":self.feed_panda()
        elif key == "fetch":self.start_fetch()
        elif key == "log":self._play_test_animation("bored",28)
        elif key == "meditate":self._play_test_animation("meditate",20)
        elif key == "water":self.show_prompt()
        elif key in ("watch","movement"):
            self._show_general_alert("Time to move!" if key=="movement" else "Your reminder", "Move with your panda" if key=="movement" else "Personal reminder preview", "preview_movement" if key=="movement" else "preview_personal")
        elif key in ("cursor_follow","cursor_avoid"):
            self._close_chatter_card()
            self.idle_mood="";self.idle_mood_until=None;self.current_action=None
            self.cursor_session_kind="Follow" if key=="cursor_follow" else "Avoid"
            self.cursor_session_until=datetime.now()+timedelta(seconds=30)
            self.motion_mode="idle";self.next_cursor_reaction=datetime.now()
        else:self._play_pack_animation(key)

    def _draw_pack_animation(self, key: str, elapsed: float) -> None:
        y = PET_CENTER_Y
        if key == "jump":
            duration=self.pack_manifest[key]["frames"]*self.pack_manifest[key]["seconds_per_frame"]
            y -= int(32*math.sin(min(1.0,elapsed/duration)*math.pi))
        if key in ("sleep","snore_sleep"):
            y += int(math.sin(elapsed*1.8)*2)
        self.canvas.create_image(SMALL_WIDTH//2,y,image=self._pack_image(key,elapsed))
        if key in ("sleep","snore_sleep"):
            self.canvas.create_text(142,38,text="z Z",fill=PALETTE["muted"],font=("Segoe UI",10))

    def _load_settings(self) -> dict[str, object]:
        defaults: dict[str, object] = {
            "pet": "panda",
            "name": "Mochi",
            "wander": True,
            "sound": True,
            "hide_fullscreen": True,
            "cursor_games": False,
            "cursor_mode": "Off",
            "sleep_enabled": True,
            "roam_rest_seconds": 30,
            "sleep_after_minutes": 3,
            "yawn_after_seconds": 60,
            "auto_activity": "Gentle routine",
            "walk_frame_ms": 180,
            "hunger_enabled": True,
            "hunger_minutes": 120,
            "routine_activities": list(GENTLE_ACTIVITIES),
            "activity_minutes": 5,
            "personality": "Balanced",
            "home_x": None,
            "home_y": None,
            "movement_enabled": True,
            "movement_minutes": 60,
            "pat_count": 0,
            "adopted_at": datetime.now().date().isoformat(),
        }
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                defaults.update(data)
        except (OSError, ValueError, TypeError):
            pass
        defaults["pet"] = "panda"
        name = str(defaults.get("name", "Mochi")).strip()[:18]
        defaults["name"] = name or "Mochi"
        personality = str(defaults.get("personality", "Balanced"))
        if personality not in ("Calm", "Balanced", "Playful"):
            defaults["personality"] = "Balanced"
        for key in (
            "wander",
            "sound",
            "hide_fullscreen",
            "movement_enabled",
        ):
            defaults[key] = bool(defaults.get(key, True))
        try:
            movement_minutes = int(defaults.get("movement_minutes", 60))
        except (TypeError, ValueError):
            movement_minutes = 60
        defaults["movement_minutes"] = max(15, min(180, movement_minutes))
        try:
            defaults["pat_count"] = max(0, int(defaults.get("pat_count", 0)))
        except (TypeError, ValueError):
            defaults["pat_count"] = 0
        try:
            datetime.fromisoformat(str(defaults.get("adopted_at", "")))
        except ValueError:
            defaults["adopted_at"] = datetime.now().date().isoformat()
        defaults["cursor_games"] = bool(defaults.get("cursor_games", False))
        defaults["sleep_enabled"] = bool(defaults.get("sleep_enabled", True))
        for key, default, low, high in (("roam_rest_seconds",30,30,600), ("sleep_after_minutes",3,2,60), ("yawn_after_seconds",60,30,120), ("activity_minutes",5,1,60)):
            try:
                defaults[key] = max(low, min(high, int(defaults[key])))
            except (ValueError, TypeError):
                defaults[key] = default
        try:
            defaults["walk_frame_ms"] = max(100,min(300,int(defaults.get("walk_frame_ms",180))))
        except (ValueError,TypeError):
            defaults["walk_frame_ms"] = 180
        defaults["hunger_enabled"] = bool(defaults.get("hunger_enabled",True))
        try:
            defaults["hunger_minutes"] = max(15,min(360,int(defaults.get("hunger_minutes",120))))
        except (ValueError,TypeError):
            defaults["hunger_minutes"] = 120
        selected = defaults.get("routine_activities",list(GENTLE_ACTIVITIES))
        defaults["routine_activities"] = list(dict.fromkeys(ACTIVITY_ALIASES.get(key,key) for key in selected if ACTIVITY_ALIASES.get(key,key) in ROUTINE_ACTIVITIES)) if isinstance(selected,list) else list(GENTLE_ACTIVITIES)
        if defaults.get("cursor_mode") not in ("Off","Follow","Avoid"):
            defaults["cursor_mode"] = "Off"
        old = defaults["auto_activity"]
        old_labels={"Rub ears":"groom", "Wash face":"groom", "Belly scratch":"groom", "Stretch":"wind_down", "Sleep":"wind_down", "Yawn and stretch":"wind_down", "Side roll":"forward_roll", "Play on log":"log"}
        if old in old_labels:
            defaults["auto_activity"] = ACTIVITY_LABELS[old_labels[old]]
        for key,metadata in self.pack_manifest.items():
            if metadata["label"].casefold() == str(old).casefold():
                canonical=ACTIVITY_ALIASES.get(key,key)
                defaults["auto_activity"] = ACTIVITY_LABELS[canonical] if canonical in ROUTINE_ACTIVITIES else "Manual only"
                break
        allowed=("Manual only","Gentle routine","Selected routine","Meditate") + tuple(ACTIVITY_LABELS[key] for key in ROUTINE_ACTIVITIES)
        if defaults["auto_activity"] not in allowed:
            defaults["auto_activity"] = "Manual only"
        return defaults

    def _save_settings(self) -> None:
        data = {
            "pet": self.pet_type.get(),
            "name": self.pet_name.get().strip()[:18] or "Mochi",
            "wander": self.roam_enabled.get(),
            "sound": self.sound_enabled.get(),
            "hide_fullscreen": self.hide_fullscreen.get(),
            "cursor_games": self.cursor_mode.get() != "Off",
            "cursor_mode": self.cursor_mode.get(),
            "sleep_enabled": self.sleep_enabled.get(),
            "roam_rest_seconds": self.roam_rest_seconds.get(),
            "sleep_after_minutes": self.sleep_after_minutes.get(),
            "yawn_after_seconds": self.yawn_after_seconds.get(),
            "auto_activity": self.auto_activity.get(),
            "activity_minutes": self.activity_minutes.get(),
            "walk_frame_ms": self.walk_frame_ms.get(),
            "hunger_enabled": self.hunger_enabled.get(),
            "hunger_minutes": self.hunger_minutes.get(),
            "routine_activities": [key for key,enabled in self.routine_enabled.items() if enabled.get()],
            "personality": self.personality.get(),
            "home_x": self.settings.get("home_x"),
            "home_y": self.settings.get("home_y"),
            "movement_enabled": self.movement_enabled.get(),
            "movement_minutes": self.movement_minutes.get(),
            "pat_count": self.pat_count,
            "adopted_at": self.adopted_at,
        }
        try:
            self.settings_path.write_text(
                json.dumps(data, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _initialize_database(self) -> None:
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = NORMAL")
            connection.execute("PRAGMA busy_timeout = 3000")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS water_entries
                (
                    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_at TEXT NOT NULL,
                    millilitres INTEGER NOT NULL CHECK (millilitres > 0)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS personal_reminders
                (
                    reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'scheduled',
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_personal_reminders_due
                ON personal_reminders(status, due_at)
                """
            )
            # Normalize existing offset-bearing reminders before lexical SQL ordering.
            for reminder_id, due_at in connection.execute("SELECT reminder_id,due_at FROM personal_reminders").fetchall():
                try:
                    normalized = datetime.fromisoformat(due_at).astimezone(timezone.utc).isoformat(timespec="seconds")
                except (ValueError, TypeError):
                    continue
                if normalized != due_at:
                    connection.execute("UPDATE personal_reminders SET due_at=? WHERE reminder_id=?",(normalized,reminder_id))

    def _write_pid(self) -> None:
        try:
            (self.app_dir / "water_puppy.pid").write_text(
                str(os.getpid()),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _place_bottom_right(self) -> None:
        left, top, right, bottom = self._screen_bounds()
        saved_x = self.settings.get("home_x")
        saved_y = self.settings.get("home_y")
        if isinstance(saved_x, int) and isinstance(saved_y, int):
            x = max(left, min(saved_x, right - SMALL_WIDTH))
            y = max(top, min(saved_y, bottom - SMALL_HEIGHT))
        else:
            x = max(left, right - SMALL_WIDTH - 18)
            y = max(top, bottom - SMALL_HEIGHT - 52)
        self.pet_x = float(x)
        self.pet_y = float(y)
        self.root.geometry(f"{SMALL_WIDTH}x{SMALL_HEIGHT}{x:+d}{y:+d}")

    def _screen_bounds(self) -> tuple[int, int, int, int]:
        if os.name == "nt":
            user32 = ctypes.windll.user32
            left = int(user32.GetSystemMetrics(76))
            top = int(user32.GetSystemMetrics(77))
            width = int(user32.GetSystemMetrics(78))
            height = int(user32.GetSystemMetrics(79))
            if width > 0 and height > 0:
                return left, top, left + width, top + height
        return 0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def _apply_pet_window_style(self) -> None:
        self._apply_tool_window_style(self.root)

    def _apply_tool_window_style(self, window: tk.Misc) -> None:
        if os.name != "nt":
            return
        try:
            window.update_idletasks()
            user32 = ctypes.windll.user32
            hwnd = user32.GetParent(window.winfo_id()) or window.winfo_id()
            get_style = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
            set_style = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
            get_style.restype = ctypes.c_ssize_t
            set_style.restype = ctypes.c_ssize_t
            extended_style = int(get_style(hwnd, -20))
            extended_style |= 0x00000080
            extended_style &= ~0x00040000
            set_style(hwnd, -20, extended_style)
            user32.SetWindowPos(
                hwnd,
                -1,
                0,
                0,
                0,
                0,
                0x0001 | 0x0002 | 0x0010 | 0x0020,
            )
        except (AttributeError, OSError, ctypes.ArgumentError, tk.TclError):
            pass

    def _resize_anchored(self, width: int, height: int) -> None:
        self.root.update_idletasks()
        left = self.root.winfo_x()
        old_gutter = 140 if self.width > SMALL_WIDTH else 0
        new_gutter = 140 if width > SMALL_WIDTH else 0
        top = self.root.winfo_y() + old_gutter - new_gutter
        screen_left, screen_top, screen_right, screen_bottom = self._screen_bounds()
        x = max(screen_left, min(left, screen_right - width))
        y = max(screen_top, min(top, screen_bottom - height))
        self.width = width
        self.height = height
        self.canvas.configure(width=width, height=height)
        self.root.geometry(f"{width}x{height}{x:+d}{y:+d}")
        self.pet_x = float(x)
        self.pet_y = float(y + new_gutter)

    def _build_menu(self) -> None:
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(
            label="Open Panda Home",
            command=self.show_history,
        )
        self.menu.add_separator()
        self.menu.add_checkbutton(
            label="Enable roaming",
            variable=self.roam_enabled,
            command=self._toggle_roaming,
        )
        self.menu.add_command(label="Ask for water now", command=self.show_prompt)
        self.menu.add_command(
            label="Pause water reminders for 1 hour",
            command=self.pause_reminders,
        )
        self.menu.add_command(
            label="Resume water reminders",
            command=self.resume_reminders,
        )
        self.menu.add_command(
            label="Add personal reminder",
            command=self.show_reminders,
        )
        self.menu.add_separator()
        self.menu.add_command(label="Exit Water Panda", command=self.close)

    def _play_test_animation(self, mood: str, seconds: float) -> None:
        if self.prompt_visible or self.active_alert_kind or self.state == "sad":
            return
        now = datetime.now()
        self.state = "normal"
        self.motion_mode = "idle"
        self.current_action = None
        self.pending_edge_action = None
        self.idle_mood = mood
        self.idle_mood_started_at = now
        self.idle_mood_until = now + timedelta(seconds=seconds)
        self.action_sequence_stage = -1

    def _test_walk_across_screen(self) -> None:
        if self.prompt_visible or self.dragging:
            return
        left, _top, right, _bottom = self._screen_bounds()
        midpoint = left + ((right - left) // 2)
        if self.pet_x < midpoint:
            self.target_x = float(right - SMALL_WIDTH - 24)
            self.walk_direction = "right"
        else:
            self.target_x = float(left + 24)
            self.walk_direction = "left"
        self.target_y = self.pet_y
        self.walk_speed = 2.8
        self.idle_mood = ""
        self.motion_mode = "walking"

    def _test_bored_at_edge(self) -> None:
        if self.prompt_visible or self.dragging:
            return
        self.idle_mood = ""
        self.current_action = None
        self.pending_edge_action = "bored_edge"
        self._choose_edge_destination()

    def _bind_events(self) -> None:
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._end_drag)
        self.canvas.bind("<Button-3>", self._show_menu)
        self.canvas.bind("<Double-Button-1>", lambda _event: self.show_history())
        self.canvas.bind("<Enter>", self._mouse_enter)
        self.canvas.bind("<Leave>", self._mouse_leave)

    def _start_drag(self, event: tk.Event) -> None:
        if "answer_button" in self.canvas.gettags("current"):
            return
        if self.hungry and not self.prompt_visible and not self.active_alert_kind:
            self.feed_panda()
            return
        self.dragging = True
        self.drag_moved = False
        self.motion_mode = "idle"
        self.current_action = None
        self.pending_edge_action = None
        self.idle_mood = ""
        self.idle_mood_until = None
        self.drag_offset_x = event.x
        self.drag_offset_y = event.y
        self.drag_start_root = (event.x_root, event.y_root)
        self.drag_samples = [(datetime.now(), self.root.winfo_x(), self.root.winfo_y())]

    def _drag(self, event: tk.Event) -> None:
        if "answer_button" in self.canvas.gettags("current"):
            return
        x = self.root.winfo_x() + event.x - self.drag_offset_x
        y = self.root.winfo_y() + event.y - self.drag_offset_y
        left, top, right, bottom = self._screen_bounds()
        x = max(left, min(x, right - self.width))
        y = max(top, min(y, bottom - self.height))
        if math.hypot(
            event.x_root - self.drag_start_root[0],
            event.y_root - self.drag_start_root[1],
        ) > 5:
            self.drag_moved = True
        self.pet_x = float(x)
        self.pet_y = float(y + (140 if self.width > SMALL_WIDTH else 0))
        self.drag_samples.append((datetime.now(), int(x), int(y)))
        self.drag_samples = self.drag_samples[-6:]
        self._move_root(x, y)

    def _end_drag(self, _event: tk.Event) -> None:
        if not self.dragging:
            return
        self.dragging = False
        self.pet_x = float(self.root.winfo_x())
        self.pet_y = float(self.root.winfo_y() + (140 if self.width > SMALL_WIDTH else 0))
        if self.drag_moved:
            self.settings["home_x"] = int(self.pet_x)
            self.settings["home_y"] = int(self.pet_y)
            self._save_settings()
            if not self.prompt_visible and not self.active_alert_kind:
                self._close_chatter_card()
            if len(self.drag_samples) >= 2 and not self.prompt_visible and not self.active_alert_kind:
                first_time, first_x, first_y = self.drag_samples[0]
                last_time, last_x, last_y = self.drag_samples[-1]
                elapsed = max(0.05, (last_time - first_time).total_seconds())
                self.velocity_x = max(
                    -14.0,
                    min(14.0, ((last_x - first_x) / elapsed) * 0.045),
                )
                self.velocity_y = max(
                    -16.0,
                    min(12.0, ((last_y - first_y) / elapsed) * 0.045),
                )
                self.motion_mode = "falling"
        self.idle_until = datetime.now() + timedelta(seconds=2)
        if not self.drag_moved:
            self._pet_reaction()

    def _show_menu(self, event: tk.Event) -> None:
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def start_fetch(self) -> None:
        if self.prompt_visible or self.dragging or self.state != "normal":
            self._show_chatter("After this reminder, promise!", seconds=3)
            return
        try:
            pointer_x, pointer_y = self.root.winfo_pointerxy()
        except tk.TclError:
            return
        left, top, right, bottom = self._screen_bounds()
        target_x = max(left, min(pointer_x - SMALL_WIDTH // 2, right - SMALL_WIDTH))
        target_y = max(top, min(pointer_y - SMALL_HEIGHT // 2, bottom - SMALL_HEIGHT - 42))
        if math.hypot(target_x - self.pet_x, target_y - self.pet_y) < 90:
            target_x = max(left, min(target_x + 180, right - SMALL_WIDTH))
        self.fetch_origin = (self.pet_x, self.pet_y)
        self.target_x = float(target_x)
        self.target_y = float(target_y)
        self.walk_direction = "right" if self.target_x >= self.pet_x else "left"
        self.walk_speed = 7.5
        self.motion_mode = "fetch_out"
        self.current_action = None
        self.idle_mood = ""
        self.idle_mood_until = None
        self._show_chatter("Ball spotted! I’m on it!", seconds=2.5)

    def _change_pet(self) -> None:
        self._save_settings()
        self.motion_mode = "idle"
        self.current_action = None
        self.idle_until = datetime.now() + timedelta(seconds=1)
        self._draw()

    def _toggle_roaming(self) -> None:
        self._save_settings()
        self.tray.roaming_enabled = self.roam_enabled.get()
        self.motion_mode = "idle"
        self.current_action = None
        self.pet_x = float(self.root.winfo_x())
        self.pet_y = float(self.root.winfo_y() + (140 if self.width > SMALL_WIDTH else 0))
        self.idle_until = datetime.now() + timedelta(seconds=1)

    def _settings_changed(self) -> None:
        self._save_settings()

    def _movement_settings_changed(self) -> None:
        minutes = max(15, min(180, int(self.movement_minutes.get())))
        self.movement_minutes.set(minutes)
        self.next_movement_reminder = datetime.now() + timedelta(
            minutes=minutes
        )
        self._save_settings()

    def _mouse_enter(self, _event: tk.Event) -> None:
        self.hovering = True
        if self.state == "normal" and not self.prompt_visible and not self.active_alert_kind and not self.dragging and not self.idle_mood and not self.chatter_until:
            self._show_chatter(f"{self.pet_name.get()} ♡  Today {self.today_total_cache} ml", seconds=3.5)

    def _mouse_leave(self, _event: tk.Event) -> None:
        self.hovering = False

    def _system_idle_seconds(self) -> float:
        if os.name != "nt":
            return 0.0
        try:
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

            info = LASTINPUTINFO()
            info.cbSize = ctypes.sizeof(info)
            if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
                return 0.0
            ctypes.windll.kernel32.GetTickCount64.restype = ctypes.c_ulonglong
            elapsed_ms = ctypes.windll.kernel32.GetTickCount64() - info.dwTime
            return max(0.0, float(elapsed_ms) / 1000.0)
        except (AttributeError, OSError, ctypes.ArgumentError):
            return 0.0

    def _move_root(self, x: int, y: int) -> None:
        self.root.geometry(f"{int(x):+d}{int(y):+d}")

    def reset_timer(self) -> None:
        self.next_reminder = datetime.now() + timedelta(
            minutes=REMINDER_MINUTES
        )
        self.prompt_visible = False
        self._clear_attention()
        self.state = "normal"
        self.happy_until = None
        self.motion_mode = "idle"
        self.current_action = None
        self.idle_until = datetime.now() + timedelta(seconds=2)
        self._resize_anchored(SMALL_WIDTH, SMALL_HEIGHT)

    def pause_reminders(self) -> None:
        self.reminders_paused_until = datetime.now() + timedelta(hours=1)
        self.next_reminder = self.reminders_paused_until
        self.prompt_visible = False
        self._clear_attention()
        self.state = "normal"
        self._resize_anchored(SMALL_WIDTH, SMALL_HEIGHT)
        self._show_chatter("Quiet time for 1 hour 🌙", seconds=5)

    def resume_reminders(self) -> None:
        self.reminders_paused_until = None
        self.next_reminder = datetime.now() + timedelta(
            minutes=REMINDER_MINUTES
        )
        self._show_chatter("I’m back on sip duty!", seconds=4)

    def show_prompt(self) -> None:
        if self.active_alert_kind:
            return
        self._close_chatter_card()
        if not self.prompt_visible:
            self._resize_anchored(PROMPT_WIDTH, PROMPT_HEIGHT)
        self.prompt_visible = True
        self.state = "asking"
        self.water_prompt_text = random.choice(WATER_PROMPTS)
        self.happy_until = None
        self.motion_mode = "idle"
        self.current_action = None
        self.pending_edge_action = None
        self.idle_mood = ""
        self.idle_mood_until = None
        self.root.deiconify()
        self.was_hidden_for_fullscreen = False
        self.root.lift()
        self._begin_attention()
        self._play_reminder_sound()

    def _play_reminder_sound(self) -> None:
        if not self.sound_enabled.get() or os.name != "nt":
            return
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except (ImportError, RuntimeError):
            pass

    def _show_chatter(self, text: str, seconds: float = 4.0) -> None:
        self.chatter_text = " ".join(text.split())
        self.chatter_until = datetime.now() + timedelta(seconds=seconds)
        self._show_chatter_card()

    def _show_chatter_card(self) -> None:
        if self.prompt_visible or self.active_alert_kind:
            return
        self._resize_anchored(PROMPT_WIDTH, PROMPT_HEIGHT)

    def _render_chatter_card(self) -> None:
        if not self.chatter_text:
            return
        self._cloud_shape(self.canvas, 194, 12, 350, 112, PALETTE["cream"], "#E0D4ED")
        self.canvas.create_oval(179, 123, 191, 135, fill=PALETTE["cream"], outline="#E0D4ED")
        self.canvas.create_oval(167, 142, 175, 150, fill=PALETTE["cream"], outline="#E0D4ED")
        self.canvas.create_text(272, 61, text=self.chatter_text, width=126,
                                fill=PALETTE["ink"], font=("Segoe UI", 9), justify="center")

    def _position_chatter_card(self) -> None:
        # Chatter shares the pet canvas, so dragging moves both together.
        pass

    def _close_chatter_card(self) -> None:
        self.chatter_window = None
        self.chatter_canvas = None
        self.chatter_until = None
        self.chatter_text = ""
        if not self.prompt_visible and not self.active_alert_kind:
            self._resize_anchored(SMALL_WIDTH, SMALL_HEIGHT)

    def _begin_attention(self) -> None:
        now = datetime.now()
        self.attention_started_at = now
        self.attention_stage = 0
        self.next_attention_nudge = now + timedelta(seconds=6)
        self.attention_sound_played = False

    def _clear_attention(self) -> None:
        self.attention_started_at = None
        self.attention_stage = 0
        self.next_attention_nudge = None
        self.attention_sound_played = False

    def _update_attention_behavior(self, now: datetime) -> None:
        alert_active = bool(self.active_alert_kind)
        if not self.prompt_visible and not alert_active:
            if self.attention_started_at is not None:
                self._clear_attention()
            return
        if self.attention_started_at is None:
            self._begin_attention()

        elapsed = (now - self.attention_started_at).total_seconds()
        new_stage = 2 if elapsed >= 16 else 1 if elapsed >= 6 else 0
        if new_stage != self.attention_stage:
            self.attention_stage = new_stage
            self.root.deiconify()
            self.root.lift()
            if alert_active and self.alert_window is not None:
                self.alert_window.lift()
            if new_stage == 2 and not self.attention_sound_played:
                self._play_reminder_sound()
                self.attention_sound_played = True

        if self.next_attention_nudge and now >= self.next_attention_nudge:
            self.root.lift()
            if alert_active and self.alert_window is not None:
                self.alert_window.lift()
            interval = 12 if self.attention_stage >= 2 else 10
            self.next_attention_nudge = now + timedelta(seconds=interval)

        if self.alert_pet_label is not None and self.alert_pet_label.winfo_exists():
            if "personal" in self.active_alert_kind:
                image_key = "watch"
            else:
                image_key = f"hula_{1 + ((self.frame // 2) % 2)}"
            self.alert_pet_label.configure(image=self._image(image_key))
        if self.alert_icon_label is not None and self.alert_icon_label.winfo_exists():
            label = (
                "PERSONAL REMINDER"
                if "personal" in self.active_alert_kind
                else "MOVEMENT BREAK"
            )
            self.alert_icon_label.configure(text=label)

    def _pet_reaction(self) -> None:
        if self.prompt_visible or self.dragging:
            return
        self.motion_mode = "idle"
        self.current_action = None
        now = datetime.now()
        self.idle_mood = "nuzzle"
        self.idle_mood_started_at = now
        self.idle_mood_until = now + timedelta(seconds=2.4)
        self.action_sequence_stage = -1
        self.pat_count += 1
        self._save_settings()
        milestone_lines = {
            5: "Five pats! We’re officially pals!",
            20: "Twenty pats… panda adores you!",
            50: "Fifty pats! Best-friend status ✦",
            100: "One hundred pats. Panda heart = full!",
        }
        if self.state == "sad":
            self._show_chatter("A sip would cheer me up…", seconds=4)
        elif self.pat_count in milestone_lines:
            self._show_chatter(milestone_lines[self.pat_count], seconds=5)
        else:
            self._show_chatter(
                random.choice(PET_REACTIONS[self.pet_type.get()]),
                seconds=3.5,
            )
            for index in range(7):
                self.particles.append(
                    {
                        "x": float(45 + random.randint(0, 28)),
                        "y": float(63 + random.randint(-5, 15)),
                        "vx": random.uniform(-0.45, 0.45),
                        "vy": random.uniform(-1.25, -0.65),
                        "life": float(20 + index * 2),
                        "kind": random.choice(("heart", "heart", "sparkle", "leaf")),
                    }
                )
        self.particles = self.particles[-28:]
        self._refresh_memory_label()

    def _memory_text(self) -> str:
        try:
            adopted_date = datetime.fromisoformat(self.adopted_at).date()
        except ValueError:
            adopted_date = datetime.now().date()
        days_together = max(1, (datetime.now().date() - adopted_date).days + 1)
        return f"Together {days_together} day{'s' if days_together != 1 else ''}  ·  {self.pat_count} panda pats"

    def _refresh_memory_label(self) -> None:
        if self.memories_label is not None and self.memories_label.winfo_exists():
            self.memories_label.configure(text=self._memory_text())

    def record_water(
        self,
        millilitres: int,
        _event: tk.Event | None = None,
    ) -> None:
        if not self.prompt_visible:
            return

        recorded_at = datetime.now().astimezone().isoformat(
            timespec="seconds"
        )
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.execute(
                """
                INSERT INTO water_entries (recorded_at, millilitres)
                VALUES (?, ?)
                """,
                (recorded_at, millilitres),
            )

        self.last_logged_amount = millilitres
        self.today_total_cache += millilitres
        self.prompt_visible = False
        self._clear_attention()
        self.state = "normal"
        self.idle_mood = "bow"
        self.idle_mood_started_at = datetime.now()
        self.idle_mood_until = datetime.now() + timedelta(seconds=4)
        self._resize_anchored(SMALL_WIDTH, SMALL_HEIGHT)
        self._show_chatter("Thank you for taking care of yourself!", seconds=4)
        self.happy_until = datetime.now() + timedelta(seconds=6)
        self.motion_mode = "idle"
        self.current_action = None
        self.next_reminder = datetime.now() + timedelta(
            minutes=REMINDER_MINUTES
        )
        particle_count = {100: 5, 200: 8, 300: 12}.get(millilitres, 6)
        for _ in range(particle_count):
            self.particles.append(
                {
                    "x": float(38 + random.randint(0, 40)),
                    "y": float(72 + random.randint(-8, 22)),
                    "vx": random.uniform(-0.8, 0.8),
                    "vy": random.uniform(-1.5, -0.7),
                    "life": float(random.randint(18, 34)),
                    "kind": random.choice(("droplet", "sparkle", "heart")),
                }
            )
        self.particles = self.particles[-32:]
        self._refresh_history()

    def _build_reminder_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="Add a personal reminder",
            style="CardTitle.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            parent,
            text="Your panda will pop up at the selected date and time.",
            style="CardSub.TLabel",
        ).pack(anchor="w", pady=(2, 12))

        form = ttk.Frame(parent, style="Studio.TFrame")
        form.pack(fill="x")
        ttk.Label(form, text="What should I remind you about?").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        title_entry = ttk.Entry(
            form,
            textvariable=self.reminder_title_var,
            width=50,
        )
        title_entry.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(4, 10),
        )

        ttk.Label(form, text="Date").grid(row=2, column=0, sticky="w")
        ttk.Label(form, text="Time").grid(row=2, column=1, sticky="w", padx=(10, 0))
        now = datetime.now()
        date_values: list[str] = []
        self.date_display_to_iso = {}
        for offset in range(181):
            day = now.date() + timedelta(days=offset)
            display = day.strftime("%a, %d %b %Y")
            if offset == 0:
                display = f"Today · {display}"
            elif offset == 1:
                display = f"Tomorrow · {display}"
            date_values.append(display)
            self.date_display_to_iso[display] = day.isoformat()
        if not self.reminder_date_var.get() in self.date_display_to_iso:
            self.reminder_date_var.set(date_values[0])
        date_box = ttk.Combobox(
            form,
            textvariable=self.reminder_date_var,
            values=date_values,
            state="readonly",
            width=27,
        )
        date_box.grid(row=3, column=0, sticky="ew", pady=(4, 12))
        time_entry = ttk.Entry(
            form,
            textvariable=self.reminder_time_var,
            width=14,
        )
        time_entry.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(4, 12))
        ttk.Button(
            form,
            text="Add reminder",
            style="Accent.TButton",
            command=self.add_personal_reminder,
        ).grid(row=3, column=2, sticky="e", padx=(10, 0), pady=(4, 12))
        form.columnconfigure(0, weight=1)

        ttk.Label(
            parent,
            text="Try times like 1:00 PM or 13:00",
            style="CardSub.TLabel",
        ).pack(anchor="w", pady=(0, 14))
        ttk.Label(parent, textvariable=self.reminder_feedback_var, style="CardSub.TLabel", wraplength=440).pack(anchor="w", pady=(0,8))
        ttk.Label(
            parent,
            text="Upcoming reminders",
            style="CardTitle.TLabel",
        ).pack(anchor="w", pady=(0, 7))
        self.reminder_tree = ttk.Treeview(
            parent,
            columns=("title", "due"),
            show="headings",
            height=8,
        )
        self.reminder_tree.heading("title", text="Reminder")
        self.reminder_tree.heading("due", text="Date and time")
        self.reminder_tree.column("title", width=265, anchor="w")
        self.reminder_tree.column("due", width=190, anchor="w")
        self.reminder_tree.pack(fill="both", expand=True)
        reminder_controls = ttk.Frame(parent, style="Studio.TFrame")
        reminder_controls.pack(fill="x", pady=(8, 0))
        ttk.Button(
            reminder_controls,
            text="Delete selected",
            command=self.delete_selected_reminder,
        ).pack(side="left")

    def _parse_reminder_due(self) -> datetime:
        selected_date = self.date_display_to_iso.get(
            self.reminder_date_var.get()
        )
        if not selected_date:
            raise ValueError("Choose a valid date.")
        raw_time = self.reminder_time_var.get().strip().upper()
        parsed_time = None
        for time_format in ("%I:%M %p", "%I %p", "%H:%M"):
            try:
                parsed_time = datetime.strptime(raw_time, time_format).time()
                break
            except ValueError:
                continue
        if parsed_time is None:
            raise ValueError("Enter time as 1:00 PM or 13:00.")
        local_due = datetime.combine(
            datetime.fromisoformat(selected_date).date(),
            parsed_time,
        ).astimezone()
        if local_due <= datetime.now().astimezone():
            raise ValueError("The reminder time must be in the future.")
        return local_due.astimezone(timezone.utc)

    def add_personal_reminder(self) -> None:
        title = self.reminder_title_var.get().strip()
        if not title:
            self.reminder_feedback_var.set("Enter what the panda should remind you about.")
            return
        if len(title) > 120:
            self.reminder_feedback_var.set("Keep the reminder under 120 characters.")
            return
        try:
            due = self._parse_reminder_due()
        except ValueError as error:
            self.reminder_feedback_var.set(str(error))
            return
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.execute(
                """
                INSERT INTO personal_reminders
                    (title, due_at, status, created_at)
                VALUES (?, ?, 'scheduled', ?)
                """,
                (
                    title,
                    due.isoformat(timespec="seconds"),
                    datetime.now().astimezone().isoformat(timespec="seconds"),
                ),
            )
        self.reminder_feedback_var.set("Reminder saved.")
        self.reminder_title_var.set("")
        self._refresh_reminders()
        self._show_chatter("Reminder saved! I won’t forget ✦", seconds=5)

    def delete_selected_reminder(self) -> None:
        if self.reminder_tree is None:
            return
        selected = self.reminder_tree.selection()
        if not selected:
            self.reminder_feedback_var.set("Select a reminder first.")
            return
        reminder_id = int(selected[0])
        if not messagebox.askyesno(
            "Delete reminder",
            "Delete the selected reminder?",
            parent=self.history_window or self.root,
        ):
            return
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            connection.execute(
                "DELETE FROM personal_reminders WHERE reminder_id = ?",
                (reminder_id,),
            )
        self._refresh_reminders()

    def _refresh_reminders(self) -> None:
        if self.reminder_tree is None or not self.reminder_tree.winfo_exists():
            return
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            rows = connection.execute(
                """
                SELECT reminder_id, title, due_at
                FROM personal_reminders
                WHERE status = 'scheduled'
                ORDER BY due_at, reminder_id
                LIMIT 100
                """
            ).fetchall()
        for item in self.reminder_tree.get_children():
            self.reminder_tree.delete(item)
        for reminder_id, title, due_at in rows:
            try:
                formatted_due = datetime.fromisoformat(due_at).astimezone().strftime(
                    "%a, %d %b · %I:%M %p"
                )
            except ValueError:
                formatted_due = due_at
            self.reminder_tree.insert(
                "",
                "end",
                iid=str(reminder_id),
                values=(title, formatted_due),
            )

    def snooze_water(self, _event: tk.Event | None = None) -> None:
        if not self.prompt_visible:
            return
        self.prompt_visible = False
        self._clear_attention()
        self.state = "normal"
        self.motion_mode = "idle"
        self.current_action = None
        self.next_reminder = datetime.now() + timedelta(minutes=10)
        self._resize_anchored(SMALL_WIDTH, SMALL_HEIGHT)
        self._show_chatter("Okay, another sip check in 10 minutes.", seconds=4)

    def answer_not_yet(self, _event: tk.Event | None = None) -> None:
        if not self.prompt_visible:
            return
        self.prompt_visible = False
        self._clear_attention()
        self.state = "sad"
        self.sad_until = datetime.now() + timedelta(seconds=WATER_DECLINE_SECONDS)
        self.happy_until = None
        self.motion_mode = "idle"
        self.current_action = None
        self.next_reminder = datetime.now() + timedelta(
            minutes=REMINDER_MINUTES
        )
        self._resize_anchored(SMALL_WIDTH, SMALL_HEIGHT)
        self._show_chatter("Okay, a little later.", seconds=WATER_DECLINE_SECONDS)

    def _update_water_response(self, now: datetime) -> None:
        if self.state == "sad" and getattr(self, "sad_until", None) and now >= self.sad_until:
            self.state = "normal"
            self.sad_until = None
            self.motion_mode = "idle"
            self.idle_until = now + timedelta(seconds=self.roam_rest_seconds.get())

    def _tick(self) -> None:
        now = datetime.now()
        self._update_water_response(now)
        if now.date() != self.cache_date:
            self.cache_date = now.date()
            self.today_total_cache = self._today_total()
        paused = (
            self.reminders_paused_until is not None
            and now < self.reminders_paused_until
        )
        if self.reminders_paused_until and not paused:
            self.reminders_paused_until = None

        if not paused and not self.active_alert_kind and not self.prompt_visible and now >= self.next_reminder:
            self.show_prompt()

        if (now - self.last_schedule_check).total_seconds() >= 10:
            self.last_schedule_check = now
            self._check_scheduled_reminders(now)

        if (
            self.state == "happy"
            and self.happy_until
            and now >= self.happy_until
        ):
            self.state = "normal"
            self.happy_until = None
            self.idle_until = now + timedelta(seconds=1)

        if not self.active_alert_kind:
            self._update_inactivity_behavior(now)
        self._update_hunger(now)
        self._update_idle_mood(now)
        self._check_cursor_reaction(now)
        self._update_attention_behavior(now)

        if (
            self.state == "normal"
            and not self.active_alert_kind
            and not self.prompt_visible
            and not self.chatter_until
            and not self.idle_mood
            and (
                self.roam_enabled.get()
                or self.motion_mode in (
                    "walking",
                    "action",
                    "falling",
                    "escaping",
                    "fetch_out",
                    "fetch_pickup",
                    "fetch_return",
                    "fetch_offer",
                )
            )
        ):
            self._update_roaming(now)

        if (
            self.state == "normal"
            and not self.prompt_visible
            and not self.active_alert_kind
            and self.motion_mode == "idle"
            and not self.idle_mood
            and now >= self.next_chatter
        ):
            self._show_chatter(self._contextual_chatter(), seconds=random.uniform(3.5, 5.0))
            interval = {
                "Calm": (150, 260),
                "Balanced": (90, 180),
                "Playful": (55, 115),
            }[self.personality.get()]
            self.next_chatter = now + timedelta(
                seconds=random.uniform(*interval)
            )

        if self.chatter_until and now >= self.chatter_until:
            self.chatter_until = None
            self.chatter_text = ""
            self._close_chatter_card()
        elif self.chatter_until and self.chatter_text:
            self._position_chatter_card()

        self._update_particles()

        if (now - self.last_fullscreen_check).total_seconds() >= 1.0:
            self.last_fullscreen_check = now
            self._update_fullscreen_visibility()

        self.frame += 1
        if not self.was_hidden_for_fullscreen:
            self._draw()
        self.root.after(self._next_tick_delay(), self._tick)

    def _next_tick_delay(self) -> int:
        if self.was_hidden_for_fullscreen:
            return HIDDEN_TICK_MILLISECONDS
        if (
            self.dragging
            or self.active_alert_kind
            or self.prompt_visible
            or self.attention_stage > 0
            or self.motion_mode in (
                "walking",
                "following",
                "falling",
                "action",
                "escaping",
                "fetch_out",
                "fetch_pickup",
                "fetch_return",
                "fetch_offer",
            )
            or self.idle_mood
            or self.particles
            or self.state == "happy"
        ):
            return ACTIVE_TICK_MILLISECONDS
        return IDLE_TICK_MILLISECONDS

    def _contextual_chatter(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 18:
            period = "afternoon"
        elif 18 <= hour < 23:
            period = "evening"
        else:
            period = "late"
        options = PET_CHATTER["panda"] + TIME_CHATTER[period]
        return random.choice(options)

    def _update_inactivity_behavior(self, now: datetime) -> None:
        if (now - self.last_system_idle_check).total_seconds() >= 1.0:
            self.last_system_idle_check = now
            self.system_idle_seconds_cache = self._system_idle_seconds()
        idle_seconds = self.system_idle_seconds_cache
        if self.idle_mood and self.idle_mood not in ("yawn", "sleep", "wave"):
            return
        if idle_seconds < 5:
            if self.user_was_inactive:
                self.user_was_inactive = False
                self.inactivity_yawn_shown = False
                if self.idle_mood in ("yawn", "sleep"):
                    self.idle_mood = "wave"
                    self.idle_mood_started_at = now
                    self.idle_mood_until = now + timedelta(seconds=2.5)
                    self.action_sequence_stage = -1
                    self._show_chatter("You’re back! I saved your spot.", seconds=3)
            return
        if (
            self.prompt_visible
            or self.dragging
            or self.state != "normal"
            or (self.motion_mode not in ("idle", "action") and not (self.motion_mode == "following" and getattr(self,"cursor_at_rest",False)))
        ):
            return
        if self.sleep_enabled.get() and idle_seconds >= self.sleep_after_minutes.get() * 60:
            self.user_was_inactive = True
            if self.idle_mood != "sleep":
                self.motion_mode = "idle"
                self.current_action = None
                self.idle_mood = "sleep"
                self.idle_mood_started_at = now
                self.action_sequence_stage = -1
            self.idle_mood_until = now + timedelta(seconds=2)
            return
        if idle_seconds >= self.yawn_after_seconds.get() and not self.inactivity_yawn_shown:
            self.user_was_inactive = True
            self.inactivity_yawn_shown = True
            self.motion_mode = "idle"
            self.current_action = None
            self.idle_mood = "yawn"
            self.idle_mood_started_at = now
            self.idle_mood_until = now + timedelta(seconds=5)
            self.action_sequence_stage = -1
            self._show_chatter("Big yawn… you’ve gone quiet.", seconds=4)

    def _behavior_settings_changed(self) -> None:
        self.cursor_session_kind="";self.cursor_session_until=None
        if self.motion_mode=="following":self.motion_mode="idle"
        self._save_settings()
        now = datetime.now()
        self.next_idle_activity = now + timedelta(minutes=self.activity_minutes.get())
        self.idle_until = now + timedelta(seconds=self.roam_rest_seconds.get())
        self.next_hunger = now + timedelta(minutes=self.hunger_minutes.get())
        if not self.hunger_enabled.get():
            self.hungry = False
            self.hunger_requested = False

    def _update_hunger(self, now: datetime) -> None:
        if not self.hunger_enabled.get():
            return
        if now >= self.next_hunger:
            self.hungry = True
        if not self.hungry or self.hunger_requested:
            return
        if self.prompt_visible or self.active_alert_kind or self.dragging or self.idle_mood or self.chatter_until or self.state != "normal" or self.motion_mode not in ("idle", "following"):
            return
        self.hunger_requested = True
        self._show_chatter("My tummy is rumbling! Click me for bamboo?", seconds=15)

    def feed_panda(self) -> None:
        if self.prompt_visible or self.active_alert_kind or self.dragging or self.state == "sad":
            return
        self.hungry = False
        self.hunger_requested = False
        self.next_hunger = datetime.now() + timedelta(minutes=self.hunger_minutes.get())
        self._play_test_animation("feed", 5.5)
        self._show_chatter("Crunch, crunch. Thank you for the bamboo!", seconds=5.5)

    def _update_idle_mood(self, now: datetime) -> None:
        if self.idle_mood and self.idle_mood_until and now >= self.idle_mood_until:
            self.idle_mood = ""
            self.idle_mood_until = None
            self.action_sequence_stage = -1
            self.idle_until = now + timedelta(seconds=self.roam_rest_seconds.get())
        if now < self.next_idle_activity or getattr(self,"hungry",False):
            return
        if (self.state != "normal" or self.prompt_visible or self.active_alert_kind or self.dragging
                or self.idle_mood or (self.motion_mode != "idle" and not (self.motion_mode=="following" and getattr(self,"cursor_at_rest",False))) or self.chatter_until):
            return
        self.next_idle_activity = now + timedelta(minutes=self.activity_minutes.get())
        if self.auto_activity.get() in ("Gentle routine", "Selected routine"):
            pool = list(GENTLE_ACTIVITIES) if self.auto_activity.get() == "Gentle routine" else [key for key,enabled in self.routine_enabled.items() if enabled.get()]
            if pool:
                index = getattr(self,"routine_index",0) % len(pool)
                if len(pool)>1 and pool[index]==getattr(self,"last_routine_key",""):
                    index=(index+1)%len(pool)
                self.routine_index = index + 1
                self.last_routine_key=pool[index]
                self._play_activity(pool[index])
        elif self.auto_activity.get() == "Meditate":
            self._play_activity("meditate")
        else:
            for key,label in ACTIVITY_LABELS.items():
                if label==self.auto_activity.get() and key in ROUTINE_ACTIVITIES:
                    self._play_activity(key)
                    break


    def _check_cursor_reaction(self, now: datetime) -> None:
        if getattr(self,"cursor_session_until",None) and now>=self.cursor_session_until:
            self.cursor_session_kind="";self.cursor_session_until=None
            if self.motion_mode=="following":self.motion_mode="idle"
        mode=getattr(self,"cursor_session_kind","") or (self.cursor_mode.get() if hasattr(self,"cursor_mode") else "Avoid" if self.cursor_games.get() else "Off")
        if mode=="Avoid" and not getattr(self,"cursor_session_kind","") and not self.roam_enabled.get():
            return
        if mode=="Off" or self.active_alert_kind or self.prompt_visible or self.dragging or self.state!="normal" or self.idle_mood or getattr(self,"chatter_until",None):
            return
        if mode=="Follow":
            if self.motion_mode not in ("idle","walking","following"):
                return
            try:px,py=self.root.winfo_pointerxy()
            except tk.TclError:return
            cx,cy=self.pet_x+SMALL_WIDTH/2,self.pet_y+SMALL_HEIGHT/2
            dx,dy=px-cx,py-cy;distance=math.hypot(dx,dy)
            self.motion_mode="following"
            self.cursor_at_rest=distance<=140
            if self.cursor_at_rest:return
            left,top,right,bottom=self._screen_bounds()
            tx=max(left,min(px-dx/distance*140-SMALL_WIDTH/2,right-SMALL_WIDTH))
            ty=max(top,min(py-dy/distance*140-SMALL_HEIGHT/2,bottom-SMALL_HEIGHT-42))
            vx,vy=tx-self.pet_x,ty-self.pet_y;remaining=math.hypot(vx,vy)
            if remaining<1:
                self.cursor_at_rest=True
                return
            step=min(remaining,(52*180/512)/(0.5*self._walk_cycle_seconds())*(ACTIVE_TICK_MILLISECONDS/1000))
            self.pet_x+=vx/remaining*step;self.pet_y+=vy/remaining*step
            self.walk_direction="right" if vx>=0 else "left"
            self._move_root(round(self.pet_x),round(self.pet_y))
            return
        if not getattr(self,"cursor_session_kind","") and not self.roam_enabled.get():
            return
        if (
            now < self.next_cursor_reaction
            or self.prompt_visible
            or self.dragging
            or self.state != "normal"
            or self.motion_mode not in ("idle", "walking")
            or self.idle_mood
        ):
            return
        try:
            pointer_x, pointer_y = self.root.winfo_pointerxy()
        except tk.TclError:
            self.next_cursor_reaction = now + timedelta(seconds=15)
            return
        distance = math.hypot(
            pointer_x - (self.root.winfo_x() + SMALL_WIDTH / 2),
            pointer_y - (self.root.winfo_y() + SMALL_HEIGHT / 2),
        )
        if distance <= 145:
            center_x = self.root.winfo_x() + SMALL_WIDTH / 2
            center_y = self.root.winfo_y() + SMALL_HEIGHT / 2
            away_x = center_x - pointer_x
            away_y = center_y - pointer_y
            length = math.hypot(away_x, away_y)
            if length < 1:
                angle = random.uniform(0, math.tau)
                away_x, away_y = math.cos(angle), math.sin(angle)
                length = 1.0
            left, top, right, bottom = self._screen_bounds()
            escape_distance = random.uniform(190, 285)
            self.target_x = max(
                left,
                min(
                    self.pet_x + (away_x / length) * escape_distance,
                    right - SMALL_WIDTH,
                ),
            )
            self.target_y = max(
                top,
                min(
                    self.pet_y + (away_y / length) * escape_distance,
                    bottom - SMALL_HEIGHT - 42,
                ),
            )
            self.walk_direction = "right" if self.target_x >= self.pet_x else "left"
            self.walk_speed = random.uniform(6.5, 8.5)
            self.motion_mode = "escaping"
            self.cursor_escape_until = now + timedelta(seconds=4)
            # Do not open chatter here: it pauses movement and used to stall the escape.
            self.next_cursor_reaction = now + timedelta(seconds=4)
        else:
            self.next_cursor_reaction = now + timedelta(seconds=1)

    def _check_scheduled_reminders(self, now: datetime) -> None:
        if self.active_alert_kind or self.prompt_visible or (
            self.alert_window is not None and self.alert_window.winfo_exists()
        ):
            return
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            due = connection.execute(
                """
                SELECT reminder_id, title
                FROM personal_reminders
                WHERE status = 'scheduled' AND due_at <= ?
                ORDER BY due_at, reminder_id
                LIMIT 1
                """,
                (now.astimezone(timezone.utc).isoformat(timespec="seconds"),),
            ).fetchone()
        if due:
            self._show_general_alert(
                title=str(due[1]),
                subtitle="Your reminder is due now",
                kind="personal",
                reminder_id=int(due[0]),
            )
            return
        if (
            self.movement_enabled.get()
            and now >= self.next_movement_reminder
        ):
            movement_title, movement_subtitle = random.choice(MOVEMENT_PROMPTS)
            self._show_general_alert(
                title=movement_title,
                subtitle=movement_subtitle,
                kind="movement",
            )

    def _show_general_alert(
        self, title: str, subtitle: str, kind: str,
        reminder_id: int | None = None,
    ) -> None:
        if self.active_alert_kind or self.prompt_visible:
            return
        self._close_chatter_card()
        self.alert_previous_state = self.state
        self.active_alert_id = reminder_id
        self.active_alert_kind = kind
        self.alert_title = title
        self.alert_subtitle = subtitle
        self.motion_mode = "idle"
        self.current_action = None
        self.pending_edge_action = None
        self.idle_mood = ""
        self.state = "normal"
        self._resize_anchored(PROMPT_WIDTH, PROMPT_HEIGHT)
        self._begin_attention()
        self.root.deiconify()
        self.root.lift()
        self._play_reminder_sound()

    def _complete_active_alert(self) -> None:
        if self.active_alert_kind == "personal" and self.active_alert_id:
            with closing(sqlite3.connect(self.database_path)) as connection, connection:
                connection.execute(
                    "UPDATE personal_reminders SET status = 'done' WHERE reminder_id = ?",
                    (self.active_alert_id,),
                )
        elif self.active_alert_kind == "movement":
            self.next_movement_reminder = datetime.now() + timedelta(
                minutes=self.movement_minutes.get()
            )
        self._close_active_alert()
        self._show_chatter("All done! Panda high-five ✦", seconds=4)
        self._refresh_reminders()

    def _snooze_active_alert(self) -> None:
        snoozed_until = datetime.now(timezone.utc) + timedelta(minutes=10)
        if self.active_alert_kind == "personal" and self.active_alert_id:
            with closing(sqlite3.connect(self.database_path)) as connection, connection:
                connection.execute(
                    """
                    UPDATE personal_reminders
                    SET due_at = ?, status = 'scheduled'
                    WHERE reminder_id = ?
                    """,
                    (
                        snoozed_until.isoformat(timespec="seconds"),
                        self.active_alert_id,
                    ),
                )
        elif self.active_alert_kind == "movement":
            self.next_movement_reminder = datetime.now() + timedelta(minutes=10)
        preview = self.active_alert_kind.startswith("preview_")
        self._close_active_alert()
        self._show_chatter("Preview closed." if preview else "Okay, I’ll nudge you in 10!", seconds=4)
        self._refresh_reminders()

    def _close_active_alert(self) -> None:
        self.alert_window = None
        self.alert_pet_label = None
        self.alert_icon_label = None
        self.active_alert_id = None
        self.active_alert_kind = ""
        self.state = getattr(self,"alert_previous_state","normal")
        self._update_water_response(datetime.now())
        self._clear_attention()
        self._resize_anchored(SMALL_WIDTH, SMALL_HEIGHT)

    def _update_particles(self) -> None:
        alive: list[dict[str, float | str]] = []
        for particle in self.particles:
            particle["x"] = float(particle["x"]) + float(particle["vx"])
            particle["y"] = float(particle["y"]) + float(particle["vy"])
            particle["life"] = float(particle["life"]) - 1
            particle["vy"] = float(particle["vy"]) + 0.025
            if float(particle["life"]) > 0:
                alive.append(particle)
        self.particles = alive

    def _update_fullscreen_visibility(self) -> None:
        should_hide = (
            self.hide_fullscreen.get()
            and not self.prompt_visible
            and not self.active_alert_kind
            and self._foreground_is_fullscreen()
        )
        if should_hide and not self.was_hidden_for_fullscreen:
            self.root.withdraw()
            if self.chatter_window is not None and self.chatter_window.winfo_exists():
                self.chatter_window.withdraw()
            self.was_hidden_for_fullscreen = True
        elif not should_hide and self.was_hidden_for_fullscreen:
            self.root.deiconify()
            if self.chatter_until and self.chatter_text:
                self._show_chatter_card()
            self.was_hidden_for_fullscreen = False

    def _foreground_is_fullscreen(self) -> bool:
        if os.name != "nt":
            return False
        try:
            user32 = ctypes.windll.user32
            user32.GetForegroundWindow.restype = ctypes.c_void_p
            foreground = user32.GetForegroundWindow()
            if not foreground or foreground == self.root.winfo_id():
                return False

            class_name_buffer = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(foreground, class_name_buffer, 256)
            if class_name_buffer.value in {
                "Progman",
                "WorkerW",
                "Shell_TrayWnd",
                "Shell_SecondaryTrayWnd",
            }:
                return False

            process_id = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(
                foreground,
                ctypes.byref(process_id),
            )
            if process_id.value == os.getpid():
                return False

            class Rect(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            rect = Rect()
            user32.GetWindowRect.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(Rect),
            ]
            user32.GetWindowThreadProcessId.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_ulong),
            ]
            if not user32.GetWindowRect(foreground, ctypes.byref(rect)):
                return False
            user32.MonitorFromWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
            user32.MonitorFromWindow.restype = ctypes.c_void_p
            monitor = user32.MonitorFromWindow(foreground, 2)

            class MonitorInfo(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.c_ulong),
                    ("rcMonitor", Rect),
                    ("rcWork", Rect),
                    ("dwFlags", ctypes.c_ulong),
                ]

            info = MonitorInfo()
            info.cbSize = ctypes.sizeof(MonitorInfo)
            user32.GetMonitorInfoW.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(MonitorInfo),
            ]
            if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
                return False
            monitor_rect = info.rcMonitor
            tolerance = 2
            return (
                rect.left <= monitor_rect.left + tolerance
                and rect.top <= monitor_rect.top + tolerance
                and rect.right >= monitor_rect.right - tolerance
                and rect.bottom >= monitor_rect.bottom - tolerance
            )
        except (AttributeError, OSError, ctypes.ArgumentError):
            return False

    def _update_roaming(self, now: datetime) -> None:
        if self.dragging or self.motion_mode == "following":
            return

        if self.motion_mode == "falling":
            self._update_falling(now)
            return

        if self.motion_mode == "fetch_pickup":
            if self.fetch_pause_until and now >= self.fetch_pause_until:
                if self.fetch_origin is None:
                    self.motion_mode = "idle"
                    return
                self.target_x, self.target_y = self.fetch_origin
                self.walk_direction = "right" if self.target_x >= self.pet_x else "left"
                self.walk_speed = 6.2
                self.motion_mode = "fetch_return"
            return

        if self.motion_mode == "fetch_offer":
            if self.fetch_pause_until and now >= self.fetch_pause_until:
                self.motion_mode = "idle"
                self.fetch_origin = None
                self.fetch_pause_until = None
                self.idle_until = now + timedelta(seconds=2)
            return

        if self.motion_mode == "action":
            if self.action_until and now >= self.action_until:
                self.motion_mode = "idle"
                self.current_action = None
                self.action_until = None
                self.idle_until = now + timedelta(
                    seconds=random.uniform(1.5, 4.0)
                )
            return

        if self.motion_mode == "idle":
            if now < self.idle_until:
                return
            self._choose_destination()
            return

        dx = self.target_x - self.pet_x
        dy = self.target_y - self.pet_y
        distance = math.hypot(dx, dy)
        if distance <= self.walk_speed:
            self.pet_x = self.target_x
            self.pet_y = self.target_y
            if self.motion_mode == "fetch_out":
                self.motion_mode = "fetch_pickup"
                self.fetch_pause_until = now + timedelta(seconds=1.5)
                self._show_chatter("Got it! Bringing it back!", seconds=2)
            elif self.motion_mode == "fetch_return":
                self.motion_mode = "fetch_offer"
                self.fetch_pause_until = now + timedelta(seconds=3)
                self._show_chatter("Again? Again? Again?", seconds=3)
            elif self.pending_edge_action:
                self.current_action = self.pending_edge_action
                self.pending_edge_action = None
                self.motion_mode = "action"
                self.action_started_at = now
                self.action_until = now + timedelta(
                    seconds=(28.0 if self.current_action == "bored_edge" else random.uniform(3.5, 5.5))
                )
            else:
                self.motion_mode = "idle"
                self.idle_until = now + timedelta(seconds=self.roam_rest_seconds.get())
        else:
            step_speed = self.walk_speed
            if self.motion_mode == "walking":
                step_speed = min(self.walk_speed, max(1.15, distance * 0.07))
            if self.motion_mode == "walking":
                # Match window travel to the supporting foot's backward motion.
                cycle_seconds=self._walk_cycle_seconds()
                step_speed=(52*180/512)/(0.5*cycle_seconds)*(ACTIVE_TICK_MILLISECONDS/1000)
                step_speed=min(distance,step_speed)
            self.pet_x += (dx / distance) * step_speed
            self.pet_y += (dy / distance) * step_speed

        self._move_root(round(self.pet_x), round(self.pet_y))

    def _choose_edge_destination(self) -> None:
        left, top, right, bottom = self._screen_bounds()
        max_x = right - SMALL_WIDTH
        max_y = bottom - SMALL_HEIGHT - 42
        side = random.choice(("left", "right", "bottom"))
        if side == "left":
            self.target_x = float(left)
            self.target_y = float(random.randint(top + 48, max(top + 48, max_y)))
        elif side == "right":
            self.target_x = float(max_x)
            self.target_y = float(random.randint(top + 48, max(top + 48, max_y)))
        else:
            self.target_x = float(random.randint(left, max(left, max_x)))
            self.target_y = float(max_y)
        self.walk_direction = "right" if self.target_x >= self.pet_x else "left"
        speed_ranges = {
            "Calm": (1.9, 2.8),
            "Balanced": (2.6, 4.1),
            "Playful": (3.5, 5.4),
        }
        self.walk_speed = random.uniform(*speed_ranges[self.personality.get()])
        self.motion_mode = "walking"

    def _choose_destination(self) -> None:
        left, top, right, bottom = self._screen_bounds()
        max_x = right - SMALL_WIDTH
        max_y = bottom - SMALL_HEIGHT - 42

        ledges = self._visible_window_ledges()
        if ledges and random.random() < 0.28:
            ledge_left, ledge_top, ledge_right = random.choice(ledges)
            safe_left = max(left, ledge_left + 8)
            safe_right = min(max_x, ledge_right - SMALL_WIDTH - 8)
            if safe_right >= safe_left:
                self.target_x = float(random.randint(safe_left, safe_right))
                self.target_y = float(ledge_top - SMALL_HEIGHT + 8)
                self.walk_direction = (
                    "right" if self.target_x >= self.pet_x else "left"
                )
                speed_ranges = {
                    "Calm": (1.7, 2.7),
                    "Balanced": (2.4, 4.0),
                    "Playful": (3.2, 5.2),
                }
                self.walk_speed = random.uniform(
                    *speed_ranges[self.personality.get()]
                )
                self.motion_mode = "walking"
                return

        candidate_x = round(self.pet_x)
        candidate_y = round(self.pet_y)
        for _ in range(10):
            candidate_x = random.randint(left, max_x)
            candidate_y = random.randint(top, max_y)
            if math.hypot(
                candidate_x - self.pet_x,
                candidate_y - self.pet_y,
            ) >= 140:
                break

        self.target_x = float(candidate_x)
        self.target_y = float(candidate_y)
        self.walk_direction = (
            "right" if self.target_x >= self.pet_x else "left"
        )
        speed_ranges = {
            "Calm": (1.7, 2.7),
            "Balanced": (2.4, 4.0),
            "Playful": (3.2, 5.2),
        }
        self.walk_speed = random.uniform(*speed_ranges[self.personality.get()])
        self.motion_mode = "walking"

    def _update_falling(self, now: datetime) -> None:
        left, _top, right, bottom = self._screen_bounds()
        self.velocity_y += 0.72
        self.velocity_x *= 0.985
        next_x = self.pet_x + self.velocity_x
        next_y = self.pet_y + self.velocity_y

        if next_x <= left:
            next_x = float(left)
            self.velocity_x = abs(self.velocity_x) * 0.68
        elif next_x >= right - SMALL_WIDTH:
            next_x = float(right - SMALL_WIDTH)
            self.velocity_x = -abs(self.velocity_x) * 0.68

        landing_y = float(bottom - SMALL_HEIGHT - 42)
        if self.velocity_y >= 0:
            center_x = next_x + SMALL_WIDTH / 2
            current_bottom = self.pet_y + SMALL_HEIGHT - 8
            next_bottom = next_y + SMALL_HEIGHT - 8
            for ledge_left, ledge_top, ledge_right in self._visible_window_ledges():
                if not (ledge_left + 8 <= center_x <= ledge_right - 8):
                    continue
                if current_bottom <= ledge_top <= next_bottom + 5:
                    landing_y = min(
                        landing_y,
                        float(ledge_top - SMALL_HEIGHT + 8),
                    )

        if next_y >= landing_y:
            self.pet_y = landing_y
            if self.velocity_y > 5.5:
                self.velocity_y = -min(3.2, self.velocity_y * 0.24)
                self.velocity_x *= 0.72
            else:
                self.velocity_x = 0.0
                self.velocity_y = 0.0
                self.motion_mode = "idle"
                self.idle_until = now + timedelta(seconds=random.uniform(2.0, 5.0))
                for _ in range(4):
                    self.particles.append(
                        {
                            "x": float(50 + random.randint(0, 18)),
                            "y": 103.0,
                            "vx": random.uniform(-0.6, 0.6),
                            "vy": random.uniform(-0.9, -0.4),
                            "life": float(random.randint(12, 22)),
                            "kind": "sparkle",
                        }
                    )
        else:
            self.pet_y = next_y
        self.pet_x = next_x
        self._move_root(round(self.pet_x), round(self.pet_y))

    def _visible_window_ledges(self) -> list[tuple[int, int, int]]:
        if os.name != "nt":
            return []
        now = datetime.now()
        if (now - self.window_ledge_cache_at).total_seconds() < 2.5:
            return self.window_ledge_cache
        ledges: list[tuple[int, int, int]] = []
        try:
            user32 = ctypes.windll.user32

            class Rect(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            callback_type = ctypes.WINFUNCTYPE(
                ctypes.c_bool,
                ctypes.c_void_p,
                ctypes.c_void_p,
            )
            user32.IsWindowVisible.argtypes = [ctypes.c_void_p]
            user32.IsIconic.argtypes = [ctypes.c_void_p]
            user32.GetWindowTextLengthW.argtypes = [ctypes.c_void_p]
            user32.GetWindowRect.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(Rect),
            ]
            user32.EnumWindows.argtypes = [callback_type, ctypes.c_void_p]
            own_window = self.root.winfo_id()
            left, top, right, bottom = self._screen_bounds()

            def collect(hwnd: int, _lparam: int) -> bool:
                if hwnd == own_window:
                    return True
                process_id = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
                if process_id.value == os.getpid():
                    return True
                if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
                    return True
                if user32.GetWindowTextLengthW(hwnd) <= 0:
                    return True
                rect = Rect()
                if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    return True
                width = rect.right - rect.left
                height = rect.bottom - rect.top
                if width < 220 or height < 120:
                    return True
                if rect.top <= top + 45 or rect.top >= bottom - 70:
                    return True
                if rect.right <= left or rect.left >= right:
                    return True
                ledges.append((int(rect.left), int(rect.top), int(rect.right)))
                return True

            callback = callback_type(collect)
            user32.EnumWindows(callback, 0)
        except (AttributeError, OSError, ctypes.ArgumentError):
            return []
        self.window_ledge_cache = ledges
        self.window_ledge_cache_at = now
        return ledges

    def _draw(self) -> None:
        self._draw_pet_scene()
        if self.width > SMALL_WIDTH and not self.prompt_visible and not self.active_alert_kind:
            self.canvas.move("all", 0, 140)
        if self.chatter_until and self.chatter_text and not self.prompt_visible and not self.active_alert_kind:
            self._render_chatter_card()

    def _walk_cycle_seconds(self) -> float:
        personality = self.personality.get() if hasattr(self,"personality") else "Balanced"
        factor = {"Calm":0.82, "Balanced":1.0, "Playful":1.16}.get(personality,1.0)
        return 8*self.walk_frame_ms.get()/1000/factor

    def _locomotion_frame(self, kind: str) -> int:
        now = time.monotonic()
        signature = (kind,self.walk_direction,self.motion_mode)
        if getattr(self,"gait_signature",None) != signature:
            self.gait_signature = signature
            self.gait_started = now
        milliseconds = self.walk_frame_ms.get() if kind == "walk" else 110
        count = len(WALK_FRAME_ORDER) if kind == "walk" else self.pack_manifest[kind]["frames"]
        interval = self._walk_cycle_seconds()/count if kind == "walk" else milliseconds/1000
        return 1 + int((now-self.gait_started)/interval) % count

    def _draw_pet_scene(self) -> None:
        self.canvas.delete("all")
        if self.motion_mode not in ("walking","following","escaping"):
            self.gait_signature=None
        if self.active_alert_kind:
            self._draw_cloud_alert()
            return
        if self.prompt_visible:
            self._draw_prompt()
            return

        if self.dragging:
            sway = int(math.sin(self.frame * 0.55) * 3)
            self.canvas.create_image(
                SMALL_WIDTH // 2 + sway,
                PET_CENTER_Y,
                image=self._image("asking"),
            )
            self._draw_overlays()
            return

        if self.motion_mode == "falling":
            wobble = int(math.sin(self.frame * 0.8) * 5)
            image_key = "happy" if self.velocity_y < 1 else "asking"
            self.canvas.create_image(
                SMALL_WIDTH // 2 + wobble,
                PET_CENTER_Y,
                image=self._image(image_key),
            )
            self._draw_overlays()
            return

        if self.idle_mood:
            self._draw_ground_shadow()
            self._draw_idle_mood()
            self._draw_overlays()
            return

        if (
            self.state == "normal"
            and self.motion_mode in ("escaping", "fetch_out", "fetch_return")
        ):
            self._draw_ground_shadow()
            if self.motion_mode == "fetch_out":
                image_key = "fetch_chase"
            elif self.motion_mode == "fetch_return":
                image_key = "fetch_carry"
            else:
                run_frame = self._locomotion_frame("run")
                image_key = f"run_{self.walk_direction}_{run_frame}"
            self.canvas.create_image(
                SMALL_WIDTH // 2,
                PET_CENTER_Y,
                image=self._image(image_key),
            )
            self._draw_overlays()
            return

        if self.state == "normal" and self.motion_mode == "fetch_pickup":
            self._draw_ground_shadow()
            self.canvas.create_image(SMALL_WIDTH // 2, PET_CENTER_Y, image=self._image("fetch_look"))
            self._draw_overlays()
            return

        if self.state == "normal" and self.motion_mode == "fetch_offer":
            self._draw_ground_shadow()
            self.canvas.create_image(SMALL_WIDTH // 2, PET_CENTER_Y, image=self._image("fetch_offer"))
            self._draw_overlays()
            return

        if (
            self.state == "normal"
            and self.motion_mode in ("walking","following")
        ):
            self._draw_ground_shadow()
            if self.motion_mode=="following" and getattr(self,"cursor_at_rest",False):
                self.canvas.create_image(SMALL_WIDTH//2,PET_CENTER_Y,image=self._image("normal"))
                self._draw_overlays()
                return
            if self.pending_edge_action == "bored_edge":
                tired_frame = 1 + ((self.frame // 4) % 2)
                tired_bob = (0, 1, 2, 1)[(self.frame // 2) % 4]
                self.canvas.create_image(
                    SMALL_WIDTH // 2,
                    PET_CENTER_Y - tired_bob,
                    image=self._image(
                        f"bored_walk_{self.walk_direction}_{tired_frame}"
                    ),
                )
                self._draw_overlays()
                return
            # One phase drives the actual stride. The sheet already contains
            # body movement, so do not layer a second bounce over it.
            walk_frame = self._locomotion_frame("walk")
            image_key = f"walk_{self.walk_direction}_{walk_frame}"
            self.canvas.create_image(
                SMALL_WIDTH // 2,
                PET_CENTER_Y,
                image=self._image(image_key),
            )
            self._draw_overlays()
            return

        if (
            self.state == "normal"
            and self.motion_mode == "action"
            and self.current_action
        ):
            if self.current_action.startswith("pack:"):
                self._draw_pack_animation(self.current_action[5:], (datetime.now()-self.action_started_at).total_seconds())
                self._draw_overlays()
                return
            self._draw_ground_shadow()
            phase = self.frame * 0.45
            offset_x = 0
            offset_y = int(math.sin(phase) * 2)
            elapsed = (datetime.now() - self.action_started_at).total_seconds()
            remaining = (
                (self.action_until - datetime.now()).total_seconds()
                if self.action_until
                else 1.0
            )
            if self.current_action == "bored_edge":
                self._draw_bored_sequence(elapsed)
                self._draw_overlays()
                return
            if self.current_action in FREE_IDLE_MOODS:
                duration = max(0.1, elapsed + max(0.0, remaining))
                progress = min(1.0, elapsed / duration)
                action_image = self._natural_pose(self.current_action, progress)
                if self.current_action == "somersault" and 0.24 <= progress <= 0.72:
                    airborne = (progress - 0.24) / 0.48
                    offset_x = int(-8 + (airborne * 16))
                    offset_y = -int(math.sin(airborne * math.pi) * 14)
                elif self.current_action == "sneeze" and action_image == "sneeze":
                    offset_x = int(math.sin(phase * 4.2) * 3)
                elif self.current_action in ("stretch", "bow"):
                    offset_y = -int(abs(math.sin(phase * 1.6)) * 3)
                elif self.current_action in ("meditate", "sploot"):
                    offset_y = int(abs(math.sin(phase * 0.7)) * 2)
            else:
                action_image = self.current_action
                if elapsed < 0.28 or remaining < 0.32:
                    action_image = "normal"
                    offset_y = 2 if elapsed < 0.28 else 0
            if action_image == self.current_action and self.current_action == "action_hang":
                offset_x = int(math.sin(phase) * 4)
                offset_y = int(abs(math.sin(phase)) * 2)
            elif action_image == self.current_action and self.current_action == "action_bamboo":
                offset_y = int(math.sin(phase * 0.6) * 1)
            elif self.current_action == "staff" and action_image == self.current_action:
                if elapsed < 0.75:
                    action_image = "kungfu"
                offset_x = int(math.sin(phase * 1.8) * 3)
                offset_y = -int(abs(math.sin(phase * 1.3)) * 3)
            self.canvas.create_image(
                (SMALL_WIDTH // 2) + offset_x,
                PET_CENTER_Y + offset_y,
                image=self._image(action_image),
            )
            self._draw_overlays()
            return

        bounce = 0
        if self.state == "happy":
            bounce = int(abs(math.sin(self.frame * 0.65)) * 10)
        elif self.state == "normal":
            bounce = int(abs(math.sin(self.frame * 0.12)) * 1)

        self._draw_ground_shadow()
        idle_image = self.state
        if self.state == "normal" and self.frame % 95 in range(0, 5):
            idle_image = "blink"
        self.canvas.create_image(
            SMALL_WIDTH // 2,
            PET_CENTER_Y - bounce,
            image=self._image(idle_image),
        )

        self._draw_overlays()

    def _draw_ground_shadow(self) -> None:
        # A painted ground line obscured the curved feet. Keep the full silhouette.
        return

    def _draw_idle_mood(self) -> None:
        if self.idle_mood in ("wind_down", "groom"):
            sequence = WIND_DOWN_SEQUENCE if self.idle_mood == "wind_down" else GROOM_SEQUENCE
            key, elapsed = sequence_pose(sequence,(datetime.now()-self.idle_mood_started_at).total_seconds())
            self._draw_pack_animation(key, elapsed)
            return
        if self.idle_mood == "meditate":
            elapsed=(datetime.now()-self.idle_mood_started_at).total_seconds()
            self.canvas.create_image(SMALL_WIDTH//2,PET_CENTER_Y+math.sin(elapsed*1.4),image=self._image("meditate"))
            return
        if self.idle_mood=="bored":
            self._draw_bored_sequence((datetime.now()-self.idle_mood_started_at).total_seconds())
            return
        pack_aliases={"wave":"wave","nuzzle":"petting","yawn":"yawn_stretch","sleep":"sleep",
                      "dance":"dance","kungfu_combo":"kung_fu","somersault":"forward_roll","sneeze":"sneeze",
                      "stretch":"lazy_stretch","bow":"bow","sploot":"sploot","bored":"bored_shuffle",
                      "ear_rub":"ear_rub","jump":"jump","feed":"eat_bamboo"}
        key=self.idle_mood.removeprefix("pack:") if self.idle_mood.startswith("pack:") else pack_aliases.get(self.idle_mood)
        if key in self.pack_manifest:
            self._draw_pack_animation(key,(datetime.now()-self.idle_mood_started_at).total_seconds())
            return
        phase = self.frame * 0.32
        mood = self.idle_mood
        elapsed = max(0.0, (datetime.now() - self.idle_mood_started_at).total_seconds())
        if mood == "wave":
            progress = min(1.0, elapsed / 2.5)
            image_key = self._natural_pose("wave", progress)
            sway = int(math.sin(progress * math.tau * 3) * 2)
            self.canvas.create_image(
                SMALL_WIDTH // 2 + sway,
                PET_CENTER_Y + int(math.sin(phase) * 2),
                image=self._image(image_key),
            )
        elif mood == "nuzzle":
            duration = max(0.1, elapsed + max(
                0.0,
                (self.idle_mood_until - datetime.now()).total_seconds()
                if self.idle_mood_until
                else 0.0,
            ))
            image_key = self._natural_pose("nuzzle", min(1.0, elapsed / duration))
            self.canvas.create_image(
                SMALL_WIDTH // 2,
                PET_CENTER_Y + int(math.sin(phase) * 2),
                image=self._image(image_key),
            )
        elif mood == "yawn":
            if elapsed < 0.7:
                yawn_key = "normal"
            elif elapsed < 1.7:
                yawn_key = "yawn_1"
            elif elapsed < 3.6:
                yawn_key = "yawn_2"
            elif elapsed < 4.5:
                yawn_key = "stretch"
            else:
                yawn_key = "normal"
            self.canvas.create_image(
                SMALL_WIDTH // 2,
                PET_CENTER_Y + int(abs(math.sin(phase)) * 2),
                image=self._image(yawn_key),
            )
        elif mood in ("sleep", "nap"):
            self._draw_sleep_animation(elapsed)
        elif mood == "dance":
            duration = max(0.1, elapsed + max(
                0.0,
                (self.idle_mood_until - datetime.now()).total_seconds()
                if self.idle_mood_until
                else 0.0,
            ))
            progress = min(1.0, elapsed / duration)
            offset_x = int(math.sin(phase * 1.8) * 5)
            bounce = int(abs(math.sin(phase * 2.2)) * 8)
            self.canvas.create_image(
                SMALL_WIDTH // 2 + offset_x,
                PET_CENTER_Y - bounce,
                image=self._image(self._natural_pose("dance", progress)),
            )
            self.canvas.create_text(
                91,
                43,
                text="♪",
                fill=PALETTE["purple"],
                font=("Segoe UI Symbol", 13, "bold"),
            )
        elif mood == "kungfu_combo":
            self._draw_kungfu_combo(elapsed)
        elif mood == "feed":
            index = min(3, int(elapsed / 0.4)) if elapsed < 1.6 else 2 + (int(elapsed / 0.5) % 2)
            self.canvas.create_image(SMALL_WIDTH // 2, PET_CENTER_Y, image=self._image(f"feed_{index}"))
        elif mood in FREE_IDLE_MOODS:
            duration = max(0.1, elapsed + max(
                0.0,
                (self.idle_mood_until - datetime.now()).total_seconds()
                if self.idle_mood_until
                else 0.0,
            ))
            progress = min(1.0, elapsed / duration)
            offset_x = 0
            offset_y = 0
            if mood == "somersault":
                offset_x = int(math.sin(phase * 1.8) * 7)
                offset_y = -int(abs(math.sin(phase * 1.8)) * 8)
            elif mood == "sneeze":
                offset_x = int(math.sin(phase * 4.2) * 3)
            elif mood in ("stretch", "bow"):
                offset_y = -int(abs(math.sin(phase * 1.6)) * 4)
            elif mood in ("meditate", "sploot", "bored"):
                offset_y = int(abs(math.sin(phase * 0.7)) * 2)
            remaining = (
                (self.idle_mood_until - datetime.now()).total_seconds()
                if self.idle_mood_until
                else 1.0
            )
            action_image = self._natural_pose(mood, progress)
            if elapsed < 0.18 or remaining < 0.20:
                offset_x = 0
                offset_y = 2 if elapsed < 0.18 else 0
            self.canvas.create_image(
                SMALL_WIDTH // 2 + offset_x,
                PET_CENTER_Y + offset_y,
                image=self._image(action_image),
            )
            if mood == "sneeze" and action_image == mood:
                self.canvas.create_text(
                    94,
                    35,
                    text="achoo!",
                    fill=GLASS["aqua"],
                    font=("Segoe UI Variable Text", 7, "bold"),
                )
        else:
            float_y = int(math.sin(phase) * 2)
            self.canvas.create_image(
                SMALL_WIDTH // 2,
                PET_CENTER_Y + float_y,
                image=self._image("normal"),
            )
            for x, y, size in ((87, 34, 5), (94, 25, 8), (104, 16, 11)):
                self.canvas.create_oval(
                    x - size,
                    y - size,
                    x + size,
                    y + size,
                    fill=PALETTE["sky"],
                    outline="#91BBD5",
                )

    @staticmethod
    def _natural_pose(action: str, progress: float) -> str:
        if action == "somersault":
            if progress < 0.18 or progress > 0.88:
                return "normal"
            return f"packframe:forward_roll:{min(7, int((progress - 0.18) / 0.70 * 8))}"
        progress = max(0.0, min(1.0, progress))
        sequences = {
            "wave": (
                (0.00, "normal"),
                (0.10, "asking"),
                (0.22, "wave"),
                (0.38, "asking"),
                (0.50, "wave"),
                (0.66, "asking"),
                (0.78, "wave"),
                (0.92, "normal"),
            ),
            "jump": (
                (0.00, "normal"),
                (0.12, "bow"),
                (0.24, "stretch"),
                (0.36, "happy"),
                (0.52, "kungfu"),
                (0.66, "happy"),
                (0.80, "stretch"),
                (0.92, "normal"),
            ),
            "stretch": (
                (0.00, "normal"),
                (0.14, "bow"),
                (0.28, "stretch"),
                (0.78, "bow"),
                (0.92, "normal"),
            ),
            "sneeze": (
                (0.00, "normal"),
                (0.16, "asking"),
                (0.32, "yawn_1"),
                (0.50, "sneeze"),
                (0.72, "asking"),
                (0.90, "normal"),
            ),
            "meditate": (
                (0.00, "normal"),
                (0.12, "bow"),
                (0.24, "meditate"),
                (0.80, "blink"),
                (0.88, "meditate"),
                (0.94, "normal"),
            ),
            "sploot": (
                (0.00, "normal"),
                (0.12, "bow"),
                (0.24, "stretch"),
                (0.36, "sploot"),
                (0.80, "stretch"),
                (0.92, "normal"),
            ),
            "bow": (
                (0.00, "normal"),
                (0.18, "bow"),
                (0.78, "bow"),
                (0.90, "normal"),
            ),
            "somersault": (
                (0.00, "normal"),
                (0.10, "stretch"),
                (0.24, "kungfu"),
                (0.36, "somersault"),
                (0.72, "bow"),
                (0.88, "normal"),
            ),
            "nuzzle": (
                (0.00, "normal"),
                (0.16, "asking"),
                (0.30, "nuzzle"),
                (0.72, "happy"),
                (0.88, "normal"),
            ),
            "dance": (
                (0.00, "normal"),
                (0.10, "stretch"),
                (0.22, "happy"),
                (0.38, "wave"),
                (0.54, "happy"),
                (0.70, "wave"),
                (0.86, "happy"),
                (0.94, "normal"),
            ),
        }
        sequence = sequences.get(action)
        if not sequence:
            return action
        pose = sequence[0][1]
        for threshold, candidate in sequence:
            if progress < threshold:
                break
            pose = candidate
        return pose

    def _draw_sleep_animation(self, elapsed: float) -> None:
        breath_phase = elapsed * 2.0
        breathe = int((math.sin(breath_phase) + 1.0) * 1.5)
        self.canvas.create_image(
            SMALL_WIDTH // 2,
            PET_CENTER_Y + breathe,
            image=self._image("sleep"),
        )
        z_colours = ("#B9AFE0", "#9181CA", "#6F5BAE")
        for index in range(3):
            progress = ((elapsed * 0.32) + (index * 0.31)) % 1.0
            x = 79 + (index * 8) + int(math.sin((progress * math.tau) + index) * 2)
            y = 54 - int(progress * 38)
            self.canvas.create_text(
                x,
                y,
                text="z",
                fill=z_colours[index],
                font=("Segoe UI Variable Display", 7 + (index * 2), "bold"),
            )

    def _draw_kungfu_combo(self, elapsed: float) -> None:
        self._draw_pack_animation("kung_fu",elapsed)
        return
        if elapsed < 0.45:
            stage, image_key, offset_x, offset_y = 0, "normal", 0, 3
        elif elapsed < 1.00:
            stage, image_key, offset_x, offset_y = 1, "stretch", 0, -2
        elif elapsed < 1.80:
            stage, image_key = 2, "kungfu"
            offset_x = int(math.sin(elapsed * 18) * 3)
            offset_y = -int(abs(math.sin(elapsed * 8)) * 5)
        elif elapsed < 2.75:
            stage, image_key = 3, "somersault"
            turn = (elapsed - 1.80) / 0.95
            offset_x = int(-12 + (turn * 24))
            offset_y = -int(math.sin(turn * math.pi) * 16)
        elif elapsed < 3.55:
            stage, image_key = 4, "kungfu"
            offset_x = int(math.sin(elapsed * 20) * 4)
            offset_y = -int(abs(math.sin(elapsed * 9)) * 4)
        elif elapsed < 4.35:
            stage, image_key = 5, "stretch"
            offset_x = 0
            offset_y = int(abs(math.sin((elapsed - 3.55) * math.pi * 2)) * 4)
        else:
            stage, image_key, offset_x, offset_y = 6, "bow", 0, 1

        if stage != self.action_sequence_stage:
            self.action_sequence_stage = stage
            if stage in (2, 4, 5):
                for _index in range(5):
                    self.particles.append(
                        {
                            "x": float(58 + random.randint(-16, 16)),
                            "y": float(75 + random.randint(-8, 8)),
                            "vx": random.uniform(-0.8, 0.8),
                            "vy": random.uniform(-1.4, -0.5),
                            "life": float(random.randint(12, 22)),
                            "kind": "sparkle",
                        }
                    )
                self.particles = self.particles[-28:]

        self.canvas.create_image(
            (SMALL_WIDTH // 2) + offset_x,
            PET_CENTER_Y + offset_y,
            image=self._image(image_key),
        )
        if stage in (2, 4):
            self.canvas.create_text(
                96,
                32,
                text="hiya!",
                fill="#6F5BAE",
                font=("Segoe UI Variable Display", 7, "bold"),
            )

    def _draw_bored_sequence(self, elapsed: float) -> None:
        key="sit_on_log" if elapsed < 14 else "balance_on_log"
        self._draw_pack_animation(key, elapsed if elapsed < 14 else elapsed-14)
        return
        frame_times = (0.0, 3.0, 6.0, 9.0, 12.0, 16.0, 20.0, 24.0)
        frame_number = 1
        for index, start_time in enumerate(frame_times, start=1):
            if elapsed >= start_time:
                frame_number = index
        sway = int(math.sin(elapsed * 2.1) * 1)
        self.canvas.create_image(
            SMALL_WIDTH // 2 + sway,
            PET_CENTER_Y,
            image=self._image(f"bored_{frame_number}"),
        )
        if frame_number == 6:
            progress = min(1.0, max(0.0, elapsed - frame_times[5]))
            self.canvas.create_text(
                145 + int(progress * 12),
                72 - int(progress * 16),
                text="· sigh ·",
                fill="#BDB4E2",
                font=("Segoe UI Variable Display", 8, "italic"),
            )

    def _draw_overlays(self) -> None:
        for particle in self.particles:
            x = float(particle["x"])
            y = float(particle["y"])
            if particle["kind"] == "heart":
                self.canvas.create_text(
                    x,
                    y,
                    text="♥",
                    fill="#F08BAA",
                    font=("Segoe UI Symbol", 9, "bold"),
                )
            elif particle["kind"] == "sparkle":
                self.canvas.create_text(
                    x,
                    y,
                    text="✦",
                    fill="#E5B84C",
                    font=("Segoe UI Symbol", 8, "bold"),
                )
            elif particle["kind"] == "droplet":
                self.canvas.create_text(
                    x,
                    y,
                    text="●",
                    fill="#64BEE7",
                    font=("Segoe UI Symbol", 7, "bold"),
                )
            else:
                self.canvas.create_text(
                    x,
                    y,
                    text="❧",
                    fill="#63B79A",
                    font=("Segoe UI Symbol", 9, "bold"),
                )

    def _today_total(self) -> int:
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            return int(
                connection.execute(
                    """
                    SELECT COALESCE(SUM(millilitres), 0)
                    FROM water_entries
                    WHERE substr(recorded_at, 1, 10) = ?
                    """,
                    (datetime.now().date().isoformat(),),
                ).fetchone()[0]
            )

    def _cloud_shape(self, canvas, x1, y1, x2, y2, fill, outline) -> None:
        # Broad rounded lobes, with all padding inside the declared bounds.
        contour = [(0.04,0.45),(0.02,0.28),(0.13,0.20),(0.16,0.07),(0.32,0.09),
                   (0.42,0.01),(0.59,0.06),(0.73,0.04),(0.84,0.18),(0.96,0.20),
                   (0.98,0.39),(0.95,0.57),(0.98,0.76),(0.88,0.86),(0.78,0.96),
                   (0.61,0.93),(0.49,0.99),(0.32,0.94),(0.18,0.96),(0.10,0.82),
                   (0.02,0.75),(0.04,0.59)]
        points = [v for x,y in contour for v in (x1+x*(x2-x1),y1+y*(y2-y1))]
        canvas.create_polygon(points, smooth=True, splinesteps=24, fill=fill, outline=outline, width=1)

    def _draw_cloud_alert(self) -> None:
        self._cloud_shape(self.canvas, 194, 6, 350, 164, PALETTE["cream"], "#E0D4ED")
        self.canvas.create_oval(179, 166, 191, 178, fill=PALETTE["cream"], outline="#E0D4ED")
        self.canvas.create_oval(167, 185, 175, 193, fill=PALETTE["cream"], outline="#E0D4ED")
        personal = "personal" in self.active_alert_kind
        elapsed = (datetime.now() - self.attention_started_at).total_seconds() if self.attention_started_at else 0
        pose = f"clock_{min(5, int(elapsed / 0.22))}" if personal else f"hoop_{int(elapsed / 0.22) % 8}"
        self.canvas.create_image(90, 234, image=self._image(pose))
        title = textwrap.shorten(self.alert_title, width=70, placeholder="…") if personal else "Time to move!"
        self.canvas.create_text(272, 25, text=title, anchor="n", width=126,
                                fill=PALETTE["ink"], font=("Segoe UI", 10, "bold"), justify="center")
        self.canvas.create_text(272, 97, text=self.alert_subtitle if personal else "Hula, stretch, or take a little walk.",
                                width=126, fill=PALETTE["muted"], font=("Segoe UI", 8), justify="center")
        self._answer_button(204, 126, 257, 150, "Done", PALETTE["purple"], PALETTE["purple_dark"], "alert_done")
        self._answer_button(263, 126, 340, 150, "10 min later", PALETTE["teal"], "#439D87", "alert_snooze")
        self.canvas.tag_bind("alert_done", "<Button-1>", lambda event: self._complete_active_alert())
        self.canvas.tag_bind("alert_snooze", "<Button-1>", lambda event: self._snooze_active_alert())

    def _draw_prompt(self) -> None:
        self._cloud_shape(self.canvas, 194, 6, 350, 159, PALETTE["cream"], "#E0D4ED")
        self.canvas.create_oval(179, 164, 191, 176, fill=PALETTE["cream"], outline="#E0D4ED")
        self.canvas.create_oval(167, 185, 175, 193, fill=PALETTE["cream"], outline="#E0D4ED")
        self.canvas.create_text(272, 29, text="Water time?", fill=PALETTE["ink"], font=("Segoe UI", 10, "bold"))
        self.canvas.create_text(272, 49, text=f"Today: {self.today_total_cache} ml", fill=PALETTE["muted"], font=("Segoe UI", 8))
        for x, amount, tag, color in ((204,100,"amount_100",PALETTE["teal"]),(251,200,"amount_200","#69B8E8"),(298,300,"amount_300",PALETTE["purple"])):
            self._answer_button(x, 66, x+42, 91, f"{amount} ml", color, color, tag)
            self.canvas.tag_bind(tag, "<Button-1>", lambda event, ml=amount: self.record_water(ml, event))
        self._answer_button(204, 102, 258, 127, "Not yet", "#746F86", "#746F86", "not_yet")
        self._answer_button(264, 102, 340, 127, "10 min later", PALETTE["purple"], PALETTE["purple_dark"], "water_snooze")
        self.canvas.tag_bind("not_yet", "<Button-1>", self.answer_not_yet)
        self.canvas.tag_bind("water_snooze", "<Button-1>", self.snooze_water)
        self.canvas.create_text(272, 141, text="Pick an amount to log a sip", fill=PALETTE["muted"], font=("Segoe UI", 7))
        elapsed = (datetime.now() - self.attention_started_at).total_seconds() if self.attention_started_at else 0
        if elapsed < 0.88:
            image = self._pack_image("jump",index=min(7,int(elapsed/0.11)))
            y = 234-int(28*math.sin(elapsed/0.88*math.pi))
        elif elapsed < 1.68:
            image = self._pack_image("wave",index=min(3,int((elapsed-0.88)/0.2)))
            y = 234
        else:
            image = self._image(f"offer_{min(7, int((elapsed-1.68) / 0.28))}")
            y = 234
        self.canvas.create_image(90, y, image=image)

    def _answer_button(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        label: str,
        fill: str,
        outline: str,
        tag: str,
    ) -> None:
        tags = (tag, "answer_button")
        self._rounded_rectangle(
            x1,
            y1,
            x2,
            y2,
            11,
            fill=fill,
            outline=outline,
            width=1,
            tags=tags,
        )
        self.canvas.create_text(
            (x1 + x2) // 2,
            (y1 + y2) // 2,
            text=label,
            fill="white",
            font=("Segoe UI", 8, "bold"),
            tags=tags,
        )

    def _small_bubble(
        self,
        message: str,
        fill: str,
        text_color: str,
    ) -> None:
        self._cloud_shape(self.canvas, 20, 5, SMALL_WIDTH - 20, 44, fill, text_color)
        self.canvas.create_text(
            SMALL_WIDTH // 2,
            24,
            text=message,
            fill=text_color,
            font=(
                "Segoe UI Variable Display",
                9,
                "bold",
            ),
            justify="center",
            width=SMALL_WIDTH - 54,
        )

    def _rounded_rectangle(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        radius: int,
        **kwargs,
    ) -> int:
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        return self.canvas.create_polygon(
            points,
            smooth=True,
            splinesteps=24,
            **kwargs,
        )

    def _apply_windows_11_backdrop(self, window: tk.Toplevel) -> None:
        if os.name != "nt":
            return
        try:
            window.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            if not hwnd:
                hwnd = window.winfo_id()
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
            )
            corner = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(corner), ctypes.sizeof(corner)
            )
            backdrop = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop)
            )
        except (AttributeError, OSError, tk.TclError):
            pass

    def _hide_studio(self) -> None:
        if self.history_window is not None and self.history_window.winfo_exists():
            self._save_studio_settings()
            self.history_window.withdraw()

    def _launch_home_activity(self, callback) -> None:
        if self.history_window is not None and self.history_window.winfo_exists():
            self.history_window.withdraw()
        self.root.deiconify()
        self.root.lift()
        self.root.after(120, callback)

    def _start_edge_activity(self, action: str) -> None:
        if self.prompt_visible or self.dragging:
            return
        self.idle_mood = ""
        self.current_action = None
        self.pending_edge_action = action
        self._choose_edge_destination()

    def _show_modern_history(self) -> None:
        if self.history_window is not None and self.history_window.winfo_exists():
            self._refresh_history()
            self.history_window.deiconify()
            self.history_window.lift()
            self.history_window.focus_force()
            return

        window = tk.Toplevel(self.root)
        self.history_window = window
        window.title(f"{self.pet_name.get()} · Panda Home")
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        studio_width = min(880, max(740, screen_width - 120))
        studio_height = min(650, max(580, screen_height - 120))
        studio_x = max(20, (screen_width - studio_width) // 2)
        studio_y = max(20, (screen_height - studio_height) // 2)
        window.geometry(
            f"{studio_width}x{studio_height}{studio_x:+d}{studio_y:+d}"
        )
        window.minsize(min(740, studio_width), min(580, studio_height))
        window.configure(bg=GLASS["window"])
        window.protocol("WM_DELETE_WINDOW", self._hide_studio)
        window.bind("<Escape>", lambda _event: self._hide_studio())

        style = ttk.Style(window)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        label_font = ("Segoe UI Variable Text", 10)
        style.configure("TFrame", background=GLASS["surface"])
        style.configure("Glass.TFrame", background=GLASS["surface"])
        style.configure("Studio.TFrame", background=GLASS["surface"])
        style.configure("TLabel", background=GLASS["surface"], foreground=GLASS["text"], font=label_font)
        style.configure("Hero.TLabel", background=GLASS["surface"], foreground=GLASS["text"], font=("Segoe UI Variable Display", 23, "bold"))
        style.configure("Sub.TLabel", background=GLASS["surface"], foreground=GLASS["muted"], font=label_font)
        style.configure("CardTitle.TLabel", background=GLASS["surface"], foreground=GLASS["text"], font=("Segoe UI Variable Display", 15, "bold"))
        style.configure("CardSub.TLabel", background=GLASS["surface"], foreground=GLASS["muted"], font=("Segoe UI Variable Text", 9))
        style.configure("Accent.TButton", background=GLASS["accent"], foreground=GLASS["text"], borderwidth=0, padding=(14, 9), font=("Segoe UI Variable Text", 9, "bold"))
        style.map("Accent.TButton", background=[("active", GLASS["accent_hover"])])
        style.configure("TButton", background=GLASS["surface_hover"], foreground=GLASS["text"], borderwidth=0, padding=(12, 8), font=("Segoe UI Variable Text", 9))
        style.map("TButton", background=[("active", GLASS["border"])])
        style.configure("TCheckbutton", background=GLASS["surface"], foreground=GLASS["text"], padding=(0, 4), font=("Segoe UI Variable Text", 9))
        style.map("TCheckbutton", background=[("active", GLASS["surface"])], foreground=[("active", GLASS["text"])])
        style.configure("TLabelframe", background=GLASS["surface"], foreground=GLASS["muted"], bordercolor=GLASS["border"], relief="solid")
        style.configure("TLabelframe.Label", background=GLASS["surface"], foreground=GLASS["muted"], font=("Segoe UI Variable Text", 9, "bold"))
        style.configure("TEntry", fieldbackground=GLASS["surface_hover"], foreground=GLASS["text"], bordercolor=GLASS["border"], lightcolor=GLASS["border"], darkcolor=GLASS["border"], insertcolor=GLASS["text"], padding=8)
        style.configure("TCombobox", fieldbackground=GLASS["surface_hover"], foreground=GLASS["text"], background=GLASS["surface_hover"], arrowcolor=GLASS["muted"], bordercolor=GLASS["border"], padding=7)
        style.map("TCombobox", fieldbackground=[("readonly", GLASS["surface_hover"])], foreground=[("readonly", GLASS["text"])])
        style.configure("Treeview", background=GLASS["surface"], fieldbackground=GLASS["surface"], foreground=GLASS["text"], borderwidth=0, rowheight=31, font=("Segoe UI Variable Text", 9))
        style.map("Treeview", background=[("selected", GLASS["accent"])], foreground=[("selected", GLASS["text"])])
        style.configure("Treeview.Heading", background=GLASS["surface_hover"], foreground=GLASS["muted"], relief="flat", padding=7, font=("Segoe UI Variable Text", 9, "bold"))
        style.map("Treeview.Heading", background=[("active", GLASS["border"])])

        shell = tk.Frame(window, bg=GLASS["window"])
        shell.pack(fill="both", expand=True, padx=1, pady=1)
        rail = tk.Frame(shell, width=168, bg=GLASS["rail"])
        rail.pack(side="left", fill="y")
        rail.pack_propagate(False)
        content = tk.Frame(shell, bg=GLASS["surface"])
        content.pack(side="left", fill="both", expand=True)

        tk.Label(rail, text="●", bg=GLASS["rail"], fg=GLASS["aqua"], font=("Segoe UI", 12)).pack(anchor="w", padx=18, pady=(22, 2))
        tk.Label(rail, text="Water Panda", bg=GLASS["rail"], fg=GLASS["text"], font=("Segoe UI Variable Display", 15, "bold")).pack(anchor="w", padx=18)
        tk.Label(rail, text="Your quiet companion", bg=GLASS["rail"], fg=GLASS["muted"], font=("Segoe UI Variable Text", 8)).pack(anchor="w", padx=18, pady=(2, 20))

        page_host = tk.Frame(content, bg=GLASS["surface"])
        page_host.pack(fill="both", expand=True, padx=30, pady=26)
        overview_frame = ttk.Frame(page_host, style="Glass.TFrame")
        history_frame = ttk.Frame(page_host, style="Glass.TFrame")
        reminder_frame = ttk.Frame(page_host, style="Glass.TFrame")
        pet_frame = ttk.Frame(page_host, style="Glass.TFrame")
        activities_frame = ttk.Frame(page_host, style="Glass.TFrame")
        behavior_frame = ttk.Frame(page_host, style="Glass.TFrame")
        pages = [overview_frame, history_frame, reminder_frame, pet_frame, activities_frame, behavior_frame]
        for page in pages:
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        nav_buttons: list[tk.Button] = []
        for label in ("Home", "Water history", "Reminders", "Panda settings", "Panda activities", "Behaviour"):
            button = tk.Button(
                rail,
                text=label,
                anchor="w",
                bd=0,
                relief="flat",
                bg=GLASS["rail"],
                fg=GLASS["muted"],
                activebackground=GLASS["surface_hover"],
                activeforeground=GLASS["text"],
                font=("Segoe UI Variable Text", 10),
                padx=16,
                pady=11,
                cursor="hand2",
            )
            button.pack(fill="x", padx=10, pady=2)
            nav_buttons.append(button)
        switcher = StudioPageSwitcher(pages, nav_buttons)
        self.studio_notebook = switcher
        for index, button in enumerate(nav_buttons):
            button.configure(command=lambda selected=index: switcher.select(selected))

        self.memories_label = tk.Label(
            rail,
            text=self._memory_text(),
            bg=GLASS["rail"],
            fg=GLASS["muted"],
            font=("Segoe UI Variable Text", 8),
            justify="left",
            wraplength=132,
        )
        self.memories_label.pack(side="bottom", anchor="w", padx=18, pady=(0, 20))

        ttk.Label(overview_frame, text="Good to see you", style="Hero.TLabel").pack(anchor="w")
        ttk.Label(overview_frame, text=f"{self.pet_name.get()} is keeping the little things on track.", style="Sub.TLabel").pack(anchor="w", pady=(2, 22))
        self.today_label = ttk.Label(overview_frame, text="Today  ·  0 ml", style="CardTitle.TLabel")
        self.today_label.pack(anchor="w")
        self.summary_label = ttk.Label(overview_frame, text="Your last seven days", style="CardSub.TLabel")
        self.summary_label.pack(anchor="w", pady=(2, 5))
        self.chart_canvas = tk.Canvas(overview_frame, height=164, bg=GLASS["surface"], highlightthickness=0)
        self.chart_canvas.pack(fill="x", pady=(0, 12))
        ttk.Label(overview_frame, text="Recent sips", style="CardTitle.TLabel").pack(anchor="w", pady=(2, 7))
        self.entry_tree = ttk.Treeview(overview_frame, columns=("time", "amount"), show="headings", height=6)
        self.entry_tree.heading("time", text="Recorded at")
        self.entry_tree.heading("amount", text="Amount")
        self.entry_tree.column("time", width=330, anchor="w")
        self.entry_tree.column("amount", width=110, anchor="center")
        self.entry_tree.pack(fill="both", expand=True)

        ttk.Label(history_frame, text="Water history", style="Hero.TLabel").pack(anchor="w")
        ttk.Label(history_frame, text="Every check-in stays on this device.", style="Sub.TLabel").pack(anchor="w", pady=(2, 18))
        self.daily_tree = ttk.Treeview(history_frame, columns=("date", "total", "count"), show="headings", height=13)
        self.daily_tree.heading("date", text="Date")
        self.daily_tree.heading("total", text="Total")
        self.daily_tree.heading("count", text="Water moments")
        self.daily_tree.column("date", width=220, anchor="w")
        self.daily_tree.column("total", width=120, anchor="center")
        self.daily_tree.column("count", width=140, anchor="center")
        self.daily_tree.pack(fill="both", expand=True, pady=(0, 14))
        history_controls = ttk.Frame(history_frame, style="Glass.TFrame")
        history_controls.pack(fill="x")
        ttk.Button(history_controls, text="Undo latest", command=self.undo_latest_entry).pack(side="left")
        ttk.Button(history_controls, text="Export CSV", command=self.export_history).pack(side="left", padx=8)

        ttk.Label(reminder_frame, text="Reminders", style="Hero.TLabel").pack(anchor="w")
        ttk.Label(reminder_frame, text="Personal alerts delivered by your panda.", style="Sub.TLabel").pack(anchor="w", pady=(2, 18))
        self._build_reminder_tab(reminder_frame)

        ttk.Label(pet_frame, text="Panda settings", style="Hero.TLabel").pack(anchor="w")
        ttk.Label(pet_frame, text="Keep the companion calm, playful or somewhere between.", style="Sub.TLabel").pack(anchor="w", pady=(2, 22))
        ttk.Label(pet_frame, text="Pet name", style="CardTitle.TLabel").pack(anchor="w")
        self.name_entry = ttk.Entry(pet_frame, textvariable=self.pet_name, width=28)
        self.name_entry.pack(anchor="w", pady=(6, 18))
        self.name_entry.bind("<FocusOut>", lambda _event: self._save_studio_settings())
        ttk.Label(pet_frame, text="Personality", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(pet_frame, text="Personality changes walking speed and chatter. Set timing in Behaviour.", style="CardSub.TLabel").pack(anchor="w", pady=(2, 7))
        personality_box = ttk.Combobox(pet_frame, textvariable=self.personality, values=("Calm", "Balanced", "Playful"), state="readonly", width=18)
        personality_box.pack(anchor="w", pady=(0, 18))
        personality_box.bind("<<ComboboxSelected>>", lambda _event: self._save_studio_settings())
        ttk.Checkbutton(pet_frame, text="Let the panda wander around my screens", variable=self.roam_enabled, command=self._toggle_roaming).pack(anchor="w", pady=3)
        ttk.Checkbutton(pet_frame, text="Play one gentle sound with reminders", variable=self.sound_enabled, command=self._settings_changed).pack(anchor="w", pady=3)
        ttk.Checkbutton(pet_frame, text="Hide the panda while an app is fullscreen", variable=self.hide_fullscreen, command=self._settings_changed).pack(anchor="w", pady=3)
        movement_card = ttk.LabelFrame(pet_frame, text="Movement reminder", padding=14)
        movement_card.pack(fill="x", pady=(18, 0))
        ttk.Checkbutton(movement_card, text="Remind me to stand and stretch", variable=self.movement_enabled, command=self._movement_settings_changed).pack(side="left")
        ttk.Label(movement_card, text="Every").pack(side="left", padx=(18, 5))
        movement_box = ttk.Combobox(movement_card, textvariable=self.movement_minutes, values=(30, 45, 60, 90, 120), width=5, state="readonly")
        movement_box.pack(side="left")
        movement_box.bind("<<ComboboxSelected>>", lambda _event: self._movement_settings_changed())
        ttk.Label(movement_card, text="minutes").pack(side="left", padx=(5, 0))

        ttk.Label(behavior_frame, text="Behaviour and timing", style="Hero.TLabel").pack(anchor="w")
        ttk.Label(behavior_frame, text="Reminders take priority. Activities wait until the panda is free.", style="Sub.TLabel").pack(anchor="w", pady=(4,18))

        ttk.Checkbutton(behavior_frame, text="Ask for bamboo when hungry", variable=self.hunger_enabled, command=self._behavior_settings_changed).pack(anchor="w",pady=3)
        ttk.Checkbutton(behavior_frame, text="Sleep when the computer is inactive", variable=self.sleep_enabled, command=self._behavior_settings_changed).pack(anchor="w", pady=3)
        for label, variable, options in (
            ("Cursor behavior", self.cursor_mode, ("Off","Follow","Avoid")),
            ("Ask for bamboo every (minutes)", self.hunger_minutes, (15,30,60,90,120,180,240,360)),
            ("Walk frame duration (milliseconds)", self.walk_frame_ms, (100,140,180,220,260,300)),
            ("Rest between walks (seconds)", self.roam_rest_seconds, (30,60,90,180,300,600)),
            ("Yawn after inactivity (seconds)", self.yawn_after_seconds, (30,60,90,120)),
            ("Sleep after inactivity (minutes)", self.sleep_after_minutes, (2,3,5,10,30,60)),
            ("Automatic activity", self.auto_activity, ("Gentle routine","Selected routine","Manual only","Meditate") + tuple(ACTIVITY_LABELS[key] for key in ROUTINE_ACTIVITIES)),
            ("Activity interval (minutes)", self.activity_minutes, (1,3,5,10,15,30,60)),
        ):
            row = ttk.Frame(behavior_frame, style="Glass.TFrame")
            row.pack(fill="x", pady=8)
            ttk.Label(row, text=label, width=32).pack(side="left")
            box = ttk.Combobox(row, textvariable=variable, values=options, state="readonly", width=16)
            box.pack(side="left")
            box.bind("<<ComboboxSelected>>", lambda _event: self._behavior_settings_changed())
        ttk.Label(behavior_frame, text="Gentle routine cycles through quiet activities. Selected routine uses your choices below.\nExisting Manual only settings are preserved: select a routine to enable automatic play.", style="Sub.TLabel", wraplength=500).pack(anchor="w", pady=12)
        routine_choices = ttk.Frame(behavior_frame,style="Glass.TFrame")
        routine_choices.pack(fill="x")
        for i,(key,enabled) in enumerate(self.routine_enabled.items()):
            ttk.Checkbutton(routine_choices,text=ACTIVITY_LABELS[key],variable=enabled,command=self._behavior_settings_changed).grid(row=i//3,column=i%3,sticky="w",padx=8,pady=3)


        ttk.Label(activities_frame, text="Panda activities", style="Hero.TLabel").pack(anchor="w")
        ttk.Label(
            activities_frame,
            text="Choose an activity and Panda Home will hide while your panda performs it.",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(2, 18))
        activity_host = ttk.Frame(activities_frame, style="Glass.TFrame")
        activity_host.pack(fill="both", expand=True)
        activity_canvas = tk.Canvas(activity_host, bg=GLASS["surface"], highlightthickness=0)
        activity_scroll = ttk.Scrollbar(activity_host, orient="vertical", command=activity_canvas.yview)
        activity_canvas.configure(yscrollcommand=activity_scroll.set)
        activity_scroll.pack(side="right",fill="y")
        activity_canvas.pack(side="left",fill="both",expand=True)
        activity_grid = ttk.Frame(activity_canvas, style="Glass.TFrame")
        activity_window = activity_canvas.create_window(0,0,window=activity_grid,anchor="nw")
        activity_grid.bind("<Configure>",lambda event: activity_canvas.configure(scrollregion=activity_canvas.bbox("all")))
        activity_canvas.bind("<Configure>",lambda event: activity_canvas.itemconfigure(activity_window,width=event.width))
        activity_canvas.bind("<MouseWheel>",lambda event: activity_canvas.yview_scroll(-int(event.delta/120),"units"))
        activities = tuple((label,lambda chosen=key:self._play_activity(chosen)) for key,label in ACTIVITY_LABELS.items())
        for index, (label, callback) in enumerate(activities):
            button = ttk.Button(
                activity_grid,
                text=label,
                command=lambda chosen=callback: self._launch_home_activity(chosen),
            )
            button.grid(
                row=index // 2,
                column=index % 2,
                sticky="ew",
                padx=(0 if index % 2 == 0 else 8, 0),
                pady=(0, 8),
            )
        for column in range(2):
            activity_grid.columnconfigure(column, weight=1)

        switcher.select(0)
        window.after(80, lambda: self._apply_windows_11_backdrop(window))
        self._refresh_history()

    def show_history(self) -> None:
        self._show_modern_history()

    def _legacy_show_history(self) -> None:
        if (
            self.history_window is not None
            and self.history_window.winfo_exists()
        ):
            self._refresh_history()
            self.history_window.deiconify()
            self.history_window.lift()
            return

        window = tk.Toplevel(self.root)
        self.history_window = window
        window.title(f"{self.pet_name.get()} · Care Studio")
        window.geometry("590x690")
        window.minsize(540, 590)
        window.configure(bg=PALETTE["lavender"])
        window.attributes("-topmost", True)

        style = ttk.Style(window)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Studio.TFrame", background=PALETTE["cream"])
        style.configure(
            "Hero.TLabel",
            background=PALETTE["lavender"],
            foreground=PALETTE["ink"],
            font=("Segoe UI", 20, "bold"),
        )
        style.configure(
            "Sub.TLabel",
            background=PALETTE["lavender"],
            foreground=PALETTE["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "CardTitle.TLabel",
            background=PALETTE["cream"],
            foreground=PALETTE["ink"],
            font=("Segoe UI", 15, "bold"),
        )
        style.configure(
            "CardSub.TLabel",
            background=PALETTE["cream"],
            foreground=PALETTE["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "Accent.TButton",
            background=PALETTE["purple"],
            foreground="white",
            padding=(12, 7),
            font=("Segoe UI", 9, "bold"),
        )
        style.map("Accent.TButton", background=[("active", PALETTE["purple_dark"])])
        style.configure("Treeview", rowheight=27, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

        hero = ttk.Frame(window, padding=(22, 18, 22, 12))
        hero.pack(fill="x")
        hero.configure(style="Studio.TFrame")
        ttk.Label(
            hero,
            text=f"{self.pet_name.get()}’s care studio ✦",
            style="CardTitle.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            hero,
            text="Water history, movement breaks and the things you do not want to forget.",
            style="CardSub.TLabel",
        ).pack(anchor="w", pady=(3, 0))
        self.memories_label = ttk.Label(
            hero,
            text=self._memory_text(),
            style="CardSub.TLabel",
        )
        self.memories_label.pack(anchor="w", pady=(5, 0))

        container = ttk.Frame(window, padding=(18, 8, 18, 14))
        container.pack(fill="both", expand=True)
        container.configure(style="Studio.TFrame")

        notebook = ttk.Notebook(container)
        self.studio_notebook = notebook
        notebook.pack(fill="both", expand=True)

        overview_frame = ttk.Frame(notebook, padding=14, style="Studio.TFrame")
        history_frame = ttk.Frame(notebook, padding=12, style="Studio.TFrame")
        reminder_frame = ttk.Frame(notebook, padding=16, style="Studio.TFrame")
        pet_frame = ttk.Frame(notebook, padding=18, style="Studio.TFrame")
        notebook.add(overview_frame, text="  Overview  ")
        notebook.add(history_frame, text="  History  ")
        notebook.add(reminder_frame, text="  Reminders  ")
        notebook.add(pet_frame, text="  Pet & comfort  ")

        self.today_label = ttk.Label(
            overview_frame,
            text="Today · 0 ml",
            style="CardTitle.TLabel",
        )
        self.today_label.pack(anchor="w")
        self.summary_label = ttk.Label(
            overview_frame,
            text="Your last seven days",
            style="CardSub.TLabel",
        )
        self.summary_label.pack(anchor="w", pady=(2, 8))
        self.chart_canvas = tk.Canvas(
            overview_frame,
            height=150,
            bg=PALETTE["cream"],
            highlightthickness=0,
        )
        self.chart_canvas.pack(fill="x", pady=(0, 10))

        ttk.Label(
            overview_frame,
            text="Recent sips",
            style="CardTitle.TLabel",
        ).pack(anchor="w", pady=(4, 7))
        self.entry_tree = ttk.Treeview(
            overview_frame,
            columns=("time", "amount"),
            show="headings",
            height=7,
        )
        self.entry_tree.heading("time", text="Recorded at")
        self.entry_tree.heading("amount", text="Amount")
        self.entry_tree.column("time", width=315, anchor="w")
        self.entry_tree.column("amount", width=110, anchor="center")
        self.entry_tree.pack(fill="both", expand=True)

        self.daily_tree = ttk.Treeview(
            history_frame,
            columns=("date", "total", "count"),
            show="headings",
            height=13,
        )
        self.daily_tree.heading("date", text="Date")
        self.daily_tree.heading("total", text="Total")
        self.daily_tree.heading("count", text="Water moments")
        self.daily_tree.column("date", width=190, anchor="w")
        self.daily_tree.column("total", width=120, anchor="center")
        self.daily_tree.column("count", width=130, anchor="center")
        self.daily_tree.pack(fill="both", expand=True)

        self._build_reminder_tab(reminder_frame)

        ttk.Label(pet_frame, text="Pet name", style="CardTitle.TLabel").pack(anchor="w")
        self.name_entry = ttk.Entry(pet_frame, textvariable=self.pet_name, width=28)
        self.name_entry.pack(anchor="w", pady=(6, 18))
        self.name_entry.bind("<FocusOut>", lambda _event: self._save_studio_settings())

        ttk.Label(
            pet_frame,
            text="Your companion · Panda",
            style="CardTitle.TLabel",
        ).pack(anchor="w", pady=(0, 18))

        ttk.Label(pet_frame, text="Personality", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(
            pet_frame,
            text="Personality changes walking speed and chatter. Set timing in Behaviour.",
            style="CardSub.TLabel",
        ).pack(anchor="w", pady=(2, 6))
        personality_box = ttk.Combobox(
            pet_frame,
            textvariable=self.personality,
            values=("Calm", "Balanced", "Playful"),
            state="readonly",
            width=18,
        )
        personality_box.pack(anchor="w", pady=(0, 18))
        personality_box.bind("<<ComboboxSelected>>", lambda _event: self._save_studio_settings())

        ttk.Checkbutton(
            pet_frame,
            text="Let the pet wander around my screens",
            variable=self.roam_enabled,
            command=self._toggle_roaming,
        ).pack(anchor="w", pady=4)
        ttk.Checkbutton(
            pet_frame,
            text="Play one gentle sound with reminders",
            variable=self.sound_enabled,
            command=self._settings_changed,
        ).pack(anchor="w", pady=4)
        ttk.Checkbutton(
            pet_frame,
            text="Hide the pet while an app is fullscreen",
            variable=self.hide_fullscreen,
            command=self._settings_changed,
        ).pack(anchor="w", pady=4)

        movement_card = ttk.LabelFrame(
            pet_frame,
            text="Movement reminder",
            padding=12,
        )
        movement_card.pack(fill="x", pady=(18, 0))
        ttk.Checkbutton(
            movement_card,
            text="Remind me to stand and stretch",
            variable=self.movement_enabled,
            command=self._movement_settings_changed,
        ).pack(side="left")
        ttk.Label(movement_card, text="Every").pack(side="left", padx=(18, 5))
        movement_box = ttk.Combobox(
            movement_card,
            textvariable=self.movement_minutes,
            values=(30, 45, 60, 90, 120),
            width=5,
            state="readonly",
        )
        movement_box.pack(side="left")
        movement_box.bind(
            "<<ComboboxSelected>>",
            lambda _event: self._movement_settings_changed(),
        )
        ttk.Label(movement_card, text="minutes").pack(side="left", padx=(5, 0))

        controls = ttk.Frame(container)
        controls.pack(fill="x", pady=(10, 0))
        ttk.Button(
            controls,
            text="Undo latest",
            command=self.undo_latest_entry,
        ).pack(side="left")
        ttk.Button(
            controls,
            text="Export CSV",
            command=self.export_history,
        ).pack(side="left", padx=8)
        ttk.Button(
            controls,
            text="Done",
            style="Accent.TButton",
            command=window.destroy,
        ).pack(side="right")

        self._refresh_history()

    def show_reminders(self) -> None:
        self.show_history()
        if self.studio_notebook is not None and self.studio_notebook.winfo_exists():
            self.studio_notebook.select(2)

    def _save_studio_settings(self) -> None:
        cleaned = self.pet_name.get().strip()[:18] or "Mochi"
        self.pet_name.set(cleaned)
        self.menu.entryconfigure(0, label="Open Panda Home")
        if self.history_window and self.history_window.winfo_exists():
            self.history_window.title(f"{cleaned} · Panda Home")
        self._save_settings()

    def _refresh_history(self) -> None:
        if (
            self.history_window is None
            or not self.history_window.winfo_exists()
            or self.daily_tree is None
            or self.entry_tree is None
        ):
            return

        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            daily_rows = connection.execute(
                """
                SELECT
                    substr(recorded_at, 1, 10) AS recorded_date,
                    SUM(millilitres) AS total_ml,
                    COUNT(*) AS entry_count
                FROM water_entries
                GROUP BY substr(recorded_at, 1, 10)
                ORDER BY recorded_date DESC
                LIMIT 60
                """
            ).fetchall()
            entry_rows = connection.execute(
                """
                SELECT recorded_at, millilitres
                FROM water_entries
                ORDER BY entry_id DESC
                LIMIT 100
                """
            ).fetchall()
            today_total = connection.execute(
                """
                SELECT COALESCE(SUM(millilitres), 0)
                FROM water_entries
                WHERE substr(recorded_at, 1, 10) = ?
                """,
                (datetime.now().date().isoformat(),),
            ).fetchone()[0]
            week_rows = connection.execute(
                """
                SELECT substr(recorded_at, 1, 10), SUM(millilitres)
                FROM water_entries
                WHERE substr(recorded_at, 1, 10) >= ?
                GROUP BY substr(recorded_at, 1, 10)
                """,
                ((datetime.now().date() - timedelta(days=6)).isoformat(),),
            ).fetchall()

        for item in self.daily_tree.get_children():
            self.daily_tree.delete(item)
        for recorded_date, total_ml, entry_count in daily_rows:
            try:
                friendly_date = datetime.fromisoformat(recorded_date).strftime(
                    "%a, %d %b %Y"
                )
            except ValueError:
                friendly_date = recorded_date
            self.daily_tree.insert(
                "",
                "end",
                values=(friendly_date, f"{total_ml} ml", entry_count),
            )

        for item in self.entry_tree.get_children():
            self.entry_tree.delete(item)
        for timestamp, millilitres in entry_rows:
            try:
                formatted_time = datetime.fromisoformat(timestamp).strftime(
                    "%d %b %Y, %I:%M %p"
                )
            except ValueError:
                formatted_time = timestamp
            self.entry_tree.insert(
                "",
                "end",
                values=(formatted_time, f"{millilitres} ml"),
            )

        if self.today_label is not None:
            self.today_label.configure(text=f"Today · {today_total} ml")
        self.today_total_cache = int(today_total)
        week_total = sum(int(row[1]) for row in week_rows)
        active_days = len(week_rows)
        if self.summary_label is not None:
            if active_days:
                average = round(week_total / active_days)
                self.summary_label.configure(
                    text=(
                        f"Last 7 days · {week_total} ml total · "
                        f"{average} ml per active day"
                    )
                )
            else:
                self.summary_label.configure(
                    text="Your first logged sip will appear here."
                )
        self._draw_week_chart(dict(week_rows))
        self._refresh_reminders()

    def _draw_week_chart(self, totals: dict[str, int]) -> None:
        if self.chart_canvas is None or not self.chart_canvas.winfo_exists():
            return
        canvas = self.chart_canvas
        canvas.delete("all")
        canvas.update_idletasks()
        width = max(440, canvas.winfo_width())
        height = 150
        days = [datetime.now().date() - timedelta(days=offset) for offset in range(6, -1, -1)]
        values = [int(totals.get(day.isoformat(), 0)) for day in days]
        maximum = max(values) if max(values, default=0) else 1
        left = 14
        gap = 10
        bar_width = max(32, (width - 2 * left - 6 * gap) // 7)
        baseline = 119

        canvas.create_line(
            left,
            baseline,
            width - left,
            baseline,
            fill=GLASS["border"],
        )
        for index, (day, value) in enumerate(zip(days, values)):
            x1 = left + index * (bar_width + gap)
            x2 = x1 + bar_width
            bar_height = 7 if value == 0 else max(16, round(78 * value / maximum))
            y1 = baseline - bar_height
            fill = GLASS["aqua"] if index == 6 else GLASS["accent"]
            canvas.create_rectangle(
                x1,
                y1 + 7,
                x2,
                baseline,
                fill=fill,
                outline="",
            )
            canvas.create_oval(
                x1,
                y1,
                x2,
                y1 + 14,
                fill=fill,
                outline="",
            )
            if value:
                canvas.create_text(
                    (x1 + x2) // 2,
                    y1 - 8,
                    text=str(value),
                    fill=GLASS["muted"],
                    font=("Segoe UI Variable Text", 7, "bold"),
                )
            canvas.create_text(
                (x1 + x2) // 2,
                137,
                text=day.strftime("%a")[0],
                fill=GLASS["muted"],
                font=("Segoe UI Variable Text", 8, "bold"),
            )

    def undo_latest_entry(self) -> None:
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            latest = connection.execute(
                """
                SELECT entry_id, recorded_at, millilitres
                FROM water_entries
                ORDER BY entry_id DESC
                LIMIT 1
                """
            ).fetchone()
            if latest is None:
                messagebox.showinfo(
                    "Water History",
                    "There is no water entry to undo.",
                    parent=self.history_window or self.root,
                )
                return

            entry_id, timestamp, millilitres = latest
            confirmed = messagebox.askyesno(
                "Undo latest entry",
                f"Remove the latest {millilitres} ml entry?\n\n{timestamp}",
                parent=self.history_window or self.root,
            )
            if not confirmed:
                return
            connection.execute(
                "DELETE FROM water_entries WHERE entry_id = ?",
                (entry_id,),
            )
        self._refresh_history()

    def export_history(self) -> None:
        with closing(sqlite3.connect(self.database_path)) as connection, connection:
            rows = connection.execute(
                """
                SELECT recorded_at, millilitres
                FROM water_entries
                ORDER BY entry_id
                """
            ).fetchall()

        if not rows:
            self._show_chatter("No water history to export yet.", seconds=4)
            return

        destination = filedialog.asksaveasfilename(
            parent=self.history_window or self.root,
            title="Export water history",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=(
                f"water_history_{datetime.now():%Y%m%d}.csv"
            ),
        )
        if not destination:
            return

        with open(destination, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["Recorded At", "Millilitres"])
            writer.writerows(rows)

        self._show_chatter("Water history exported.", seconds=4)

    def close(self) -> None:
        self._save_settings()
        self._close_chatter_card()
        self.tray.stop()
        try:
            (self.app_dir / "water_puppy.pid").unlink(missing_ok=True)
        except OSError:
            pass
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    if "--verify-ui" in sys.argv:
        from windows_ui_validation import run_validation
        output_index = sys.argv.index("--verify-ui") + 1
        output_path = Path(sys.argv[output_index]).resolve()
        enable_windows_dpi_awareness()
        run_validation(WaterPet, output_path)
        return
    try:
        enable_windows_dpi_awareness()
        install_and_restart_if_needed()
        ensure_single_instance(Path(__file__).resolve().parent)
        WaterPet().run()
    except SystemExit:
        raise
    except Exception as error:
        error_path = Path(__file__).resolve().parent / "startup_error.log"
        details = traceback.format_exc()
        try:
            error_path.write_text(details, encoding="utf-8")
        except OSError:
            pass
        try:
            emergency_root = tk.Tk()
            emergency_root.withdraw()
            messagebox.showerror(
                "Water Panda could not start",
                f"{error}\n\nA diagnostic file was saved as startup_error.log.",
                parent=emergency_root,
            )
            emergency_root.destroy()
        except tk.TclError:
            pass


if __name__ == "__main__":
    main()
