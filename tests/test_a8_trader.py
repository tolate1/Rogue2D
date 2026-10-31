import unittest
import sys
import os
import pygame
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.map_manager import Level

class TestA8Trader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_trader_full_health_rejection(self):
        """Trader should refuse purchase when health is already full without deducting gold."""
        level = Level()
        level.player.stats['health'] = 100
        level.player.health = 100
        level.player.gold = 100

        success, msg = level.interact_trader()
        self.assertFalse(success)
        self.assertEqual(msg, "Health Full!")
        self.assertEqual(level.player.gold, 100, "Gold must not be deducted when health is full")
        self.assertEqual(level.player.health, 100)

    def test_trader_insufficient_gold(self):
        """Trader should refuse purchase when gold is less than 50."""
        level = Level()
        level.player.stats['health'] = 100
        level.player.health = 30
        level.player.gold = 35

        success, msg = level.interact_trader()
        self.assertFalse(success)
        self.assertEqual(msg, "Not enough gold!")
        self.assertEqual(level.player.gold, 35, "Gold must not change on failed purchase")
        self.assertEqual(level.player.health, 30, "Health must not change on failed purchase")

    def test_trader_successful_purchase(self):
        """Trader restores up to 50 health and deducts 50 gold."""
        level = Level()
        level.player.stats['health'] = 100
        level.player.health = 40
        level.player.gold = 75

        success, msg = level.interact_trader()
        self.assertTrue(success)
        self.assertEqual(msg, "Bought Potion!")
        self.assertEqual(level.player.gold, 25)
        self.assertEqual(level.player.health, 90)

    def test_trader_single_purchase_per_press(self):
        """Pressing 'E' opens shop modal without auto-purchasing or deducting gold."""
        level = Level()
        level.player.stats['health'] = 100
        level.player.health = 20
        level.player.gold = 150

        # Create a mock trader right next to player
        trader = pygame.sprite.Sprite([level.visible_sprites, level.trader_sprites])
        trader.image = pygame.Surface((32, 32))
        trader.rect = trader.image.get_rect(center=level.player.rect.center)
        trader.hitbox = trader.rect

        # Simulate keypress E being held for 5 frames
        keys_mock = [0] * 323
        keys_mock[pygame.K_e] = 1

        with patch('pygame.key.get_pressed', return_value=keys_mock):
            for _ in range(5):
                level.update()

        # Modal is opened and gold is intact (isolation achieved)
        self.assertEqual(level.active_modal, 'shop')
        self.assertEqual(level.player.gold, 150, "Opening shop must not auto-deduct gold!")
        self.assertEqual(level.player.health, 20)

if __name__ == '__main__':
    unittest.main()
