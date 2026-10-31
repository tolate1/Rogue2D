import unittest
import os
import shutil
import tempfile
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1280, 720))

from src.items import Item, Gold
from src.entities import Player
from src.map_manager import Level
from src.ui import ShopModal, BlacksmithModal, ItemInspectModal, EquipmentModal
from src import save_manager


class TestInventoryShopForgeInteractions(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_profile = save_manager.PROFILE_FILE
        self.orig_save = save_manager.SAVE_FILE
        save_manager.PROFILE_FILE = os.path.join(self.temp_dir, 'profile.json')
        save_manager.SAVE_FILE = os.path.join(self.temp_dir, 'savegame.json')

        # Clean slate level and player
        self.level = Level(current_floor=1)
        self.player = self.level.player
        self.player.inventory = []
        self.player.gold = 300

    def tearDown(self):
        save_manager.PROFILE_FILE = self.orig_profile
        save_manager.SAVE_FILE = self.orig_save
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_potion_stacking_and_consuming_single(self):
        """Drinking one potion from a stack of 3 should decrement count to 2, not wipe the stack."""
        pot1 = Item("Health Potion", "common", {'heal': 25}, 10, 'assets/sprites/item_heart.png', slot='consumable', count=1)
        pot2 = Item("Health Potion", "common", {'heal': 25}, 10, 'assets/sprites/item_heart.png', slot='consumable', count=2)

        self.player.add_item(pot1)
        self.player.add_item(pot2)
        self.assertEqual(len(self.player.inventory), 1)
        self.assertEqual(self.player.inventory[0].count, 3)

        # Damage player and drink 1 potion
        self.player.health = 50.0
        success = self.player.consume_item(self.player.inventory[0])
        self.assertTrue(success)
        self.assertEqual(self.player.health, 75.0)
        self.assertEqual(len(self.player.inventory), 1)
        self.assertEqual(self.player.inventory[0].count, 2)

    def test_inspect_modal_consumes_specific_potion(self):
        """ItemInspectModal.action_consume calls player.consume_item on the exact inspected item."""
        small_pot = Item("Малое зелье", "common", {'heal': 10}, 10, 'assets/sprites/item_heart.png', slot='consumable', count=1)
        big_pot = Item("Большое зелье", "rare", {'heal': 50}, 30, 'assets/sprites/item_potion.png', slot='consumable', count=1)
        self.player.inventory = [small_pot, big_pot]

        self.player.health = 30.0
        inspect = ItemInspectModal(None, big_pot, self.player, self.level, source='inventory')
        inspect.action_consume()

        self.assertEqual(self.player.health, 80.0)
        self.assertNotIn(big_pot, self.player.inventory)
        self.assertIn(small_pot, self.player.inventory)

    def test_shop_all_purchases_mark_sold(self):
        """All item categories in ShopModal (buffs, gear, shards, bombs) must set sold=True upon purchase."""
        shop = ShopModal(self.level, self.player)
        self.player.gold = 2000

        for i, itm in enumerate(shop.items):
            cost = itm['cost']
            pre_gold = self.player.gold
            shop.buy_item(i)
            self.assertTrue(itm.get('sold', False), f"Item {itm['name']} (type {itm['type']}) must be marked as sold!")
            self.assertEqual(self.player.gold, pre_gold - cost)

            # Try to buy again - must be rejected
            pre_gold2 = self.player.gold
            shop.buy_item(i)
            self.assertEqual(self.player.gold, pre_gold2, "Sold out item must NOT be purchasable again!")

    def test_hub_armory_loading_and_saving(self):
        """Hub must load items from prof['armory'] into inventory and save them upon equip/sync."""
        prof = save_manager.get_default_profile()
        prof['permanent_gold'] = 150
        prof['armory'] = [
            {'name': 'Трофейный Клинок', 'rarity': 'rare', 'effects': {'attack': 12}, 'value': 80,
             'slot': 'weapon', 'upgrade_level': 2, 'max_level': 10, 'count': 1}
        ]
        save_manager.save_profile(prof)

        hub = Level(is_hub=True)
        self.assertTrue(hub.is_hub)
        self.assertEqual(len(hub.player.inventory), 1)
        self.assertEqual(hub.player.inventory[0].name, 'Трофейный Клинок')
        self.assertEqual(hub.player.inventory[0].upgrade_level, 2)

        # Equip the weapon in the hub and sync
        eq_modal = EquipmentModal(hub, hub.player)
        hub.player.equip_item(hub.player.inventory[0])
        eq_modal._sync_hub_profile()

        # Check saved profile has it equipped and armory updated
        saved_prof = save_manager.load_profile()
        self.assertIsNotNone(saved_prof['equipped']['weapon'])
        self.assertEqual(saved_prof['equipped']['weapon']['name'], 'Трофейный Клинок')

    def test_recalculate_stats_bonus_energy(self):
        """Equipped items and relics giving energy must increase player max_energy."""
        base_energy = 60
        ring = Item("Кольцо Упорства", "common", {'energy': 15}, 30, slot='ring')
        self.player.equipped['ring'] = ring
        self.player.recalculate_stats()

        self.assertEqual(self.player.stats['energy'], base_energy + 15)
        self.assertEqual(self.player.max_energy, base_energy + 15)

    def test_gold_magnet_reads_equipped_items(self):
        """Gold pickup should detect magnet effects from equipped items as well as inventory."""
        magnet_acc = Item("Кольцо Притяжения", "rare", {'magnet': 2}, 50, slot='accessory')
        self.player.equipped['accessory'] = magnet_acc
        self.player.inventory = []

        gold = Gold((self.player.rect.centerx + 80, self.player.rect.centery), [], 10, self.player)
        # Without magnet, radius is 50 -> 80 is out of reach
        # With magnet:2, radius is 50 + 2*35 = 120 -> 80 is within pickup pull range
        pre_x = gold.rect.x
        gold.update()
        self.assertNotEqual(gold.rect.x, pre_x, "Gold should be magnetically pulled towards player!")

    def test_blacksmith_hub_permanent_gold_deduction(self):
        """Sharpening or upgrading at Blacksmith in Hub must deduct and persist permanent_gold."""
        prof = save_manager.get_default_profile()
        prof['permanent_gold'] = 100
        save_manager.save_profile(prof)

        hub = Level(is_hub=True)
        hub.player.gold = 100
        bs = BlacksmithModal(hub, hub.player)
        bs.upgrade_selected_item()

        self.assertEqual(hub.player.gold, 60)
        saved_prof = save_manager.load_profile()
        self.assertEqual(saved_prof['permanent_gold'], 60, "Permanent gold must be saved in profile when forging in hub!")


if __name__ == '__main__':
    unittest.main()
