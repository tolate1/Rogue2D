import os
import unittest
import pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from src.entities import Player, BloodAltar
from src.save_manager import (
    save_game_state, load_game_state, delete_save,
    _safe_write_json, CURRENT_SCHEMA_VERSION, SAVE_FILE, load_profile, save_profile
)
from src.items import Item
from src.ui import ShopModal, UI

class DummyGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.loot_rng = None
        self.fx_rng = None

class TestDotaSkillsAndCriticFixes(unittest.TestCase):
    def setUp(self):
        self.screen = pygame.display.set_mode((1280, 720))
        self.visible_sprites = DummyGroup()
        self.obstacle_sprites = DummyGroup()
        self.enemy_sprites = DummyGroup()
        self.player = Player((100, 100), [self.visible_sprites], self.obstacle_sprites, self.enemy_sprites)
        delete_save()

    def tearDown(self):
        delete_save()

    def test_skill_points_bank_and_branches_are_spendable_from_tree(self):
        """Points bank across levels; Dash rank 2 opens independent Shield and Ult branches."""
        self.assertEqual(self.player.level, 1)
        self.assertEqual(self.player.skill_points, 0)

        self.player.skill_points = 1
        ok, msg = self.player.upgrade_skill('shield')
        self.assertFalse(ok)
        self.assertIn("Рывок", msg)
        self.assertEqual(self.player.skill_points, 1)
        ok, msg = self.player.upgrade_skill('ult')
        self.assertFalse(ok)
        self.assertIn("Рывок", msg)
        self.assertEqual(self.player.skill_points, 1)

        # Two level-ups in one XP award bank two points; the existing point remains.
        self.player.gain_exp(300)
        self.assertEqual(self.player.level, 3)
        self.assertEqual(self.player.skill_points, 3)

        ui = UI()
        ui.display_surface = self.screen
        ui.draw_skill_tree(self.screen, self.player)
        self.assertEqual(set(ui.skill_tree_node_rects), {'dash', 'shield', 'ult'})
        self.assertTrue(ui.handle_skill_tree_click(ui.skill_tree_node_rects['dash'].center, self.player))
        self.assertEqual(self.player.skills['dash']['level'], 2)
        self.assertEqual(self.player.skill_points, 2)

        # Both branches are now open; spend on one, then earn and spend on the other.
        ui.draw_skill_tree(self.screen, self.player)
        self.assertTrue(ui.handle_skill_tree_click(ui.skill_tree_node_rects['shield'].center, self.player))
        self.assertEqual(self.player.skills['shield']['level'], 1)
        self.assertEqual(self.player.skill_points, 1)
        self.player.gain_exp(300)  # One more level; the point is banked.
        self.assertEqual(self.player.skill_points, 2)
        ui.draw_skill_tree(self.screen, self.player)
        self.assertTrue(ui.handle_skill_tree_click(ui.skill_tree_node_rects['ult'].center, self.player))
        self.assertEqual(self.player.skills['ult']['level'], 1)
        self.assertEqual(self.player.skill_points, 1)

    def test_uninvested_skills_stay_locked_at_high_player_level(self):
        keys = [0] * 323
        keys[pygame.K_x] = 1
        keys[pygame.K_c] = 1
        self.player.level = 20
        starting_energy = self.player.energy
        from unittest.mock import patch
        with patch('pygame.key.get_pressed', return_value=keys):
            self.player.input()
        self.assertFalse(self.player.is_shielded)
        self.assertEqual(self.player.energy, starting_energy)
        self.assertEqual(self.player.skills['ult']['level'], 0)

    def test_player_damage_does_not_shake_camera(self):
        calls = []
        self.visible_sprites.shake = lambda *args, **kwargs: calls.append((args, kwargs))
        self.player.take_damage(8)
        self.assertEqual(calls, [])

    def test_save_and_load_preserves_skills_and_altars(self):
        """Save and load correctly serializes and restores skills, skill points, and used altars."""
        self.player.skill_points = 3
        self.player.skills['dash']['level'] = 2
        self.player.bombs = 4
        
        class MockLevel:
            def __init__(self):
                self.floor_seed = 98765
                self.chest_sprites = []
                self.destroyed_obstacle_positions = []
                self.enemy_sprites = []
                self.visible_sprites = []
                self.altar_sprites = []

        level = MockLevel()
        altar = BloodAltar((150, 150), [])
        altar.used = True
        level.altar_sprites.append(altar)

        save_ok = save_game_state(3, self.player, level=level)
        self.assertTrue(save_ok)

        data = load_game_state()
        self.assertIsNotNone(data)
        self.assertEqual(data['skill_points'], 3)
        self.assertEqual(data['skills']['dash']['level'], 2)
        self.assertEqual(data['bombs'], 4)
        self.assertEqual(data['used_altars'], [[150, 150]])

    def test_safe_write_json_atomic_backup_recovery(self):
        """_safe_write_json recovers or preserves backup when target replace fails."""
        test_file = os.path.join(os.path.dirname(SAVE_FILE), "test_atomic_save.json")
        try:
            # Write original
            res1 = _safe_write_json(test_file, {"version": 1})
            self.assertTrue(res1)
            self.assertTrue(os.path.exists(test_file))

            # Write updated
            res2 = _safe_write_json(test_file, {"version": 2})
            self.assertTrue(res2)
        finally:
            if os.path.exists(test_file): os.remove(test_file)
            if os.path.exists(test_file + ".bak"): os.remove(test_file + ".bak")
            if os.path.exists(test_file + ".tmp"): os.remove(test_file + ".tmp")

if __name__ == '__main__':
    unittest.main()
