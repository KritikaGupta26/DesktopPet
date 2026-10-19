import json
from pathlib import Path
import random
import runpy
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from character_routines import STORIES, story_duration, story_pose, routine_pool
from organic_behavior import OrganicQueue

ROOT = Path(__file__).resolve().parents[1]
M = runpy.run_path(str(ROOT/'Start_Water_Puppy.pyw'))
WaterPet = M['WaterPet']


def var(value):
    result = Mock()
    result.get.return_value = value
    return result


class Character38Tests(unittest.TestCase):
    def test_every_story_uses_bundled_artwork_and_finishes_with_a_recovery(self):
        manifest = json.loads((ROOT/'assets/sprite_collection_manifest.json').read_text())
        for key, (_, timeline) in STORIES.items():
            self.assertGreater(story_duration(key), 4)
            elapsed = 0
            for pose, seconds in timeline:
                self.assertIn(pose, manifest, (key, pose))
                self.assertEqual(story_pose(key, elapsed+.001)[0], pose)
                elapsed += seconds
                for index in range(manifest[pose]['frames']):
                    self.assertTrue((ROOT/f'assets/pack_{pose}_{index}.png').exists())
            self.assertEqual(story_pose(key, elapsed+100)[0], timeline[-1][0])

    def test_checked_pool_respects_choices_and_pending_hunger(self):
        self.assertEqual(routine_pool({'groom','boo'}, M['ROUTINE_ACTIVITIES']), ('groom','boo'))
        self.assertNotIn('snack_story', routine_pool({'snack_story','groom'}, M['ROUTINE_ACTIVITIES'], True))
        self.assertEqual(routine_pool(set(), M['ROUTINE_ACTIVITIES']), ())

    def test_organic_scheduler_never_selects_unchecked_actions(self):
        pet = WaterPet.__new__(WaterPet)
        pet.idle_mood='';pet.night_active=False;pet.motion_mode='idle'
        pet.state='normal';pet.prompt_visible=pet.dragging=False;pet.active_alert_kind=''
        pet.chatter_until=None;pet.next_idle_activity=datetime.min
        pet._studio_is_open=Mock(return_value=False)
        pet.auto_activity=var('Organic routine');pet.pranks_enabled=var(False)
        pet.next_prank=datetime.min;pet.activity_minutes=var(1);pet.personality=var('Balanced')
        pet.routine_enabled={key:var(key=='doodle') for key in M['ROUTINE_ACTIVITIES']}
        pet._play_activity=Mock()
        pet._update_idle_mood(datetime.now())
        pet._play_activity.assert_called_once_with('doodle', automatic=True)

    def test_new_performance_is_single_finite_mood_and_reminders_prevent_launch(self):
        pet=WaterPet.__new__(WaterPet)
        pet.prompt_visible=pet.dragging=False;pet.active_alert_kind='';pet.state='normal'
        pet._close_chatter_card=Mock();pet._play_test_animation=Mock()
        pet._play_activity('kungfu_story', automatic=True)
        pet._play_test_animation.assert_called_once_with('story:kungfu_story',story_duration('kungfu_story'))
        pet._play_test_animation.reset_mock();pet.prompt_visible=True
        pet._play_activity('doodle')
        pet._play_test_animation.assert_not_called()

    def test_water_interrupt_discards_the_entire_story(self):
        pet=WaterPet.__new__(WaterPet)
        pet.prompt_visible=False;pet.active_alert_kind='';pet.idle_mood='story:snack_story'
        pet._close_chatter_card=Mock();pet._resize_anchored=Mock()
        pet._begin_attention=Mock();pet._play_reminder_sound=Mock();pet.root=Mock()
        pet.show_prompt()
        self.assertEqual(pet.idle_mood,'')
        self.assertIsNone(pet.idle_mood_until)
        self.assertTrue(pet.prompt_visible)

    def test_subpixel_travel_is_retained_for_fast_redraws(self):
        pet=WaterPet.__new__(WaterPet)
        pet.width=180;pet.height=184;pet.root=Mock()
        pet._screen_bounds=Mock(return_value=(0,0,1920,1080))
        pet._move_root(500.42,300.18)
        self.assertAlmostEqual(pet.pet_x,500.42)
        self.assertAlmostEqual(pet.pet_y,300.18)
        self.assertIn('+500+300',pet.root.geometry.call_args.args[0])

    def test_old_complete_pool_extends_once_and_later_disabled_stories_stay_off(self):
        pet=WaterPet.__new__(WaterPet);pet.pack_manifest={}
        old_pool=[key for key in M['ROUTINE_ACTIVITIES'] if key not in STORIES]
        with tempfile.TemporaryDirectory() as td:
            pet.settings_path=Path(td)/'settings.json'
            pet.settings_path.write_text(json.dumps({'organic_schema':1,'auto_activity':'Organic routine','routine_activities':old_pool}))
            result=pet._load_settings()
            self.assertEqual(set(result['routine_activities']),set(M['ROUTINE_ACTIVITIES']))
            result['routine_activities'].remove('doodle')
            pet.settings_path.write_text(json.dumps(result))
            self.assertNotIn('doodle',pet._load_settings()['routine_activities'])

    def test_all_enabled_stories_get_a_turn_without_immediate_repeats(self):
        queue=OrganicQueue(random.Random(38));pool=M['ROUTINE_ACTIVITIES']
        result=[queue.choose(pool) for _ in range(len(pool)*2)]
        self.assertEqual(set(result[:len(pool)]),set(pool))
        self.assertTrue(all(a!=b for a,b in zip(result,result[1:])))

    def test_new_props_keep_their_pixels_in_front_of_every_costume(self):
        pet=WaterPet.__new__(WaterPet);pet.app_dir=ROOT
        with patch('PIL.ImageTk.PhotoImage',side_effect=lambda im:im):
            pet._load_images()
        themes=json.loads((ROOT/'assets/wardrobe_manifest.json').read_text())
        examined=0
        for key,mask in pet.wardrobe.prop_masks.items():
            raw=pet.image_pil[key]
            points=[(x,y) for y in range(raw.height) for x in range(raw.width)
                    if mask.getpixel((x,y))>=250 and raw.getpixel((x,y))[3]==255]
            if not points:continue
            examined+=1
            for theme in themes:
                out=pet.wardrobe.dress(raw,theme,key)
                preserved=sum(out.getpixel(point)==raw.getpixel(point) for point in points)/len(points)
                self.assertGreaterEqual(preserved,.98,(theme,key,preserved))
        self.assertGreaterEqual(examined,10)


if __name__=='__main__': unittest.main()
