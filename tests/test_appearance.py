import json
import unittest
from pathlib import Path
from PIL import Image, ImageChops, ImageOps
from pose_appearance import fit_sequence
from wardrobe import Wardrobe

ASSETS=Path(__file__).resolve().parents[1]/'assets'
MANIFEST=json.loads((ASSETS/'sprite_collection_manifest.json').read_text())


def sequence(family):
    count=MANIFEST[family.removesuffix('_left')]['frames']
    keys=[f'pack_{family}_{i}' for i in range(count)]
    sources=[]
    for key in keys:
        with Image.open(ASSETS/f'{key}.png') as im:
            sources.append(im.convert('RGBA'))
    return keys,fit_sequence(sources,keys)


class AppearanceTests(unittest.TestCase):
    def test_front_head_scale_matches_standing_sitting_and_resting(self):
        # Sitting/sleeping height must differ; head scale should not.
        for family in ('happy_idle','sit_down','sleep'):
            for key,(image,g) in zip(*sequence(family)):
                self.assertTrue(96<=g[0][2]-g[0][0]<=108,(key,g))
                self.assertEqual(image.getchannel('A').getbbox()[3],172,key)

    def test_fit_never_crops_any_animation_at_canvas_edge(self):
        for family in MANIFEST:
            for key,(image,g) in zip(*sequence(family)):
                box=image.getchannel('A').getbbox()
                self.assertGreaterEqual(box[0],2,key)
                self.assertGreaterEqual(box[1],2,key)
                self.assertLessEqual(box[2],178,key)
                self.assertLessEqual(box[3],178,key)

    def test_left_and_right_walk_remain_exact_mirrors(self):
        right=sequence('walk')[1];left=sequence('walk_left')[1]
        for (r,_),(l,_) in zip(right,left):
            # Compare channels separately: RGBA getbbox ignores RGB-only diffs.
            diff=ImageChops.difference(ImageOps.mirror(r),l)
            self.assertFalse(any(b.getbbox() for b in diff.split()))

    def test_seated_feet_keep_original_paw_colours_under_outfit(self):
        w=Wardrobe(ASSETS)
        for key,(im,g) in zip(*sequence('eat_bamboo')):
            w.geometry[key]=g
            out=w.dress(im,'navratri',key)
            # Foreground pads at the outside bottom corners stay unpainted.
            for x0,x1 in ((25,62),(122,155)):
                region=(x0,153,x1,172)
                diff=ImageChops.difference(im.crop(region),out.crop(region))
                self.assertFalse(any(b.getbbox() for b in diff.split()),key)

    def test_sleeping_scarf_does_not_paint_the_far_back(self):
        w=Wardrobe(ASSETS)
        for key,(im,g) in zip(*sequence('snore_sleep')):
            w.geometry[key]=g
            out=w.dress(im,'christmas',key)
            diff=ImageChops.difference(im.crop((138,125,173,172)),out.crop((138,125,173,172)))
            self.assertFalse(any(b.getbbox() for b in diff.split()),key)

    def test_sleeping_ghost_has_no_rectangular_fabric_outside_hood(self):
        w=Wardrobe(ASSETS)
        for key,(im,g) in zip(*sequence('sleep')):
            w.geometry[key]=g
            out=w.dress(im,'spooky',key)
            self.assertEqual(out.getpixel((172,94))[3],0,key)


if __name__=='__main__':unittest.main()
