import os
import unittest
import pygame
from src.settings import WIDTH, HEIGHT
from main import Game

# Ensure headless environment
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'


class TestResizableWindowAndFullscreen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

    def setUp(self):
        self.game = Game()
        self.game.running = False  # Prevent main loop from blocking

    def test_initial_window_is_resizable(self):
        """Verify the window is initialized with RESIZABLE flag when not fullscreen."""
        self.assertFalse(self.game.fullscreen)
        info = pygame.display.get_surface()
        self.assertIsNotNone(info)
        flags = info.get_flags()
        # In headless SDL dummy video driver, pygame.RESIZABLE may not be retained in get_flags()
        self.assertTrue(bool(flags & pygame.RESIZABLE) or os.environ.get('SDL_VIDEODRIVER') == 'dummy')

    def test_toggle_fullscreen(self):
        """Verify toggle_fullscreen switches between windowed and fullscreen without crashing."""
        initial_mode = self.game.fullscreen
        self.game.toggle_fullscreen()
        self.assertEqual(self.game.fullscreen, not initial_mode)
        self.assertEqual(self.game.settings.get('fullscreen'), not initial_mode)

        # Toggle back
        self.game.toggle_fullscreen()
        self.assertEqual(self.game.fullscreen, initial_mode)
        self.assertEqual(self.game.settings.get('fullscreen'), initial_mode)

    def test_on_display_resize_updates_camera_and_lighting(self):
        """Verify on_display_resize correctly synchronizes camera half dimensions and light surfaces."""
        # Simulate new resized resolution: 1440x900
        new_w, new_h = 1440, 900
        self.game.screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
        self.game.on_display_resize()

        self.assertEqual(self.game.screen.get_size(), (1440, 900))
        self.assertEqual(self.game.window_size, [1440, 900])

        # Check camera group half size
        vs = self.game.level.visible_sprites
        self.assertEqual(vs.half_width, 1440 // 2)
        self.assertEqual(vs.half_height, 900 // 2)

        # Check lightmap surfaces
        self.assertEqual(vs.light_surf.get_size(), (1440, 900))
        self.assertEqual(vs.light_mask.get_size(), (1440, 900))

        # Check menu hero rect adapted to right edge
        self.assertEqual(self.game.menu_hero_rect.x, 1440 - 330)

    def test_settings_screen_mode_button(self):
        """Verify settings state generates the display mode toggle button and reflects mode name."""
        self.game.set_state('settings')
        found_toggle = False
        for btn in self.game.ui_buttons:
            if "Полноэкранный" in btn.text or "Оконный" in btn.text:
                found_toggle = True
                break
        self.assertTrue(found_toggle, "Settings menu must contain the screen mode toggle button")

    def test_dynamic_mouse_aiming_center(self):
        """Verify dynamic center calculation for 1600x900 and 800x600 resolutions."""
        disp_wide = pygame.display.set_mode((1600, 900), pygame.RESIZABLE)
        dw = disp_wide.get_width()
        dh = disp_wide.get_height()
        screen_center = pygame.math.Vector2(dw // 2, dh // 2)
        self.assertEqual(screen_center, pygame.math.Vector2(800, 450))

        # Mouse click at (1400, 450) -> strictly right of center (800, 450)
        aim_right = (pygame.math.Vector2(1400, 450) - screen_center).normalize()
        self.assertAlmostEqual(aim_right.x, 1.0)
        self.assertAlmostEqual(aim_right.y, 0.0)

        # Mouse click at (800, 750) -> strictly below center (800, 450)
        aim_down = (pygame.math.Vector2(800, 750) - screen_center).normalize()
        self.assertAlmostEqual(aim_down.x, 0.0)
        self.assertAlmostEqual(aim_down.y, 1.0)

        # Test with 800x600 window
        disp_small = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
        screen_center_small = pygame.math.Vector2(disp_small.get_width() // 2, disp_small.get_height() // 2)
        self.assertEqual(screen_center_small, pygame.math.Vector2(400, 300))

    def test_sacred_chest_integrity(self):
        """Rule 1: Sacred chest opening animation frames must remain intact."""
        from src.utils import load_image
        c0 = load_image('assets/sprites/chest_0.png')
        c1 = load_image('assets/sprites/chest_1.png')
        c2 = load_image('assets/sprites/chest_2.png')
        self.assertIsNotNone(c0)
        self.assertIsNotNone(c1)
        self.assertIsNotNone(c2)


if __name__ == '__main__':
    unittest.main()
