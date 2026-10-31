import unittest
import sys
import os
import pygame

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.entities import Enemy, Player
from src.settings import TILE_SIZE

class DummyObstacle(pygame.sprite.Sprite):
    def __init__(self, rect):
        super().__init__()
        self.rect = pygame.Rect(rect)
        self.hitbox = self.rect.copy()

class TestA5Pathfinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.visible_sprites = pygame.sprite.Group()
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

    def test_last_known_player_pos_pursuit(self):
        """When player breaks LOS behind a corner, enemy pursues last known position instead of freezing."""
        player = Player((200, 100), [self.visible_sprites], self.obstacle_sprites, self.enemy_sprites)
        enemy = Enemy((100, 100), [self.visible_sprites, self.enemy_sprites],
                      self.obstacle_sprites, player, 'zombie', visible_sprites=self.visible_sprites)
        
        # 1. Direct LOS: enemy sees player
        enemy.check_line_of_sight(force=True) if hasattr(enemy, 'check_line_of_sight') else None
        enemy.move_towards_player()
        self.assertIsNotNone(enemy.last_known_player_pos)
        self.assertEqual(enemy.last_known_player_pos, pygame.math.Vector2(player.hitbox.center))

        # 2. Block LOS by placing wall in between and moving player behind it
        wall = DummyObstacle((150, 80, 40, 100))
        self.obstacle_sprites.add(wall)
        player.hitbox.center = (300, 100)
        player.rect.center = player.hitbox.center
        enemy.los_timer = enemy.los_interval # force check on next call

        # Call move_towards_player: LOS should be False, but enemy must move toward last known pos
        enemy.move_towards_player()
        self.assertFalse(enemy.has_los)
        self.assertNotEqual(enemy.direction, pygame.math.Vector2(0, 0), "Enemy must not freeze when LOS is lost!")
        # Direction should point towards the last known position (which was ~200, 100)
        self.assertGreater(enemy.direction.x, 0, "Enemy should still be moving right toward last known position")

    def test_corner_obstacle_avoidance(self):
        """When primary axis is blocked by an obstacle, enemy selects perpendicular bypass axis."""
        player = Player((200, 100), [self.visible_sprites], self.obstacle_sprites, self.enemy_sprites)
        enemy = Enemy((100, 100), [self.visible_sprites, self.enemy_sprites],
                      self.obstacle_sprites, player, 'zombie', visible_sprites=self.visible_sprites)

        # Place a 32x32 wall directly in front of enemy's path to the right: at x=130..162, y=90..130
        wall = DummyObstacle((130, 90, 32, 40))
        self.obstacle_sprites.add(wall)

        # Direct step to (200, 100) along X is blocked by wall
        chosen_dir = enemy.calculate_direction(pygame.math.Vector2(200, 100))
        # It must choose a perpendicular direction (y != 0) rather than walking straight into wall
        self.assertNotEqual(chosen_dir.y, 0, f"Enemy should slide vertically around wall, got direction {chosen_dir}")

    def test_skeleton_ranged_chase_vs_shooting(self):
        """Skeleton moves towards player when far, but stops to shoot when within range."""
        player = Player((100, 100), [self.visible_sprites], self.obstacle_sprites, self.enemy_sprites)
        # Skeleton at distance 400 (far)
        skeleton = Enemy((500, 100), [self.visible_sprites, self.enemy_sprites],
                         self.obstacle_sprites, player, 'skeleton', visible_sprites=self.visible_sprites)
        
        skeleton.los_timer = skeleton.los_interval
        skeleton.move_towards_player()
        self.assertNotEqual(skeleton.direction, pygame.math.Vector2(0, 0), "Skeleton far away should advance")

        # Move skeleton close (distance 150 < 250)
        skeleton.hitbox.center = (250, 100)
        skeleton.rect.center = skeleton.hitbox.center
        skeleton.los_timer = skeleton.los_interval
        skeleton.move_towards_player()
        self.assertEqual(skeleton.direction, pygame.math.Vector2(0, 0), "Skeleton close with LOS should stop to shoot")

if __name__ == '__main__':
    unittest.main()
