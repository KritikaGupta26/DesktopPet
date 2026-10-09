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

class FinalReleaseRegressionTests(unittest.TestCase):
    def test_not_yet_recovers_without_pause_and_without_logging(self):
        pet=WaterPet.__new__(WaterPet);pet.prompt_visible=True
        pet._clear_attention=Mock();pet._resize_anchored=Mock();pet._show_chatter=Mock()
        pet.roam_rest_seconds=Mock();pet.roam_rest_seconds.get.return_value=30
        before=datetime.now();pet.answer_not_yet();due=pet.next_reminder
        self.assertEqual(pet.state,'sad');self.assertFalse(pet.prompt_visible)
        self.assertGreaterEqual(due,before+timedelta(minutes=30))
        self.assertLessEqual(due,datetime.now()+timedelta(minutes=30))
        pet._update_water_response(before+timedelta(seconds=7))
        self.assertEqual(pet.state,'sad')
        pet._update_water_response(datetime.now()+timedelta(seconds=9))
        self.assertEqual(pet.state,'normal');self.assertIsNone(pet.sad_until)
        self.assertEqual(pet.next_reminder,due)
        self.assertFalse(hasattr(pet,'reminders_paused_until'))
        self.assertFalse(hasattr(pet,'database_path'))

    def test_idle_detection_does_not_interrupt_a_user_sequence(self):
        pet=WaterPet.__new__(WaterPet);pet.last_system_idle_check=datetime.now()
        pet.system_idle_seconds_cache=1000;pet.idle_mood='wind_down'
        pet.motion_mode='idle';pet._update_inactivity_behavior(datetime.now())
        self.assertEqual(pet.idle_mood,'wind_down')

    def test_stationary_follow_does_not_starve_selected_routines(self):
        pet=WaterPet.__new__(WaterPet);pet.idle_mood='';pet.next_idle_activity=datetime.now()-timedelta(seconds=1)
        pet.state='normal';pet.prompt_visible=False;pet.active_alert_kind='';pet.dragging=False
        pet.motion_mode='following';pet.cursor_at_rest=True;pet.chatter_until=None
        pet.activity_minutes=Mock();pet.activity_minutes.get.return_value=5
        pet.auto_activity=Mock();pet.auto_activity.get.return_value='Selected routine'
        enabled=Mock();enabled.get.return_value=True;pet.routine_enabled={'groom':enabled}
        pet._play_activity=Mock();pet._update_idle_mood(datetime.now())
        pet._play_activity.assert_called_once_with('groom', automatic=True)

    def test_all_reminder_clouds_are_smaller_than_pet_canvas(self):
        pet=WaterPet.__new__(WaterPet);pet.canvas=Mock();pet._cloud_shape=Mock()
        pet._image=Mock();pet._pack_image=Mock();pet._answer_button=Mock();pet.active_alert_kind='movement'
        pet.alert_title='Move';pet.alert_subtitle='Stretch';pet.attention_started_at=datetime.now()
        pet._draw_cloud_alert()
        _,x1,y1,x2,y2,*_=pet._cloud_shape.call_args.args
        self.assertLess(x2-x1,180);self.assertLess(y2-y1,180)
        pet.pet_name=Mock();pet.pet_name.get.return_value='Mochi';pet.water_prompt_text='Water?';pet.today_total_cache=200
        pet.pet_y=300;pet._screen_bounds=Mock(return_value=(0,0,1920,1080))
        pet._draw_prompt()
        _,x1,y1,x2,y2,*_=pet._cloud_shape.call_args.args
        self.assertLess(x2-x1,180);self.assertLess(y2-y1,180)

    def test_dragging_a_cloud_dialog_preserves_panda_screen_anchor(self):
        pet=WaterPet.__new__(WaterPet);pet.root=Mock();pet.root.winfo_x.return_value=100;pet.root.winfo_y.return_value=60
        pet.width=360;pet.height=324;pet.canvas=Mock();pet._screen_bounds=Mock(return_value=(0,0,1920,1080))
        pet._draw=Mock()
        pet._resize_anchored(180,184)
        self.assertEqual((pet.pet_x,pet.pet_y),(100.,200.))

    def test_reminder_validation_does_not_open_an_error_popup(self):
        pet=WaterPet.__new__(WaterPet);pet.reminder_title_var=Mock();pet.reminder_title_var.get.return_value=''
        pet.reminder_feedback_var=Mock();pet.add_personal_reminder()
        pet.reminder_feedback_var.set.assert_called_once_with('Enter what the panda should remind you about.')

