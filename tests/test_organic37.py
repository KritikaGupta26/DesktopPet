import json
import random
import runpy
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
from contextlib import ExitStack

from organic_behavior import OrganicQueue, activity_delay, clock_in_window
from wardrobe import front_surface, headgear_geometry
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
M = runpy.run_path(str(ROOT / "Start_Water_Puppy.pyw"))
WaterPet = M["WaterPet"]


def variable(value):
    v = Mock()
    v.get.return_value = value
    return v


class Organic37Tests(unittest.TestCase):
    def test_themes_page_constructs_without_behaviour_page_locals(self):
        pet=WaterPet.__new__(WaterPet)
        pet.home_pages=[Mock() for _ in range(7)]
        pet.theme_mode=variable("classic")
        pet.theme_effects_enabled=variable(True)
        pet.theme_hemisphere=variable("Northern")
        pet.thanksgiving_region=variable("US")
        pet.birthday=variable("")
        pet.theme_activity_enabled=variable(True)
        pet.theme_activity_minutes=variable(20)
        pet.theme_enabled={key:variable(True) for key in M["PROP_KEYS"]}
        pet.theme_feedback=Mock()
        pet.settings={}
        with ExitStack() as stack:
            for name in ("Label", "Checkbutton", "Combobox", "Button", "Frame", "Entry", "Spinbox"):
                stack.enter_context(patch.object(M["ttk"],name,Mock()))
            stack.enter_context(patch.object(M["tk"],"Text",Mock()))
            stack.enter_context(patch.object(M["tk"],"StringVar",side_effect=lambda **kwargs:variable(kwargs.get("value",""))))
            pet._build_themes_page(Mock())

    def test_queue_visits_every_action_before_repeating_and_avoids_boundary_repeat(self):
        pool = M["ROUTINE_ACTIVITIES"]
        queue = OrganicQueue(random.Random(7))
        chosen = [queue.choose(pool) for _ in range(len(pool)*4)]
        for offset in range(0, len(chosen), len(pool)):
            self.assertEqual(set(chosen[offset:offset+len(pool)]), set(pool))
        self.assertTrue(all(a != b for a,b in zip(chosen, chosen[1:])))

    def test_prank_is_deferred_without_being_dropped_from_cycle(self):
        queue = OrganicQueue(random.Random(3))
        self.assertEqual(queue.choose(["boo", "groom"], ["boo"]), "groom")
        self.assertIsNone(queue.choose(["boo", "groom"], ["boo"]))
        self.assertEqual(queue.choose(["boo", "groom"]), "boo")

    def test_pool_changes_remove_disabled_actions(self):
        queue = OrganicQueue(random.Random(3))
        queue.choose(["groom", "boo", "dance"])
        for _ in range(10):
            self.assertEqual(queue.choose(["groom"]), "groom")

    def test_night_window_crosses_midnight_and_has_exact_boundaries(self):
        for hour, minute, expected in ((21,59,False),(22,0,True),(0,0,True),(6,59,True),(7,0,False)):
            self.assertEqual(clock_in_window(datetime(2026,10,14,hour,minute), "22:00", "07:00"), expected)
        self.assertTrue(clock_in_window(datetime(2026,10,14,14), "13:00", "17:00"))
        self.assertFalse(clock_in_window(datetime(2026,10,14,14), "13:00", "13:00"))

    def test_personality_varies_interval_with_bounded_jitter(self):
        calm = activity_delay(5,"Calm",random.Random(2))
        playful = activity_delay(5,"Playful",random.Random(2))
        self.assertGreater(calm, playful)
        values = [activity_delay(5,"Balanced",random.Random(seed)) for seed in range(10)]
        self.assertGreater(len(set(values)), 5)
        self.assertTrue(all(216 <= delay <= 384 for delay in values))

    def pet(self):
        p = WaterPet.__new__(WaterPet)
        p.night_enabled=variable(True);p.night_start=variable("22:00");p.night_end=variable("07:00")
        p.night_corner=variable("Bottom right");p.night_check_minutes=variable(20)
        p.night_manual_until=None;p.night_active=False;p.night_phase=""
        p.idle_mood="";p.idle_mood_until=None;p.motion_mode="walking";p.state="normal"
        p.prompt_visible=p.dragging=False;p.active_alert_kind="";p.chatter_until=None
        p._studio_is_open=Mock(return_value=False);p._screen_bounds=Mock(return_value=(0,0,1920,1080))
        p._move_root=Mock();p._resize_anchored=Mock();p._walk_cycle_seconds=Mock(return_value=1.44)
        p.pet_x=1732.;p.pet_y=400.;p.activity_minutes=variable(5);p.personality=variable("Balanced")
        p.roam_rest_seconds=variable(30);p._play_activity=Mock();p.next_idle_activity=datetime(2026,10,14,0)
        return p

    def test_night_rests_despite_active_computer_and_resleeps_after_check(self):
        p=self.pet();now=datetime(2026,10,14,1)
        p._update_night_behavior(now)
        self.assertEqual(p.idle_mood,"night_settle")
        self.assertEqual((p.pet_x,p.pet_y),(1732.,888))
        p._update_night_behavior(now+timedelta(seconds=4))
        self.assertEqual(p.idle_mood,"night_sleep")
        p.last_system_idle_check=now;p.system_idle_seconds_cache=0;p._system_idle_seconds=Mock(return_value=0)
        p._update_inactivity_behavior(now+timedelta(seconds=5))
        self.assertEqual(p.idle_mood,"night_sleep")
        check_at=p.night_next_check
        p._update_night_behavior(check_at)
        self.assertEqual(p.idle_mood,"night_check")
        p._update_night_behavior(check_at+timedelta(seconds=5))
        self.assertEqual(p.idle_mood,"night_sleep")

    def test_night_does_not_suppress_or_replace_reminder(self):
        p=self.pet();p.prompt_visible=True;p.idle_mood="water_offer"
        p._update_night_behavior(datetime(2026,10,14,1))
        self.assertTrue(p.prompt_visible)
        self.assertEqual(p.idle_mood,"water_offer")
        p._move_root.assert_not_called()

    def test_night_waits_for_manual_action_then_resumes(self):
        p=self.pet();p.idle_mood="pack:kung_fu"
        p._update_night_behavior(datetime(2026,10,14,1))
        self.assertEqual(p.idle_mood,"pack:kung_fu")
        p._move_root.assert_not_called()
        p.idle_mood="";p._update_night_behavior(datetime(2026,10,14,1,1))
        self.assertEqual(p.idle_mood,"night_settle")

    def test_night_exits_at_wake_time_and_resumes_day_schedule(self):
        p=self.pet();p.idle_mood="night_sleep";p.night_active=True;p.night_phase="sleep"
        now=datetime(2026,10,14,7)
        p._update_night_behavior(now)
        self.assertFalse(p.night_active)
        self.assertEqual(p.idle_mood,"")
        self.assertGreater(p.next_idle_activity,now)

    def test_feeding_or_petting_does_not_leave_night_standing_after_action(self):
        p=self.pet();p.night_active=True;p.night_phase="sleep";p.idle_mood="feed"
        p._update_night_behavior(datetime(2026,10,14,1))
        self.assertFalse(p.night_active)
        self.assertEqual(p.idle_mood,"feed")
        p.idle_mood="";p._update_night_behavior(datetime(2026,10,14,1,1))
        self.assertTrue(p.night_active)
        self.assertEqual(p.idle_mood,"night_settle")

    def test_night_does_not_deadlock_an_edge_approach_or_manual_walk(self):
        p=self.pet();p.pending_edge_action="pack:bamboo_hang"
        p._update_night_behavior(datetime(2026,10,14,1))
        self.assertFalse(p.night_active)
        self.assertEqual(p.pending_edge_action,"pack:bamboo_hang")
        p._move_root.assert_not_called()
        p.pending_edge_action=None;p.manual_motion_until=datetime(2026,10,14,1,5)
        p._update_night_behavior(datetime(2026,10,14,1,1))
        self.assertFalse(p.night_active)
        p._move_root.assert_not_called()

    def test_due_organic_action_gets_turn_during_roaming_without_interrupting_manual_walk(self):
        p=self.pet();p.night_active=False;p.auto_activity=variable("Organic routine")
        p.pranks_enabled=variable(True);p.next_prank=datetime(2026,10,13);p.pending_edge_action=None
        p.next_idle_activity=datetime(2026,10,13)
        p._update_idle_mood(datetime(2026,10,14,12))
        p._play_activity.assert_called_once()
        p._play_activity.reset_mock();p.next_idle_activity=datetime(2026,10,13)
        p.manual_motion_until=datetime(2026,10,14,12,5)
        p._update_idle_mood(datetime(2026,10,14,12))
        p._play_activity.assert_not_called()

    def test_old_gentle_default_upgrades_to_complete_organic_pool(self):
        p=WaterPet.__new__(WaterPet);p.pack_manifest={}
        with tempfile.TemporaryDirectory() as td:
            p.settings_path=Path(td)/"settings.json"
            p.settings_path.write_text(json.dumps({"auto_activity":"Gentle routine","routine_activities":["groom","wind_down"],"pranks_enabled":False}))
            settings=p._load_settings()
            self.assertEqual(settings["auto_activity"],"Organic routine")
            self.assertEqual(set(settings["routine_activities"]),set(M["ROUTINE_ACTIVITIES"]))
            self.assertTrue(settings["pranks_enabled"])

    def test_new_manual_choice_is_preserved_after_migration(self):
        p=WaterPet.__new__(WaterPet);p.pack_manifest={}
        with tempfile.TemporaryDirectory() as td:
            p.settings_path=Path(td)/"settings.json"
            p.settings_path.write_text(json.dumps({"organic_schema":1,"auto_activity":"Manual only"}))
            self.assertEqual(p._load_settings()["auto_activity"],"Manual only")

    def test_caps_rotate_with_sideways_and_inverted_head(self):
        size=(300,250)
        upright=headgear_geometry((51,50,139,123),(74,127,121,160),size,"navratri","pack_happy_idle_0")
        lying=headgear_geometry((44,107,135,162),(121,120,158,153),size,"navratri","pack_sleep_0")
        inverted=headgear_geometry((44,83,138,156),(61,58,120,87),size,"navratri","pack_forward_roll_2")
        self.assertLess(abs(upright[2]),20)
        self.assertLess(abs(lying[2]),20)
        self.assertGreater(abs(inverted[2]),150)

    def test_rear_vest_lining_is_removed_but_front_panels_remain(self):
        part=Image.open(ROOT/"assets/wardrobe_navratri_front.png").convert("RGBA")
        front=front_surface(part,"navratri","front")
        self.assertEqual(front.getpixel((part.width//2,part.height//2))[3],0)
        self.assertGreater(front.getpixel((part.width//5,part.height//2))[3],0)


if __name__ == "__main__":
    unittest.main()
