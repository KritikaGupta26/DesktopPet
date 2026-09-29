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

    def test_version_is_14(self):
        self.assertIn("APP_VERSION = 14", self.source)

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

    def test_all_pose_canvases_match(self):
        sizes = set()
        for path in ASSETS.glob("panda_*.png"):
            with Image.open(path) as image:
                sizes.add(image.size)
        self.assertEqual(sizes, {(180, 180)})

    def test_all_pose_ground_lines_match(self):
        for path in ASSETS.glob("panda_*.png"):
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

    def test_bamboo_hanging_is_preserved(self):
        self.assertTrue((ASSETS / "panda_action_hang.png").exists())
        self.assertIn('"action_hang"', self.source)

    def test_old_test_menu_is_removed(self):
        self.assertNotIn('label="Test animations"', self.source)
        self.assertIn('text="Panda activities"', self.source)

    def test_alert_uses_content_aware_height(self):
        self.assertNotIn('window.geometry(f"510x270', self.source)
        self.assertIn("window.winfo_reqheight()", self.source)
        self.assertIn("alert_height = max(300", self.source)

    def test_installer_definition_exists(self):
        installer = ROOT / "installer" / "WaterPanda.iss"
        self.assertTrue(installer.exists())
        self.assertIn("Water_Panda_Setup", installer.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
