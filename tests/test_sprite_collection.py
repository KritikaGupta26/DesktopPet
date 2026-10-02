import json
import runpy
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/'assets/sprite_collection_manifest.json').read_text(encoding='utf-8'))
WaterPet=runpy.run_path(str(ROOT/'Start_Water_Puppy.pyw'))['WaterPet']

class SpriteCollectionTests(unittest.TestCase):
    def test_every_sheet_and_pose_is_accounted_for(self):
        self.assertEqual(len({m['sheet'] for m in MANIFEST.values()}),17)
        self.assertEqual(len(MANIFEST),47)
        self.assertEqual(sum(m['frames'] for m in MANIFEST.values()),240)

    def test_every_frame_has_padding_and_transparency(self):
        for key,meta in MANIFEST.items():
            for i in range(meta['frames']):
                with Image.open(ROOT/'assets'/f'pack_{key}_{i}.png') as im:
                    self.assertEqual(im.size,(512,512))
                    box=im.getchannel('A').getbbox()
                    self.assertIsNotNone(box)
                    self.assertGreaterEqual(box[0],16)
                    self.assertGreaterEqual(box[1],16)
                    self.assertLessEqual(box[2],496)
                    self.assertLessEqual(box[3],496)

    def test_once_hold_and_loop_have_distinct_end_behavior(self):
        pet=WaterPet.__new__(WaterPet);pet.pack_manifest=MANIFEST
        pet.images={'panda':{f'pack_{key}_{i}':f'{key}:{i}' for key,m in MANIFEST.items() for i in range(m['frames'])}}
        self.assertEqual(pet._pack_image('water_offer',1000),'water_offer:7')
        self.assertEqual(pet._pack_image('walk',8*MANIFEST['walk']['seconds_per_frame']),'walk:0')

    def test_all_sequences_reach_the_renderer(self):
        pet=WaterPet.__new__(WaterPet);pet.pack_manifest=MANIFEST
        pet.canvas=Mock();pet._pack_image=Mock(return_value='sprite')
        for key in MANIFEST:
            pet._draw_pack_animation(key,0.5)
            self.assertEqual(pet._pack_image.call_args.args,(key,0.5))

    def test_hanging_is_routed_to_an_edge(self):
        pet=WaterPet.__new__(WaterPet);pet.pack_manifest=MANIFEST
        pet.prompt_visible=False;pet.active_alert_kind='';pet.dragging=False;pet.state='normal'
        pet.pet_x=100;pet.pet_y=200;pet._screen_bounds=Mock(return_value=(0,0,1920,1080))
        pet._start_edge_activity=Mock();pet._play_test_animation=Mock()
        pet._play_pack_animation('bamboo_hang')
        pet._start_edge_activity.assert_called_once_with('pack:bamboo_hang')
        self.assertEqual(pet.target_x,0)
        pet._play_test_animation.assert_not_called()

    def test_walk_uses_requested_stride_frame_in_both_directions(self):
        pet=WaterPet.__new__(WaterPet);pet.pack_manifest=MANIFEST
        pet.images={'panda':{f'pack_walk{suffix}_{i}':f'{suffix}:{i}' for suffix in ('','_left') for i in range(8)}}
        for i in range(8):
            self.assertEqual(pet._image(f'walk_right_{i+1}'),f':{i}')
            self.assertEqual(pet._image(f'walk_left_{i+1}'),f'_left:{i}')

    def test_sleep_has_no_fragment_from_preceding_row(self):
        for i in range(6):
            with Image.open(ROOT/'assets'/f'pack_sleep_{i}.png') as im:
                box=im.getchannel('A').getbbox()
                # Sleeping panda is low and wide; preceding-row legs made
                # the broken extraction taller than it was wide.
                self.assertLess(box[3]-box[1],box[2]-box[0])

    def test_stride_timing_is_elapsed_time_and_restarts_on_turn(self):
        from unittest.mock import patch
        pet=WaterPet.__new__(WaterPet);pet.pack_manifest=MANIFEST
        pet.walk_direction='right';pet.motion_mode='walking';pet.walk_frame_ms=Mock();pet.walk_frame_ms.get.return_value=180
        with patch('time.monotonic',side_effect=[10,10.1,10.2,10.4]):
            self.assertEqual(pet._locomotion_frame('walk'),1)
            self.assertEqual(pet._locomotion_frame('walk'),1)
            self.assertEqual(pet._locomotion_frame('walk'),2)
            pet.walk_direction='left'
            self.assertEqual(pet._locomotion_frame('walk'),1)

    def test_selected_routine_cycles_without_repeating_one_activity(self):
        from datetime import timedelta
        pet=WaterPet.__new__(WaterPet);pet.idle_mood='';pet.next_idle_activity=datetime.now()-timedelta(seconds=1)
        pet.state='normal';pet.prompt_visible=False;pet.active_alert_kind='';pet.dragging=False;pet.motion_mode='idle';pet.chatter_until=None
        pet.activity_minutes=Mock();pet.activity_minutes.get.return_value=3
        pet.auto_activity=Mock();pet.auto_activity.get.return_value='Selected routine'
        pet.routine_enabled={key:Mock() for key in ('dance','ear_rub')}
        for enabled in pet.routine_enabled.values():enabled.get.return_value=True
        pet._play_pack_animation=Mock()
        for _ in range(3):
            now=datetime.now();pet.next_idle_activity=now-timedelta(seconds=1);pet._update_idle_mood(now)
        self.assertEqual([c.args[0] for c in pet._play_pack_animation.call_args_list],['dance','ear_rub','dance'])
