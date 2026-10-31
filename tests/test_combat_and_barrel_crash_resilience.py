import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import unittest
import pygame
import random
from src.settings import TILE_SIZE, WIDTH, HEIGHT
from src.entities import Player, Enemy, Weapon, EnemyProjectile, Particle, DebrisParticle, DamageText
from src.items import Breakable, Gold, Item
from src.map_manager import CameraGroup

class TestCombatAndBarrelCrashResilience(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((WIDTH, HEIGHT))

    def setUp(self):
        self.visible_sprites = CameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.player = Player((200, 200), [self.visible_sprites], self.obstacle_sprites, self.enemy_sprites)
        self.player.visible_sprites = self.visible_sprites

    def test_breakable_destruction_and_particles(self):
        """Stress-tests barrel destruction, debris generation, gold and potion spawning."""
        for i in range(15):
            brk = Breakable((250 + i * 20, 200), [self.visible_sprites, self.obstacle_sprites])
            # Call destroy multiple times to ensure idempotency
            loot1 = brk.destroy()
            loot2 = brk.destroy()
            self.assertIsNone(loot2)

        # Update visible sprites multiple frames to ensure particle physics and gold magnet do not crash
        for _ in range(30):
            self.visible_sprites.update()
            self.visible_sprites.custom_draw(self.player)

    def test_debris_particle_small_size_no_randrange_error(self):
        """Specifically verifies that small sizes (1, 2, 3) in DebrisParticle do not trigger empty range ValueError."""
        for sz in [1, 2, 3, 4, 5, 6, 8, 12]:
            p = DebrisParticle((100, 100), [self.visible_sprites], size=sz)
            for _ in range(15):
                p.update()

    def test_weapon_strikes_barrel_and_enemy_simultaneously(self):
        """Verifies that swinging a weapon hitting both an enemy and a barrel in one tick does not crash."""
        enemy = Enemy((220, 200), [self.visible_sprites, self.enemy_sprites], self.obstacle_sprites, self.player, 'goblin', visible_sprites=self.visible_sprites)
        brk = Breakable((220, 200), [self.visible_sprites, self.obstacle_sprites])

        # Swing weapon towards target
        w = Weapon(self.player, [self.visible_sprites], pygame.math.Vector2(1, 0), weapon_type='sword')
        
        # Run 20 updates (full lifespan of weapon)
        for _ in range(20):
            w.update()
            self.visible_sprites.update()
            self.visible_sprites.custom_draw(self.player)

    def test_enemy_hits_player_and_dies(self):
        """Verifies player taking damage, projectile collision, and enemy taking lethal damage."""
        # Player taking damage from position
        self.player.take_damage(20, source_pos=(180, 200))
        self.assertEqual(self.player.health, 80)
        self.player.animate()

        # Projectile hitting player
        proj = EnemyProjectile((200, 200), [self.visible_sprites], pygame.math.Vector2(1, 0), self.obstacle_sprites, self.player)
        proj.update()

        # Enemy taking fatal damage
        enemy = Enemy((250, 200), [self.visible_sprites, self.enemy_sprites], self.obstacle_sprites, self.player, 'skeleton', visible_sprites=self.visible_sprites)
        enemy.take_damage(100, source='claymore')
        self.assertFalse(enemy.alive())

        # Render pass
        self.visible_sprites.update()
        self.visible_sprites.custom_draw(self.player)

    def test_gold_magnet_and_none_groups_safety(self):
        """Verifies Gold and Particles never crash even when groups is None or contains None."""
        g = Gold((205, 200), [None], 10, self.player)
        p = Particle((200, 200), [None])
        dt = DamageText("-15", (200, 200), [None])
        dp = DebrisParticle((200, 200), [None])
        
        # Safe updates
        g.update()
        p.update()
        dt.update()
        dp.update()

if __name__ == '__main__':
    unittest.main()
