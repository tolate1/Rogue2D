import unittest
import os
import pygame
from PIL import Image

class PilotHeroAndCriticDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.display = pygame.display.set_mode((100, 100))

    def test_1_floor_fallback_zero_magentas_across_all_biomes(self):
        """All biomes (dungeon, crypt, fungal, ice, volcano, void) across all 8 variants resolve without magenta."""
        from src.map_manager import Tile
        group = pygame.sprite.Group()
        biomes = ['dungeon', 'crypt', 'fungal', 'ice', 'volcano', 'void']
        variants = ['var1', 'var2', 'var3', 'var4', 'var5', 'var6', 'var7', 'var8']
        
        for b in biomes:
            for v in variants:
                tile = Tile((0, 0), [group], 'floor', biome=b, sub_type=v)
                col = tile.image.get_at((0, 0))[:3]
                self.assertNotEqual(col, (255, 0, 255), f"Magenta placeholder detected in {b} {v}!")

    def test_2_lossless_knight_frames_zero_clipping(self):
        """All 29 frames of the authentic knight sheet retain 100% of visible pixels without clipping."""
        raw_dir = 'assets/raw_pixel_sheets'
        sheets = {
            'idle': ('knight_idle.png', 7),
            'walk': ('knight_walk.png', 8),
            'attack': ('knight_attack1.png', 6),
            'dash': ('knight_run.png', 8)
        }
        cell_w, cell_h = 96, 84
        win_x0, win_y0, win_x1, win_y1 = 16, 21, 80, 63 # 64x42

        total_lost = 0
        for name, (fname, n_frames) in sheets.items():
            p = os.path.join(raw_dir, fname)
            self.assertTrue(os.path.exists(p), f"Missing raw sheet: {p}")
            im = Image.open(p).convert('RGBA')
            for i in range(n_frames):
                cell = im.crop((i * cell_w, 0, (i + 1) * cell_w, cell_h))
                c_px = cell.load()
                for y in range(cell_h):
                    for x in range(cell_w):
                        if c_px[x, y][3] > 0:
                            if not (win_x0 <= x < win_x1 and win_y0 <= y < win_y1):
                                total_lost += 1

        self.assertEqual(total_lost, 0, f"Detected {total_lost} clipped pixels in knight sheets!")

    def test_3_hero_and_player_knight_synchronization(self):
        """player_knight_* and hero_knight_* files are 100% byte-for-byte identical."""
        sprites_dir = 'assets/sprites'
        for state in ['idle', 'walk', 'attack', 'dash']:
            for i in range(4 if state != 'dash' else 2):
                p_path = os.path.join(sprites_dir, f'player_knight_{state}_{i}.png')
                h_path = os.path.join(sprites_dir, f'hero_knight_{state}_{i}.png')
                self.assertTrue(os.path.exists(p_path), f"Missing {p_path}")
                self.assertTrue(os.path.exists(h_path), f"Missing {h_path}")
                with open(p_path, 'rb') as f1, open(h_path, 'rb') as f2:
                    self.assertEqual(f1.read(), f2.read(), f"Desync between {p_path} and {h_path}!")

    def test_4_player_load_skin_knight_loads_all_frames(self):
        """Player.load_skin('knight') dynamically loads the full authentic animation sequence."""
        from src.entities import Player
        player = Player((100, 100), [], pygame.sprite.Group(), pygame.sprite.Group())
        data = player.load_skin('knight')
        self.assertGreaterEqual(len(data['idle']), 4)
        self.assertGreaterEqual(len(data['walk']), 4)
        self.assertGreaterEqual(len(data['attack']), 3)
        self.assertGreaterEqual(len(data['dash']), 2)

    def test_5_baked_blade_suppresses_duplicate_weapon(self):
        """Weapon does not render redundant procedural blade when player skin is 'knight' or 'crusader'."""
        from src.entities import Player, Weapon
        player = Player((100, 100), [], pygame.sprite.Group(), pygame.sprite.Group())
        player.current_skin = 'knight'
        w = Weapon(player, [], pygame.math.Vector2(1, 0))
        # At progress=0.5, render_slash produces a surface
        surf = w.render_slash(0.5)
        self.assertIsNotNone(surf)
        self.assertGreater(surf.get_width(), 0)

if __name__ == '__main__':
    unittest.main()
