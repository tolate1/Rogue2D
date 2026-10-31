import unittest
import sys
import os
import pygame

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.entities import Player, Enemy, Weapon, DamageText
from src.sound_manager import SoundManager, play_sfx

class TestStageDJuiceAndSFX(unittest.TestCase):
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
        self.player = Player((100, 100), [self.visible_sprites], self.obstacle_sprites, self.enemy_sprites)

    def test_sound_manager_safe_execution(self):
        """Sound manager operates safely without crashing even in headless / dummy environments."""
        sm = SoundManager.get_instance()
        self.assertIsNotNone(sm)
        # Playing valid or non-existent sounds should never raise exceptions
        play_sfx('hit')
        play_sfx('dash')
        play_sfx('chest')
        play_sfx('unknown_sound')

    def test_damage_text_spawning_and_float(self):
        """DamageText renders floating numbers that drift upward and terminate after duration."""
        dmg = DamageText("-25", (100, 100), [self.visible_sprites])
        initial_y = dmg.rect.y
        self.assertTrue(dmg.alive())

        dmg.update()
        self.assertLess(dmg.rect.y, initial_y, "Damage text must float upward")

        # Advance past duration
        dmg.spawn_time = pygame.time.get_ticks() - 600
        dmg.update()
        self.assertFalse(dmg.alive(), "Damage text should expire after duration")

    def test_weapon_knockback(self):
        """Hitting an enemy with weapon applies physical knockback in attack direction."""
        zombie = Enemy((130, 100), [self.visible_sprites, self.enemy_sprites],
                       self.obstacle_sprites, self.player, 'zombie', visible_sprites=self.visible_sprites)
        initial_x = zombie.rect.centerx

        weapon = Weapon(self.player, [self.visible_sprites], pygame.math.Vector2(1, 0))
        weapon.rect.center = zombie.rect.center

        weapon.update()
        self.assertEqual(zombie.rect.centerx, initial_x + 8, "Enemy should be knocked back by 8 pixels")

    def test_enemy_white_flash_on_damage(self):
        """Enemy takes damage and triggers flash visual feedback."""
        zombie = Enemy((100, 100), [self.visible_sprites, self.enemy_sprites],
                       self.obstacle_sprites, self.player, 'zombie', visible_sprites=self.visible_sprites)
        zombie.take_damage(10)
        self.assertGreater(zombie.took_damage_time, 0)

        # Trigger animate while flash is active
        zombie.animate()
        self.assertIsNotNone(zombie.image)

if __name__ == '__main__':
    unittest.main()
