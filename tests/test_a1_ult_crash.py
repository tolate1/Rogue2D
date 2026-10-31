import unittest
import os
import sys

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
from src.entities import Player, Enemy, EnemyProjectile

class TestA1UltAndProjectileSafety(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.screen = pygame.display.set_mode((100, 100))
        self.visible_sprites = pygame.sprite.Group()
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        
        self.player = Player((100, 100), [self.visible_sprites], self.obstacle_sprites, self.enemy_sprites)

    def tearDown(self):
        pygame.quit()

    def test_living_skeleton_shoots_normally(self):
        """Verifies that a living skeleton ready to attack shoots normally and spawns a projectile in visible_sprites."""
        skeleton = Enemy((200, 100), [self.visible_sprites, self.enemy_sprites], 
                         self.obstacle_sprites, self.player, 'skeleton', visible_sprites=self.visible_sprites)
        skeleton.can_attack = True
        skeleton.attack_time = 0
        skeleton.has_los = True
        skeleton.los_timer = 0
        
        initial_proj_count = len([s for s in self.visible_sprites if isinstance(s, EnemyProjectile)])
        self.assertEqual(initial_proj_count, 0)
        
        # Calling update on skeleton triggers shoot()
        skeleton.update()
        
        # Verify projectile spawned into visible_sprites
        projs = [s for s in self.visible_sprites if isinstance(s, EnemyProjectile)]
        self.assertEqual(len(projs), 1, "Living skeleton should spawn 1 projectile")
        proj = projs[0]
        self.assertTrue(proj.alive(), "Spawned projectile should be alive")
        
        # Verify projectile updates and moves
        start_x = proj.rect.x
        proj.update()
        self.assertNotEqual(proj.rect.x, start_x, "Projectile should move when updated")

    def test_ult_during_full_visible_sprites_update(self):
        """Verifies that when player ults during a full visible_sprites.update(),
        skeletons updated in the same frame do not crash with IndexError and do not spawn projectiles."""
        # Create multiple skeletons within ult range (dist < 800)
        s1 = Enemy((150, 100), [self.visible_sprites, self.enemy_sprites], 
                   self.obstacle_sprites, self.player, 'skeleton', visible_sprites=self.visible_sprites)
        s2 = Enemy((180, 120), [self.visible_sprites, self.enemy_sprites], 
                   self.obstacle_sprites, self.player, 'skeleton', visible_sprites=self.visible_sprites)
        
        for s in (s1, s2):
            s.can_attack = True
            s.attack_time = 0
            s.has_los = True
            s.los_timer = 0
        
        # Configure player to trigger ult during its update
        original_player_update = self.player.update
        def player_update_with_ult():
            self.player.ult()
            original_player_update()
        self.player.update = player_update_with_ult
        
        # Run normal world update on visible_sprites
        # Player updates first, kills s1 and s2 via ult()
        # visible_sprites.update() continues iterating and calls s1.update(), s2.update()
        try:
            self.visible_sprites.update()
        except IndexError as e:
            self.fail(f"visible_sprites.update() crashed with IndexError: {e}")
        except Exception as e:
            self.fail(f"visible_sprites.update() raised unexpected exception: {e}")
            
        # Verify all skeletons were killed
        self.assertFalse(s1.alive(), "Skeleton 1 should be dead")
        self.assertFalse(s2.alive(), "Skeleton 2 should be dead")
        
        # Verify no projectiles were created by the killed skeletons
        projs = [s for s in self.visible_sprites if isinstance(s, EnemyProjectile)]
        self.assertEqual(len(projs), 0, "Dead skeletons should not spawn projectiles")

    def test_dead_enemy_shoot_is_noop(self):
        """Verifies that calling shoot directly on a dead enemy does not crash or spawn projectiles."""
        skeleton = Enemy((150, 100), [self.visible_sprites, self.enemy_sprites], 
                         self.obstacle_sprites, self.player, 'skeleton', visible_sprites=self.visible_sprites)
        skeleton.kill()
        
        initial_visible_count = len(self.visible_sprites)
        skeleton.shoot()
        self.assertEqual(len(self.visible_sprites), initial_visible_count, "No projectile should be spawned by dead enemy")

    def test_projectile_wall_collision_stops_damage(self):
        """Verifies that a projectile hitting a wall dies and does not damage player in the same frame."""
        wall = pygame.sprite.Sprite([self.obstacle_sprites])
        wall.image = pygame.Surface((32, 32))
        wall.rect = pygame.Rect(100, 100, 32, 32)
        wall.hitbox = wall.rect
        
        # Player is placed right behind/overlapping the wall
        self.player.rect.topleft = (100, 100)
        self.player.hitbox.topleft = (100, 100)
        initial_health = self.player.health
        
        # Projectile spawned right on the wall
        proj = EnemyProjectile((100, 100), [self.visible_sprites], pygame.math.Vector2(1, 0), self.obstacle_sprites, self.player)
        proj.update()
        
        self.assertFalse(proj.alive(), "Projectile should be killed on wall collision")
        self.assertEqual(self.player.health, initial_health, "Player should not take damage when projectile hits wall")

if __name__ == '__main__':
    unittest.main()
