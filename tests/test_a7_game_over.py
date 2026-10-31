import unittest
import sys
import os
import pygame

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

from main import Game
from src.map_manager import Level
from src.entities import Player

class TestA7GameOver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_player_terminal_death(self):
        """Player at zero or negative health becomes terminally dead and stops movement."""
        obstacle_sprites = pygame.sprite.Group()
        enemy_sprites = pygame.sprite.Group()
        visible_sprites = pygame.sprite.Group()
        player = Player((100, 100), [visible_sprites], obstacle_sprites, enemy_sprites)

        self.assertFalse(player.is_dead)
        player.health = 0
        player.direction = pygame.math.Vector2(1, 1)
        player.update()

        self.assertTrue(player.is_dead)
        self.assertEqual(player.direction, pygame.math.Vector2(0, 0))

    def test_level_game_over_trigger(self):
        """Level sets game_over = True when player health drops to zero."""
        level = Level()
        self.assertFalse(level.game_over)

        level.player.health = -10
        level.update()

        self.assertTrue(level.game_over)
        self.assertTrue(level.player.is_dead)

    def test_game_over_state_transition(self):
        """Game transitions from 'game' to 'game_over' and records stats."""
        game = Game()
        game.state = 'game'
        game.level.player.gold = 120
        game.level.player.kills = 7
        game.level.current_floor = 3

        # Trigger death
        game.level.player.health = 0
        game.update()

        self.assertEqual(game.state, 'game_over')
        self.assertEqual(game.last_run_stats.get('floor'), 3)
        self.assertEqual(game.last_run_stats.get('gold'), 120)
        self.assertEqual(game.last_run_stats.get('kills'), 7)
        self.assertGreater(len(game.ui_buttons), 0)

    def test_start_new_run_clean_reset(self):
        """start_new_run creates fresh run at floor 1 while preserving user settings."""
        game = Game()
        game.level.visible_sprites.zoom_level = 1.35
        game.ui.ui_scale = 1.2
        game.level.player.gold = 350
        game.level.current_floor = 4

        game.start_new_run()

        self.assertEqual(game.state, 'game')
        self.assertEqual(game.level.current_floor, 1)
        self.assertEqual(game.level.player.gold, 0)
        self.assertEqual(game.level.player.health, 100)
        self.assertFalse(game.level.game_over)
        self.assertAlmostEqual(game.level.visible_sprites.zoom_level, 1.35)
        self.assertAlmostEqual(game.ui.ui_scale, 1.2)

if __name__ == '__main__':
    unittest.main()
