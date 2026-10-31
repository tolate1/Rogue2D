import sys
import os
import pygame
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock display before importing pygame dependent modules if needed, 
# but we can set SDL_VIDEODRIVER=dummy
os.environ["SDL_VIDEODRIVER"] = "dummy"

import src.settings as settings
from src.entities import Player

class TestMovementSimulation(unittest.TestCase):
    def setUp(self):
        pygame.init()
        # Create a dummy display surface required for some sprite operations
        self.screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
        
        # Mock Groups
        self.visible_sprites = pygame.sprite.Group()
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        
        # Instantiate Player
        # Player(pos, groups, obstacle_sprites, enemy_sprites)
        self.start_pos = (100, 100)
        self.player = Player(self.start_pos, [self.visible_sprites], self.obstacle_sprites, self.enemy_sprites)
        
        # Default keys state (all False)
        self.mock_keys = {
            pygame.K_w: False,
            pygame.K_a: False,
            pygame.K_s: False,
            pygame.K_d: False,
            pygame.K_z: False, # Dash
            pygame.K_x: False, # Shield
            pygame.K_c: False, # Ult
            pygame.K_e: False  # Interact
        }

    def tearDown(self):
        pygame.quit()

    def get_mock_pressed(self):
        pressed = [0] * 512 # Standard size
        for key, value in self.mock_keys.items():
            if key < len(pressed):
                pressed[key] = 1 if value else 0
        return pressed

    @patch('pygame.key.get_pressed')
    @patch('pygame.mouse.get_pressed')
    def test_wasd_movement(self, mock_mouse, mock_keys):
        print(f"\n--- Starting WASD Simulation ---")
        print(f"Start Pos: {self.player.pos}")

        # Mock Mouse (No clicking)
        mock_mouse.return_value = (0, 0, 0)
        
        # Setup Mock Keys return
        mock_keys.side_effect = self.get_mock_pressed

        # Capture initial position
        start_x = self.player.pos.x

        # --- Phase 1: Move Right (D) ---
        print("\n[Phase 1] Simulating Press 'D' (Right)")
        self.mock_keys[pygame.K_d] = True
        
        # Run 10 frames
        for _ in range(10):
            self.player.update()
            
        print(f"Pos after 10 frames Right: {self.player.pos}")
        self.assertGreater(self.player.pos.x, start_x, "Player should move right")
        current_x = self.player.pos.x
        
        # Reset keys
        self.mock_keys[pygame.K_d] = False

        # --- Phase 2: Move Left (A) ---
        print("\n[Phase 2] Simulating Press 'A' (Left)")
        self.mock_keys[pygame.K_a] = True
        
        for _ in range(10):
            self.player.update()
            
        print(f"Pos after 10 frames Left: {self.player.pos}")
        self.assertLess(self.player.pos.x, current_x, "Player should move left")
        current_y = self.player.pos.y

        # Reset keys
        self.mock_keys[pygame.K_a] = False

        # --- Phase 3: Move Down (S) ---
        print("\n[Phase 3] Simulating Press 'S' (Down)")
        self.mock_keys[pygame.K_s] = True
        
        for _ in range(10):
            self.player.update()
            
        print(f"Pos after 10 frames Down: {self.player.pos}")
        self.assertGreater(self.player.pos.y, current_y, "Player should move down")
        current_y = self.player.pos.y
        
        # Reset keys
        self.mock_keys[pygame.K_s] = False

        # --- Phase 4: Move Up (W) ---
        print("\n[Phase 4] Simulating Press 'W' (Up)")
        self.mock_keys[pygame.K_w] = True
        
        for _ in range(10):
            self.player.update()
            
        print(f"Pos after 10 frames Up: {self.player.pos}")
        self.assertLess(self.player.pos.y, current_y, "Player should move up")
        
        print("\n--- Simulation Complete: All Directions Verified ---")

if __name__ == '__main__':
    unittest.main()
