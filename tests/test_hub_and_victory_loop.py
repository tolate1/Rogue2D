import os
import unittest
import pygame
from src.settings import WIDTH, HEIGHT
from src.save_manager import (
    load_profile, save_profile, get_default_profile,
    load_game_state, save_game_state, clear_run_state, has_save,
    PROFILE_FILE, SAVE_FILE
)
from src.items import Item, PERMANENT_GEAR_CATALOGUE, RUN_RELICS, check_synergies
from src.map_manager import Level
from src.entities import Player, Weapon
from src.ui import BlacksmithModal, EquipmentModal

class TestHubAndVictoryLoop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((WIDTH, HEIGHT))

    def setUp(self):
        # Create a fresh isolated profile
        self.orig_profile = load_profile() if os.path.exists(PROFILE_FILE) else None
        p = get_default_profile()
        p['permanent_gold'] = 100
        p['dark_iron'] = 5
        save_profile(p)
        clear_run_state()

    def tearDown(self):
        clear_run_state()
        if self.orig_profile:
            save_profile(self.orig_profile)
        elif os.path.exists(PROFILE_FILE):
            os.remove(PROFILE_FILE)

    def test_hub_structure_and_interactions(self):
        """Refuge Hub contains trader, blacksmith, armory chest and catacombs portal."""
        level = Level(is_hub=True)
        self.assertTrue(level.is_hub)
        self.assertEqual(level.current_floor, 0)
        self.assertGreater(len(level.trader_sprites), 0)
        self.assertGreater(len(level.blacksmith_sprites), 0)
        self.assertTrue(hasattr(level, 'armory_chest'))
        self.assertTrue(hasattr(level, 'catacombs_portal'))

    def test_two_distinct_weapons(self):
        """Verifies Sword (fast, 90 deg) and Claymore (slow, 160 deg) are distinct."""
        sword_data = PERMANENT_GEAR_CATALOGUE['sword_knight']
        claymore_data = PERMANENT_GEAR_CATALOGUE['claymore_heavy']

        sword = Item.from_dict(sword_data)
        claymore = Item.from_dict(claymore_data)

        self.assertEqual(sword.weapon_type, 'sword')
        self.assertEqual(claymore.weapon_type, 'claymore')
        self.assertGreater(claymore.effects.get('attack', 0), sword.effects.get('attack', 0))

        v_group = pygame.sprite.Group()
        o_group = pygame.sprite.Group()
        e_group = pygame.sprite.Group()
        player = Player((100, 100), [v_group], o_group, e_group)

        # Equip Sword
        player.equipped['weapon'] = sword
        player.recalculate_stats()
        player.attack()
        self.assertLessEqual(player.attack_cooldown, 450)
        weapons_sword = [s for s in v_group if isinstance(s, Weapon)]
        self.assertTrue(len(weapons_sword) > 0)
        self.assertEqual(weapons_sword[-1].arc_degrees, 90.0)

        # Reset attack cooldown and equip Claymore
        player.can_attack = True
        player.attack_time = 0
        player.equipped['weapon'] = claymore
        player.recalculate_stats()
        player.attack()
        self.assertGreaterEqual(player.attack_cooldown, 650)
        weapons_claymore = [s for s in v_group if isinstance(s, Weapon)]
        self.assertEqual(weapons_claymore[-1].arc_degrees, 160.0)

    def test_run_relics_and_synergies(self):
        """Verifies 4 temporary run relics and 2 synergies."""
        self.assertIn('vampiric_fang', RUN_RELICS)
        self.assertIn('bloodstone_core', RUN_RELICS)
        self.assertIn('gale_feather', RUN_RELICS)
        self.assertIn('storm_shard', RUN_RELICS)

        # Synergy 1: Berserk
        relics_berserk = [
            Item.from_dict(RUN_RELICS['vampiric_fang']),
            Item.from_dict(RUN_RELICS['bloodstone_core'])
        ]
        synergies_1 = check_synergies(relics_berserk)
        self.assertEqual(len(synergies_1), 1)

        # Synergy 2: Stormbringer
        relics_storm = [
            Item.from_dict(RUN_RELICS['gale_feather']),
            Item.from_dict(RUN_RELICS['storm_shard'])
        ]
        synergies_2 = check_synergies(relics_storm)
        self.assertEqual(len(synergies_2), 1)

    def test_blacksmith_hub_forge_and_profile_sync(self):
        """Blacksmith in Hub upgrades item and saves changes directly to profile."""
        from main import Game
        game = Game()
        game.start_hub()
        p = game.level.player

        # Initial weapon attack
        initial_atk = p.equipped['weapon'].effects.get('attack', 0)
        modal = BlacksmithModal(game.level, p)

        # Upgrade sharpen
        modal.sharpen_weapon()
        self.assertEqual(p.equipped['weapon'].effects['attack'], initial_atk + 3)
        self.assertEqual(p.equipped['weapon'].upgrade_level, 1)

        # Verify profile updated
        prof = load_profile()
        self.assertEqual(prof['equipped']['weapon']['upgrade_level'], 1)
        self.assertEqual(prof['equipped']['weapon']['effects']['attack'], initial_atk + 3)

    def test_chapter_victory_end_to_end(self):
        """Floor 2 boss defeat + exit -> victory state -> dark iron + gold credit -> return to hub."""
        from main import Game
        game = Game()
        game.start_dungeon_run()
        game.level.current_floor = 2
        game.level.player.gold = 75
        game.level.player.kills = 12

        # Trigger chapter victory flag
        game.level.chapter_victory = True
        game.update()

        self.assertEqual(game.state, 'victory')
        self.assertFalse(has_save())

        # Check profile rewarded
        prof = load_profile()
        self.assertEqual(prof['permanent_gold'], 175) # 100 + 75
        self.assertEqual(prof['dark_iron'], 8)       # 5 + 3
        self.assertIn('catacombs_2', prof['unlocked_chapters'])

        # Check victory buttons
        btn_labels = [b.text_str for b in game.ui_buttons]
        self.assertTrue(any("В УБЕЖИЩЕ" in l for l in btn_labels))
        self.assertTrue(any("В ГЛАВНОЕ МЕНЮ" in l for l in btn_labels))

        # Click "В УБЕЖИЩЕ"
        hub_btn = next(b for b in game.ui_buttons if "В УБЕЖИЩЕ" in b.text_str)
        hub_btn.callback()
        self.assertEqual(game.state, 'hub')
        self.assertTrue(game.level.is_hub)

if __name__ == '__main__':
    unittest.main()
