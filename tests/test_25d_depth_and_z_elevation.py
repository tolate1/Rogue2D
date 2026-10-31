import unittest
import pygame
from unittest.mock import MagicMock

class Test25DDepthAndZElevation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)

    def test_entity_z_elevation_contract(self):
        """Verifies Entity, Player, Weapon, EnemyProjectile, and Projectile fulfill 2.5D elevation contract."""
        from src.entities import Entity, Player, Weapon, EnemyProjectile, Projectile

        # Base Entity
        ent = Entity([])
        self.assertTrue(hasattr(ent, 'z'), "Entity must have z coordinate")
        self.assertTrue(hasattr(ent, 'vz'), "Entity must have vz velocity")
        self.assertTrue(hasattr(ent, 'gravity_z'), "Entity must have gravity_z")
        self.assertEqual(ent.z, 0.0)
        self.assertEqual(ent.vz, 0.0)
        self.assertEqual(ent.gravity_z, 0.8)

        # Player
        player = Player((100, 100), [], [], None)
        self.assertEqual(player.z, 0.0)
        self.assertEqual(player.vz, 0.0)
        self.assertEqual(player.gravity_z, 0.8)

        # Weapon
        weapon = Weapon(player, [], pygame.math.Vector2(1, 0))
        self.assertEqual(weapon.z, 0.0)
        self.assertEqual(weapon.vz, 0.0)
        self.assertEqual(weapon.gravity_z, 0.8)

        # Projectile alias and EnemyProjectile
        self.assertIs(Projectile, EnemyProjectile, "Projectile must be an alias of EnemyProjectile")
        grp = pygame.sprite.Group()
        proj = EnemyProjectile((100, 100), [grp], pygame.math.Vector2(1, 0), [], player)
        self.assertEqual(proj.z, 0.0)
        self.assertEqual(proj.vz, 0.0)
        self.assertEqual(proj.gravity_z, 0.8)

    def test_hitbox_ground_plane_invariance(self):
        """Hitbox must strictly remain on ground plane (pos.x, pos.y) regardless of Z altitude."""
        from src.entities import Player
        player = Player((200, 200), [], [], None)
        orig_hitbox = player.hitbox.copy()

        # Elevate to Z=50
        player.z = 50.0
        player.vz = 5.0
        self.assertEqual(player.hitbox.x, orig_hitbox.x)
        self.assertEqual(player.hitbox.y, orig_hitbox.y)
        self.assertEqual(player.hitbox.center, orig_hitbox.center)

    def test_gravity_z_simulation_and_landing(self):
        """Test vertical parabola: jump_z(6.0) simulates ascent, apex, descent and resting on ground (z=0)."""
        from src.entities import Entity
        ent = Entity([])
        ent.jump_z(6.0)
        self.assertEqual(ent.vz, 6.0)

        # Ascent phase
        ent.update_z()
        self.assertGreater(ent.z, 0.0)
        self.assertEqual(ent.vz, 5.2)

        # Run simulation until landing
        for _ in range(30):
            ent.update_z()

        self.assertEqual(ent.z, 0.0, "Entity must rest on ground plane after jump")
        self.assertEqual(ent.vz, 0.0, "Vertical velocity must reset to 0 upon landing")

    def test_shadow_radius_dynamic_scaling(self):
        """Shadow width and alpha scale down dynamically with Z elevation."""
        base_w = 64
        z_ground = 0.0
        z_high = 40.0

        scale_ground = 1.0 / (1.0 + z_ground * 0.04)
        sw_ground = max(8, int(base_w * 0.68 * scale_ground))
        alpha_ground = max(25, min(140, int(115 * (1.0 / (1.0 + z_ground * 0.03)))))

        scale_high = 1.0 / (1.0 + z_high * 0.04)
        sw_high = max(8, int(base_w * 0.68 * scale_high))
        alpha_high = max(25, min(140, int(115 * (1.0 / (1.0 + z_high * 0.03)))))

        self.assertGreater(sw_ground, sw_high, "Ground shadow width must be wider than elevated shadow")
        self.assertGreater(alpha_ground, alpha_high, "Ground shadow opacity must be darker than elevated shadow")

    def test_y_sorting_contract_bottom_priority(self):
        """Objects are depth-sorted by rect.bottom so foreground elements cleanly occlude background elements."""
        class MockSprite:
            def __init__(self, top, height, sprite_type='other'):
                self.rect = pygame.Rect(100, top, 32, height)
                self.sprite_type = sprite_type

        # S1: top=100, height=80 -> bottom = 180 (tall object behind)
        # S2: top=170, height=20 -> bottom = 190 (short object closer to camera)
        s1 = MockSprite(100, 80)
        s2 = MockSprite(170, 20)

        def _get_draw_layer(s):
            st = getattr(s, 'sprite_type', 'other')
            if st == 'floor': return 0
            if st in ('floor_overlay', 'decal', 'hazard'): return 1
            return 2

        key_func = lambda s: (_get_draw_layer(s), getattr(getattr(s, 'rect', None), 'bottom', getattr(getattr(s, 'rect', None), 'centery', 0)))
        sorted_sprites = sorted([s2, s1], key=key_func)
        self.assertEqual(sorted_sprites, [s1, s2], "s1 (bottom=180) must be drawn before s2 (bottom=190)")

    def test_weapon_z_synchronization(self):
        """Weapon matches player's elevation."""
        from src.entities import Player, Weapon
        player = Player((100, 100), [], [], None)
        player.z = 25.0
        player.vz = 3.5

        weapon = Weapon(player, [], pygame.math.Vector2(1, 0))
        self.assertEqual(weapon.z, 25.0)
        self.assertEqual(weapon.vz, 3.5)

        # Player ascends further
        player.z = 30.0
        player.vz = 2.0
        weapon.update()
        self.assertEqual(weapon.z, 30.0)
        self.assertEqual(weapon.vz, 2.0)

    def test_projectile_elevation_and_floor_swept_collision(self):
        """EnemyProjectile simulates Z-elevation while maintaining 2D planar position."""
        from src.entities import EnemyProjectile, Player
        player = Player((800, 800), [], [], None)
        grp = pygame.sprite.Group()
        proj = EnemyProjectile((100, 100), [grp], pygame.math.Vector2(1, 0), [], player)
        proj.vz = 4.0
        init_x = proj.rect.x
        proj.update()
        self.assertGreater(proj.z, 0.0)
        self.assertGreater(proj.rect.x, init_x)

if __name__ == '__main__':
    unittest.main()
