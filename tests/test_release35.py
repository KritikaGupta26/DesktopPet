import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from wardrobe import Wardrobe

ROOT = Path(__file__).resolve().parents[1]

class GhostCloakTests(unittest.TestCase):
    def test_ghost_uses_one_continuous_asset_for_front_and_both_profile_directions(self):
        wardrobe = Wardrobe(ROOT / 'assets')
        for action,part in [('happy_idle','full_front'),('walk','full_profile'),('walk_left','full_profile')]:
            key=f'pack_{action}_0'
            raw=Image.open(ROOT/'assets'/f'{key}.png').convert('RGBA').resize((180,180),Image.Resampling.LANCZOS)
            with patch.object(wardrobe,'part',wraps=wardrobe.part) as read:
                wardrobe.dress(raw,'spooky',key)
                read.assert_called_once_with('spooky',part)

    def test_generated_cloak_has_real_transparency_and_continuous_neck_fabric(self):
        for direction in ('front','profile'):
            image=Image.open(ROOT/'assets'/f'wardrobe_spooky_full_{direction}.png').convert('RGBA')
            alpha=image.getchannel('A')
            self.assertEqual(alpha.getpixel((0,0)),0)
            # Face openings are punched by the renderer; only background alpha
            # and full continuous body cloth are required in the source texture.
            for fraction in (.40,.45,.50,.55,.60,.65,.70):
                row=alpha.crop((0,round(image.height*fraction),image.width,round(image.height*fraction)+1))
                self.assertGreater(sum(a>=128 for a in row.getdata()),image.width*.25)
