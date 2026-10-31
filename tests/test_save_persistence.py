import unittest
import sys
import os
import tempfile
import pygame

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import src.save_manager
from src.map_manager import Level
from src.save_manager import save_game_state, load_game_state

class TestSavePersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        # Isolate save file in temporary directory
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.orig_save_file = src.save_manager.SAVE_FILE
        src.save_manager.SAVE_FILE = os.path.join(self.tmp_dir.name, "savegame.json")

    def tearDown(self):
        src.save_manager.SAVE_FILE = self.orig_save_file
        self.tmp_dir.cleanup()

    def test_autosave_seed_matches_actual_level_seed(self):
        """Floor transition auto-save must preserve actual level seed, not fallback floor * 9876543."""
        # Start at floor 2 with fixed seed
        level = Level(current_floor=2, floor_seed=777)
        self.assertEqual(level.floor_seed, 777)

        # Trigger floor transition logic
        # Player steps on stairs
        self.player = level.player
        self.player.kills = 5
        
        # Simulate transition to floor 3 through stairs collision handler
        stairs_sprite = pygame.sprite.Sprite()
        stairs_sprite.rect = pygame.Rect(self.player.rect)
        stairs_sprite.hitbox = pygame.Rect(self.player.hitbox)
        level.stairs_sprites.add(stairs_sprite)

        # Update level once to trigger floor transition
        level.update()

        self.assertEqual(level.current_floor, 3)
        self.assertEqual(level.player.kills, 5, "Kills must persist across floor transition")

        # Load saved data from autosave
        save_data = load_game_state()
        self.assertIsNotNone(save_data)
        saved_seed = save_data.get('floor_seed')
        saved_floor = save_data.get('floor')

        self.assertEqual(saved_floor, 3)
        # CRITICAL CHECK: saved_seed must equal the actual current level.floor_seed
        self.assertEqual(saved_seed, level.floor_seed, "Autosave seed must match actual level.floor_seed")
        self.assertNotEqual(saved_seed, 3 * 9876543, "Autosave seed must not be unseeded fallback")

    def test_continue_saved_run_player_on_valid_floor_not_in_wall(self):
        """Loading a saved run must generate identical dungeon and place player on valid floor, not in wall."""
        level = Level(current_floor=2, floor_seed=12345)
        
        # Trigger transition to floor 3
        stairs_sprite = pygame.sprite.Sprite()
        stairs_sprite.rect = pygame.Rect(level.player.rect)
        stairs_sprite.hitbox = pygame.Rect(level.player.hitbox)
        level.stairs_sprites.add(stairs_sprite)
        level.update()

        save_data = load_game_state()
        saved_seed = save_data.get('floor_seed')
        saved_floor = save_data.get('floor')
        saved_pos = save_data.get('player_pos')

        # Load level from save
        loaded_level = Level(current_floor=saved_floor, floor_seed=saved_seed)
        
        # Verify identical geometry
        self.assertEqual(loaded_level.floor_positions, level.floor_positions, "Loaded level floor layout must match original")

        # Verify player position is valid on loaded map
        tile_pos = (saved_pos[0] // 64, saved_pos[1] // 64)
        self.assertIn(tile_pos, loaded_level.floor_positions, f"Player pos {saved_pos} tile {tile_pos} must be in floor_positions")

        # Verify player does not collide with obstacles
        player_rect = pygame.Rect(saved_pos[0], saved_pos[1], 48, 48)
        wall_collisions = [w for w in loaded_level.obstacle_sprites if hasattr(w, 'hitbox') and player_rect.colliderect(w.hitbox)]
        self.assertEqual(len(wall_collisions), 0, f"Player must not collide with walls upon loading: {wall_collisions}")

    def test_floor_transition_generates_distinct_seeds(self):
        """Successive floor transitions must produce different floor seeds so map layouts vary."""
        level = Level(current_floor=1, floor_seed=1001)
        seed_f1 = level.floor_seed

        # Transition 1 -> 2
        stairs1 = pygame.sprite.Sprite()
        stairs1.rect = pygame.Rect(level.player.rect)
        level.stairs_sprites.add(stairs1)
        level.update()
        seed_f2 = level.floor_seed

        # Transition 2 -> 3
        stairs2 = pygame.sprite.Sprite()
        stairs2.rect = pygame.Rect(level.player.rect)
        level.stairs_sprites.add(stairs2)
        level.update()
        seed_f3 = level.floor_seed

        self.assertNotEqual(seed_f1, seed_f2, "Floor 2 seed must differ from Floor 1")
        self.assertNotEqual(seed_f2, seed_f3, "Floor 3 seed must differ from Floor 2")

if __name__ == '__main__':
    unittest.main()
