import ast
import runpy
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

SOURCE = Path(__file__).resolve().parents[1] / 'Start_Water_Puppy.pyw'
MODULE = runpy.run_path(str(SOURCE))
WaterPet = MODULE['WaterPet']

class ReminderBehaviorTests(unittest.TestCase):
    def test_no_dialogue_method_creates_a_window(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        methods = {'_show_general_alert', '_show_chatter_card', '_render_chatter_card', '_draw_prompt', '_draw_cloud_alert'}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in methods:
                self.assertNotIn('Toplevel', ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), node))

    def test_water_snooze_sets_ten_minutes_without_logging(self):
        pet = WaterPet.__new__(WaterPet)
        pet.prompt_visible = True
        pet._clear_attention = Mock()
        pet._resize_anchored = Mock()
        pet._show_chatter = Mock()
        before = datetime.now()
        pet.snooze_water()
        self.assertFalse(pet.prompt_visible)
        self.assertEqual(pet.state, 'normal')
        self.assertTrue(before + timedelta(minutes=10) <= pet.next_reminder <= datetime.now() + timedelta(minutes=10))

    def test_cloud_actions_and_offer_hold(self):
        pet = WaterPet.__new__(WaterPet)
        pet.canvas = Mock()
        pet._image = Mock(return_value='sprite')
        pet._answer_button = Mock()
        pet.active_alert_kind = 'movement'
        pet.attention_started_at = datetime.now()
        pet._draw_cloud_alert()
        self.assertEqual(pet.canvas.tag_bind.call_count, 2)
        pet.pet_name = Mock()
        pet.pet_name.get.return_value = 'Mochi'
        pet.water_prompt_text = 'Time for water?'
        pet.today_total_cache = 200
        pet.attention_started_at = datetime.now() - timedelta(minutes=5)
        pet._draw_prompt()
        self.assertEqual(pet._image.call_args.args, ('offer_7',))
        self.assertIn('water_snooze', [call.args[0] for call in pet.canvas.tag_bind.call_args_list])

if __name__ == '__main__':
    unittest.main()
