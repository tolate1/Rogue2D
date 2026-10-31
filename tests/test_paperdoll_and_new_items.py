import os
import unittest
import pygame

from src.settings import WIDTH, HEIGHT
from src.entities import Player
from src.map_manager import Level
from src.items import ASTRAL_WEAPONS_CATALOGUE, RUN_RELICS, generate_random_item, Item
from src.ui import EquipmentModal, Button, ItemInspectModal
from main import Game


class TestPaperdollAndNewAAAItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((WIDTH, HEIGHT))

    def setUp(self):
        self.level = Level(current_floor=1, floor_seed=42)
        self.player = self.level.player

    def test_new_items_in_catalogues(self):
        """Verify new AAA weapons and relics exist in catalogue and have valid attributes."""
        # Check Astral Weapons
        self.assertIn('warhammer_crusher', ASTRAL_WEAPONS_CATALOGUE)
        self.assertIn('reaper_scythe', ASTRAL_WEAPONS_CATALOGUE)
        self.assertIn('dueling_rapier', ASTRAL_WEAPONS_CATALOGUE)

        warhammer = ASTRAL_WEAPONS_CATALOGUE['warhammer_crusher']
        self.assertEqual(warhammer['slot'], 'weapon')
        self.assertEqual(warhammer['weapon_type'], 'claymore')
        self.assertGreater(warhammer['effects']['attack'], 20)

        scythe = ASTRAL_WEAPONS_CATALOGUE['reaper_scythe']
        self.assertEqual(scythe['slot'], 'weapon')
        self.assertGreater(scythe['effects']['crit_dmg'], 20.0)

        rapier = ASTRAL_WEAPONS_CATALOGUE['dueling_rapier']
        self.assertEqual(rapier['slot'], 'weapon')
        self.assertEqual(rapier['weapon_type'], 'spear')

        # Check Run Relics
        self.assertIn('mimic_fang', RUN_RELICS)
        mimic = RUN_RELICS['mimic_fang']
        self.assertEqual(mimic['slot'], 'relic')
        self.assertGreater(mimic['effects']['gold_multiplier'], 0.3)

    def test_random_item_generation_includes_new_types(self):
        """Verify generate_random_item can produce new item types cleanly."""
        found_types = set()
        for _ in range(200):
            item = generate_random_item()
            self.assertIsInstance(item, Item)
            self.assertIsNotNone(item.name)
            self.assertIsNotNone(item.rarity)
            for key in ['warhammer', 'scythe', 'rapier', 'void_elixir']:
                if key in item.image_path:
                    found_types.add(key)
        self.assertGreater(len(found_types), 0, "generate_random_item should produce newly added item variants")

    def test_all_item_sprites_exist_on_disk(self):
        """Verify all AAA item sprites exist in assets/sprites."""
        required_sprites = [
            'item_sword.png', 'item_wide_blade.png', 'item_warhammer.png',
            'item_scythe.png', 'item_rapier.png', 'item_armor.png',
            'item_shield.png', 'item_boots.png', 'item_amulet.png',
            'item_ring.png', 'item_mimic_fang.png', 'item_void_elixir.png',
            'item_heart.png', 'item_potion.png', 'item_gear.png',
            'item_gloves.png', 'item_magnet.png', 'item_scroll.png', 'item_star.png'
        ]
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for spr in required_sprites:
            full_path = os.path.join(base_dir, 'assets', 'sprites', spr)
            self.assertTrue(os.path.exists(full_path), f"Item sprite missing: {spr}")
            self.assertGreater(os.path.getsize(full_path), 100, f"Sprite file corrupted or empty: {spr}")

    def test_equipment_modal_paperdoll_sockets_and_layout(self):
        """Verify EquipmentModal has the 6 anatomical sockets and 16 backpack slots."""
        modal = EquipmentModal(self.level, self.player)
        required_slots = {'weapon', 'offhand', 'boots', 'armor', 'amulet', 'ring'}
        self.assertEqual(set(modal.slot_rects.keys()), required_slots)

        # Check left sockets (weapon, offhand, boots) vs right sockets (armor, amulet, ring)
        left_x = modal.slot_rects['weapon'].x
        self.assertEqual(modal.slot_rects['offhand'].x, left_x)
        self.assertEqual(modal.slot_rects['boots'].x, left_x)

        right_x = modal.slot_rects['armor'].x
        self.assertGreater(right_x, left_x + 100)
        self.assertEqual(modal.slot_rects['amulet'].x, right_x)
        self.assertEqual(modal.slot_rects['ring'].x, right_x)

        # Check 16 backpack rects
        self.assertEqual(len(modal.backpack_rects), 16)
        # Check 4 relic rects
        self.assertEqual(len(modal.relic_rects), 4)

    def test_equipment_modal_stat_deltas_calculation(self):
        """Verify stat comparison deltas return correct positive and negative deltas."""
        modal = EquipmentModal(self.level, self.player)

        # 1. Weapon comparison
        old_sword = Item("Старый Клинок", "common", {'attack': 10, 'defense': 2}, 50, slot='weapon')
        new_hammer = Item("Молот Громовержца", "epic", {'attack': 24, 'defense': 0, 'crit_dmg': 30.0}, 140, slot='weapon')

        self.player.equip_item(old_sword)
        deltas, equipped = modal._calculate_stat_deltas(new_hammer)
        self.assertEqual(equipped, old_sword)

        delta_map = {d['key']: d['diff'] for d in deltas}
        # Attack should have +14 delta
        self.assertEqual(delta_map.get('attack'), 14)
        # Defense should have -2 delta
        self.assertEqual(delta_map.get('defense'), -2)
        # Crit damage should have +30 delta
        self.assertEqual(delta_map.get('crit_dmg'), 30.0)

        # 2. Unequipped slot comparison (e.g. amulet when none equipped)
        self.player.equipped['amulet'] = None
        new_amulet = Item("Амулет Теней", "rare", {'crit_rate': 8.0, 'health': 25}, 80, slot='amulet')
        deltas_amulet, eq_amulet = modal._calculate_stat_deltas(new_amulet)
        self.assertIsNone(eq_amulet)
        delta_map_amulet = {d['key']: d['diff'] for d in deltas_amulet}
        self.assertEqual(delta_map_amulet.get('crit_rate'), 8.0)
        self.assertEqual(delta_map_amulet.get('health'), 25)

    def test_equipment_modal_hover_tracking_and_draw(self):
        """Verify EquipmentModal tracks hovered item and renders without errors."""
        modal = EquipmentModal(self.level, self.player)
        sword = Item("Меч Паладина", "rare", {'attack': 16}, 90, slot='weapon')
        self.player.equip_item(sword)

        # Hover over weapon slot
        weapon_rect = modal.slot_rects['weapon']
        modal.update(weapon_rect.center)
        self.assertEqual(modal.hovered_item, sword)
        self.assertEqual(modal.hovered_source, 'equipped')

        # Hover over first backpack slot
        armor = Item("Латный Доспех", "epic", {'defense': 12}, 110, slot='armor')
        self.player.inventory.append(armor)
        backpack_0 = modal.backpack_rects[0]
        modal.update(backpack_0.center)
        self.assertEqual(modal.hovered_item, armor)
        self.assertEqual(modal.hovered_source, 'inventory')

        # Draw call should execute cleanly with hover tooltip and radar
        test_surf = pygame.Surface((WIDTH, HEIGHT))
        modal.draw(test_surf)

    def test_settings_tabbed_navigation(self):
        """Verify Settings tabs (video, audio, game) switch state and generate correct controls."""
        game = Game()
        game.set_state('settings')

        # 1. Default tab is video
        self.assertEqual(game.settings_tab, 'video')
        video_buttons = [btn.text for btn in game.ui_buttons]
        self.assertTrue(any("Полноэкранный" in t or "Оконный" in t for t in video_buttons))
        self.assertTrue(any("НАЗАД" in t for t in video_buttons))

        # 2. Switch to audio tab
        game.settings_tab = 'audio'
        game.set_state('settings')
        audio_buttons = [btn.text for btn in game.ui_buttons]
        # Audio tab should have tab navigation buttons + back button + +/- sliders
        self.assertIn("1. ВИДЕО И ЭКРАН", audio_buttons)
        self.assertIn("2. ЗВУК И МУЗЫКА", audio_buttons)
        self.assertIn("3. УПРАВЛЕНИЕ", audio_buttons)
        self.assertIn("НАЗАД", audio_buttons)

        # 3. Switch to game tab
        game.settings_tab = 'game'
        game.set_state('settings')
        game_buttons = [btn.text for btn in game.ui_buttons]
        self.assertIn("3. УПРАВЛЕНИЕ", game_buttons)

        # Test draw execution for all 3 tabs
        test_surf = pygame.Surface((WIDTH, HEIGHT))
        for tab in ['video', 'audio', 'game']:
            game.settings_tab = tab
            game.draw()

    def test_button_brass_chevrons_and_click_offset(self):
        """Verify button renders brass chevrons on hover and updates mechanical click offset."""
        clicked = []
        btn = Button("ТЕСТ КНОПКА", (100, 100), 200, 40, lambda: clicked.append(True))
        surf = pygame.Surface((400, 300))

        # 1. Initial idle draw
        btn.draw(surf)
        self.assertEqual(btn.click_offset_y, 0.0)

        # 2. Hover draw
        btn.check_hover((150, 120))
        self.assertTrue(btn.hovered)
        btn.draw(surf)

        # 3. Click execution
        event_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (150, 120)})
        btn.check_click([event_click])
        self.assertEqual(len(clicked), 1)
        self.assertEqual(btn.click_offset_y, 2.0)
        self.assertGreater(btn.pressed_until, pygame.time.get_ticks())


if __name__ == '__main__':
    unittest.main()
