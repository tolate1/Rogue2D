import unittest
import pygame
import os
import sys
import math

# Headless pygame
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

sys.path.insert(0, os.path.abspath('.'))

class TestGroundMistAndFlameWind(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((200, 200))

    def setUp(self):
        self.group = pygame.sprite.Group()

    def test_ground_mist_creation_and_attributes(self):
        from src.entities import GroundMist
        biomes = ['dungeon', 'crypt', 'ice', 'volcano', 'forest', 'fungal', 'void']
        for b in biomes:
            mist = GroundMist((100, 100), [self.group], biome=b)
            self.assertEqual(mist.sprite_type, 'floor_overlay')
            self.assertEqual(mist.hitbox, pygame.Rect(0, 0, 0, 0))
            self.assertIsNotNone(mist.image)
            self.assertEqual(mist.rect.center, (100, 100))

    def test_ground_mist_drift_and_pulsation(self):
        from src.entities import GroundMist
        bound = pygame.Rect(50, 50, 200, 200)
        mist = GroundMist((100, 100), [self.group], bound_rect=bound, biome='crypt')
        init_x = mist.pos.x
        
        # Update several frames
        for _ in range(15):
            mist.update()
            
        # Pos X should drift forward
        self.assertGreater(mist.pos.x, init_x)
        self.assertEqual(mist.rect.center, (int(mist.pos.x), int(mist.pos.y)))

    def test_ground_mist_wind_reaction_on_dash(self):
        from src.entities import GroundMist
        mist = GroundMist((120, 100), [self.group], biome='dungeon')
        self.assertEqual(mist.wind_vx, 0.0)
        self.assertEqual(mist.part_alpha, 1.0)

        # Player dashes right from (80, 100)
        p_center = (80, 100)
        dash_dir = pygame.math.Vector2(1, 0)
        mist.on_player_dash_wind(p_center, dash_dir, strength=1.0)

        self.assertGreater(mist.wind_vx, 0.0, "Mist should receive forward wind impulse from player dash")
        self.assertLess(mist.part_alpha, 1.0, "Mist should part / disperse slightly under the dash gust")

    def test_torch_wind_flutter_and_spring_return(self):
        from src.map_manager import Torch
        torch = Torch((150, 100), [self.group])
        self.assertEqual(torch.sprite_type, 'torch')
        self.assertEqual(torch.hitbox, pygame.Rect(0, 0, 0, 0))
        self.assertEqual(torch.wind_angle, 0.0)

        # Apply wind gust from player dashing right
        p_center = (110, 100) # within 180 px
        dash_dir = pygame.math.Vector2(1, 0)
        torch.on_wind_gust(p_center, dash_dir, intensity=1.0)

        # Wind angular velocity should have deflected flame
        self.assertNotEqual(torch.wind_angular_vel, 0.0)

        # Update torch: wind angle deflects and rotates image around base
        torch.update()
        self.assertNotEqual(torch.wind_angle, 0.0)
        self.assertEqual(torch.rect.midbottom, torch.base_rect.midbottom, "Torch base must remain firmly affixed to wall!")

        # Over multiple frames, spring damping restores wind angle toward 0
        for _ in range(60):
            torch.update()
        self.assertAlmostEqual(torch.wind_angle, 0.0, delta=2.5)

    def test_level_spawns_ground_mist_patches(self):
        from src.map_manager import Level
        lvl = Level(current_floor=1)
        lvl.create_map()

        self.assertTrue(hasattr(lvl, 'ground_mist_patches'))
        self.assertGreaterEqual(len(lvl.ground_mist_patches), 4, "Dungeon floor must have multiple creeping mist waves")

    def test_ground_mist_does_not_obstruct_los_or_movement(self):
        from src.entities import Player, Enemy, GroundMist
        obs_group = pygame.sprite.Group()
        vis_group = pygame.sprite.Group()
        player = Player((50, 50), [vis_group], obs_group, pygame.sprite.Group())
        enemy = Enemy((200, 200), [vis_group], obs_group, player, 'skeleton')

        # Put mist in obstacles
        mist = GroundMist((125, 125), [obs_group, vis_group])
        has_los = enemy.has_line_of_fire()
        self.assertTrue(has_los, "GroundMist must never block line-of-fire")

if __name__ == '__main__':
    unittest.main()
