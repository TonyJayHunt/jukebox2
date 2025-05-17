import pytest
from utils import center_window

def test_center_window(monkeypatch):
    class DummyWindow:
        def update_idletasks(self): self.updated = True
        def winfo_width(self): return 200
        def winfo_height(self): return 100
        def winfo_screenwidth(self): return 800
        def winfo_screenheight(self): return 600
        def geometry(self, val): self.geo = val
    win = DummyWindow()
    center_window(win)
    # The window should be centered (200x100 in 800x600 is at +300+250)
    assert win.geo == '200x100+300+250'
