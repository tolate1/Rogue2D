import unittest
import sys
import os
import pygame
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.entities import Player, Enemy

class TestBossCleave(unittest.TestCase):
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
        self.player = Player((200, 200), [self.visible_sprites], self.obstacle_sprites, self.enemy_sprites)
        self.player.hitbox = pygame.Rect(190, 190, 20, 20)
        self.boss = Enemy(
            (100, 100),
            [self.visible_sprites, self.enemy_sprites],
            self.obstacle_sprites,
            self.player,
            'boss_void_knight',
            visible_sprites=self.visible_sprites
        )

    def test_boss_cleave_cycle_phase1(self):
        """Phase 1 boss completes telegraph without error at 1000ms, does not damage player early, and can repeat."""
        self.boss.hp = 250
        initial_hp = self.player.health

        current_time = 10000
        with patch('pygame.time.get_ticks') as mock_ticks:
            mock_ticks.return_value = current_time

            # Start telegraph
            self.boss.boss_attack_state = 'telegraph'
            self.boss.boss_telegraph_start = current_time
            self.boss.cleave_dir = pygame.math.Vector2(1, 0)
            self.boss.update()

            self.assertEqual(self.boss.boss_attack_state, 'telegraph')
            self.assertEqual(self.player.health, initial_hp, "No damage dealt at telegraph start")

            # 999 ms into telegraph - still warming up
            current_time = 10999
            mock_ticks.return_value = current_time
            self.boss.update()
            self.assertEqual(self.boss.boss_attack_state, 'telegraph')
            self.assertEqual(self.player.health, initial_hp, "No damage dealt before 1000ms")

            # 1000 ms - telegraph finishes, cleave triggers
            current_time = 11000
            mock_ticks.return_value = current_time
            self.boss.update() # Should NOT raise UnboundLocalError!

            self.assertEqual(self.boss.boss_attack_state, 'idle', "Boss should return to idle after cleave release")
            self.assertEqual(self.boss.boss_cleave_timer, 11000 + 4200, "Cleave cooldown should be set")
            self.assertLess(self.player.health, initial_hp, "Player in range should take cleave damage on release")

            # Repeat cycle after cooldown
            current_time = 11000 + 4300
            mock_ticks.return_value = current_time
            self.boss.boss_attack_state = 'telegraph'
            self.boss.boss_telegraph_start = current_time
            self.boss.cleave_dir = pygame.math.Vector2(1, 0)

            # Advance to completion of second cycle
            current_time += 1000
            mock_ticks.return_value = current_time
            self.boss.update()
            self.assertEqual(self.boss.boss_attack_state, 'idle', "Second cleave cycle should also complete cleanly")

    def test_boss_cleave_cycle_phase2(self):
        """Phase 2 boss (HP <= 100) completes cleave and projectile bursts without error."""
        self.boss.hp = 80
        initial_hp = self.player.health

        current_time = 20000
        with patch('pygame.time.get_ticks') as mock_ticks:
            mock_ticks.return_value = current_time

            self.boss.boss_attack_state = 'telegraph'
            self.boss.boss_telegraph_start = current_time
            self.boss.cleave_dir = pygame.math.Vector2(1, 0)
            self.boss.boss_burst_time = current_time - 3000 # ready for burst
            self.boss.update()

            self.assertEqual(self.boss.boss_attack_state, 'telegraph')
            self.assertEqual(self.player.health, initial_hp)

            # 999 ms
            current_time = 20999
            mock_ticks.return_value = current_time
            self.boss.update()
            self.assertEqual(self.boss.boss_attack_state, 'telegraph')

            # 1000 ms - Cleave release in phase 2
            current_time = 21000
            mock_ticks.return_value = current_time
            self.boss.update()

            self.assertEqual(self.boss.boss_attack_state, 'idle')
            self.assertEqual(self.boss.boss_phase, 2)
            self.assertLess(self.player.health, initial_hp)

if __name__ == '__main__':
    unittest.main()
