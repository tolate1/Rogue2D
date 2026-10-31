import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pygame

# Ensure headless pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1280, 720))

from src.items import Item, item_sort_key, sort_items_by_rarity
from src.entities import Player
from src.ui import EquipmentModal, BlacksmithModal, ShopModal, ItemInspectModal


class MockLevel:
    def __init__(self, player):
        self.player = player
        self.active_modal = None
        self.modal_instance = None
        self.is_hub = False

    def open_modal(self, modal_name):
        if modal_name == 'blacksmith':
            self.modal_instance = BlacksmithModal(self, self.player)
            self.active_modal = self.modal_instance
        elif modal_name == 'equipment':
            self.modal_instance = EquipmentModal(self, self.player)
            self.active_modal = self.modal_instance
        elif modal_name == 'shop':
            self.modal_instance = ShopModal(self, self.player)
            self.active_modal = self.modal_instance


class TestInventoryStackingPaginationAndSorting(unittest.TestCase):
    def setUp(self):
        grp = pygame.sprite.Group()
        self.player = Player((100, 100), [grp], grp, grp)
        self.player.inventory = []
        self.player.gold = 500
        self.level = MockLevel(self.player)

    def test_item_can_stack_with(self):
        pot1 = Item("Зелье лечения", "common", {'heal': 50}, 20, slot='consumable')
        pot2 = Item("Зелье лечения", "common", {'heal': 50}, 20, slot='consumable')
        sword1 = Item("Железный меч", "common", {'attack': 5}, 30, slot='weapon', upgrade_level=0)
        sword2 = Item("Железный меч", "common", {'attack': 5}, 30, slot='weapon', upgrade_level=0)
        sword_up = Item("Железный меч +1", "common", {'attack': 7}, 30, slot='weapon', upgrade_level=1)

        self.assertTrue(pot1.can_stack_with(pot2))
        self.assertTrue(sword1.can_stack_with(sword2))
        self.assertFalse(sword1.can_stack_with(sword_up))
        self.assertFalse(pot1.can_stack_with(sword1))

    def test_player_add_item_and_stacking(self):
        pot1 = Item("Зелье лечения", "common", {'heal': 50}, 20, slot='consumable', count=1)
        pot2 = Item("Зелье лечения", "common", {'heal': 50}, 20, slot='consumable', count=2)
        self.player.add_item(pot1)
        self.assertEqual(len(self.player.inventory), 1)
        self.assertEqual(self.player.inventory[0].count, 1)

        self.player.add_item(pot2)
        self.assertEqual(len(self.player.inventory), 1)
        self.assertEqual(self.player.inventory[0].count, 3)

    def test_rarity_sorting_order(self):
        common = Item("Деревянный щит", "common", {'defense': 2}, 15, slot='offhand')
        rare = Item("Лазурный лук", "rare", {'attack': 8}, 40, slot='weapon')
        epic = Item("Огненный клинок", "epic", {'attack': 15}, 80, slot='weapon')
        legendary = Item("Корона Бездны", "legendary", {'attack': 30}, 200, slot='relic')

        items = [common, legendary, rare, epic]
        sorted_items = sort_items_by_rarity(items)

        self.assertEqual(sorted_items[0].rarity, 'legendary')
        self.assertEqual(sorted_items[1].rarity, 'epic')
        self.assertEqual(sorted_items[2].rarity, 'rare')
        self.assertEqual(sorted_items[3].rarity, 'common')

    def test_inventory_consolidation(self):
        self.player.inventory = [
            Item("Зелье лечения", "common", {'heal': 50}, 20, slot='consumable', count=1),
            Item("Клинок Тени", "epic", {'attack': 18}, 90, slot='weapon', count=1),
            Item("Зелье лечения", "common", {'heal': 50}, 20, slot='consumable', count=3),
            Item("Сфера Пустоты", "legendary", {'attack': 35}, 250, slot='relic', count=1),
        ]
        self.player.consolidate_inventory()

        # Should merge the two potion entries and sort legendary > epic > common
        self.assertEqual(len(self.player.inventory), 3)
        self.assertEqual(self.player.inventory[0].rarity, 'legendary')
        self.assertEqual(self.player.inventory[1].rarity, 'epic')
        self.assertEqual(self.player.inventory[2].rarity, 'common')
        self.assertEqual(self.player.inventory[2].count, 4)

    def test_equipment_modal_pagination(self):
        # Fill player inventory with 25 different items
        self.player.inventory = [
            Item(f"Предмет #{i}", "common" if i % 2 == 0 else "rare", {'attack': i}, 10, slot='weapon')
            for i in range(25)
        ]
        modal = EquipmentModal(self.level, self.player)
        self.assertEqual(modal.inventory_page, 0)

        # Total pages for 25 items should be 2
        pages = max(1, (len(self.player.inventory) + 15) // 16)
        self.assertEqual(pages, 2)

        modal.next_inventory_page()
        self.assertEqual(modal.inventory_page, 1)

        # On page 1, slot 0 corresponds to item index 16
        real_idx = modal.inventory_page * 16 + 0
        self.assertEqual(real_idx, 16)
        self.assertEqual(self.player.inventory[real_idx].name, "Предмет #16")

        modal.next_inventory_page()
        self.assertEqual(modal.inventory_page, 0)

        modal.prev_inventory_page()
        self.assertEqual(modal.inventory_page, 1)

    def test_blacksmith_sorting_and_stack_split_upgrade(self):
        # Add a stack of 3 identical swords and 1 legendary sword
        common_sword = Item("Железный меч", "common", {'attack': 5}, 30, slot='weapon', count=3,
                            main_stat={'id': 'attack', 'label': 'Атака', 'value': 5, 'growth': 2},
                            substats=[{'id': 'crit_rate', 'label': 'Крит. шанс', 'value': 5.0, 'growth': 1.0, 'is_percent': True}])
        legendary_sword = Item("Экскалибур", "legendary", {'attack': 25}, 200, slot='weapon', count=1,
                               main_stat={'id': 'attack', 'label': 'Атака', 'value': 25, 'growth': 4},
                               substats=[{'id': 'crit_dmg', 'label': 'Крит. урон', 'value': 15.0, 'growth': 2.0, 'is_percent': True}])

        self.player.inventory = [common_sword, legendary_sword]
        forge = BlacksmithModal(self.level, self.player)

        # Blacksmith available items should have legendary first
        available = forge.get_available_items()
        inv_items_in_forge = [it for it, is_eq, _ in available if not is_eq]
        self.assertEqual(inv_items_in_forge[0].rarity, 'legendary')
        self.assertEqual(inv_items_in_forge[1].rarity, 'common')

        # Select the stacked common sword to upgrade
        forge.select_item(common_sword)
        self.assertEqual(common_sword.count, 3)

        # Perform upgrade
        forge.upgrade_selected_item()

        # The stack of common sword should decrease to 2, and a new +1 sword should be created
        self.assertEqual(common_sword.count, 2)
        self.assertEqual(common_sword.upgrade_level, 0)
        self.assertEqual(forge.selected_item.upgrade_level, 1)
        self.assertEqual(forge.selected_item.count, 1)
        self.assertIn(forge.selected_item, self.player.inventory)

    def test_shop_modal_stack_aware_selling_and_pagination(self):
        potion_stack = Item("Эликсир мощи", "rare", {'attack': 5}, 60, slot='consumable', count=3)
        self.player.inventory = [potion_stack]
        shop = ShopModal(self.level, self.player)
        shop.set_tab('sell')

        initial_gold = self.player.gold
        val = max(10, int(potion_stack.value * 0.45))

        # Sell 1 from stack
        shop.sell_item(0)
        self.assertEqual(self.player.gold, initial_gold + val)
        self.assertEqual(potion_stack.count, 2)
        self.assertEqual(len(self.player.inventory), 1)

        # Sell second unit
        shop.sell_item(0)
        self.assertEqual(potion_stack.count, 1)
        self.assertEqual(len(self.player.inventory), 1)

        # Sell final unit -> item should be removed from inventory
        shop.sell_item(0)
        self.assertEqual(len(self.player.inventory), 0)


if __name__ == '__main__':
    unittest.main()
