import os
import unittest
import pygame

# Initialize headless pygame for testing
os.environ['SDL_VIDEODRIVER'] = 'dummy'
pygame.init()
pygame.display.set_mode((1280, 720))

from src.items import Item, PERMANENT_GEAR_CATALOGUE, RUN_RELICS, generate_relic
from src.entities import Player, Enemy, Weapon, EnemyProjectile
from src.map_manager import Level
from src.ui import EquipmentModal, ItemInspectModal, ShopModal, BlacksmithModal

class MockLevel:
    def __init__(self):
        self.active_modal = None
        self.modal_instance = None
        self.is_hub = False
        self.visible_sprites = pygame.sprite.Group()
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

    def open_modal(self, modal_type):
        self.active_modal = modal_type
        if modal_type == 'blacksmith':
            self.modal_instance = BlacksmithModal(self, getattr(self, 'player', None))
        elif modal_type == 'shop':
            self.modal_instance = ShopModal(self, getattr(self, 'player', None))
        elif modal_type == 'equipment':
            self.modal_instance = EquipmentModal(self, getattr(self, 'player', None))

class TestNewContentAndInspection(unittest.TestCase):
    def setUp(self):
        self.level = MockLevel()
        self.player = Player((200, 200), [self.level.visible_sprites], self.level.obstacle_sprites, self.level.enemy_sprites)
        self.level.player = self.player

    def test_new_weapon_spear_and_daggers(self):
        spear = Item.from_dict(PERMANENT_GEAR_CATALOGUE['spear_abyss'])
        self.assertEqual(spear.slot, 'weapon')
        self.assertEqual(spear.weapon_type, 'spear')
        self.assertEqual(spear.main_stat['id'], 'attack')
        self.assertGreater(spear.main_stat['value'], 0)

        daggers = Item.from_dict(PERMANENT_GEAR_CATALOGUE['daggers_shadow'])
        self.assertEqual(daggers.slot, 'weapon')
        self.assertEqual(daggers.weapon_type, 'daggers')
        self.assertEqual(daggers.main_stat['id'], 'attack')

    def test_new_relics_catalogue(self):
        self.assertIn('vampiric_fang', RUN_RELICS)
        self.assertIn('zephyr_feather', RUN_RELICS)
        self.assertIn('midas_crown', RUN_RELICS)
        self.assertIn('obsidian_heart', RUN_RELICS)

        fang = generate_relic('vampiric_fang')
        self.assertEqual(fang.slot, 'relic')
        self.assertIn('vampirism', fang.effects)

        feather = generate_relic('zephyr_feather')
        self.assertEqual(feather.slot, 'relic')
        self.assertIn('dash_distance_boost', feather.effects)

        crown = generate_relic('midas_crown')
        self.assertEqual(crown.slot, 'relic')
        self.assertIn('gold_multiplier', crown.effects)

        heart = generate_relic('obsidian_heart')
        self.assertEqual(heart.slot, 'relic')
        self.assertIn('death_defiance', heart.effects)

    def test_obsidian_heart_death_defiance(self):
        heart = generate_relic('obsidian_heart')
        self.player.relics = [heart]
        self.player.health = 10

        # Fatal blow
        survived = self.player.take_damage(50)
        self.assertTrue(survived)
        self.assertFalse(self.player.is_dead)
        self.assertGreater(self.player.health, 0)
        self.assertTrue(self.player.is_shielded)
        self.assertTrue(getattr(heart, 'used_this_floor', False))

        # Second fatal blow after used: now dies
        self.player.is_shielded = False
        self.player.take_damage(200)
        self.assertTrue(self.player.is_dead)
        self.assertEqual(self.player.health, 0)

    def test_item_inspect_modal_equipped_item(self):
        wpn = Item.from_dict(PERMANENT_GEAR_CATALOGUE['spear_abyss'])
        self.player.equip_item(wpn)

        eq_modal = EquipmentModal(self.level, self.player)
        inspect = ItemInspectModal(eq_modal, wpn, self.player, self.level, source='equipped', slot_name='weapon')

        # Check action button is "СНЯТЬ"
        self.assertIn("СНЯТЬ", inspect.buttons[0].text)

        # Unequip action via inspect modal
        inspect.action_unequip()
        self.assertIsNone(self.player.equipped.get('weapon'))
        self.assertTrue(inspect.closed)

    def test_item_inspect_modal_inventory_item(self):
        daggers = Item.from_dict(PERMANENT_GEAR_CATALOGUE['daggers_shadow'])
        self.player.inventory.append(daggers)

        eq_modal = EquipmentModal(self.level, self.player)
        inspect = ItemInspectModal(eq_modal, daggers, self.player, self.level, source='inventory')

        # Check action button is "НАДЕТЬ"
        self.assertIn("НАДЕТЬ", inspect.buttons[0].text)

        # Equip action via inspect modal
        inspect.action_equip()
        self.assertEqual(self.player.equipped.get('weapon'), daggers)
        self.assertTrue(inspect.closed)

    def test_item_inspect_modal_close_keys_and_backdrop(self):
        daggers = Item.from_dict(PERMANENT_GEAR_CATALOGUE['daggers_shadow'])
        eq_modal = EquipmentModal(self.level, self.player)

        # Close via Escape
        inspect = ItemInspectModal(eq_modal, daggers, self.player, self.level)
        event_esc = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE})
        inspect.handle_event(event_esc)
        self.assertTrue(inspect.closed)

        # Close via I key
        inspect = ItemInspectModal(eq_modal, daggers, self.player, self.level)
        event_i = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_i})
        inspect.handle_event(event_i)
        self.assertTrue(inspect.closed)

        # Close via Backdrop click (click at 10, 10 outside modal)
        inspect = ItemInspectModal(eq_modal, daggers, self.player, self.level)
        event_backdrop = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (10, 10)})
        inspect.handle_event(event_backdrop)
        self.assertTrue(inspect.closed)

        # Close via [X] button click
        inspect = ItemInspectModal(eq_modal, daggers, self.player, self.level)
        event_x = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': inspect.close_x_rect.center})
        inspect.handle_event(event_x)
        self.assertTrue(inspect.closed)

    def test_equipment_modal_universal_close(self):
        eq_modal = EquipmentModal(self.level, self.player)
        self.level.active_modal = 'equipment'

        # Close on Backdrop click (click outside modal at 5, 5)
        event_click_out = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (5, 5)})
        eq_modal.handle_event(event_click_out)
        self.assertIsNone(self.level.active_modal)

        # Close on [X] button
        self.level.active_modal = 'equipment'
        event_x = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': eq_modal.close_x_rect.center})
        eq_modal.handle_event(event_x)
        self.assertIsNone(self.level.active_modal)

        # Close on 'C' key
        self.level.active_modal = 'equipment'
        event_c = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_c})
        eq_modal.handle_event(event_c)
        self.assertIsNone(self.level.active_modal)

    def test_shop_and_blacksmith_universal_close(self):
        # Shop modal universal close
        shop = ShopModal(self.level, self.player)
        self.level.active_modal = 'shop'

        event_out = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (5, 5)})
        shop.handle_event(event_out)
        self.assertIsNone(self.level.active_modal)

        self.level.active_modal = 'shop'
        event_i = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_i})
        shop.handle_event(event_i)
        self.assertIsNone(self.level.active_modal)

        # Blacksmith modal universal close
        bs = BlacksmithModal(self.level, self.player)
        self.level.active_modal = 'blacksmith'

        event_out2 = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (5, 5)})
        bs.handle_event(event_out2)
        self.assertIsNone(self.level.active_modal)

        self.level.active_modal = 'blacksmith'
        event_tab = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_TAB})
        bs.handle_event(event_tab)
        self.assertIsNone(self.level.active_modal)

    def test_new_enemies_creation_and_stats(self):
        vis = [self.level.visible_sprites]
        obs = self.level.obstacle_sprites

        necro = Enemy((100, 100), vis, obs, self.player, 'necromancer', visible_sprites=self.level.visible_sprites)
        self.assertEqual(necro.max_hp, 70)
        self.assertEqual(necro.hp, 70)

        bomber = Enemy((100, 100), vis, obs, self.player, 'spore_bomber', visible_sprites=self.level.visible_sprites)
        self.assertEqual(bomber.max_hp, 35)
        self.assertEqual(bomber.speed, 3.6)

        slime = Enemy((100, 100), vis, obs, self.player, 'toxic_slime', visible_sprites=self.level.visible_sprites)
        self.assertEqual(slime.max_hp, 60)

        phantom = Enemy((100, 100), vis, obs, self.player, 'phantom', visible_sprites=self.level.visible_sprites)
        self.assertEqual(phantom.max_hp, 45)

        boss_necro = Enemy((100, 100), vis, obs, self.player, 'boss_necro_lord', visible_sprites=self.level.visible_sprites)
        self.assertEqual(boss_necro.max_hp, 380)
        self.assertTrue(boss_necro.is_boss)

    def test_spore_bomber_detonation(self):
        vis = [self.level.visible_sprites]
        obs = self.level.obstacle_sprites
        bomber = Enemy((220, 200), vis, obs, self.player, 'spore_bomber', visible_sprites=self.level.visible_sprites)

        # Within 65px: triggers detonation state
        bomber.move_towards_player()
        self.assertTrue(getattr(bomber, 'detonating', False))

        # Advance detonation timer past 1000ms
        bomber.detonate_start -= 1100
        p_hp_before = self.player.health
        bomber.move_towards_player()
        self.assertFalse(bomber.alive())
        self.assertLess(self.player.health, p_hp_before)

if __name__ == '__main__':
    unittest.main()
