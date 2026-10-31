import unittest
import sys
import os
import pygame

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.entities import Player, Enemy, Weapon

class DummyObstacle(pygame.sprite.Sprite):
    def __init__(self, rect, groups):
        super().__init__(groups)
        self.rect = pygame.Rect(rect)
        self.hitbox = pygame.Rect(rect)

class TestCombatAndMovement(unittest.TestCase):
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
        self.player = Player((500, 500), [self.visible_sprites], self.obstacle_sprites, self.enemy_sprites)

    def test_r03_terminal_death_cannot_be_undone_by_levelup(self):
        """Lethal damage immediately sets is_dead=True; subsequent XP gain/levelup cannot revive player."""
        self.player.health = 1.0
        self.player.exp = 90
        self.player.level = 1
        self.assertFalse(self.player.is_dead)

        # Take lethal damage
        self.player.take_damage(20)
        self.assertTrue(self.player.is_dead, "Player must be dead immediately after lethal damage")
        self.assertEqual(self.player.health, 0, "Health must not be negative or positive")

        # Concurrent level up from existing projectile / slash
        self.player.gain_exp(20) # 90 + 20 = 110 >= 100
        self.assertTrue(self.player.is_dead, "Player must remain dead after XP gain")
        self.assertEqual(self.player.health, 0, "Health must not be restored by level-up after death")

    def test_r04_enemy_separation_does_not_penetrate_walls(self):
        """Separate_from_enemies must never push an enemy into a static obstacle."""
        # Static wall from x=0 to x=64, y=0 to y=200
        wall = DummyObstacle((0, 0, 64, 200), [self.obstacle_sprites])
        
        # Enemy 1 placed right against wall at x=64
        enemy1 = Enemy((64, 100), [self.visible_sprites, self.enemy_sprites], self.obstacle_sprites, self.player, 'zombie')
        enemy1.hitbox.topleft = (64, 100)
        enemy1.pos = pygame.math.Vector2(enemy1.hitbox.topleft)

        # Enemy 2 placed at x=80, pushing enemy1 to the left (into wall)
        enemy2 = Enemy((80, 100), [self.visible_sprites, self.enemy_sprites], self.obstacle_sprites, self.player, 'zombie')
        enemy2.hitbox.topleft = (80, 100)
        enemy2.pos = pygame.math.Vector2(enemy2.hitbox.topleft)

        # Run separation
        enemy1.separate_from_enemies()

        # Enemy1 must NOT be inside the wall (hitbox.left must remain >= wall.hitbox.right)
        self.assertFalse(enemy1.hitbox.colliderect(wall.hitbox),
                        f"Enemy1 hitbox {enemy1.hitbox} penetrated wall {wall.hitbox}")
        self.assertGreaterEqual(enemy1.hitbox.left, wall.hitbox.right)

    def test_weapon_hit_does_not_shake_camera(self):
        calls = []
        self.visible_sprites.shake = lambda *args, **kwargs: calls.append((args, kwargs))
        enemy = Enemy((530, 500), [self.visible_sprites, self.enemy_sprites],
                      self.obstacle_sprites, self.player, 'zombie')
        hp_before = enemy.hp
        weapon = Weapon(self.player, [self.visible_sprites], pygame.math.Vector2(1, 0))
        weapon.update()
        self.assertLess(enemy.hp, hp_before)
        self.assertEqual(calls, [])

    def test_r04_weapon_knockback_does_not_push_enemy_into_wall(self):
        """Weapon knockback must respect obstacle collisions and not push enemy into walls."""
        # Wall at x=100..164
        wall = DummyObstacle((100, 0, 64, 200), [self.obstacle_sprites])

        # Enemy at x=90, facing right towards wall
        enemy = Enemy((90, 80), [self.visible_sprites, self.enemy_sprites], self.obstacle_sprites, self.player, 'zombie')
        enemy.hitbox.topleft = (90, 80)
        enemy.pos = pygame.math.Vector2(enemy.hitbox.topleft)

        # Weapon swing facing right (towards wall)
        self.player.rect.center = (70, 80)
        weapon = Weapon(self.player, [self.visible_sprites], pygame.math.Vector2(1, 0))
        weapon.update()

        self.assertFalse(enemy.hitbox.colliderect(wall.hitbox),
                        f"Enemy knocked back into wall: enemy hitbox {enemy.hitbox}, wall {wall.hitbox}")

    def test_r05_enemy_navigates_around_obstacle_to_target(self):
        """Enemy with blocked direct line navigates around straight wall and reaches goal."""
        # Obstacle wall: Rect(150, 50, 64, 200)
        wall = DummyObstacle((150, 50, 64, 200), [self.obstacle_sprites])
        
        target_pos = pygame.math.Vector2(300, 150)
        enemy = Enemy((110, 150), [self.visible_sprites, self.enemy_sprites], self.obstacle_sprites, self.player, 'zombie')
        enemy.hitbox.center = (110, 150)
        enemy.pos = pygame.math.Vector2(enemy.hitbox.topleft)
        enemy.speed = 3.0

        # Simulate updates
        for step in range(300):
            diff = target_pos - pygame.math.Vector2(enemy.hitbox.center)
            if diff.magnitude() < 20:
                break
            direction = enemy.calculate_direction(target_pos)
            enemy.direction = direction
            enemy.move(enemy.speed)

        final_pos = enemy.hitbox.center
        self.assertGreater(final_pos[0], 214, f"Enemy should navigate past wall x=214, but ended at {final_pos}")
        dist_to_target = (target_pos - pygame.math.Vector2(final_pos)).magnitude()
        self.assertLess(dist_to_target, 50, f"Enemy should reach near target (300,150), distance was {dist_to_target}")

if __name__ == '__main__':
    unittest.main()
