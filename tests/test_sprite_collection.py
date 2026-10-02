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
            self.assertEqual(pet._image(f'walk_right_{i+1}'),f':{(0,1,2,4,5,6)[i%6]}')
            self.assertEqual(pet._image(f'walk_left_{i+1}'),f'_left:{(0,1,2,4,5,6)[i%6]}')

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
            self.assertEqual(pet._locomotion_frame('walk'),1)
            pet.walk_direction='left'
            self.assertEqual(pet._locomotion_frame('walk'),1)

    def test_selected_routine_cycles_without_repeating_one_activity(self):
        from datetime import timedelta
        pet=WaterPet.__new__(WaterPet);pet.idle_mood='';pet.next_idle_activity=datetime.now()-timedelta(seconds=1)
        pet.state='normal';pet.prompt_visible=False;pet.active_alert_kind='';pet.dragging=False;pet.motion_mode='idle';pet.chatter_until=None
        pet.activity_minutes=Mock();pet.activity_minutes.get.return_value=3
        pet.auto_activity=Mock();pet.auto_activity.get.return_value='Selected routine'
        pet.routine_enabled={key:Mock() for key in ('dance','groom')}
        for enabled in pet.routine_enabled.values():enabled.get.return_value=True
        pet._play_activity=Mock()
        for _ in range(3):
            now=datetime.now();pet.next_idle_activity=now-timedelta(seconds=1);pet._update_idle_mood(now)
        self.assertEqual([c.args[0] for c in pet._play_activity.call_args_list],['dance','groom','dance'])

    def test_hunger_waits_for_water_and_click_feeds_once(self):
        from datetime import timedelta
        pet=WaterPet.__new__(WaterPet);pet.hunger_enabled=Mock();pet.hunger_enabled.get.return_value=True
        pet.next_hunger=datetime.now()-timedelta(seconds=1);pet.hungry=False;pet.hunger_requested=False
        pet.prompt_visible=True;pet.active_alert_kind='';pet.dragging=False;pet.idle_mood='';pet.chatter_until=None;pet.state='normal';pet.motion_mode='idle'
        pet._show_chatter=Mock();pet._update_hunger(datetime.now())
        self.assertTrue(pet.hungry);pet._show_chatter.assert_not_called()
        pet.prompt_visible=False;pet._update_hunger(datetime.now());pet._update_hunger(datetime.now())
        pet._show_chatter.assert_called_once()
        pet.hunger_minutes=Mock();pet.hunger_minutes.get.return_value=120
        pet._play_test_animation=Mock();pet.canvas=Mock();pet.canvas.gettags.return_value=()
        pet._start_drag(Mock())
        self.assertFalse(pet.hungry);self.assertFalse(pet.dragging)
        pet._play_test_animation.assert_called_once_with('feed',5.5)
        self.assertGreater(pet.next_hunger,datetime.now()+timedelta(minutes=119))
        # Mouse release after a feed click must not overwrite the eating pose.
        pet._end_drag(Mock());self.assertEqual(pet.motion_mode,'idle')

    def test_activity_catalog_has_no_duplicate_controls_or_automatic_food(self):
        module=runpy.run_path(str(ROOT/'Start_Water_Puppy.pyw'))
        labels=module['ACTIVITY_LABELS'];aliases=module['ACTIVITY_ALIASES']
        self.assertEqual(len(labels),len(set(labels.values())))
        self.assertTrue(set(aliases).isdisjoint(labels))
        self.assertNotIn('feed',module['ROUTINE_ACTIVITIES'])
        self.assertNotIn('eat_bamboo',module['ROUTINE_ACTIVITIES'])
        self.assertEqual(aliases['wiggle'],'dance')
        self.assertEqual(aliases['greeting'],'wave')

    def test_cursor_follow_moves_retargets_and_yields_to_reminders(self):
        pet=WaterPet.__new__(WaterPet);pet.cursor_mode=Mock();pet.cursor_mode.get.return_value='Follow'
        pet.prompt_visible=False;pet.active_alert_kind='';pet.dragging=False;pet.state='normal';pet.idle_mood='';pet.motion_mode='idle'
        pet.walk_frame_ms=Mock();pet.walk_frame_ms.get.return_value=180
        pet.pet_x=300.;pet.pet_y=300.;pet.root=Mock();pet.root.winfo_pointerxy.return_value=(900,392)
        pet._screen_bounds=Mock(return_value=(0,0,1920,1080));pet._move_root=Mock()
        pet._check_cursor_reaction(datetime.now())
        self.assertGreater(pet.pet_x,300);self.assertEqual(pet.walk_direction,'right')
        previous=pet.pet_x;pet.root.winfo_pointerxy.return_value=(10,392)
        pet._check_cursor_reaction(datetime.now())
        self.assertLess(pet.pet_x,previous);self.assertEqual(pet.walk_direction,'left')
        previous=pet.pet_x;pet.prompt_visible=True;pet._check_cursor_reaction(datetime.now())
        self.assertEqual(pet.pet_x,previous)
        pet.prompt_visible=False;pet.root.winfo_pointerxy.return_value=(round(pet.pet_x+90),392)
        pet._check_cursor_reaction(datetime.now())
        self.assertEqual(pet.pet_x,previous);self.assertTrue(pet.cursor_at_rest)

    def test_manual_follow_launches_motion_instead_of_a_pose(self):
        pet=WaterPet.__new__(WaterPet);pet.prompt_visible=False;pet.active_alert_kind='';pet.dragging=False;pet.state='normal'
        pet._close_chatter_card=Mock();pet._play_test_animation=Mock()
        pet._play_pack_animation('cursor_follow')
        self.assertEqual(pet.cursor_session_kind,'Follow')
        self.assertIsNotNone(pet.cursor_session_until)
        pet._play_test_animation.assert_not_called()

    def test_wind_down_sequence_and_duplicate_roll_controls(self):
        module=runpy.run_path(str(ROOT/'Start_Water_Puppy.pyw'))
        pose=module['wind_down_pose']
        for elapsed,key in ((0,'yawn_stretch'),(3,'lazy_stretch'),(6,'sleep'),(24,'wake_up'),(28,'wake_up')):
            self.assertEqual(pose(elapsed)[0],key)
        self.assertNotIn('side_roll',module['ACTIVITY_LABELS'])
        for key in ('sleep','lazy_stretch','yawn_stretch','snore_sleep','wake_up'):
            self.assertEqual(module['ACTIVITY_ALIASES'][key],'wind_down')
            self.assertNotIn(key,module['ACTIVITY_LABELS'])

    def test_standing_scale_matches_walk_without_clipping(self):
        normalize=runpy.run_path(str(ROOT/'Start_Water_Puppy.pyw'))['normalize_standing_sprite']
        walk=Image.open(ROOT/'assets/pack_walk_0.png').getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
        for i in range(MANIFEST['happy_idle']['frames']):
            image=normalize(Image.open(ROOT/f'assets/pack_happy_idle_{i}.png').convert('RGBA'))
            box=image.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
            self.assertLess(abs((box[3]-box[1])-(walk[3]-walk[1])),20)
            self.assertLessEqual(abs(box[3]-walk[3]),2)
            self.assertGreater(box[0],0);self.assertLess(box[2],512)
            self.assertGreater(box[1],0);self.assertLess(box[3],512)

    def test_legacy_routines_merge_without_losing_enabled_activity(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            pet=WaterPet.__new__(WaterPet);pet.pack_manifest=MANIFEST
            pet.settings_path=Path(directory)/'settings.json'
            pet.settings_path.write_text(json.dumps({'auto_activity':'Rub ears','routine_activities':['ear_rub','wash_face','sleep','lazy_stretch','eat_bamboo']}))
            settings=pet._load_settings()
            self.assertEqual(settings['auto_activity'],'Grooming')
            self.assertEqual(settings['routine_activities'],['groom','wind_down'])

    def test_grooming_combines_three_rows_in_one_control(self):
        module=runpy.run_path(str(ROOT/'Start_Water_Puppy.pyw'))
        sequence=module['GROOM_SEQUENCE'];pose=module['sequence_pose']
        self.assertEqual([pose(sequence,t)[0] for t in (0,3,6)],['wash_face','ear_rub','belly_scratch'])
        for key in ('wash_face','ear_rub','belly_scratch'):
            self.assertNotIn(key,module['ACTIVITY_LABELS'])
            self.assertEqual(module['ACTIVITY_ALIASES'][key],'groom')

    def test_new_walk_retains_previous_art_and_uses_matching_mirrors(self):
        from PIL import ImageOps,ImageChops
        self.assertEqual(MANIFEST['walk']['selected_playback_frames'],[0,1,2,4,5,6])
        self.assertTrue((ROOT/'artwork/walk_v25_source.png').is_file())
        for i in range(8):
            self.assertTrue((ROOT/f'artwork/v24_walk/pack_walk_{i}.png').is_file())
            right=Image.open(ROOT/f'assets/pack_walk_{i}.png').convert('RGBA')
            left=Image.open(ROOT/f'assets/pack_walk_left_{i}.png').convert('RGBA')
            self.assertIsNone(ImageChops.difference(ImageOps.mirror(right),left).getbbox())
