import runpy
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1]/"Start_Water_Puppy.pyw"))
WaterPet = MODULE["WaterPet"]

class WaterHoursTests(unittest.TestCase):
    def test_daytime_boundaries(self):
        f=MODULE["water_window_contains"]
        for hour,minute,expected in ((8,59,False),(9,0,True),(20,59,True),(21,0,False)):
            self.assertEqual(f(datetime(2026,10,5,hour,minute),"09:00","21:00"),expected)

    def test_overnight_and_equal_hours(self):
        f=MODULE["water_window_contains"]
        for hour,expected in ((21,False),(22,True),(0,True),(5,True),(6,False)):
            self.assertEqual(f(datetime(2026,10,5,hour),"22:00","06:00"),expected)
        self.assertTrue(f(datetime(2026,10,5,15),"09:00","09:00"))

    def test_next_opening(self):
        f=MODULE["next_water_window_time"]
        self.assertEqual(f(datetime(2026,10,5,22),"09:00","21:00"),datetime(2026,10,6,9))
        self.assertEqual(f(datetime(2026,10,5,7),"09:00","21:00"),datetime(2026,10,5,9))
        self.assertEqual(f(datetime(2026,10,5,7),"22:00","06:00"),datetime(2026,10,5,22))

    def test_clock_input(self):
        f=MODULE["parse_water_clock"]
        self.assertEqual(f("9 AM"),"09:00")
        self.assertEqual(f("9:30 PM"),"21:30")
        with self.assertRaises(ValueError):f("25:10")

    def make_pet(self):
        p=WaterPet.__new__(WaterPet)
        p.water_window_enabled=Mock();p.water_window_enabled.get.return_value=True
        p.water_start=Mock();p.water_start.get.return_value="09:00"
        p.water_end=Mock();p.water_end.get.return_value="21:00"
        p.prompt_visible=True;p.state="asking";p.water_prompt_manual=False
        p.next_reminder=datetime(2026,10,5,22)
        p._clear_attention=Mock();p._resize_anchored=Mock()
        return p

    def test_end_closes_automatic_offer_without_logging(self):
        p=self.make_pet();p._enforce_water_window(datetime(2026,10,5,22))
        self.assertFalse(p.prompt_visible);self.assertEqual(p.state,"normal")
        self.assertEqual(p.next_reminder,datetime(2026,10,6,9))
        self.assertFalse(hasattr(p,"database_path"))

    def test_manual_offer_remains_available_outside_hours(self):
        p=self.make_pet();p.water_prompt_manual=True
        p._enforce_water_window(datetime(2026,10,5,22))
        self.assertTrue(p.prompt_visible)

    def test_log_play_skips_bored_approach(self):
        p=WaterPet.__new__(WaterPet);p.prompt_visible=False;p.active_alert_kind="";p.dragging=False;p.state="normal"
        p._play_test_animation=Mock();p._test_bored_at_edge=Mock()
        p.scene_manifest={"log":{"timeline":[[0,16]]}}
        p._play_activity("log")
        p._play_test_animation.assert_called_once_with("log_play",16)
        p._test_bored_at_edge.assert_not_called()
