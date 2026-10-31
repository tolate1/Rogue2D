import unittest
import sys
import os
import pygame
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

from main import Game
from src.entities import Player, Enemy

class TestA9Pause(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_on_resume_shifts_all_timers(self):
        """on_resume shifts player and enemy timers by pause duration to preserve cooldowns."""
        game = Game()
        p = game.level.player
        p.attack_time = 1000
        p.dash_time = 1500
        p.shield_time = 800
        p.ult_time = 500

        # Create enemy in level
        enemy = list(game.level.enemy_sprites)[0] if game.level.enemy_sprites else None
        if enemy:
            enemy.attack_time = 2000

        # Simulate 2500ms pause
        game.on_resume(2500)

        self.assertEqual(p.attack_time, 3500)
        self.assertEqual(p.dash_time, 4000)
        self.assertEqual(p.shield_time, 3300)
        self.assertEqual(p.ult_time, 3000)
        if enemy:
            self.assertEqual(enemy.attack_time, 4500)

    def test_pause_state_transition_timing(self):
        """Entering pause records start time, and resuming shifts timers by exact elapsed time."""
        game = Game()
        game.set_state('game')
        p = game.level.player
        p.attack_time = 500

        # 1. Enter pause at t = 1000
        with patch('pygame.time.get_ticks', return_value=1000):
            game.set_state('pause')
            self.assertEqual(game.pause_start_time, 1000)

        # 2. Enter settings_ingame at t = 1500: pause_start_time must NOT be overwritten
        with patch('pygame.time.get_ticks', return_value=1500):
            game.set_state('settings_ingame')
            self.assertEqual(game.pause_start_time, 1000)

        # 3. Resume game at t = 3000 (total pause duration 2000ms)
        with patch('pygame.time.get_ticks', return_value=3000):
            game.set_state('game')
            self.assertIsNone(game.pause_start_time)
            # attack_time should be 500 + 2000 = 2500
            self.assertEqual(p.attack_time, 2500)

if __name__ == '__main__':
    unittest.main()
