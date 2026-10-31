import unittest
import os
import sys

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
from src.entities import Player

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, rect, groups):
        super().__init__(groups)
        self.image = pygame.Surface((rect.width, rect.height))
        self.rect = pygame.Rect(rect)
        self.hitbox = pygame.Rect(rect)

class TestA2Collisions(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.screen = pygame.display.set_mode((200, 200))
        self.visible_sprites = pygame.sprite.Group()
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        
        self.player = Player((50, 50), [self.visible_sprites], self.obstacle_sprites, self.enemy_sprites)
        self.player.pos = pygame.math.Vector2(50, 50)
        self.player.hitbox.topleft = (50, 50)
        self.player.rect.center = self.player.hitbox.center
        self.player.velocity = pygame.math.Vector2(0, 0)
        self.player.direction = pygame.math.Vector2(0, 0)

    def tearDown(self):
        pygame.quit()

    def test_1_inertia_stop_before_wall(self):
        """1. Releasing key before wall: residual velocity stops exactly at wall edge, no penetration."""
        # Wall at x=100
        wall = Obstacle(pygame.Rect(100, 0, 64, 200), [self.obstacle_sprites])
        
        # Player right edge is at x=50 + hitbox.width
        # Give player rightward velocity with direction = 0 (simulating key just released)
        self.player.direction = pygame.math.Vector2(0, 0)
        self.player.velocity = pygame.math.Vector2(8, 0)
        
        # Step movement until stopped
        for _ in range(15):
            self.player.move(self.player.speed)
            
        self.assertLessEqual(self.player.hitbox.right, wall.hitbox.left, "Hitbox must not penetrate wall")
        self.assertEqual(self.player.hitbox.right, wall.hitbox.left, "Hitbox must be flush against wall")
        self.assertEqual(self.player.velocity.x, 0, "Velocity into wall must be zeroed")

    def test_2_turnaround_during_inertia(self):
        """2. Turning around while still carrying inertia towards wall: no jumping across wall."""
        wall = Obstacle(pygame.Rect(100, 0, 64, 200), [self.obstacle_sprites])
        
        # Player close to wall, moving right with velocity=5, but direction pressed LEFT (-1)
        self.player.hitbox.right = wall.hitbox.left - 2
        self.player.pos.x = float(self.player.hitbox.x)
        self.player.velocity = pygame.math.Vector2(5, 0)
        self.player.direction = pygame.math.Vector2(-1, 0)
        
        self.player.move(self.player.speed)
        
        # Player must be stopped at the left wall boundary, NOT flipped to the right side of the wall
        self.assertLessEqual(self.player.hitbox.right, wall.hitbox.left, "Must not penetrate or teleport through wall")
        self.assertEqual(self.player.hitbox.right, wall.hitbox.left, "Must stop at near wall face")

    def test_3_escape_existing_overlap(self):
        """3. Trying to escape an existing 3px overlap: player escapes freely without jumping to opposite face."""
        wall = Obstacle(pygame.Rect(100, 0, 64, 200), [self.obstacle_sprites])
        
        # Artificially create a 3px overlap into the left edge of the wall
        self.player.hitbox.right = wall.hitbox.left + 3
        self.player.pos.x = float(self.player.hitbox.x)
        
        # Player presses LEFT to escape
        self.player.direction = pygame.math.Vector2(-1, 0)
        self.player.velocity = pygame.math.Vector2(-4, 0)
        
        self.player.move(self.player.speed)
        
        # Player should have moved left, away from wall
        self.assertLessEqual(self.player.hitbox.right, wall.hitbox.left, "Player must have moved out of the wall")
        self.assertLess(self.player.hitbox.left, wall.hitbox.left, "Player must NOT jump to the right side of wall")

    def test_4_slide_along_wall(self):
        """4. Moving diagonally into a wall: velocity into wall blocked, velocity along wall preserved."""
        # Vertical wall on the right at x=100
        wall = Obstacle(pygame.Rect(100, 0, 64, 200), [self.obstacle_sprites])
        
        self.player.hitbox.right = wall.hitbox.left - 1
        self.player.pos.x = float(self.player.hitbox.x)
        start_y = self.player.pos.y
        
        # Press W + D (diagonal up-right)
        self.player.direction = pygame.math.Vector2(1, -1)
        self.player.velocity = pygame.math.Vector2(4, -4)
        
        self.player.move(self.player.speed)
        
        self.assertLessEqual(self.player.hitbox.right, wall.hitbox.left, "X must be clamped at wall")
        self.assertLess(self.player.pos.y, start_y, "Y movement must be preserved (sliding along wall)")

    def test_5_corner_multi_tile_collision(self):
        """5. Pushing into an internal L-corner: stopped on both axes without remaining overlap."""
        # Corner: wall on the right (x=100) and wall below (y=100)
        wall_v = Obstacle(pygame.Rect(100, 0, 64, 200), [self.obstacle_sprites])
        wall_h = Obstacle(pygame.Rect(0, 100, 200, 64), [self.obstacle_sprites])
        
        # Place player 2px away from corner, moving down-right (S+D) with speed 15 (dash)
        self.player.hitbox.right = 98
        self.player.hitbox.bottom = 98
        self.player.pos = pygame.math.Vector2(self.player.hitbox.topleft)
        
        self.player.direction = pygame.math.Vector2(1, 1)
        self.player.velocity = pygame.math.Vector2(10, 10)
        
        self.player.move(15)
        
        self.assertEqual(self.player.hitbox.right, wall_v.hitbox.left, "Must clamp to vertical wall")
        self.assertEqual(self.player.hitbox.bottom, wall_h.hitbox.top, "Must clamp to horizontal wall")
        self.assertFalse(self.player.hitbox.colliderect(wall_v.hitbox), "No overlap with vertical wall")
        self.assertFalse(self.player.hitbox.colliderect(wall_h.hitbox), "No overlap with horizontal wall")

    def test_6_symmetry_both_axes_and_directions(self):
        """6. Movement into walls works symmetrically in all 4 cardinal directions."""
        # Test Left
        left_wall = Obstacle(pygame.Rect(0, 0, 32, 200), [self.obstacle_sprites])
        self.player.hitbox.left = 35
        self.player.pos.x = 35.0
        self.player.velocity = pygame.math.Vector2(-10, 0)
        self.player.move(15)
        self.assertEqual(self.player.hitbox.left, left_wall.hitbox.right, "Left collision symmetry")
        left_wall.kill()
        
        # Test Top
        top_wall = Obstacle(pygame.Rect(0, 0, 200, 32), [self.obstacle_sprites])
        self.player.hitbox.top = 35
        self.player.pos.y = 35.0
        self.player.velocity = pygame.math.Vector2(0, -10)
        self.player.move(15)
        self.assertEqual(self.player.hitbox.top, top_wall.hitbox.bottom, "Top collision symmetry")
        top_wall.kill()

    def test_7_dash_speed_into_wall(self):
        """7. High speed burst (Dash speed = 15 px/frame) into wall: stops cleanly at wall face, no tunneling."""
        wall = Obstacle(pygame.Rect(100, 0, 64, 200), [self.obstacle_sprites])
        
        # Player right edge at 90. High speed velocity = 15 moves to 105 (past wall boundary)
        self.player.hitbox.right = 90
        self.player.pos.x = float(self.player.hitbox.x)
        self.player.velocity = pygame.math.Vector2(15, 0)
        
        self.player.move(15)
        
        self.assertEqual(self.player.hitbox.right, wall.hitbox.left, "Must not tunnel through wall on dash")
        self.assertEqual(self.player.velocity.x, 0, "Velocity must be stopped on collision")

    def test_8_subpixel_precision_preserved(self):
        """8. Non-integer velocity preserves float position between frames when moving freely."""
        # Non-integer initial float pos
        self.player.pos = pygame.math.Vector2(50.25, 50.75)
        self.player.hitbox.topleft = (50, 50)
        self.player.direction = pygame.math.Vector2(1, 0)
        self.player.velocity = pygame.math.Vector2(2.5, 0)
        
        # Move freely: direction is active, acceleration applied, no collision
        self.player.move(10)
        
        # Position should maintain its float precision (not be truncated to int)
        self.assertIsInstance(self.player.pos.x, float)
        self.assertNotEqual(self.player.pos.x, round(self.player.pos.x), "Subpixel float precision must be maintained")

if __name__ == '__main__':
    unittest.main()
