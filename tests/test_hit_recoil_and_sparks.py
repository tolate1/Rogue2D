import unittest
import pygame
import math
from src.entities import Player, Enemy, Weapon
from src.settings import TILE_SIZE

class TestHitRecoilAndDirectionalSparks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100), pygame.HIDDEN)

    def setUp(self):
        self.groups = [pygame.sprite.Group()]
        self.obstacles = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.player = Player((100, 100), self.groups, self.obstacles, self.enemy_group)
        self.enemy = Enemy((140, 100), self.groups, self.obstacles, self.player, 'skeleton')
        self.enemy_group.add(self.enemy)

    def test_enemy_take_damage_records_hit_angle_and_hit_stop(self):
        """Enemy.take_damage correctly records hit_angle, is_crit_hit, and hit_stop_until."""
        now = pygame.time.get_ticks()
        self.enemy.take_damage(15, source='weapon', is_crit=True, hit_angle=math.radians(45))
        self.assertTrue(self.enemy.is_crit_hit)
        self.assertAlmostEqual(self.enemy.hit_angle, math.radians(45), places=2)
        self.assertGreaterEqual(self.enemy.hit_stop_until, now + 40)

    def test_enemy_squash_and_stretch_deformation(self):
        """Enemy.animate dynamically squashes/stretches sprite during hurt window."""
        self.enemy.took_damage_time = pygame.time.get_ticks() - 40 # Middle of hurt window
        self.enemy.is_crit_hit = True
        self.enemy.hit_angle = 0.0 # Horizontal blow
        
        orig_w = self.enemy.image.get_width()
        orig_h = self.enemy.image.get_height()
        
        self.enemy.animate()
        
        # Horizontal blow compresses width and stretches height
        self.assertNotEqual((self.enemy.image.get_width(), self.enemy.image.get_height()), (orig_w, orig_h),
                           "Sprite dimensions should deform during hit squash window")
        self.assertLessEqual(self.enemy.image.get_width(), orig_w, "Width should compress on horizontal hit")
        self.assertGreaterEqual(self.enemy.image.get_height(), orig_h, "Height should stretch on horizontal hit")

    def test_hit_stop_freezes_enemy_direction(self):
        """Enemy.update zeros out direction vector during hit-stop."""
        now = pygame.time.get_ticks()
        self.enemy.hit_stop_until = now + 500
        self.enemy.direction = pygame.math.Vector2(1, 1)
        self.enemy.update()
        self.assertEqual(self.enemy.direction.length(), 0.0, "Direction should be zeroed during hit-stop")

    def test_player_hit_stop_freezes_movement(self):
        """Player.update zeros out effective movement while hit_stop_until is active."""
        now = pygame.time.get_ticks()
        self.player.hit_stop_until = now + 500
        self.player.direction = pygame.math.Vector2(1, 0)
        old_pos_x = self.player.hitbox.x
        self.player.update()
        self.assertEqual(self.player.hitbox.x, old_pos_x, "Player should not move during hit-stop micro-freeze")

    def test_weapon_directional_sparks_spawn_on_hit(self):
        """Weapon swing collision against enemy spawns directional spark particles."""
        weapon = Weapon(self.player, self.groups, pygame.math.Vector2(1, 0), weapon_type='claymore')
        self.enemy.rect.center = weapon.rect.center
        
        initial_particles = [s for s in self.groups[0] if getattr(s, 'sprite_type', None) == 'particle']
        weapon.update()
        new_particles = [s for s in self.groups[0] if getattr(s, 'sprite_type', None) == 'particle']
        
        self.assertGreater(len(new_particles), len(initial_particles), "Weapon hit must spawn high-velocity spark particles")
        self.assertGreaterEqual(self.player.hit_stop_until, pygame.time.get_ticks(), "Player must receive micro-freeze on claymore swing")

if __name__ == '__main__':
    unittest.main()
