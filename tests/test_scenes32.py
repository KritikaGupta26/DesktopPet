import json
import unittest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock
import runpy
from PIL import Image, ImageChops
from scene_playback import scene_pose, scene_duration
from seasonal_themes import PROP_KEYS

ROOT=Path(__file__).resolve().parents[1]
SCENES=json.loads((ROOT/'assets/scene_manifest.json').read_text())
WaterPet=runpy.run_path(str(ROOT/'Start_Water_Puppy.pyw'))['WaterPet']


class SceneTests(unittest.TestCase):
    def test_all_themes_and_repaired_core_scenes_are_present(self):
        self.assertEqual(set(SCENES),set(PROP_KEYS)|{'log','meditate'})
        for key,meta in SCENES.items():
            self.assertEqual(meta['frames'],8)
            self.assertEqual(set(i for i,_ in meta['timeline']),set(range(8)),key)
            self.assertTrue(all(0<seconds<=5 for _,seconds in meta['timeline']))
            self.assertLess(scene_duration(meta),30)

    def test_all_scene_poses_are_transparent_padded_and_distinct(self):
        for key,meta in SCENES.items():
            hashes=set()
            for index in range(meta['frames']):
                with Image.open(ROOT/f'assets/scene_{key}_{index}.png') as im:
                    self.assertEqual(im.size,(512,512));self.assertEqual(im.mode,'RGBA')
                    alpha=im.getchannel('A').point(lambda a:255 if a>=128 else 0)
                    box=alpha.getbbox();self.assertIsNotNone(box)
                    self.assertGreaterEqual(box[0],16,key);self.assertGreaterEqual(box[1],16,key)
                    self.assertLessEqual(box[2],496,key);self.assertLessEqual(box[3],496,key)
                    self.assertEqual(alpha.getpixel((0,0)),0)
                    hashes.add(im.tobytes())
            self.assertEqual(len(hashes),8,key)

    def test_finite_scenes_visit_every_phase_and_hold_last_pose(self):
        for key,meta in SCENES.items():
            elapsed=0
            for index,seconds in meta['timeline']:
                self.assertEqual(scene_pose(meta,elapsed+seconds/2),index,key)
                elapsed+=seconds
            self.assertEqual(scene_pose(meta,9999),meta['timeline'][-1][0])
            self.assertEqual(scene_pose(meta,-1),meta['timeline'][0][0])

    def test_scene_does_not_launch_over_water_drag_or_alert(self):
        p=WaterPet.__new__(WaterPet);p.scene_manifest=SCENES
        p._play_test_animation=Mock();p._close_chatter_card=Mock()
        for flag in ('prompt_visible','active_alert_kind','dragging'):
            p.prompt_visible=False;p.active_alert_kind='';p.dragging=False;p.state='normal'
            setattr(p,flag,True);p._play_theme_scene('spooky')
            p._play_test_animation.assert_not_called()
        p.dragging=False;p._play_theme_scene('spooky')
        p._play_test_animation.assert_called_once_with('theme:spooky',scene_duration(SCENES['spooky']))

    def test_custom_scene_interval_and_busy_timer_do_not_drop_due_scene(self):
        p=WaterPet.__new__(WaterPet);p.theme_activity_enabled=Mock();p.theme_activity_enabled.get.return_value=True
        p.theme_activity_minutes=Mock();p.theme_activity_minutes.get.return_value=35
        now=datetime.now();p.next_theme_activity=now-timedelta(seconds=1)
        p.prompt_visible=True;p._play_theme_scene=Mock();p._show_chatter=Mock()
        p._check_theme_activity(now);self.assertLess(p.next_theme_activity,now)
        p.prompt_visible=False;p.active_alert_kind='';p.dragging=False;p.state='normal';p.motion_mode='idle'
        p.idle_mood='';p.chatter_until=None;p.hungry=False;p._studio_is_open=Mock(return_value=False)
        p._current_theme=Mock(return_value='spooky');p._check_theme_activity(now)
        p._play_theme_scene.assert_called_once_with('spooky')
        self.assertEqual(p.next_theme_activity,now+timedelta(minutes=35))

    def test_walk_has_eight_unique_poses_without_detached_islands(self):
        # A flood fill catches the stray triangle which bounding boxes missed.
        signatures=set()
        for i in range(8):
            with Image.open(ROOT/f'assets/pack_walk_{i}.png') as im:
                alpha=im.getchannel('A').point(lambda a:255 if a>=128 else 0)
                pixels=alpha.load();occupied={(x,y) for y in range(512) for x in range(512) if pixels[x,y]}
                signatures.add(im.tobytes())
            frontier=[next(iter(occupied))];visited=set(frontier)
            while frontier:
                x,y=frontier.pop()
                for neighbor in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if neighbor in occupied and neighbor not in visited:
                        visited.add(neighbor);frontier.append(neighbor)
            # Tiny resampling islands can be a few fur pixels, never limb scraps.
            self.assertLess(len(occupied-visited),50,i)
        self.assertEqual(len(signatures),8)
