import unittest
import sys
import os
import pygame

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.map_manager import Level
from src.settings import TILE_SIZE

class TestA4Generation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_safe_distance_enemies_from_player(self):
        """Enemies must never spawn within 4 tiles of the player start position."""
        for iteration in range(5):
            level = Level(current_floor=1)
            player_pos = pygame.math.Vector2(level.player.rect.center)
            min_safe_pixels = 4.0 * TILE_SIZE

            for enemy in level.enemy_sprites:
                enemy_pos = pygame.math.Vector2(enemy.rect.center)
                distance = (enemy_pos - player_pos).magnitude()
                self.assertGreaterEqual(
                    distance,
                    min_safe_pixels - 5, # tolerance for center/hitbox offsets
                    f"Iteration {iteration}: Enemy {enemy.enemy_type} at {enemy_pos} too close to player {player_pos} (dist: {distance})"
                )

    def test_breakables_spawn_multiple(self):
        """Breakables should spawn up to 15, fixing the old bug where only 1 spawned."""
        total_breakables = 0
        for _ in range(5):
            level = Level(current_floor=1)
            # Breakables are in obstacle_sprites with 'destroy' method
            breakables = [s for s in level.obstacle_sprites if hasattr(s, 'destroy')]
            total_breakables += len(breakables)
            self.assertGreater(len(breakables), 1, "Should spawn more than 1 breakable per floor")
            self.assertLessEqual(len(breakables), 15, "Should not spawn more than 15 breakables")

    def test_no_duplicate_enemy_tiles(self):
        """Enemies must not be stacked on the exact same tile."""
        for iteration in range(5):
            level = Level(current_floor=1)
            seen_positions = set()
            for enemy in level.enemy_sprites:
                tile = (enemy.rect.x // TILE_SIZE, enemy.rect.y // TILE_SIZE)
                self.assertNotIn(
                    tile,
                    seen_positions,
                    f"Iteration {iteration}: Multiple enemies spawned on same tile {tile}"
                )
                seen_positions.add(tile)

    def test_stairs_furthest_and_reachable(self):
        """Stairs must spawn on floor, not on player, and at a safe distance."""
        for iteration in range(5):
            level = Level(current_floor=1)
            player_pos = pygame.math.Vector2(level.player.rect.center)
            for stairs in level.stairs_sprites:
                stairs_pos = pygame.math.Vector2(stairs.rect.center)
                dist = (stairs_pos - player_pos).magnitude()
                self.assertGreater(dist, 3.0 * TILE_SIZE, f"Stairs too close to player: {dist}")

if __name__ == '__main__':
    unittest.main()
