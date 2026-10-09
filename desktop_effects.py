"""Finite, click-through seasonal effects. Never capture keyboard or mouse."""
import ctypes
import math
import os
import random
import time
import tkinter as tk


class DesktopEffects:
    def __init__(self, root):
        self.root = root
        self.window = None
        self.after_id = None
        self.started = 0
        self.particles = []

    def stop(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if self.window is not None:
            self.window.destroy()
            self.window = None
        self.particles = []

    def play(self, theme, bounds, origin):
        self.stop()
        if os.name != "nt" or theme not in ("diwali", "new_year", "holi", "birthday"):
            return
        left, top, right, bottom = bounds
        width, height = right-left, bottom-top
        self.window = tk.Toplevel(self.root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg="#010203")
        self.window.attributes("-transparentcolor", "#010203")
        self.window.geometry(f"{width}x{height}{left:+d}{top:+d}")
        self.canvas = tk.Canvas(self.window, bg="#010203", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.window.update_idletasks()
        user32 = ctypes.windll.user32
        user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        user32.GetAncestor.restype = ctypes.c_void_p
        hwnd = user32.GetAncestor(self.window.winfo_id(), 2)
        get = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
        put = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
        get.restype = put.restype = ctypes.c_ssize_t
        get.argtypes = [ctypes.c_void_p, ctypes.c_int]
        put.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t]
        put(hwnd, -20, get(hwnd, -20) | 0x20 | 0x80 | 0x08000000)
        user32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        user32.SetWindowPos(hwnd, ctypes.c_void_p(-1), left, top, width, height, 0x0010 | 0x0040)
        self.window.deiconify()
        self.started = time.monotonic()
        self.theme, self.size = theme, (width, height)
        self.origin = (origin[0]-left, origin[1]-top)
        self.next_burst = 0
        self._tick()

    def _burst(self, elapsed):
        width, height = self.size
        colours = ("#EEC968", "#F2A87E", "#C6AFF1", "#84D8CE")
        if self.theme == "holi":
            colours = ("#EF94BF", "#80CFC7", "#E6C47E", "#BB9CDD")
            x, y = self.origin
            x = max(35, min(width-35, x + random.uniform(-100, 100)))
            y = max(35, min(height-35, y + random.uniform(-60, 20)))
        else:
            x = random.uniform(width*.2, width*.8)
            y = random.uniform(height*.15, height*.45)
        for index in range(32):
            angle = math.tau*index/32
            speed = random.uniform(30, 70) if self.theme == "holi" else random.uniform(50, 105)
            self.particles.append([x, y, math.cos(angle)*speed, math.sin(angle)*speed,
                                   elapsed, random.choice(colours), random.uniform(3, 10)])
        self.particles = self.particles[-160:]

    def _tick(self):
        elapsed = time.monotonic()-self.started
        if self.window is None or elapsed >= 7:
            self.stop()
            return
        if elapsed >= self.next_burst and elapsed < 4.8:
            self._burst(elapsed)
            self.next_burst = elapsed + 1.2
        self.canvas.delete("all")
        for x, y, vx, vy, born, colour, size in self.particles:
            age = elapsed-born
            if age > 2:
                continue
            px, py = x+vx*age, y+vy*age+25*age*age
            radius = max(1, size*(1-age/2))
            if self.theme == "holi":
                self.canvas.create_oval(px-radius, py-radius, px+radius, py+radius,
                                        fill=colour, outline="")
            else:
                self.canvas.create_line(px-vx*.07, py-vy*.07, px, py, fill=colour, width=2)
        self.after_id = self.root.after(40, self._tick)