class TimeAndPaceRegressionTests(unittest.TestCase):
    def test_offset_reminders_migrate_to_utc_and_fire_by_instant(self):
        import tempfile
        import sqlite3
        from contextlib import closing
        from datetime import timezone
        with tempfile.TemporaryDirectory() as directory:
            pet=WaterPet.__new__(WaterPet);pet.database_path=Path(directory)/'history.db';pet._initialize_database()
            with closing(sqlite3.connect(pet.database_path)) as db,db:
                db.execute("INSERT INTO personal_reminders(title,due_at,status,created_at) VALUES (?,?,?,?)",('Offset test','2026-10-02T15:30:00+04:00','scheduled','2026-10-02T10:00:00+04:00'))
            pet._initialize_database();pet._initialize_database()
            with closing(sqlite3.connect(pet.database_path)) as db:
                due=db.execute('SELECT due_at FROM personal_reminders').fetchone()[0]
            self.assertEqual(due,'2026-10-02T11:30:00+00:00')
            pet.active_alert_kind='';pet.prompt_visible=False;pet.alert_window=None
            pet.movement_enabled=Mock();pet.movement_enabled.get.return_value=False;pet._show_general_alert=Mock()
            pet._check_scheduled_reminders(datetime(2026,10,2,11,0,tzinfo=timezone.utc))
            pet._show_general_alert.assert_not_called()
            pet._check_scheduled_reminders(datetime(2026,10,2,12,0,tzinfo=timezone.utc))
            self.assertEqual(pet._show_general_alert.call_args.kwargs['title'],'Offset test')

    def test_personality_changes_gait_and_travel_at_one_pace(self):
        pet=WaterPet.__new__(WaterPet);pet.personality=Mock();pet.walk_frame_ms=Mock();pet.walk_frame_ms.get.return_value=180
        values=[]
        for personality in ('Calm','Balanced','Playful'):
            pet.personality.get.return_value=personality;values.append(pet._walk_cycle_seconds())
        self.assertGreater(values[0],values[1]);self.assertGreater(values[1],values[2])
        self.assertAlmostEqual(values[1],1.44)

class ReminderPriorityRegressionTests(unittest.TestCase):
    def test_due_personal_reminder_defers_an_open_water_offer(self):
        import tempfile
        import sqlite3
        from contextlib import closing
        from datetime import timezone
        with tempfile.TemporaryDirectory() as directory:
            pet=WaterPet.__new__(WaterPet);pet.database_path=Path(directory)/'history.db';pet._initialize_database()
            now=datetime.now(timezone.utc)
            with closing(sqlite3.connect(pet.database_path)) as db,db:
                db.execute("INSERT INTO personal_reminders(title,due_at,status,created_at) VALUES (?,?,?,?)",('Meeting', (now-timedelta(minutes=1)).isoformat(timespec='seconds'),'scheduled',now.isoformat(timespec='seconds')))
            pet.active_alert_kind='';pet.prompt_visible=True;pet.alert_window=None;pet._show_general_alert=Mock()
            pet._check_scheduled_reminders(now)
            self.assertFalse(pet.prompt_visible);self.assertTrue(pet.water_prompt_deferred)
            self.assertEqual(pet._show_general_alert.call_args.kwargs['kind'],'personal')

    def test_closing_personal_alert_resumes_deferred_water(self):
        pet=WaterPet.__new__(WaterPet);pet.water_prompt_deferred=True;pet.alert_previous_state='normal'
        pet._clear_attention=Mock();pet._resize_anchored=Mock();pet.show_prompt=Mock()
        pet._close_active_alert()
        self.assertFalse(pet.water_prompt_deferred);pet.show_prompt.assert_called_once()

    def test_pausing_water_does_not_shrink_a_personal_alert(self):
        pet=WaterPet.__new__(WaterPet);pet.active_alert_kind='personal';pet.water_prompt_deferred=True
        pet._clear_attention=Mock();pet._resize_anchored=Mock();pet._show_chatter=Mock()
        pet.pause_reminders()
        pet._resize_anchored.assert_not_called();self.assertFalse(pet.water_prompt_deferred)

class CloudTextRegressionTests(unittest.TestCase):
    def test_long_titles_fit_three_lines_and_retain_full_source(self):
        source='W'*120
        fitted=MODULE['fit_cloud_text'](source,lambda value:len(value)*12,126,3)
        self.assertEqual(len(fitted.splitlines()),3)
        self.assertTrue(fitted.endswith('…'))
        self.assertTrue(all(len(line)*12<=126 for line in fitted.splitlines()))
        self.assertEqual(len(source),120)
