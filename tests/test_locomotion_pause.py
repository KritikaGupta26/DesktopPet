import runpy
import unittest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock

WaterPet = runpy.run_path(str(Path(__file__).resolve().parents[1] / "Start_Water_Puppy.pyw"))["WaterPet"]


class LocomotionPauseTests(unittest.TestCase):
    def pet(self, mode):
        p = WaterPet.__new__(WaterPet)
        p.canvas = Mock()
        p._image = Mock(side_effect=lambda key: key)
        p._draw_overlays = Mock()
        p._draw_ground_shadow = Mock()
        p._studio_is_open = Mock(return_value=False)
        p.active_alert_kind = ""
        p.prompt_visible = p.dragging = False
        p.state = "normal"
        p.idle_mood = ""
        p.motion_mode = mode
        p.pending_edge_action = None
        p.walk_direction = "left"
        p._locomotion_frame = Mock(return_value=2)
        p.gait_signature = ("walk", "left", mode)
        p.chatter_until = datetime.now() + timedelta(seconds=3)
        return p

    def test_hover_cloud_stops_walk_run_and_follow_frames(self):
        for mode in ("walking", "following", "escaping"):
            p = self.pet(mode)
            p._draw_pet_scene()
            p._image.assert_called_once_with("normal")
            p._locomotion_frame.assert_not_called()
            self.assertIsNone(p.gait_signature)

    def test_walk_resumes_after_cloud_closes(self):
        p = self.pet("walking")
        p._draw_pet_scene()
        p.chatter_until = None
        p._draw_pet_scene()
        self.assertEqual(p._image.call_args.args, ("walk_left_2",))
        p._locomotion_frame.assert_called_once_with("walk")

    def test_follow_stands_at_standoff(self):
        p = self.pet("following")
        p.chatter_until = None
        p.cursor_at_rest = True
        p._draw_pet_scene()
        p._image.assert_called_once_with("normal")
        p._locomotion_frame.assert_not_called()
