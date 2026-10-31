import os
import tempfile
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
pygame.init()
pygame.display.set_mode((960, 640))

from src.entities import Player
from src.items import Item
from src.map_manager import Level
from src.save_manager import load_game_state, save_game_state
from src import save_manager
from src.ui import ShopModal, _group_inventory_for_hud


class TestCouncilFunctionalFixes(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_profile = save_manager.PROFILE_FILE
        self.old_save = save_manager.SAVE_FILE
        save_manager.PROFILE_FILE = os.path.join(self.temp_dir.name, 'profile.json')
        save_manager.SAVE_FILE = os.path.join(self.temp_dir.name, 'run.json')
        self.groups = pygame.sprite.Group()
        self.player = Player((100, 100), [self.groups], self.groups, self.groups)
        self.player.gold = 1000

    def tearDown(self):
        save_manager.PROFILE_FILE = self.old_profile
        save_manager.SAVE_FILE = self.old_save
        self.temp_dir.cleanup()

    def test_shop_shard_purchase_updates_single_persistent_wallet(self):
        profile = save_manager.get_default_profile()
        profile['purple_shards'] = 2
        save_manager.save_profile(profile)
        self.player.purple_shards = 1
        shop = ShopModal(None, self.player)
        shop.items = [{'name': 'Shard', 'type': 'shard', 'cost': 125}]

        shop.buy_item(0)

        self.assertEqual(self.player.purple_shards, 3)
        self.assertEqual(save_manager.load_profile()['purple_shards'], 3)

    def test_shop_buffs_are_applied_to_combat_and_survive_recalculation(self):
        shop = ShopModal(None, self.player)
        shop.items = [{'name': 'Attack', 'type': 'buff_atk', 'cost': 75, 'bonus': 6}]
        base_attack = self.player.attack_power
        shop.buy_item(0)
        self.assertEqual(self.player.attack_power, base_attack + 6)
        self.player.recalculate_stats()
        self.assertEqual(self.player.attack_power, base_attack + 6)

        shop.items = [{'name': 'Defense', 'type': 'buff_def', 'cost': 70, 'bonus': 8}]
        shop.buy_item(0)
        self.assertEqual(self.player.defense, 8)
        before = self.player.health
        self.player.take_damage(20)
        self.assertEqual(before - self.player.health, 18)

    def test_hud_stacks_only_items_allowed_by_stack_contract(self):
        same_a = Item('Same Blade', 'common', {'attack': 5}, 20, slot='weapon')
        same_b = Item('Same Blade', 'common', {'attack': 5}, 20, slot='weapon')
        different_roll = Item('Same Blade', 'common', {'attack': 7}, 20, slot='weapon')
        for item in (same_a, same_b, different_roll):
            item.substats = []
        same_a.count = 2
        same_b.count = 1

        groups = _group_inventory_for_hud([same_a, same_b, different_roll])

        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0][1], 3)
        self.assertEqual(groups[1][1], 1)

    def test_lightning_flash_decay_is_update_time_based_and_triggerable(self):
        level = object.__new__(Level)
        level.lightning_flash_alpha = 150.0
        level._lightning_flash_updated_at = 100
        level.dungeon_motes = []
        with patch('src.map_manager.pygame.time.get_ticks', return_value=1000):
            level._update_render_effects()
        self.assertLess(level.lightning_flash_alpha, 1.0)

        with patch('src.map_manager.pygame.time.get_ticks', return_value=1100):
            level.trigger_lightning_flash(120)
        self.assertEqual(level.lightning_flash_alpha, 120.0)
        self.assertEqual(level._lightning_flash_updated_at, 1100)

    def test_motes_advance_in_update_effect_step(self):
        level = object.__new__(Level)
        level.lightning_flash_alpha = 0.0
        level._lightning_flash_updated_at = 100
        mote = Mock()
        level.dungeon_motes = [mote]
        with patch('src.map_manager.pygame.time.get_ticks', return_value=116):
            level._update_render_effects()
        mote.update.assert_called_once_with()

    def test_run_save_keeps_skin_and_shop_bonuses(self):
        self.player.current_skin = 'dark_knight'
        self.player.shop_stat_bonuses = {'attack': 6, 'defense': 8}
        save_game_state(1, self.player)
        data = load_game_state()
        self.assertEqual(data['current_skin'], 'dark_knight')
        self.assertEqual(data['shop_stat_bonuses'], {'attack': 6, 'defense': 8})


if __name__ == '__main__':
    unittest.main()
