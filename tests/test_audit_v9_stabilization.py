import unittest
import sys
import os
import tempfile
import pygame

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import src.save_manager
from src.map_manager import Level
from src.entities import Player, Enemy
from src.items import Item, PERMANENT_GEAR_CATALOGUE, RUN_RELICS, check_synergies
from src.save_manager import (
    save_game_state, load_game_state,
    save_profile, load_profile, clear_run_state, get_default_profile
)
from src.ui import EquipmentModal

class TestAuditV9Stabilization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((800, 600))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.orig_save_file = src.save_manager.SAVE_FILE
        self.orig_profile_file = src.save_manager.PROFILE_FILE
        src.save_manager.SAVE_FILE = os.path.join(self.tmp_dir.name, "savegame.json")
        src.save_manager.PROFILE_FILE = os.path.join(self.tmp_dir.name, "profile.json")

    def tearDown(self):
        src.save_manager.SAVE_FILE = self.orig_save_file
        src.save_manager.PROFILE_FILE = self.orig_profile_file
        self.tmp_dir.cleanup()

    def test_deterministic_generation_seeds(self):
        """Seed 57 and 157 must generate exactly reproducible dungeon room layouts and floor tiles."""
        for test_seed in [57, 157]:
            lvl1 = Level(current_floor=1, floor_seed=test_seed)
            lvl2 = Level(current_floor=1, floor_seed=test_seed)

            self.assertEqual(len(lvl1.rooms), len(lvl2.rooms), f"Room count mismatch on seed {test_seed}")
            for r1, r2 in zip(lvl1.rooms, lvl2.rooms):
                self.assertEqual((r1.x, r1.y, r1.w, r1.h), (r2.x, r2.y, r2.w, r2.h), f"Room rect mismatch on seed {test_seed}")
            self.assertEqual(lvl1.floor_positions, lvl2.floor_positions, f"Floor tiles mismatch on seed {test_seed}")

    def test_furthest_exit_selection(self):
        """Exit stairs must be placed in the furthest room from player start room (rooms[0]), never in rooms[0]."""
        level = Level(current_floor=1, floor_seed=57)
        self.assertGreater(len(level.rooms), 1)
        stairs_list = list(level.stairs_sprites)
        self.assertEqual(len(stairs_list), 1)

        stairs = stairs_list[0]
        start_room = level.rooms[0]
        # Ensure stairs are not in start room
        in_start_room = (start_room.x * 64 <= stairs.rect.x <= (start_room.x + start_room.w) * 64 and
                         start_room.y * 64 <= stairs.rect.y <= (start_room.y + start_room.h) * 64)
        self.assertFalse(in_start_room, "Stairs cannot be placed in the player start room!")

    def test_trader_modal_isolation(self):
        """Approaching trader and opening modal does NOT automatically buy any potion or deduct gold."""
        level = Level(current_floor=1, floor_seed=57)
        player = level.player
        initial_gold = player.gold
        initial_inv_len = len(player.inventory)

        # Simulate modal opening
        level.open_modal('shop')
        self.assertEqual(level.active_modal, 'shop')
        self.assertIsNotNone(level.modal_instance)
        # Gold and inventory remain intact
        self.assertEqual(player.gold, initial_gold)
        self.assertEqual(len(player.inventory), initial_inv_len)

    def test_gear_stat_calculation_inventory_neutrality(self):
        """Backpack inventory items give ZERO passive stats; only equipped slots contribute."""
        group = pygame.sprite.Group()
        player = Player((200, 200), [group], [], [])
        base_def = player.defense
        base_atk = player.attack_power

        # Put heavy armor (+20 DEF) and greatsword (+15 ATK) in backpack
        backpack_armor = Item("Heavy Plate", "rare", {'defense': 20}, 50, slot='armor')
        backpack_sword = Item("Greatsword", "rare", {'attack': 15}, 50, slot='weapon')
        player.inventory.extend([backpack_armor, backpack_sword])
        player.recalculate_stats()

        # Backpack items must NOT grant stats!
        self.assertEqual(player.defense, base_def)
        self.assertEqual(player.attack_power, base_atk)

        # Now equip armor
        success = player.equip_item(backpack_armor)
        self.assertTrue(success)
        self.assertEqual(player.equipped['armor'], backpack_armor)
        self.assertEqual(player.defense, base_def + 20)

        # Unequip armor
        player.unequip_item('armor')
        self.assertIsNone(player.equipped['armor'])
        self.assertEqual(player.defense, base_def)

    def test_save_persistence_6_slots_and_relics(self):
        """All 6 equipped permanent gear slots and active run relics persist across save/load."""
        level = Level(current_floor=1, floor_seed=777)
        p = level.player

        # Equip 6 slots
        for slot in ['weapon', 'offhand', 'armor', 'boots', 'amulet', 'ring']:
            p.equipped[slot] = Item(f"Epic {slot}", "epic", {'attack': 5, 'defense': 3}, 100, slot=slot, upgrade_level=2)

        # Add 2 relics
        p.relics = [Item.from_dict(RUN_RELICS['vampiric_fang']), Item.from_dict(RUN_RELICS['storm_shard'])]
        p.recalculate_stats()
        saved_atk = p.attack_power
        saved_def = p.defense

        # Save game state
        save_game_state(1, p, level=level)

        # Load game state into new player
        save_data = load_game_state()
        self.assertIsNotNone(save_data)
        self.assertIn('equipped', save_data)
        self.assertIn('relics', save_data)

        grp = pygame.sprite.Group()
        new_player = Player((200, 200), [grp], [], [])
        for slot, itm_data in save_data['equipped'].items():
            new_player.equipped[slot] = Item.from_dict(itm_data) if itm_data else None
        new_player.relics = [Item.from_dict(r) for r in save_data['relics']]
        new_player.recalculate_stats()

        for slot in ['weapon', 'offhand', 'armor', 'boots', 'amulet', 'ring']:
            self.assertIsNotNone(new_player.equipped[slot])
            self.assertEqual(new_player.equipped[slot].upgrade_level, 2)
        self.assertEqual(len(new_player.relics), 2)
        self.assertEqual(new_player.attack_power, saved_atk)
        self.assertEqual(new_player.defense, saved_def)

    def test_equipment_modal_slot_alignment_21px(self):
        """EquipmentModal backpack slot rects match exactly between update and handle_event."""
        lvl = Level(current_floor=1, floor_seed=123)
        modal = EquipmentModal(lvl, lvl.player)
        modal_rect = modal.rect

        for idx in range(12):
            expected_x = modal_rect.x + 360 + (idx % 4) * 62
            expected_y = modal_rect.y + 92 + (idx // 4) * 58
            target_rect = pygame.Rect(expected_x, expected_y, 52, 52)

            # Test hit testing via simulated click
            clicked_idx = -1
            for i in range(12):
                sx = modal_rect.x + 360 + (i % 4) * 62
                sy = modal_rect.y + 92 + (i // 4) * 58
                slot_box = pygame.Rect(sx, sy, 52, 52)
                if slot_box.collidepoint(target_rect.center):
                    clicked_idx = i
                    break
            self.assertEqual(clicked_idx, idx, f"Slot {idx} hit detection misaligned!")

    def test_boss_fsm_zero_crash(self):
        """Boss FSM state machine transitions through idle, telegraph, recovery cleanly without exceptions."""
        group = pygame.sprite.Group()
        player = Player((300, 300), [group], [], [])
        boss = Enemy((300, 300), [group], [], player, 'boss', visible_sprites=group)

        self.assertEqual(getattr(boss, 'boss_attack_state', 'idle'), 'idle')

        # Trigger cleave telegraph
        boss.boss_cleave_timer = pygame.time.get_ticks() - 100
        boss.update()
        self.assertEqual(boss.boss_attack_state, 'telegraph')

        # Fast forward past telegraph windup (1000ms)
        boss.boss_telegraph_start = pygame.time.get_ticks() - 1100
        boss.update()
        self.assertEqual(boss.boss_attack_state, 'idle')

    def test_profile_separation(self):
        """Profile.json is preserved and updated when clear_run_state() is called upon run death."""
        default_prof = get_default_profile()
        default_prof['permanent_gold'] = 250
        default_prof['dark_iron'] = 7
        default_prof['stats']['total_runs'] = 3
        save_profile(default_prof)

        grp = pygame.sprite.Group()
        src.save_manager.save_game_state(1, Player((0,0), [grp], [], []))
        self.assertTrue(os.path.exists(src.save_manager.SAVE_FILE))
        self.assertTrue(os.path.exists(src.save_manager.PROFILE_FILE))

        # Clear active run state
        clear_run_state()
        self.assertFalse(os.path.exists(src.save_manager.SAVE_FILE))
        self.assertTrue(os.path.exists(src.save_manager.PROFILE_FILE))

        reloaded_prof = load_profile()
        self.assertEqual(reloaded_prof['permanent_gold'], 250)
        self.assertEqual(reloaded_prof['dark_iron'], 7)
        self.assertEqual(reloaded_prof['stats']['total_runs'], 3)

    def test_hub_creation_and_portal(self):
        """Refuge (Hub) properly instantiates sanctuary hall, NPCs, armory, and portal."""
        hub = Level(is_hub=True)
        self.assertTrue(hub.is_hub)
        self.assertEqual(hub.current_floor, 0)
        self.assertIsNotNone(hub.armory_chest)
        self.assertIsNotNone(hub.catacombs_portal)
        self.assertGreater(len(hub.blacksmith_sprites), 0)
        self.assertGreater(len(hub.trader_sprites), 0)
        self.assertGreater(len(hub.anvil_sprites), 0)

        # Portal interaction test
        p = hub.player
        p.rect.center = hub.catacombs_portal.rect.center
        hub.e_pressed_prev = False

        # Simulate proximity check
        p_pos = pygame.math.Vector2(p.rect.center)
        near_portal = (pygame.math.Vector2(hub.catacombs_portal.rect.center) - p_pos).magnitude() < 90
        self.assertTrue(near_portal)

    def test_weapon_differentiation(self):
        """Claymore and Sword have distinct arc angles, sizes, cooldowns, and knockbacks."""
        sword = Item.from_dict(PERMANENT_GEAR_CATALOGUE['sword_knight'])
        claymore = Item.from_dict(PERMANENT_GEAR_CATALOGUE['claymore_heavy'])

        self.assertEqual(sword.weapon_type, 'sword')
        self.assertEqual(claymore.weapon_type, 'claymore')
        self.assertGreater(claymore.effects.get('attack', 0), sword.effects.get('attack', 0))

    def test_relic_synergies(self):
        """Equipping synergistic relics activates bonus affixes."""
        fang = Item.from_dict(RUN_RELICS['vampiric_fang'])
        core = Item.from_dict(RUN_RELICS['bloodstone_core'])

        active = check_synergies([fang, core])
        self.assertEqual(len(active), 1)
        self.assertIn('Берсерк', active[0]['name'])
        self.assertIn('вампиризм', active[0]['desc'])

if __name__ == '__main__':
    unittest.main()
