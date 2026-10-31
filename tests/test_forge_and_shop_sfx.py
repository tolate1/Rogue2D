import os
import unittest
from unittest.mock import patch, MagicMock
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
if not pygame.display.get_surface():
    pygame.display.set_mode((960, 640))

from src.entities import Player
from src.items import Item
from src.ui import ShopModal, BlacksmithModal
from src.sound_manager import SoundManager

class TestForgeAndShopSFX(unittest.TestCase):
    def setUp(self):
        self.group = pygame.sprite.Group()
        self.player = Player((100, 100), [self.group], self.group, self.group)
        self.player.gold = 500

    def test_anvil_sound_registered_and_exists(self):
        """Verify anvil sound asset exists and is registered in sound manager."""
        snd_mgr = SoundManager.get_instance()
        self.assertIn('anvil', snd_mgr.sounds)
        anvil_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sounds", "anvil.wav")
        self.assertTrue(os.path.exists(anvil_path))

    @patch('src.sound_manager.play_sfx')
    def test_blacksmith_spark_sfx_plays_anvil(self, mock_play_sfx):
        """Verify BlacksmithModal plays metallic anvil sound upon gear upgrade/spark effect."""
        modal = BlacksmithModal(None, self.player)
        modal._spark_sfx()
        mock_play_sfx.assert_called_with('anvil')

    @patch('src.sound_manager.play_sfx')
    def test_shop_buy_item_plays_coin(self, mock_play_sfx):
        """Verify ShopModal plays coin sfx on item purchase."""
        modal = ShopModal(None, self.player)
        self.player.health = 50
        # Buy potion (idx 0 is typically potion)
        initial_gold = self.player.gold
        modal.buy_item(0)
        self.assertLess(self.player.gold, initial_gold)
        mock_play_sfx.assert_called_with('coin')

    @patch('src.sound_manager.play_sfx')
    def test_shop_sell_item_plays_coin(self, mock_play_sfx):
        """Verify ShopModal plays coin sfx on item sale."""
        modal = ShopModal(None, self.player)
        test_item = Item("Iron Sword", "common", {'attack': 2}, value=50, slot='weapon')
        self.player.inventory.append(test_item)
        initial_gold = self.player.gold
        modal.sell_item(len(self.player.inventory) - 1)
        self.assertGreater(self.player.gold, initial_gold)
        mock_play_sfx.assert_called_with('coin')

if __name__ == '__main__':
    unittest.main()
