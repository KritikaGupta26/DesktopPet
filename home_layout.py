"""One scrollable, responsive viewport for every Panda Home page."""
import tkinter as tk
from tkinter import ttk


class HomePage(ttk.Frame):
    def __init__(self, parent, background, style="Glass.TFrame", padding=(4, 4, 12, 20)):
        super().__init__(parent, style=style)
        self.canvas = tk.Canvas(self, bg=background, highlightthickness=0,
                                borderwidth=0, width=1, height=1, yscrollincrement=24)
        self.vertical = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vertical.set, xscrollcommand=self.horizontal.set)
        self.vertical.grid(row=0, column=1, sticky="ns")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.body = ttk.Frame(self.canvas, style=style, padding=padding)
        self.item = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.body.bind("<Configure>", self._layout)
        self.canvas.bind("<Configure>", self._layout)

    def _layout(self, event=None):
        width = max(1, self.canvas.winfo_width())
        def wrap(widget):
            for child in widget.winfo_children():
                if isinstance(child, (ttk.Label, tk.Label)) and not child.cget("width"):
                    child.configure(wraplength=max(100, width - 32))
                wrap(child)
        if width > 80:
            wrap(self.body)
        needed = self.body.winfo_reqwidth()
        self.canvas.itemconfigure(self.item, width=max(width, needed))
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        if needed > width + 2:
            self.horizontal.grid(row=1, column=0, sticky="ew")
        else:
            self.horizontal.grid_remove()
            self.canvas.xview_moveto(0)

    def wheel(self, event):
        if event.delta:
            units = -max(1, round(abs(event.delta) / 120)) * (1 if event.delta > 0 else -1)
        else:
            units = -1 if event.num == 4 else 1
        self.canvas.yview_scroll(units, "units")
        return "break"


def bind_page_wheel(window, pages):
    """Window-level routing also works over newly added controls and empty space."""
    def wheel(event):
        widget = event.widget
        while widget is not None:
            for page in pages:
                if widget is page or widget is page.body or widget is page.canvas:
                    return page.wheel(event)
            widget = getattr(widget, "master", None)
    tag = "PandaHomeWheel" + str(window.winfo_id())
    for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        window.bind_class(tag, sequence, wheel)
    def install(widget):
        tags = widget.bindtags()
        if tag not in tags:
            widget.bindtags((tags[0], tag, *tags[1:]))
        for child in widget.winfo_children():
            install(child)
    install(window)
    window.bind("<Map>", lambda event: install(event.widget), add="+")
