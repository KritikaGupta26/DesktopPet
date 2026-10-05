import runpy
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch
M=runpy.run_path(str(Path(__file__).resolve().parents[1]/"Start_Water_Puppy.pyw"))
WaterPet=M["WaterPet"]
class ScreenEdgesTests(unittest.TestCase):
    def pet(self,bounds=(0,0,1920,1080)):
        p=WaterPet.__new__(WaterPet);p._screen_bounds=Mock(return_value=bounds)
        p.pet_x=500.;p.pet_y=300.;p.personality=Mock();p.personality.get.return_value="Balanced"
        p.prompt_visible=False;p.dragging=False
        return p
    def test_all_four_edge_destinations(self):
        for bounds in ((0,0,1920,1080),(-1920,-200,1920,1080)):
            left,top,right,bottom=bounds
            for side in ("left","right","top","bottom"):
                p=self.pet(bounds)
                with patch.object(WaterPet._choose_edge_destination.__globals__["random"],"choice",return_value=side):p._choose_edge_destination()
                self.assertGreaterEqual(p.target_x,left);self.assertLessEqual(p.target_x+180,right)
                self.assertGreaterEqual(p.target_y,top);self.assertLessEqual(p.target_y+184,bottom)
                if side=="left":self.assertEqual(p.target_x,left)
                if side=="right":self.assertEqual(p.target_x+180,right)
                if side=="top":self.assertEqual(p.target_y,top)
                if side=="bottom":self.assertEqual(p.target_y+184,bottom)
    def test_manual_walk_reaches_both_edges(self):
        p=self.pet();p._test_walk_across_screen();self.assertEqual(p.target_x,1740)
        p.pet_x=1800;p._test_walk_across_screen();self.assertEqual(p.target_x,0)
    def test_roaming_can_visit_an_edge(self):
        p=self.pet();p._choose_edge_destination=Mock()
        with patch.object(WaterPet._choose_destination.__globals__["random"],"random",return_value=.1):p._choose_destination()
        p._choose_edge_destination.assert_called_once()
    def follow_pet(self,point):
        p=self.pet();p.cursor_session_until=None;p.cursor_session_kind="";p.cursor_mode=Mock();p.cursor_mode.get.return_value="Follow"
        p.active_alert_kind="";p.state="normal";p.idle_mood="";p.chatter_until=None;p._studio_is_open=Mock(return_value=False)
        p.root=Mock();p.root.winfo_pointerxy.return_value=point;p.motion_mode="idle"
        p._walk_cycle_seconds=Mock(return_value=1.44);p._move_root=Mock()
        return p
    def test_follow_reaches_corners_without_clipping_canvas(self):
        for point,target in (((0,0),(0,0)),((1919,0),(1740,0)),((0,1079),(0,896)),((1919,1079),(1740,896))):
            p=self.follow_pet(point)
            for _ in range(1500):p._check_cursor_reaction(datetime.now())
            self.assertAlmostEqual(p.pet_x,target[0],delta=1)
            self.assertAlmostEqual(p.pet_y,target[1],delta=1)
            self.assertTrue(p.cursor_at_rest)
    def test_interior_follow_keeps_its_usual_standoff(self):
        p=self.follow_pet((650,392));p.pet_x=500;p.pet_y=300
        p._check_cursor_reaction(datetime.now());self.assertTrue(p.cursor_at_rest)
        p._move_root.assert_not_called()
