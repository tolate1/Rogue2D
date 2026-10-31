import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from src.map_manager import _VIGNETTE_CACHE, _get_cached_vignette


class TestVignetteShader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_vignette_is_a_smooth_monotone_radial_falloff(self):
        _VIGNETTE_CACHE.clear()
        width, height = 320, 180
        vignette = _get_cached_vignette(width, height)

        center_alpha = vignette.get_at((width // 2, height // 2)).a
        edge_samples = [vignette.get_at((x, height // 2)).a for x in range(width // 2, width)]
        corner_alpha = vignette.get_at((width - 1, height - 1)).a

        self.assertEqual(center_alpha, 0)
        self.assertTrue(all(a <= b for a, b in zip(edge_samples, edge_samples[1:])))
        self.assertGreater(corner_alpha, edge_samples[-1])
        self.assertGreater(len(set(edge_samples)), 35)

    def test_vignette_cache_stays_bounded_across_resizes(self):
        _VIGNETTE_CACHE.clear()
        for index in range(12):
            _get_cached_vignette(128 + index * 7, 96 + index * 5)
        self.assertLessEqual(len(_VIGNETTE_CACHE), 8)
        self.assertIn((128 + 11 * 7, 96 + 11 * 5), _VIGNETTE_CACHE)


if __name__ == "__main__":
    unittest.main()
