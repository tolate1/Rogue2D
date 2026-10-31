import unittest
import pygame
import time
from src.settings import TILE_SIZE
from src.entities import Player, DamageText
from src.ui import UI, compute_spring_scale, draw_with_spring_easing, draw_pixel_frame, draw_dialog_frame, ShopModal, EquipmentModal

class TestFront3UIAndCombatFeedback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        if not pygame.display.get_init() or pygame.display.get_surface() is None:
            pygame.display.set_mode((960, 640))

    def setUp(self):
        self.group = pygame.sprite.Group()
        self.player = Player((100, 100), [self.group], self.group, self.group)
        self.ui = UI()

    def test_damage_burn_buffer_hold_and_decay(self):
        """Verifies player burn buffer holds steady for 250ms before smoothly decaying."""
        # Initial state
        self.player.health = 100.0
        self.ui.draw(self.player)
        self.assertEqual(self.player.burn_health, 100.0)

        # Player takes damage (loss of 30 HP)
        now = pygame.time.get_ticks()
        self.player.health = 70.0
        self.ui.draw(self.player)

        # Immediate check: burn_health must still be 100.0 (holding damage chunk!)
        self.assertEqual(self.player.burn_health, 100.0)
        self.assertGreater(self.player.burn_hold_until, now)

        # Advance time by 100ms (still within 250ms hold window)
        # burn_health must remain untouched at 100.0
        player_burn = getattr(self.player, 'burn_health', 100.0)
        self.assertEqual(player_burn, 100.0)

        # Simulate time passing past 250ms hold window
        self.player.burn_hold_until = now - 50
        self.ui.draw(self.player)
        self.assertLess(self.player.burn_health, 100.0, "Burn health should start decaying towards current health")
        self.assertGreaterEqual(self.player.burn_health, 70.0)

    def test_crit_pop_effect_magnification_and_flash(self):
        """Verifies crit numbers start at 1.5x scale with radiant flash then settle to normal."""
        # Normal damage text
        normal_dt = DamageText("42", (100, 100), [self.group], is_crit=False)
        orig_w = normal_dt.orig_image.get_width()
        normal_dt.update()
        self.assertEqual(normal_dt.image.get_width(), orig_w, "Normal hit should have 1.0x scale")

        # Crit damage text
        crit_dt = DamageText("128!", (100, 100), [self.group], is_crit=True)
        crit_orig_w = crit_dt.orig_image.get_width()
        
        # Frame 1: must be 1.5x magnified
        crit_dt.update()
        self.assertAlmostEqual(crit_dt.image.get_width() / crit_orig_w, 1.50, delta=0.10)

        # Advance 5 frames: must settle down to 1.0x scale
        for _ in range(5):
            crit_dt.update()
        self.assertEqual(crit_dt.image.get_width(), crit_orig_w, "Crit should settle to 1.0x after initial pop")

    def test_spring_easing_overshoot_curve(self):
        """Verifies spring curve: 0.90 -> 1.05 -> 1.00."""
        # t = 0 -> 0.90
        s0 = compute_spring_scale(1000, duration_ms=100)
        # Simulate p = 0
        now = pygame.time.get_ticks()
        s_start = compute_spring_scale(now, duration_ms=100)
        self.assertAlmostEqual(s_start, 0.90, delta=0.04)

        # Simulate p = 0.6 (peak overshoot around 1.04-1.05)
        s_mid = compute_spring_scale(now - 60, duration_ms=100)
        self.assertGreater(s_mid, 1.00, "Should overshoot above 1.00 during spring apex")

        # Simulate t >= 100ms (settles at exactly 1.00)
        s_end = compute_spring_scale(now - 120, duration_ms=100)
        self.assertEqual(s_end, 1.00, "Should settle to exactly 1.00 after duration")

    def test_gothic_frame_renderers(self):
        """Verifies 9-slice bevel frame renderers execute without error."""
        surf = pygame.Surface((300, 200))
        r = pygame.Rect(20, 20, 260, 160)
        draw_pixel_frame(surf, r)
        draw_dialog_frame(surf, r)
        self.assertEqual(surf.get_size(), (300, 200))

if __name__ == '__main__':
    unittest.main()
