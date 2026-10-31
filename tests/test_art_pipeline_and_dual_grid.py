"""
Unit tests for Rogue2D Art Pipeline & Dual-Grid System:
- NormalMapGenerator (Tangent space normals, specular maps, height maps)
- NormalMappedLighting (Physical N·L diffuse and N·H Blinn-Phong specular calculation)
- DualGridTilemap (16-tile corner bitmasking, half-tile coordinate shifts)
- LPCCompositor (Z-order stacking, frame extraction, palette multipliers)
"""

import unittest
from PIL import Image
from tools.art_pipeline.normal_map_generator import NormalMapGenerator
from tools.art_pipeline.normal_light_shader import NormalMappedLighting
from tools.art_pipeline.lpc_compositor import LPCCompositor, LPC_LAYER_ORDER
from src.dual_grid import (
    DualGridTilemap,
    CORNER_TL, CORNER_TR, CORNER_BR, CORNER_BL,
    TILE_NAMES
)

class TestArtPipelineAndDualGrid(unittest.TestCase):
    def setUp(self):
        self.norm_gen = NormalMapGenerator(strength=2.5, bevel_radius=2)
        self.shader = NormalMappedLighting()
        self.lpc = LPCCompositor(cell_size=64)

        # Create a simple test sprite (32x32 circle with opaque center)
        self.test_img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        pixels = self.test_img.load()
        for y in range(32):
            for x in range(32):
                if (x - 16)**2 + (y - 16)**2 <= 100:
                    pixels[x, y] = (180, 180, 200, 255)

    def test_normal_map_dimensions_and_channels(self):
        norm = self.norm_gen.generate_normal_map(self.test_img)
        self.assertEqual(norm.size, (32, 32))
        self.assertEqual(norm.mode, "RGBA")

        # Center pixel of circular bevel should face outward (Z close to 255, X & Y near 128)
        nr, ng, nb, na = norm.getpixel((16, 16))
        self.assertEqual(na, 255)
        self.assertTrue(120 <= nr <= 136) # Nx near 0
        self.assertTrue(120 <= ng <= 136) # Ny near 0
        self.assertTrue(nb >= 200)        # Nz pointing towards camera

        # Left edge should slope left (Nx < 0 -> R < 128)
        left_r, _, _, _ = norm.getpixel((8, 16))
        self.assertTrue(left_r < 128, f"Expected left slope Nx < 0, got R={left_r}")

        # Right edge should slope right (Nx > 0 -> R > 128)
        right_r, _, _, _ = norm.getpixel((24, 16))
        self.assertTrue(right_r > 128, f"Expected right slope Nx > 0, got R={right_r}")

    def test_specular_and_height_maps(self):
        spec = self.norm_gen.generate_specular_map(self.test_img)
        self.assertEqual(spec.size, (32, 32))
        sr, _, _, sa = spec.getpixel((16, 16))
        self.assertEqual(sa, 255)
        self.assertTrue(sr > 0)

        hgt = self.norm_gen.generate_height_map(self.test_img)
        self.assertEqual(hgt.size, (32, 32))
        h_center = hgt.getpixel((16, 16))
        h_outer = hgt.getpixel((6, 16))
        self.assertTrue(h_center > h_outer, "Center height must exceed boundary slope height")

    def test_directional_normal_lighting_physics(self):
        norm = self.norm_gen.generate_normal_map(self.test_img)
        spec = self.norm_gen.generate_specular_map(self.test_img)

        # Light from Left (lx = -50)
        lit_left = self.shader.render_lit_sprite(
            self.test_img, norm, spec,
            light_pos_rel=(-50, 0, 20),
            light_color=(255, 255, 255),
            ambient_color=(20, 20, 20)
        )
        # Light from Right (lx = +50)
        lit_right = self.shader.render_lit_sprite(
            self.test_img, norm, spec,
            light_pos_rel=(50, 0, 20),
            light_color=(255, 255, 255),
            ambient_color=(20, 20, 20)
        )

        left_px_when_light_left = lit_left.getpixel((8, 16))[0]
        right_px_when_light_left = lit_left.getpixel((24, 16))[0]
        self.assertTrue(left_px_when_light_left > right_px_when_light_left,
                        "Left facet must be brighter than right facet when light is on left")

        left_px_when_light_right = lit_right.getpixel((8, 16))[0]
        right_px_when_light_right = lit_right.getpixel((24, 16))[0]
        self.assertTrue(right_px_when_light_right > left_px_when_light_right,
                        "Right facet must be brighter than left facet when light is on right")

    def test_dual_grid_16_bitmasks(self):
        dg = DualGridTilemap(width=4, height=4, default_value=0)
        self.assertEqual(len(TILE_NAMES), 16)

        # Bitmask verification
        self.assertEqual(CORNER_TL, 1)
        self.assertEqual(CORNER_TR, 2)
        self.assertEqual(CORNER_BR, 4)
        self.assertEqual(CORNER_BL, 8)

        # Place single wall at (1, 1)
        dg.set_cell(1, 1, 1)

        # Dual cell at (1, 1) has BR corner at (1, 1) -> mask should be CORNER_BR (4)
        mask_1_1 = dg.calculate_dual_bitmask(1, 1)
        self.assertEqual(mask_1_1, CORNER_BR)

        # Dual cell at (2, 2) has TL corner at (1, 1) -> mask should be CORNER_TL (1)
        mask_2_2 = dg.calculate_dual_bitmask(2, 2)
        self.assertEqual(mask_2_2, CORNER_TL)

        # Full dual tilemap has dimensions (height + 1, width + 1)
        dual_matrix = dg.generate_dual_tilemap()
        self.assertEqual(len(dual_matrix), 5)
        self.assertEqual(len(dual_matrix[0]), 5)

        # Check render metadata
        info = dg.get_tile_render_info(1, 1, tile_size=32)
        self.assertEqual(info["world_x"], 16) # 1 * 32 - 16
        self.assertEqual(info["world_y"], 16)
        self.assertEqual(info["bitmask"], 4)
        self.assertEqual(info["tile_name"], "outer_corner_br")

    def test_lpc_compositor_layer_order_and_recolor(self):
        self.assertTrue("body" in LPC_LAYER_ORDER)
        self.assertTrue("torso" in LPC_LAYER_ORDER)
        self.assertTrue("weapon" in LPC_LAYER_ORDER)
        # Verify torso is drawn after body
        self.assertTrue(LPC_LAYER_ORDER.index("torso") > LPC_LAYER_ORDER.index("body"))
        # Verify weapon is drawn after torso
        self.assertTrue(LPC_LAYER_ORDER.index("weapon") > LPC_LAYER_ORDER.index("torso"))

        # Test recoloring
        sample = Image.new("RGBA", (10, 10), (100, 100, 100, 255))
        recolored = self.lpc.recolor_layer(sample, (1.5, 0.5, 0.5))
        r, g, b, a = recolored.getpixel((0, 0))
        self.assertEqual(r, 150)
        self.assertEqual(g, 50)
        self.assertEqual(b, 50)

if __name__ == "__main__":
    unittest.main()
