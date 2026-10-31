import unittest
import pygame
import os
import sys

# Ensure headless pygame
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

sys.path.insert(0, os.path.abspath('.'))

class TestBulletproofHitboxAndLOS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100))

    def test_particle_in_obstacle_sprites_does_not_crash_enemy_los(self):
        from src.entities import Player, Enemy, Particle, DebrisParticle
        from src.map_manager import CameraGroup

        vis_group = CameraGroup()
        obs_group = pygame.sprite.Group()
        enemy_group = pygame.sprite.Group()

        player = Player((100, 100), [vis_group], obs_group, enemy_group)
        enemy = Enemy((150, 150), [vis_group, enemy_group], obs_group, player, 'skeleton', visible_sprites=vis_group)

        # Force a Particle directly into obstacle_sprites
        p = Particle((125, 125), [obs_group, vis_group], color=(255, 100, 50))
        # Even if hitbox was deleted or missing:
        if hasattr(p, 'hitbox'):
            delattr(p, 'hitbox')

        # check line of fire must return without crashing
        has_fire = enemy.has_line_of_fire(player.hitbox.center)
        self.assertIsInstance(has_fire, bool)

        # check line of sight
        los = enemy.check_line_of_sight(force=True)
        self.assertIsInstance(los, bool)

    def test_arbitrary_sprite_without_hitbox_in_obstacles(self):
        from src.entities import Player, Enemy, FloorDecal

        obs_group = pygame.sprite.Group()
        dummy_sprite = pygame.sprite.Sprite(obs_group)
        dummy_sprite.rect = pygame.Rect(120, 120, 10, 10)
        # Note: no .hitbox attribute!

        decal = FloorDecal((130, 130), [obs_group], 'moss')
        self.assertIsNone(decal.hitbox)

        player = Player((50, 50), [], obs_group, pygame.sprite.Group())
        enemy = Enemy((200, 200), [], obs_group, player, 'skeleton')

        # None of these should raise AttributeError: '...' object has no attribute 'hitbox'
        los = enemy.has_line_of_fire()
        self.assertIsInstance(los, bool)

        dir_vec = enemy.calculate_direction(pygame.math.Vector2(player.hitbox.center))
        self.assertIsInstance(dir_vec, pygame.math.Vector2)

        # Movement collision check
        enemy.collision('horizontal', enemy.hitbox.copy())
        enemy.collision('vertical', enemy.hitbox.copy())

    def test_debris_particle_bounce_physics(self):
        from src.entities import DebrisParticle
        g = pygame.sprite.Group()
        debris = DebrisParticle((100, 100), [g], velocity=(2.0, 5.0))
        self.assertTrue(hasattr(debris, 'ground_y'))
        self.assertTrue(hasattr(debris, 'bounces'))
        self.assertTrue(hasattr(debris, 'restitution'))
        self.assertEqual(debris.restitution, 0.40)
        self.assertEqual(debris.bounces, 0)

        # Simulate fall past ground_y
        debris.pos.y = debris.ground_y + 1.0
        debris.vel.y = 8.0
        debris.update()
        self.assertEqual(debris.bounces, 1)
        self.assertLess(debris.vel.y, 0) # Bounced upward!

    def test_decorations_have_safe_hitboxes(self):
        from src.entities import FloorDecal, WaterRipple, CeilingDrip
        from src.map_manager import Torch, BossRunicCircle
        g = pygame.sprite.Group()

        decal = FloorDecal((50, 50), [g], 'moss')
        self.assertIsNone(decal.hitbox) # Floor decals have no physical hitbox

        torch = Torch((50, 50), [g])
        self.assertIsNotNone(torch.hitbox)
        self.assertIsInstance(torch.hitbox, pygame.Rect)

        runic = BossRunicCircle((50, 50), [g])
        self.assertIsNotNone(runic.hitbox)
        self.assertIsInstance(runic.hitbox, pygame.Rect)


    def test_enemy_projectile_with_hitboxless_or_particle_obstacle(self):
        from src.entities import EnemyProjectile, Particle
        obs_group = pygame.sprite.Group()
        vis_group = pygame.sprite.Group()
        p = Particle((100, 100), [obs_group, vis_group], color=(255, 200, 50))
        if hasattr(p, 'hitbox'):
            delattr(p, 'hitbox')
        
        # Hitboxless dummy obstacle
        dummy = pygame.sprite.Sprite(obs_group)
        dummy.rect = pygame.Rect(100, 100, 20, 20)
        
        proj = EnemyProjectile((100, 90), [vis_group], pygame.math.Vector2(0, 1), obs_group, None, proj_type='arrow')
        # update must not crash even with non-standard obstacles
        proj.update()
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
