# Author: Paul: https://github.com/PaulleDemon
# Made using PyUibuilder: https://pyuibuilder.com
# MIT License - keep the copy of this license

import tkinter as tk

class ScrollableFrameProxy:
    def __init__(self, scrollable, inner):
        self._scrollable = scrollable
        self._inner = inner

    def __getattr__(self, name):
        # Layout methods like pack(), grid(), place() go to outer scrollable frame
        if name in ("pack", "grid", "place", "update_scroll"):
            return getattr(self._scrollable, name)
        return getattr(self._inner, name)

    def __repr__(self):
        return f"<ScrollableFrameProxy wrapping {self._inner}>"

class ScrollableWidget(tk.Frame):

    def __new__(cls, parent, scrollWidth=16, **kwargs):
        instance = super().__new__(cls)
        instance.__init__(parent, scrollWidth, **kwargs)
        return ScrollableFrameProxy(instance, instance.inner)


    def __init__(self, parent, scrollWidth=16, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # Scrollbars
        self.v_scroll = tk.Scrollbar(self, orient="vertical", width=scrollWidth)
        self.h_scroll = tk.Scrollbar(self, orient="horizontal", width=scrollWidth)

        # Canvas for scrolling
        self.canvas = tk.Canvas(self, yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        # Layout (just internal)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Inner frame for user widgets
        self.inner = tk.Frame(self.canvas)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        # Bind size changes
        self.inner.bind("<Configure>", self._on_inner_config)
        self.canvas.bind("<Configure>", self._on_canvas_config)

        # Mouse scroll
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _on_inner_config(self, event):
        self.canvas.config(scrollregion=self.canvas.bbox(self._window))

    def _on_canvas_config(self, event):
        # Only stretch width if needed
        self.canvas.itemconfig(self._window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def update_scroll(self):
        self.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox(self._window))
