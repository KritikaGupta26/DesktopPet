import json
import runpy
import unittest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock
from PIL import Image, ImageChops
from locomotion import escape_target, run_step
from wardrobe import Wardrobe

ROOT=Path(__file__).resolve().parents[1]
M=runpy.run_path(str(ROOT/'Start_Water_Puppy.pyw'))
WaterPet=M['WaterPet']


class Release33Tests(unittest.TestCase):
    def test_escape_does_not_collapse_for_pointer_directly_above_or_below(self):
        self.assertGreaterEqual(abs(escape_target(500,590,0,1920)-500),200)
        self.assertGreaterEqual(abs(escape_target(-900,-810,-1920,1920)+900),200)

    def test_avoid_chooses_room_when_preferred_escape_hits_edge(self):
        self.assertGreater(escape_target(0,100,0,1920),0)
        self.assertLess(escape_target(1740,1750,0,1920),1740)
        for start in (0,100,900,1740):
            target=escape_target(start,start+90,0,1920)
            self.assertTrue(0<=target<=1740)

    def test_run_travel_matches_two_steps_per_cycle(self):
        cycle=1.12
        travelled=run_step(cycle,tick_seconds=.04)*cycle/.04
        self.assertAlmostEqual(travelled,2*92*180/512)

    def test_fetch_removed_from_controls_and_old_routines(self):
        self.assertNotIn('fetch',M['ACTIVITY_LABELS'])
        self.assertNotIn('fetch',M['ROUTINE_ACTIVITIES'])
        self.assertNotIn('chase_ball',M['ACTIVITY_ALIASES'])
        p=WaterPet.__new__(WaterPet)
        p.prompt_visible=p.active_alert_kind=p.dragging=False
        p.state='normal';p.start_fetch=Mock()
        p._play_activity('fetch')
        p.start_fetch.assert_not_called()

    def test_outfits_cover_running_water_and_core_scenes(self):
        w=Wardrobe(ROOT/'assets')
        themes=json.loads((ROOT/'assets/wardrobe_manifest.json').read_text())
        names=['pack_walk_0','pack_run_4','pack_water_offer_7','pack_bow_2',
               'pack_sleep_0','pack_eat_bamboo_3','pack_hula_hoop_4',
               'scene_log_4','scene_meditate_3','scene_peekaboo_3']
        for name in names:
            size=(360,180) if name.startswith('scene_peekaboo') else (180,180)
            im=Image.open(ROOT/'assets'/f'{name}.png').convert('RGBA').resize(size)
            for theme in themes:
                out=w.dress(im,theme,name)
                self.assertIsNotNone(ImageChops.difference(im.convert('RGB'),out.convert('RGB')).getbbox(),(theme,name))
                self.assertEqual(set(out.getchannel('A').getdata()),{0,255})
                self.assertEqual(out.getchannel('A').getpixel((0,0)),0)
        self.assertIs(w.dress(im,'classic',name),im)

    def test_running_has_eight_distinct_opposing_phases_and_exact_left_mirrors(self):
        from PIL import ImageOps
        seen=set()
        for i in range(8):
            im=Image.open(ROOT/f'assets/pack_run_{i}.png').convert('RGBA')
            left=Image.open(ROOT/f'assets/pack_run_left_{i}.png').convert('RGBA')
            self.assertIsNone(ImageChops.difference(ImageOps.mirror(im),left).getbbox())
            seen.add(im.tobytes())
            box=im.getchannel('A').getbbox()
            self.assertGreaterEqual(box[0],16);self.assertLessEqual(box[2],496)
        self.assertEqual(len(seen),8)

    def test_water_interrupt_stops_desktop_effect(self):
        p=WaterPet.__new__(WaterPet)
        p.desktop_effects=Mock();p.prompt_visible=True
        p.active_alert_kind='';p.dragging=False
        p.root=Mock();p._close_chatter_card=Mock();p._begin_attention=Mock();p._play_reminder_sound=Mock()
        p.show_prompt()
        p.desktop_effects.stop.assert_called_once()
