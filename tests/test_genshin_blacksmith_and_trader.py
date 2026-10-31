import os
import unittest
import pygame

# Headless display for automated test environments
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((960, 640))

from src.items import Item, generate_default_substats, create_astral_weapon, ASTRAL_WEAPONS_CATALOGUE
from src.entities import Player
from src.save_manager import get_default_profile, load_profile, save_profile
from src.ui import ShopModal, BlacksmithModal
from src.map_manager import Level
from main import Game

class TestGenshinBlacksmithAndTrader(unittest.TestCase):
    def setUp(self):
        self.group = pygame.sprite.Group()
        self.player = Player((100, 100), [self.group], self.group, self.group)
        self._orig_profile = load_profile()

    def tearDown(self):
        if hasattr(self, '_orig_profile'):
            save_profile(self._orig_profile)

    def test_genshin_resonance_4_substats_generation_and_upgrade(self):
        """Verifies gear has 4 distinct substats and upgrades main stat + rolls 1 substat."""
        # 1. Generation
        sword = Item("Стальной Меч", "rare", {'attack': 10}, 50, slot='weapon', weapon_type='sword')
        self.assertEqual(len(sword.substats), 4)
        sub_ids = [s['id'] for s in sword.substats]
        self.assertEqual(len(set(sub_ids)), 4, "All 4 substats must be unique")
        self.assertNotIn(sword.main_stat['id'], sub_ids, "Main stat must not appear in substats")

        # Initial level 0 state
        self.assertEqual(sword.upgrade_level, 0)
        self.assertEqual(sword.main_stat['value'], 10)
        for s in sword.substats:
            self.assertEqual(s.get('rolls', 0), 0)

        # 2. Upgrade at Blacksmith bench
        init_main = sword.main_stat['value']
        success, msg = sword.upgrade()
        self.assertTrue(success)
        self.assertEqual(sword.upgrade_level, 1)
        self.assertGreater(sword.main_stat['value'], init_main)
        total_rolls = sum(s.get('rolls', 0) for s in sword.substats)
        self.assertEqual(total_rolls, 1, "Exactly 1 substat should roll upon upgrade")
        self.assertIn("+1", sword.name)

        # Upgrade again to level 2
        success2, msg2 = sword.upgrade()
        self.assertTrue(success2)
        self.assertEqual(sword.upgrade_level, 2)
        total_rolls2 = sum(s.get('rolls', 0) for s in sword.substats)
        self.assertEqual(total_rolls2, 2, "2 total rolls after 2 upgrades")

    def test_astral_weapons_and_purple_shards_crafting(self):
        """Astral weapons require 10 purple shards and come with 4 pre-rolled epic substats."""
        self.player.purple_shards = 15
        prof = load_profile()
        prof['purple_shards'] = 15
        save_profile(prof)

        # Forge Astral Blade
        level = Level(current_floor=1, floor_seed=123)
        modal = BlacksmithModal(level, self.player)
        modal.current_tab = 1 # Astral Forge tab

        modal.forge_astral_weapon('astral_blade')
        self.assertEqual(self.player.purple_shards, 5, "Crafting should consume 10 purple shards")
        equipped_wpn = self.player.equipped.get('weapon')
        self.assertIsNotNone(equipped_wpn)
        self.assertEqual(equipped_wpn.rarity, 'epic')
        self.assertEqual(len(equipped_wpn.substats), 4)
        for sub in equipped_wpn.substats:
            self.assertGreater(sub['value'], 0, "Astral weapon substats are pre-tuned")

    def test_trader_dialogue_and_shop_modal(self):
        """Trader UI stands on the right and greets with 'Хочешь что-то купить?'."""
        level = Level(current_floor=1, floor_seed=456)
        shop = ShopModal(level, self.player)

        # Initial speech bubble
        self.assertIn("Хочешь что-то купить?", shop.speech_text)
        self.assertGreaterEqual(len(shop.items), 4, "Shop sells at least 4 items")

        # Attempt purchase with 0 gold
        self.player.gold = 0
        shop.buy_item(1)
        self.assertIn("золота", shop.speech_text.lower())

        # Give gold and buy successfully (e.g. item 1 = Paladin blade)
        self.player.gold = 500
        shop.buy_item(1)
        self.assertEqual(self.player.equipped['weapon'].name, "Клинок Паладина")
        self.assertIn("Острый клинок", shop.speech_text)

    def test_separate_dungeon_rooms_for_merchant_and_blacksmith(self):
        """Level generates merchant in Room 1 and Blacksmith in Room 2."""
        level = Level(current_floor=1, floor_seed=999)
        self.assertFalse(level.is_hub)
        self.assertGreaterEqual(len(level.rooms), 4)

        # Room 1: Merchant NPC present
        self.assertGreaterEqual(len(level.trader_sprites), 1, "Dungeon Room 1 must contain Trader sprite")

        # Room 2: Blacksmith NPC present
        self.assertGreaterEqual(len(level.anvil_sprites), 1, "Dungeon Room 2 must contain Anvil/Blacksmith sprite")

    def test_main_menu_hero_inspection_toggle(self):
        """Clicking on the player pedestal in Main Menu toggles equipment inspection."""
        game = Game()
        self.assertEqual(game.state, 'menu')
        self.assertFalse(game.menu_show_gear)

        # Toggle gear inspection
        game.toggle_menu_gear()
        self.assertTrue(game.menu_show_gear)

        # Toggle off
        game.toggle_menu_gear()
        self.assertFalse(game.menu_show_gear)

    def test_ascension_good_ending_and_shard_rewards(self):
        """Ascension (Good ending) awards +25 Purple Shards and increments total_ascensions."""
        game = Game()
        game.start_dungeon_run()
        game.level.current_floor = 2
        game.level.player.gold = 50
        game.level.player.kills = 16

        # Trigger victory
        game.level.chapter_victory = True
        game.update()
        self.assertEqual(game.state, 'victory')

        prof = load_profile()
        self.assertGreaterEqual(prof.get('purple_shards', 0), 25)
        self.assertGreaterEqual(prof.get('total_ascensions', 0), 1)

if __name__ == '__main__':
    unittest.main()
