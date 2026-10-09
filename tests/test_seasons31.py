import json
import runpy
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock
from seasonal_themes import resolve_theme, valid_birthday, normalize_custom_dates, THEMES, PROP_KEYS

ROOT=Path(__file__).resolve().parents[1]
WaterPet=runpy.run_path(str(ROOT/'Start_Water_Puppy.pyw'))['WaterPet']

class SeasonalTests(unittest.TestCase):
    def test_every_manual_theme_can_override_calendar_and_disabled_list(self):
        for key in THEMES:
            self.assertEqual(resolve_theme(date(2026,11,8),key,enabled=[]),key)
    def test_all_requested_festivals_have_automatic_dates(self):
        cases=[('2026-11-08','diwali'),('2026-03-04','holi'),('2026-10-11','navratri'),
               ('2026-09-14','ganesh'),('2026-09-04','krishna'),('2026-02-15','shiva'),
               ('2026-11-26','thanksgiving'),('2026-12-25','christmas'),('2026-12-31','new_year'),
               ('2027-01-01','new_year'),('2027-02-14','valentine'),('2026-10-09','autumn'),('2026-10-31','spooky')]
        for day,key in cases:
            self.assertEqual(resolve_theme(date.fromisoformat(day)),key)
    def test_lunar_dates_change_between_years(self):
        for day,key in [('2027-10-29','diwali'),('2027-03-22','holi'),('2027-08-25','krishna'),
                        ('2027-09-04','ganesh'),('2027-03-06','shiva'),('2027-09-30','navratri')]:
            self.assertEqual(resolve_theme(date.fromisoformat(day)),key)
        self.assertNotEqual(resolve_theme(date(2027,11,8)),'diwali')
    def test_unknown_lunar_year_never_reuses_old_dates(self):
        self.assertEqual(resolve_theme(date(2028,11,8)),'autumn')
    def test_birthday_priority_and_leap_day(self):
        self.assertEqual(resolve_theme(date(2026,11,8),birthday='11-08'),'birthday')
        for year in (2026,2100):
            self.assertEqual(resolve_theme(date(year,2,28),birthday='02-29'),'birthday')
        self.assertEqual(resolve_theme(date(2028,2,29),birthday='02-29'),'birthday')
        self.assertNotEqual(resolve_theme(date(2028,2,28),birthday='02-29'),'birthday')
    def test_custom_local_dates_override_builtin_for_year_only(self):
        custom={'diwali':[['2026-11-07','2026-11-07']]}
        self.assertEqual(resolve_theme(date(2026,11,7),custom=custom),'diwali')
        self.assertEqual(resolve_theme(date(2026,11,8),custom=custom),'autumn')
        self.assertEqual(resolve_theme(date(2027,10,29),custom=custom),'diwali')
    def test_invalid_calendar_input_is_discarded(self):
        self.assertEqual(normalize_custom_dates({'diwali':[{},['bad','dates'],['2026-11-08','2026-11-07']], 'bogus':[]} ),{})
        for birthday in ('13-01','02-30','2-1',[],{}):
            with self.assertRaises(ValueError): valid_birthday(birthday or 'bad')
    def test_can_disable_events_or_seasons(self):
        self.assertEqual(resolve_theme(date(2026,11,8),enabled=['autumn']),'autumn')
        self.assertEqual(resolve_theme(date(2026,10,9),enabled=[]),'classic')
    def test_southern_seasons_and_canadian_thanksgiving(self):
        self.assertEqual(resolve_theme(date(2026,10,9),hemisphere='Southern'),'spring')
        self.assertEqual(resolve_theme(date(2026,10,12),thanksgiving='Canada'),'navratri')
        self.assertEqual(resolve_theme(date(2026,10,12),thanksgiving='Canada',enabled=['thanksgiving']),'thanksgiving')
    def test_settings_migration_preserves_existing_choices(self):
        with tempfile.TemporaryDirectory() as d:
            p=WaterPet.__new__(WaterPet);p.settings_path=Path(d)/'settings.json';p.pack_manifest={}
            p.settings_path.write_text(json.dumps({'wander':False,'auto_activity':'Manual only','theme_mode':[],'birthday':'bad'}))
            settings=p._load_settings()
            self.assertEqual(settings['theme_mode'],'Auto');self.assertEqual(settings['birthday'],'')
            self.assertFalse(settings['wander']);self.assertEqual(settings['auto_activity'],'Manual only')
    def test_themed_activity_waits_for_reminders_then_runs(self):
        p=WaterPet.__new__(WaterPet);p.theme_activity_enabled=Mock();p.theme_activity_enabled.get.return_value=True
        p.next_theme_activity=datetime.now()-timedelta(seconds=1);p.prompt_visible=True
        p._play_theme_scene=Mock();p._play_activity=Mock();p._show_chatter=Mock();p._current_theme=Mock(return_value='shiva')
        p._check_theme_activity(datetime.now());p._play_activity.assert_not_called()
        p.prompt_visible=False;p.active_alert_kind='';p.dragging=False;p.state='normal';p.motion_mode='idle'
        p.idle_mood='';p.chatter_until=None;p._studio_is_open=Mock(return_value=False);p.hungry=False
        p._check_theme_activity(datetime.now());p._play_theme_scene.assert_called_once_with('shiva')
        self.assertGreater(p.next_theme_activity,datetime.now()+timedelta(minutes=19))
    def test_props_have_actual_transparent_padding(self):
        from PIL import Image
        for key in PROP_KEYS:
            with Image.open(ROOT/f'assets/theme_{key}.png') as im:
                self.assertEqual(im.mode,'RGBA');alpha=im.getchannel('A')
                self.assertEqual(alpha.getpixel((0,0)),0);self.assertIsNotNone(alpha.getbbox())
                self.assertGreater(alpha.getextrema()[1],200)
    def test_horizontal_roaming_corrects_obsolete_vertical_target(self):
        p=WaterPet.__new__(WaterPet);p.dragging=False;p.motion_mode='walking';p.pet_x=500.;p.pet_y=300.
        p.target_x=1000.;p.target_y=50.;p.walk_speed=3.;p._walk_cycle_seconds=Mock(return_value=1.44)
        p.pending_edge_action=None;p._move_root=Mock()
        p._update_roaming(datetime.now())
        self.assertEqual(p.pet_y,300.);self.assertEqual(p.target_y,300.);self.assertGreater(p.pet_x,500.)
