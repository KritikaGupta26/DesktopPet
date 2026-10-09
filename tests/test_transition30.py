import runpy
import unittest
from pathlib import Path
from unittest.mock import Mock
from types import SimpleNamespace

WaterPet = runpy.run_path(str(Path(__file__).resolve().parents[1]/"Start_Water_Puppy.pyw"))["WaterPet"]


class TransitionTests(unittest.TestCase):
    def test_resize_redraws_before_final_window_flush(self):
        p=WaterPet.__new__(WaterPet);p.height=184;p.width=180
        p.root=Mock();p.root.winfo_x.return_value=500;p.root.winfo_y.return_value=300
        p.canvas=Mock();p._screen_bounds=Mock(return_value=(0,0,1920,1080))
        events=[]
        p.root.geometry.side_effect=lambda *a:events.append("geometry")
        p.root.update_idletasks.side_effect=lambda:events.append("flush")
        p._draw=Mock(side_effect=lambda:events.append("draw"))
        p._resize_anchored(360,324)
        self.assertEqual(events,["flush","geometry","draw","flush"])

    def test_posted_menu_suspends_tick_before_any_behavior(self):
        p=WaterPet.__new__(WaterPet);p._context_menu_active=Mock(return_value=True)
        p._draw=Mock();p.root=Mock();p._update_roaming=Mock();p.show_prompt=Mock()
        p._tick()
        p._draw.assert_called_once();p.root.after.assert_called_once()
        p._update_roaming.assert_not_called();p.show_prompt.assert_not_called()

    def test_menu_closes_chatter_before_posting(self):
        p=WaterPet.__new__(WaterPet);p.prompt_visible=False;p.active_alert_kind=""
        events=[];p._close_chatter_card=Mock(side_effect=lambda:events.append("close"))
        p.menu=Mock();p.menu.tk_popup.side_effect=lambda *a:events.append("post")
        p._show_menu(SimpleNamespace(x_root=500,y_root=300))
        self.assertEqual(events,["close","post"])
        p.menu.grab_release.assert_called_once()

    def test_hover_cannot_open_cloud_over_posted_menu(self):
        p=WaterPet.__new__(WaterPet);p._context_menu_active=Mock(return_value=True)
        p._show_chatter=Mock();p._mouse_enter(None);p._show_chatter.assert_not_called()
