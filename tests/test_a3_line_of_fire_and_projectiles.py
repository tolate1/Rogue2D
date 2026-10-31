import unittest
import os
import sys

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
from src.entities import Player, Enemy, EnemyProjectile, Particle

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, rect, groups):
        super().__init__(groups)
        self.image = pygame.Surface((rect.width, rect.height))
        self.rect = pygame.Rect(rect)
        self.hitbox = pygame.Rect(rect)

class BreakableObstacle(Obstacle):
    def __init__(self, rect, groups):
        super().__init__(rect, groups)
        self.destroyed = False

    def destroy(self):
        self.destroyed = True
        self.kill()
        return None


class TestA3LineOfFireAndProjectiles(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.screen = pygame.display.set_mode((400, 400))
        self.visible_sprites = pygame.sprite.Group()
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        
        self.player = Player((300, 100), [self.visible_sprites], self.obstacle_sprites, self.enemy_sprites)
        self.skeleton = Enemy((100, 100), [self.visible_sprites, self.enemy_sprites], 
                              self.obstacle_sprites, self.player, 'skeleton', visible_sprites=self.visible_sprites)
        self.skeleton.can_attack = True
        self.skeleton.attack_time = 0

    def tearDown(self):
        pygame.quit()

    def test_1_los_blocked_by_wall(self):
        """1. Wall directly between shooter and player blocks line of fire."""
        # Wall placed at x=200 between skeleton (x=100) and player (x=300)
        Obstacle(pygame.Rect(190, 70, 32, 64), [self.obstacle_sprites])
        
        self.assertFalse(self.skeleton.has_line_of_fire(), "Line of fire must be False when wall is between")

    def test_2_los_clear_when_no_obstacle(self):
        """2. Clear path between shooter and player returns True for line of fire."""
        self.assertTrue(self.skeleton.has_line_of_fire(), "Line of fire must be True when path is clear")

    def test_3_shoot_cancelled_if_player_behind_wall(self):
        """3. Even if attacking, shoot() cancels and does not spawn projectile if line of fire is blocked."""
        Obstacle(pygame.Rect(190, 70, 32, 64), [self.obstacle_sprites])
        
        count_before = len([s for s in self.visible_sprites if isinstance(s, EnemyProjectile)])
        self.skeleton.shoot()
        count_after = len([s for s in self.visible_sprites if isinstance(s, EnemyProjectile)])
        
        self.assertEqual(count_after, count_before, "No projectile should be spawned through wall")

    def test_4_shoot_succeeds_when_clear(self):
        """4. shoot() spawns projectile into visible_sprites when line of fire is clear."""
        count_before = len([s for s in self.visible_sprites if isinstance(s, EnemyProjectile)])
        self.skeleton.shoot()
        count_after = len([s for s in self.visible_sprites if isinstance(s, EnemyProjectile)])
        
        self.assertEqual(count_after, count_before + 1, "Projectile must be spawned when line of fire is clear")

    def test_5_projectile_lifetime_expiration(self):
        """5. Expired projectile dies and does not process further."""
        proj = EnemyProjectile((150, 100), [self.visible_sprites], pygame.math.Vector2(1, 0), self.obstacle_sprites, self.player)
        # Artificially expire
        proj.spawn_time = pygame.time.get_ticks() - 2000
        proj.update()
        
        self.assertFalse(proj.alive(), "Expired projectile must be killed")

    def test_6_projectile_wall_collision_blocks_damage_and_kills_projectile(self):
        """6. Wall placed before player intercepts projectile, killing it with zero damage to player."""
        # Obstacle between projectile and player
        wall = Obstacle(pygame.Rect(200, 80, 32, 64), [self.obstacle_sprites])
        proj = EnemyProjectile((195, 100), [self.visible_sprites], pygame.math.Vector2(1, 0), self.obstacle_sprites, self.player)
        
        initial_hp = self.player.health
        proj.update()
        
        self.assertFalse(proj.alive(), "Projectile must be killed on wall collision")
        self.assertEqual(self.player.health, initial_hp, "Player must not take damage when wall is hit")

    def test_7_projectile_single_hit_damage(self):
        """7. Projectile deals damage exactly once and cannot damage repeatedly."""
        # Spawn projectile overlapping player directly
        proj = EnemyProjectile(self.player.rect.center, [self.visible_sprites], pygame.math.Vector2(1, 0), self.obstacle_sprites, self.player)
        initial_hp = self.player.health
        
        proj.update()
        self.assertEqual(self.player.health, initial_hp - 10, "First hit should deal 10 damage")
        self.assertFalse(proj.alive(), "Projectile must be dead after hit")
        
        # Subsequent update on dead projectile does nothing
        proj.update()
        self.assertEqual(self.player.health, initial_hp - 10, "Must not deal duplicate damage")

    def test_8_projectile_swept_clipline_prevents_tunneling(self):
        """8. Fast moving projectile sweeping across thin obstacle detects collision via clipline."""
        # Thin obstacle at x=150
        wall = Obstacle(pygame.Rect(150, 80, 4, 64), [self.obstacle_sprites])
        
        # Projectile at x=148 moving right at speed 6 (would jump from 148 to 154)
        proj = EnemyProjectile((148, 100), [self.visible_sprites], pygame.math.Vector2(1, 0), self.obstacle_sprites, self.player)
        proj.update()
        
        self.assertFalse(proj.alive(), "Swept projectile trajectory must collide with wall")

    def test_14_projectile_enemy_hit_applies_damage_without_signature_error(self):
        """Projectile damage must use Enemy.take_damage's actual source contract."""
        proj = EnemyProjectile(self.skeleton.rect.center, [self.visible_sprites], pygame.math.Vector2(1, 0), self.obstacle_sprites, None, proj_type='fireball')
        proj.target_group = [self.skeleton]
        initial_hp = self.skeleton.hp

        proj.update()

        self.assertEqual(self.skeleton.hp, initial_hp - proj.damage)
        self.assertFalse(proj.alive())

    def test_15_bow_attack_uses_aim_and_player_attack_stat(self):
        """Bow projectiles must use the requested direction and equipped attack total."""
        class Bow:
            weapon_type = 'bow'

        self.player.equipped['weapon'] = Bow()
        self.player.stats['attack'] = 23
        self.player.crit_rate = 0
        self.player.attack(pygame.math.Vector2(-1, 0))
        projectiles = [sprite for sprite in self.visible_sprites if isinstance(sprite, EnemyProjectile)]
        proj = projectiles[-1]

        self.assertLess(proj.direction.x, 0)
        self.assertEqual(proj.damage, 23)

    def test_9_fireball_wall_hit_has_impact_effect(self):
        """Elemental projectiles should visibly resolve when blocked by a wall."""
        Obstacle(pygame.Rect(200, 70, 32, 64), [self.obstacle_sprites])
        proj = EnemyProjectile((185, 100), [self.visible_sprites], pygame.math.Vector2(1, 0), self.obstacle_sprites, self.player, proj_type='fireball')

        proj.update()

        self.assertFalse(proj.alive())
        self.assertTrue(any(isinstance(sprite, Particle) for sprite in self.visible_sprites))

    def test_10_player_projectile_breaks_destructible(self):
        """Player arrows should interact with crates and barrels like melee strikes do."""
        crate = BreakableObstacle(pygame.Rect(200, 70, 32, 64), [self.obstacle_sprites])
        proj = EnemyProjectile((185, 100), [self.visible_sprites], pygame.math.Vector2(1, 0), self.obstacle_sprites, None, proj_type='arrow')
        proj.owner = self.player

        proj.update()

        self.assertTrue(crate.destroyed)
        self.assertFalse(proj.alive())

    def test_11_enemy_projectile_does_not_break_destructible(self):
        """Enemy shots remain blocked by destructibles without destroying player loot."""
        crate = BreakableObstacle(pygame.Rect(200, 70, 32, 64), [self.obstacle_sprites])
        proj = EnemyProjectile((185, 100), [self.visible_sprites], pygame.math.Vector2(1, 0), self.obstacle_sprites, self.player, proj_type='arrow')

        proj.update()

        self.assertFalse(crate.destroyed)
        self.assertFalse(proj.alive())

    def test_12_black_hole_pull_respects_obstacle_collision(self):
        """Black-hole gravity must stop at walls instead of teleporting entities through them."""
        wall = Obstacle(pygame.Rect(200, 40, 20, 120), [self.obstacle_sprites])
        proj = EnemyProjectile((250, 86), [self.visible_sprites], pygame.math.Vector2(), self.obstacle_sprites, None, proj_type='black_hole')
        proj.speed = 0
        proj.target_group = [self.skeleton]

        for _ in range(100):
            proj.update()

        self.assertLessEqual(self.skeleton.hitbox.right, wall.hitbox.left)

    def test_13_enemy_black_hole_pull_respects_player_collision(self):
        """Enemy black-hole gravity must also use the player's wall collision rules."""
        wall = Obstacle(pygame.Rect(260, 40, 20, 120), [self.obstacle_sprites])
        proj = EnemyProjectile((220, 100), [self.visible_sprites], pygame.math.Vector2(), self.obstacle_sprites, self.player, proj_type='black_hole')
        proj.speed = 0

        for _ in range(100):
            proj.update()

        self.assertGreaterEqual(self.player.hitbox.left, wall.hitbox.right)

if __name__ == '__main__':
    unittest.main()
