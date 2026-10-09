import json
import runpy
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock
from PIL import Image
from wardrobe import Wardrobe, landmarks

ROOT = Path(__file__).resolve().parents[1]
M = runpy.run_path(str(ROOT / "Start_Water_Puppy.pyw"))


class Release34Tests(unittest.TestCase):
    def test_each_theme_has_real_scene_and_only_distinct_effect_controls(self):
        manifest = json.loads((ROOT / "assets/scene_manifest.json").read_text())
        for key in M["PROP_KEYS"]:
            options = M["theme_activity_options"](key, manifest)
            self.assertEqual(options[0], ("scene", manifest[key]["title"], True))
            self.assertEqual(len(options), 2 if key in M["THEME_EFFECT_LABELS"] else 1)
            self.assertEqual(len(set(item[1] for item in options)), len(options))
        self.assertEqual(M["theme_activity_options"]("classic", manifest), ())

    def test_disabled_effects_remain_visible_but_not_enabled(self):
        manifest = json.loads((ROOT / "assets/scene_manifest.json").read_text())
        options = M["theme_activity_options"]("holi", manifest, False)
        self.assertEqual(options[0][2], True)
        self.assertEqual(options[1], ("effect", "Throw Holi colours", False))

    def test_effect_launch_is_distinct_and_respects_reminder_priority(self):
        pet = M["WaterPet"].__new__(M["WaterPet"])
        pet.theme_effects_enabled = Mock(); pet.theme_effects_enabled.get.return_value = True
        pet.prompt_visible = pet.active_alert_kind = pet.dragging = False
        pet.state = "normal"; pet.pet_x = pet.pet_y = 20
        pet._close_chatter_card = Mock(); pet._resize_anchored = Mock()
        pet._play_test_animation = Mock(); pet._screen_bounds = Mock(return_value=(0,0,1920,1080))
        pet.desktop_effects = Mock()
        pet._play_theme_effect("holi")
        pet._play_test_animation.assert_called_once_with("pack:dance", 7.0)
        pet.desktop_effects.play.assert_called_once()
        pet.desktop_effects.reset_mock(); pet.prompt_visible = True
        pet._play_theme_effect("diwali")
        pet.desktop_effects.play.assert_not_called()
        pet.prompt_visible = False; pet.theme_effects_enabled.get.return_value = False
        pet._play_theme_effect("diwali")
        pet.desktop_effects.play.assert_not_called()

    def test_ghost_hood_preserves_front_eye_pixels_in_both_directions(self):
        wardrobe = Wardrobe(ROOT / "assets")
        for variant in ("walk", "walk_left", "run", "run_left"):
            for index in range(8):
                key = f"pack_{variant}_{index}"
                raw = Image.open(ROOT / "assets" / (key + ".png")).convert("RGBA").resize((180,180), Image.Resampling.LANCZOS)
                raw.putalpha(raw.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
                out = wardrobe.dress(raw, "spooky", key)
                (l,t,r,b),_,_,left = landmarks(raw,key)
                xs = range(l, l+(r-l)//2) if left else range(l+(r-l)//2,r)
                pixels = [(x,y) for y in range(t+int((b-t)*.35),t+int((b-t)*.75)) for x in xs
                          if raw.getpixel((x,y))[3] and max(raw.getpixel((x,y))[:3]) < 100]
                self.assertTrue(pixels, key)
                preserved = sum(raw.getpixel(point) == out.getpixel(point) for point in pixels)/len(pixels)
                self.assertGreaterEqual(preserved, .95, (key,preserved))
