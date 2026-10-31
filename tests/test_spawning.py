import unittest
import sys
import os
import pygame
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.map_manager import Level
from src.entities import Enemy, Player

class TestSpawning(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((100, 100))
        
    def test_biome_enemies(self):
        # We need to mock Player level to control biome choice in Level.create_map
        # Logic: if player.level > 1, random biome. Else 'dungeon'.
        
        # Test Dungeon (Level 1)
        # We need to instantiate Level without it auto-creating everything perfectly or mock bits.
        # Level() calls create_map() in __init__.
        # It creates a Player there too.
        
        print("\n--- Testing Dungeon Spawning ---")
        level = Level()
        # By default Level 1 -> Dungeon
        # Check enemies
        enemy_types = [e.enemy_type for e in level.enemy_sprites]
        print(f"Dungeon Enemies: {set(enemy_types)}")
        
        allowed_dungeon = {'skeleton', 'zombie', 'lurker', 'bat', 'goblin', 'imp'}
        for et in enemy_types:
            self.assertIn(et, allowed_dungeon, f"Enemy {et} not allowed in Dungeon")
            
    def tearDown(self):
        pygame.quit()

if __name__ == '__main__':
    unittest.main()
