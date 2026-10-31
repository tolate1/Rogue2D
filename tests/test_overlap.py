import unittest
import sys
import os
import pygame
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.map_manager import Level
from src.entities import Player

class TestOverlap(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((100, 100))
        
    def test_stairs_obstacle_overlap(self):
        print("\n--- Testing Overlap (Stairs vs Breakables) ---")
        
        # Run multiple generations to increase confidence
        for i in range(10):
            level = Level()
            
            stairs_group = level.stairs_sprites
            obstacles_group = level.obstacle_sprites
            chests_group = level.chest_sprites
            
            # Check collisions: Stairs vs Obstacles
            collisions_stairs_obs = pygame.sprite.groupcollide(stairs_group, obstacles_group, False, False)
            # Check collisions: Chests vs Stairs
            collisions_chests_stairs = pygame.sprite.groupcollide(chests_group, stairs_group, False, False)
            
            if collisions_stairs_obs:
                print(f"Iteration {i}: Stairs Overlap Obstacle!")
            if collisions_chests_stairs:
                print(f"Iteration {i}: Chest Overlap Stairs!")
            
            self.assertFalse(collisions_stairs_obs, f"Iteration {i}: Stairs should not overlap obstacles")
            self.assertFalse(collisions_chests_stairs, f"Iteration {i}: Chest should not overlap stairs")
            
    def tearDown(self):
        pygame.quit()

if __name__ == '__main__':
    unittest.main()
