import ast
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "Start_Water_Puppy.pyw"
ASSETS = ROOT / "assets"


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_source_parses(self):
        self.assertIsInstance(self.tree, ast.Module)

    def test_color_key_renderer_has_no_partial_alpha(self):
        loader = next(node for node in ast.walk(self.tree)
                      if isinstance(node, ast.FunctionDef) and node.name == "_load_images")
        threshold = next(node for node in ast.walk(loader)
                         if isinstance(node, ast.Lambda))
        convert = eval(compile(ast.Expression(threshold), "alpha_threshold", "eval"))
        self.assertEqual({convert(value) for value in range(256)}, {0, 255})
        self.assertEqual(convert(0), 0)
        self.assertEqual(convert(255), 255)

    def test_version_is_15(self):
        self.assertIn("APP_VERSION = 15", self.source)

    def test_panda_face_icon_exists(self):
        icon = ASSETS / "panda.ico"
        self.assertTrue(icon.exists())
        self.assertGreater(icon.stat().st_size, 10_000)

    def test_animation_assets_exist(self):
        for direction in ("left", "right"):
            for frame in range(1, 9):
                self.assertTrue(
                    (ASSETS / f"panda_walk_{direction}_{frame}.png").exists()
                )
        for frame in range(1, 9):
            self.assertTrue((ASSETS / f"panda_bored_{frame}.png").exists())

    def test_generated_reminder_assets_are_high_resolution(self):
        names = (
            "idle_hd",
            "hula_1",
            "hula_2",
            "watch",
            "water",
            "bored_walk_right_1",
            "bored_walk_right_2",
            "bored_walk_left_1",
            "bored_walk_left_2",
        )
        for name in names:
            path = ASSETS / f"panda_{name}.png"
            with Image.open(path) as image:
                self.assertEqual(image.size, (512, 512), path.name)
                box = image.getchannel("A").getbbox()
            self.assertIsNotNone(box, path.name)
            self.assertGreaterEqual(box[0], 16, path.name)
            self.assertGreaterEqual(box[1], 16, path.name)
            self.assertLessEqual(box[2], 496, path.name)
            self.assertLessEqual(box[3], 496, path.name)

    def test_all_pose_ground_lines_match(self):
        for path in ASSETS.glob("panda_*.png"):
            if path.name in {
                "panda_idle_hd.png",
                "panda_hula_1.png",
                "panda_hula_2.png",
                "panda_watch.png",
                "panda_water.png",
                "panda_bored_walk_right_1.png",
                "panda_bored_walk_right_2.png",
                "panda_bored_walk_left_1.png",
                "panda_bored_walk_left_2.png",
            }:
                continue
            with Image.open(path) as image:
                box = image.getchannel("A").getbbox()
            self.assertIsNotNone(box, path.name)
            self.assertEqual(box[3], 172, path.name)

    def test_walk_frames_keep_original_resolution(self):
        for direction in ("left", "right"):
            for frame in range(1, 9):
                path = ASSETS / f"panda_walk_{direction}_{frame}.png"
                with Image.open(path) as image:
                    box = image.getchannel("A").getbbox()
                self.assertIsNotNone(box)
                self.assertEqual(box[3], 172)
                self.assertGreaterEqual(box[3] - box[1], 108)
                self.assertLessEqual(box[3] - box[1], 124)

    def test_bamboo_edge_activities_are_not_exposed(self):
        self.assertNotIn('"Bamboo staff at edge"', self.source)
        self.assertNotIn('"Hang from bamboo"', self.source)
        self.assertNotIn('"Eat bamboo at edge"', self.source)

    def test_old_test_menu_is_removed(self):
        self.assertNotIn('label="Test animations"', self.source)
        self.assertIn('text="Panda activities"', self.source)

    def test_alert_uses_content_aware_height(self):
        self.assertNotIn('window.geometry(f"510x270', self.source)
        self.assertIn("window.winfo_reqheight()", self.source)
        self.assertIn("alert_height = max(318", self.source)

    def test_water_prompt_has_separate_card_layout(self):
        self.assertIn("PROMPT_WIDTH = 440", self.source)
        self.assertIn('text=f"{self.pet_name.get().upper()} · WATER CHECK"', self.source)
        self.assertIn("188,\n            105,\n            290,\n            145", self.source)

    def test_reminders_use_purpose_built_poses(self):
        self.assertIn('initial_image = "watch"', self.source)
        self.assertIn('image_key = f"hula_', self.source)
        self.assertIn('image=self._image("water")', self.source)
        self.assertNotIn("_draw_water_glass_animation", self.source)

    def test_installer_definition_exists(self):
        installer = ROOT / "installer" / "WaterPanda.iss"
        self.assertTrue(installer.exists())
        self.assertIn("Water_Panda_Setup", installer.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
