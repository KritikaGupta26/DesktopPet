import ast
import runpy
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / 'Start_Water_Puppy.pyw'
MODULE = runpy.run_path(str(SOURCE))
WaterPet = MODULE['WaterPet']

class ReminderBehaviorTests(unittest.TestCase):
    def test_no_dialogue_method_creates_a_window(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        methods = {'_show_general_alert', '_show_chatter_card', '_render_chatter_card', '_draw_prompt', '_draw_cloud_alert'}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in methods:
                self.assertNotIn('Toplevel', ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), node))

    def test_water_snooze_sets_ten_minutes_without_logging(self):
        pet = WaterPet.__new__(WaterPet)
        pet.prompt_visible = True
        pet._clear_attention = Mock()
        pet._resize_anchored = Mock()
        pet._show_chatter = Mock()
        before = datetime.now()
        pet.snooze_water()
        self.assertFalse(pet.prompt_visible)
        self.assertEqual(pet.state, 'normal')
        self.assertTrue(before + timedelta(minutes=10) <= pet.next_reminder <= datetime.now() + timedelta(minutes=10))

    def test_cloud_actions_and_offer_hold(self):
        pet = WaterPet.__new__(WaterPet)
        pet.canvas = Mock()
        pet._image = Mock(return_value='sprite')
        pet._answer_button = Mock()
        pet.active_alert_kind = 'movement'
        pet.attention_started_at = datetime.now()
        with patch.object(MODULE["tkfont"], "Font") as font:
            font.return_value.measure.side_effect = lambda text: len(text) * 8
            pet._draw_cloud_alert()
        self.assertEqual(pet.canvas.tag_bind.call_count, 2)
        pet.pet_name = Mock()
        pet.pet_name.get.return_value = 'Mochi'
        pet.water_prompt_text = 'Time for water?'
        pet.today_total_cache = 200
        pet.attention_started_at = datetime.now() - timedelta(minutes=5)
        pet._draw_prompt()
        self.assertEqual(pet._image.call_args.args, ('offer_7',))
        self.assertIn('water_snooze', [call.args[0] for call in pet.canvas.tag_bind.call_args_list])

    def test_cursor_games_respect_roaming_toggle(self):
        pet = WaterPet.__new__(WaterPet)
        pet.cursor_games = Mock(); pet.cursor_games.get.return_value = True
        pet.roam_enabled = Mock(); pet.roam_enabled.get.return_value = False
        pet.root = Mock()
        pet._check_cursor_reaction(datetime.now())
        pet.root.winfo_pointerxy.assert_not_called()

    def test_automatic_activity_waits_for_reminder(self):
        pet = WaterPet.__new__(WaterPet)
        pet.idle_mood = ""
        pet.next_idle_activity = datetime.now() - timedelta(seconds=1)
        pet.state = "normal"
        pet.prompt_visible = True
        pet._play_test_animation = Mock()
        pet._update_idle_mood(datetime.now())
        pet._play_test_animation.assert_not_called()

    def test_new_assets_are_full_resolution(self):
        from PIL import Image
        for name in ["meditate_hd"] + [f"feed_{i}" for i in range(4)]:
            with Image.open(SOURCE.parent / "assets" / f"panda_{name}.png") as im:
                self.assertEqual(im.size, (512,512))
                bbox = im.getchannel("A").getbbox()
                self.assertGreaterEqual(bbox[1],16)
                self.assertLessEqual(bbox[3],496)

if __name__ == '__main__':
    unittest.main()

class AuditRegressionTests(unittest.TestCase):
    def test_fullscreen_does_not_hide_active_reminder(self):
        pet=WaterPet.__new__(WaterPet)
        pet.hide_fullscreen=Mock();pet.hide_fullscreen.get.return_value=True
        pet.prompt_visible=False;pet.active_alert_kind='movement';pet.was_hidden_for_fullscreen=False
        pet.root=Mock();pet._foreground_is_fullscreen=Mock(return_value=True)
        pet._update_fullscreen_visibility()
        pet.root.withdraw.assert_not_called()

    def test_preview_snooze_does_not_claim_a_scheduled_reminder(self):
        pet=WaterPet.__new__(WaterPet);pet.active_alert_kind='preview_personal'
        pet._close_active_alert=Mock();pet._show_chatter=Mock();pet._refresh_reminders=Mock()
        pet._snooze_active_alert()
        pet._show_chatter.assert_called_once_with('Preview closed.',seconds=4)

    def test_movement_snooze_schedules_ten_minutes(self):
        pet=WaterPet.__new__(WaterPet);pet.active_alert_kind='movement'
        pet._close_active_alert=Mock();pet._show_chatter=Mock();pet._refresh_reminders=Mock()
        before=datetime.now();pet._snooze_active_alert()
        self.assertGreaterEqual(pet.next_movement_reminder,before+timedelta(minutes=10))
        self.assertLessEqual(pet.next_movement_reminder,datetime.now()+timedelta(minutes=10))

    def test_hunger_can_interrupt_persistent_cursor_follow(self):
        pet=WaterPet.__new__(WaterPet);pet.hunger_enabled=Mock();pet.hunger_enabled.get.return_value=True
        pet.next_hunger=datetime.now()-timedelta(seconds=1);pet.hungry=False;pet.hunger_requested=False
        pet.prompt_visible=False;pet.active_alert_kind='';pet.dragging=False;pet.idle_mood='';pet.chatter_until=None
        pet.state='normal';pet.motion_mode='following';pet._show_chatter=Mock()
        pet._update_hunger(datetime.now())
        self.assertTrue(pet.hunger_requested);pet._show_chatter.assert_called_once()

    def test_follow_pauses_while_cloud_changes_window_geometry(self):
        pet=WaterPet.__new__(WaterPet);pet.cursor_mode=Mock();pet.cursor_mode.get.return_value='Follow'
        pet.active_alert_kind='';pet.prompt_visible=False;pet.dragging=False;pet.state='normal';pet.idle_mood=''
        pet.chatter_until=datetime.now()+timedelta(seconds=5);pet.root=Mock()
        pet._check_cursor_reaction(datetime.now())
        pet.root.winfo_pointerxy.assert_not_called()
