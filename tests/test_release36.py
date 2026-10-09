import runpy, unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock
from PIL import Image, ImageOps
from wardrobe import Wardrobe, landmarks
from playful_activities import mirror_pose, reflected_pose, MIRROR_DURATION, boo_phase

ROOT=Path(__file__).resolve().parents[1]
M=runpy.run_path(str(ROOT/'Start_Water_Puppy.pyw'))

class ClosedGhostAndPranksTests(unittest.TestCase):
    def test_no_original_black_body_or_feet_show_in_standing_or_gait(self):
        wardrobe=Wardrobe(ROOT/'assets')
        for action,count in [('happy_idle',6),('walk',8),('walk_left',8),('run',8),('run_left',8)]:
            for index in range(count):
                key=f'pack_{action}_{index}'
                raw=Image.open(ROOT/'assets'/f'{key}.png').convert('RGBA').resize((180,180),Image.Resampling.LANCZOS)
                raw.putalpha(raw.getchannel('A').point(lambda a:255 if a>=128 else 0))
                out=wardrobe.dress(raw,'spooky',key)
                head,*_=landmarks(raw,key)
                bare=[(x,y) for y in range(head[3]+3,180) for x in range(180)
                      if raw.getpixel((x,y))[3] and max(raw.getpixel((x,y))[:3])<100
                      and raw.getpixel((x,y))==out.getpixel((x,y))]
                self.assertFalse(bare,key)

    def test_mirror_reflection_is_exact_same_dressed_pose_flipped(self):
        wardrobe=Wardrobe(ROOT/'assets')
        for theme in ('classic','spooky','diwali'):
            raw=Image.open(ROOT/'assets/pack_mirror_3.png').convert('RGBA')
            dressed=wardrobe.dress(raw,theme,'pack_mirror_3')
            expected=ImageOps.mirror(dressed).resize((104,104),Image.Resampling.LANCZOS)
            self.assertEqual(reflected_pose(dressed).tobytes(),expected.tobytes())

    def test_routines_are_finite_and_have_clear_surprise_then_recovery(self):
        self.assertEqual([mirror_pose(t) for t in (0,1.1,2.2,3.2,4,5,6,7.5)],[0,1,2,3,4,5,6,7])
        self.assertEqual(mirror_pose(MIRROR_DURATION+10),7)
        self.assertEqual([boo_phase(t)[0] for t in (0,.6,1.5,3)],[0,1,2,3])

    def test_automatic_pranks_respect_toggle_cooldown_and_reminders(self):
        pet=M['WaterPet'].__new__(M['WaterPet'])
        pet.prompt_visible=pet.active_alert_kind=pet.dragging=False;pet.state='normal'
        pet.pranks_enabled=Mock();pet.pranks_enabled.get.return_value=False
        pet.next_prank=datetime.now()-timedelta(minutes=1)
        pet._play_test_animation=Mock();pet._close_chatter_card=Mock();pet._resize_anchored=Mock()
        pet._play_activity('mirror',automatic=True);pet._play_test_animation.assert_not_called()
        pet.pranks_enabled.get.return_value=True;pet.next_prank=datetime.now()+timedelta(minutes=5)
        pet._play_activity('boo',automatic=True);pet._play_test_animation.assert_not_called()
        pet.next_prank=datetime.now()-timedelta(seconds=1)
        pet._play_activity('mirror',automatic=True);pet._play_test_animation.assert_called_once()
        pet._play_test_animation.reset_mock();pet.prompt_visible=True
        pet._play_activity('boo');pet._play_test_animation.assert_not_called()

    def test_manual_pranks_work_when_automatic_toggle_is_off(self):
        pet=M['WaterPet'].__new__(M['WaterPet'])
        pet.prompt_visible=pet.active_alert_kind=pet.dragging=False;pet.state='normal'
        pet.pranks_enabled=Mock();pet.pranks_enabled.get.return_value=False
        pet._play_test_animation=Mock();pet._close_chatter_card=Mock();pet._resize_anchored=Mock()
        pet._play_activity('mirror');pet._play_test_animation.assert_called_once_with('mirror_surprise',MIRROR_DURATION)
