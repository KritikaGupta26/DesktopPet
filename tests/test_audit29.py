import json
import runpy
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

M = runpy.run_path(str(Path(__file__).resolve().parents[1]/"Start_Water_Puppy.pyw"))
WaterPet = M["WaterPet"]


class Audit29Tests(unittest.TestCase):
    def geometry_pet(self, x, y):
        p = WaterPet.__new__(WaterPet)
        p.width, p.height = 180, 184
        p.root, p.canvas = Mock(), Mock()
        p._draw = Mock()
        p.root.winfo_x.return_value = x
        p.root.winfo_y.return_value = y
        p._screen_bounds = Mock(return_value=(0, 0, 1920, 1080))
        return p

    def test_cloud_expand_close_preserves_each_corner(self):
        for x, y in ((0,0),(1740,0),(0,896),(1740,896),(500,300)):
            p = self.geometry_pet(x,y)
            p._resize_anchored(360,324)
            self.assertEqual((p.pet_x,p.pet_y),(x,y))
            self.assertEqual(p.cloud_left, x==1740)
            self.assertEqual(p.cloud_below, y==0)
            ox,oy=p.pet_canvas_offset
            p.root.winfo_x.return_value=x-ox
            p.root.winfo_y.return_value=y-oy
            p._resize_anchored(180,184)
            self.assertEqual((p.pet_x,p.pet_y),(x,y))
            self.assertEqual(p.pet_canvas_offset,(0,0))

    def test_hover_does_not_stop_walk_follow_or_escape(self):
        for mode in ("walking","following","escaping"):
            p=WaterPet.__new__(WaterPet);p.motion_mode=mode;p._show_chatter=Mock()
            p._mouse_enter(None)
            p._show_chatter.assert_not_called()

    def test_hover_still_shows_total_when_idle(self):
        p=WaterPet.__new__(WaterPet);p.motion_mode="idle";p.state="normal"
        p.prompt_visible=p.dragging=False;p.active_alert_kind=p.idle_mood="";p.chatter_until=None
        p.pet_name=Mock();p.pet_name.get.return_value="Mochi";p.today_total_cache=200;p._show_chatter=Mock()
        p._mouse_enter(None);p._show_chatter.assert_called_once()

    def test_drag_can_reach_edges_with_expanded_cloud(self):
        p=self.geometry_pet(500,300);p.width,p.height=360,324
        p.canvas.gettags.return_value=();p.drag_start_pet=(500,300);p.drag_start_root=(600,400)
        p.drag_samples=[];p.drag_moved=False
        for px,py,expected in ((0,0,(0,0)),(3000,2000,(1740,896))):
            p._drag(SimpleNamespace(x_root=px,y_root=py))
            self.assertEqual((p.pet_x,p.pet_y),expected)

    def test_explicit_walk_clears_previous_edge_action(self):
        p=self.geometry_pet(500,300);p.pet_x,p.pet_y=500,300;p.prompt_visible=p.dragging=False
        p.pending_edge_action="bored_edge";p.current_action="bored_edge"
        p._test_walk_across_screen();self.assertIsNone(p.pending_edge_action);self.assertIsNone(p.current_action)

    def test_fetch_waits_for_general_reminder(self):
        p=WaterPet.__new__(WaterPet);p.prompt_visible=False;p.active_alert_kind="personal";p._show_chatter=Mock();p.root=Mock()
        p.start_fetch();p.root.winfo_pointerxy.assert_not_called()

    def test_roaming_does_not_walk_vertically_to_ledge(self):
        p=self.geometry_pet(500,300);p.pet_x,p.pet_y=500,300
        p._visible_window_ledges=Mock(return_value=[(0,50,1000)])
        p.personality=Mock();p.personality.get.return_value="Balanced"
        with patch.object(WaterPet._choose_destination.__globals__["random"],"random",side_effect=[.5,.1]):
            p._choose_destination()
        self.assertEqual(p.target_y,300)

    def test_invalid_activity_settings_are_normalized(self):
        with tempfile.TemporaryDirectory() as d:
            p=WaterPet.__new__(WaterPet);p.settings_path=Path(d)/"settings.json";p.pack_manifest={}
            p.settings_path.write_text(json.dumps({"routine_activities":[{},[],"groom",None],"auto_activity":[]}))
            settings=p._load_settings()
            self.assertEqual(settings["routine_activities"],["groom"])
            self.assertEqual(settings["auto_activity"],"Manual only")

    def test_throw_upward_stays_inside_screen(self):
        p=self.geometry_pet(500,0);p.pet_x,p.pet_y=500,0;p.velocity_x=0;p.velocity_y=-16
        p._visible_window_ledges=Mock(return_value=[]);p._move_root=Mock()
        p._update_falling(datetime.now())
        self.assertEqual(p.pet_y,0);self.assertGreater(p.velocity_y,0)
