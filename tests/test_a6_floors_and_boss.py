import unittest
import sys
import os
import pygame

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.map_manager import Level
from src.settings import TILE_SIZE

class TestA6FloorsAndBoss(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_floor_progression_via_stairs(self):
        """Touching stairs increments current_floor and preserves player progress."""
        level = Level(current_floor=1)
        self.assertEqual(level.current_floor, 1)

        level.player.gold = 75
        level.player.health = 80
        level.player.exp = 40

        # Move player onto stairs
        stairs = list(level.stairs_sprites)[0]
        level.player.rect.topleft = stairs.rect.topleft
        level.player.hitbox.topleft = stairs.rect.topleft
        level.player.pos = pygame.math.Vector2(level.player.hitbox.topleft)

        # Call update() to trigger stairs collision
        level.update()

        self.assertEqual(level.current_floor, 2)
        self.assertEqual(level.player.gold, 75)
        self.assertEqual(level.player.health, 80)
        self.assertEqual(level.player.exp, 40)

    def test_boss_level_spawns_void_knight(self):
        """Floor 5 is boss level: spawns exactly one void knight boss, no chests or breakables."""
        level = Level(current_floor=5)
        self.assertTrue(level.is_boss_level)
        self.assertEqual(len(level.enemy_sprites), 1)

        boss = list(level.enemy_sprites)[0]
        self.assertEqual(boss.enemy_type, 'boss_void_knight')
        self.assertTrue(boss.is_boss)
        self.assertEqual(boss.exp_value, 250)
        self.assertGreaterEqual(len(boss.frames), 2)
        self.assertEqual(len(level.chest_sprites), 0)
        self.assertEqual(len(level.trader_sprites), 0)

        # Breakables check
        breakables = [s for s in level.obstacle_sprites if hasattr(s, 'destroy')]
        self.assertEqual(len(breakables), 0)

    def test_boss_defeat_unlocks_stairs(self):
        """On floor 5, stairs are locked until the boss is killed."""
        level = Level(current_floor=5)
        self.assertEqual(len(level.stairs_sprites), 0, "Stairs should not be present while boss is alive")

        # Defeat the boss
        boss = list(level.enemy_sprites)[0]
        boss.kill()

        # Update level to detect boss defeat
        level.update()
        self.assertEqual(len(level.stairs_sprites), 1, "Stairs must spawn after boss defeat")

if __name__ == '__main__':
    unittest.main()
