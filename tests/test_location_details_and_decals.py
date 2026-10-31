import os
import unittest
import pygame
import math
from src.settings import TILE_SIZE
from src.entities import FloorDecal, WaterRipple, CeilingDrip, InteractiveDebris, Player
from src.map_manager import Level, CameraGroup

class TestLocationDetailsAndDecals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        if not pygame.display.get_init() or pygame.display.get_surface() is None:
            pygame.display.set_mode((960, 640))

    def setUp(self):
        self.group = pygame.sprite.Group()

    def test_floor_decal_types_and_layer(self):
        decal_types = ['cracks', 'moss', 'blood', 'puddle', 'rune']
        for idx, dt in enumerate(decal_types):
            pos = (100 + idx * 50, 150)
            decal = FloorDecal(pos, [self.group], decal_type=dt, var=0)
            self.assertEqual(decal.sprite_type, 'decal')
            self.assertIsNone(decal.hitbox)
            self.assertEqual(decal.rect.center, pos)
            self.assertIsNotNone(decal.image)

    def test_water_ripple_expansion_and_decay(self):
        pos = (200, 200)
        ripple = WaterRipple(pos, [self.group])
        self.assertEqual(ripple.sprite_type, 'floor_overlay')
        self.assertEqual(ripple.rect.center, pos)
        
        # Initial frame
        ripple.update()
        self.assertTrue(ripple.alive())

        # Simulate time passing past duration (520ms)
        ripple.spawn_time -= 600
        ripple.update()
        self.assertFalse(ripple.alive(), "Ripple should kill itself after duration expires")

    def test_ceiling_drip_gravity_and_impact(self):
        target_pos = (300, 400)
        drip = CeilingDrip(target_pos, [self.group])
        self.assertEqual(drip.sprite_type, 'ui_effect')
        self.assertLess(drip.y, drip.target_y)
        self.assertTrue(drip.alive())

        # Simulate falling until impact
        initial_y = drip.y
        for _ in range(50):
            if not drip.alive():
                break
            drip.update()

        self.assertFalse(drip.alive(), "Ceiling drop should terminate upon hitting target_y")
        # Check that WaterRipple was spawned in group
        ripples = [s for s in self.group if isinstance(s, WaterRipple)]
        self.assertGreaterEqual(len(ripples), 1, "Impact should spawn a WaterRipple")
        self.assertEqual(ripples[0].pos, target_pos)

    def test_interactive_debris_proximity_crush(self):
        pos = (250, 250)
        debris = InteractiveDebris(pos, [self.group])
        self.assertFalse(debris.is_crushed)
        self.assertEqual(debris.sprite_type, 'decal')

        # Dummy player far away
        class DummyPlayer:
            def __init__(self, p):
                self.hitbox = pygame.Rect(p[0] - 10, p[1] - 10, 20, 20)
                self.rect = self.hitbox

        player_far = DummyPlayer((500, 500))
        debris.update_proximity(player_far)
        self.assertFalse(debris.is_crushed)

        # Player steps onto debris
        player_near = DummyPlayer(pos)
        debris.update_proximity(player_near)
        self.assertTrue(debris.is_crushed, "Stepping on bone pile should trigger crush")
        self.assertEqual(debris.image, debris.crushed_img)

        # Second trigger should be idempotent
        debris.trigger_crush()
        self.assertTrue(debris.is_crushed)

    def test_dungeon_level_decals_and_debris_spawn(self):
        level = Level(current_floor=1)
        level.create_map()
        
        self.assertTrue(hasattr(level, 'floor_decals'), "Level should track floor_decals")
        self.assertGreaterEqual(len(level.floor_decals), 5, "Dungeon floor should spawn multiple floor decals")
        
        self.assertTrue(hasattr(level, 'debris_sprites'), "Level should track debris_sprites")
        self.assertGreaterEqual(len(level.debris_sprites), 1, "Dungeon floor should spawn breakable bone debris")

    def test_camera_group_sorting_layer(self):
        cg = CameraGroup()
        f_decal = FloorDecal((100, 100), [cg], 'cracks', 0)
        ripple = WaterRipple((120, 120), [cg])

        def get_layer(s):
            st = getattr(s, 'sprite_type', 'other')
            if st == 'floor': return 0
            if st in ('floor_overlay', 'decal', 'hazard'): return 1
            return 2

        self.assertEqual(get_layer(f_decal), 1)
        self.assertEqual(get_layer(ripple), 1)

if __name__ == '__main__':
    unittest.main()
