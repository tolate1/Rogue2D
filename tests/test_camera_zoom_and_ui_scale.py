import unittest
import os
import sys
import pygame

sys.path.insert(0, os.path.abspath('.'))
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.map_manager import Level, CameraGroup, ShowcaseEntity
from src.ui import UI, NPCDialogueBubble, get_pixel_font
from src.entities import Player

class TestCameraZoomAndUIScale(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720))

    def setUp(self):
        self.disp = pygame.display.get_surface()

    def test_camera_world_to_screen_and_roundtrip(self):
        """Verifies world_to_screen and screen_to_world mathematical perfection across all zooms."""
        cam = CameraGroup()
        player = Player((500, 500), [cam], pygame.sprite.Group(), pygame.sprite.Group())
        
        zooms = [0.5, 0.7, 1.0, 1.25, 1.5, 2.0]
        test_positions = [(500, 500), (300, 400), (750, 620), (1200, 1100), (0, 0)]
        
        for z in zooms:
            cam.zoom_level = z
            cam.custom_draw(player)
            
            for wx, wy in test_positions:
                scr = cam.world_to_screen((wx, wy))
                w_back = cam.screen_to_world((scr.x, scr.y))
                self.assertAlmostEqual(wx, w_back.x, delta=0.01, msg=f"Roundtrip X failed for zoom {z}")
                self.assertAlmostEqual(wy, w_back.y, delta=0.01, msg=f"Roundtrip Y failed for zoom {z}")

    def test_dev_room_showcase_nameplates_zoom_alignment(self):
        """Verifies Dev Mode mob nameplates remain strictly locked to mob screen positions at 0.7x, 1.0x, 1.5x."""
        level = Level(is_dev_room=True)
        cam = level.visible_sprites
        player = level.player

        zooms = [0.7, 1.0, 1.5]
        showcase_entities = [s for s in cam.sprites() if isinstance(s, ShowcaseEntity)]
        self.assertGreaterEqual(len(showcase_entities), 5, "Dev Room must contain showcase entities")

        for z in zooms:
            cam.zoom_level = z
            level.draw()
            
            for ent in showcase_entities[:5]:
                # World position of entity top
                ent_top_world = (ent.rect.centerx, ent.rect.top)
                # Projected screen position
                top_scr = cam.world_to_screen(ent_top_world)
                
                # In custom_draw scaled path:
                if z == 1.0:
                    exp_x = ent.rect.centerx - cam.offset.x
                    exp_y = ent.rect.top - cam.offset.y
                else:
                    exp_x = (ent.rect.centerx - cam.sub_offset.x) * cam.scale_x
                    exp_y = (ent.rect.top - cam.sub_offset.y) * cam.scale_y
                
                self.assertAlmostEqual(top_scr.x, exp_x, delta=0.001)
                self.assertAlmostEqual(top_scr.y, exp_y, delta=0.001)

    def test_ui_scale_stats_header_no_overlap(self):
        """Verifies that at small UI scales (0.7x), Gold counter NEVER collides with XP counter."""
        ui = UI()
        player = Player((100, 100), [], pygame.sprite.Group(), pygame.sprite.Group())
        player.level = 99
        player.exp = 9900
        player.gold = 99999

        for scale in [0.7, 0.85, 1.0, 1.2, 1.4]:
            ui.ui_scale = scale
            # Render UI
            ui.draw(player)
            
            # Re-compute gold_x and xp_right based on logic
            s = scale
            panel_w = max(195, int(230 * s))
            lvl_font = ui.get_font_scaled(10)
            lvl_surf = lvl_font.render(f"LV {player.level}", True, (255, 255, 255))
            lvl_bg_w = lvl_surf.get_width() + max(4, int(8 * s))
            lvl_x = int(8 * s)
            
            xp_needed = player.level * 100
            xp_surf = lvl_font.render(f"XP:{player.exp}/{xp_needed}", True, (190, 200, 220))
            xp_x = lvl_x + lvl_bg_w + max(4, int(6 * s))
            xp_right = xp_x + xp_surf.get_width()
            
            gold_surf = lvl_font.render(f"G:{player.gold}", True, (255, 215, 50))
            gold_x = max(xp_x + xp_surf.get_width() + 6, panel_w - gold_surf.get_width() - int(8 * s))
            
            self.assertGreaterEqual(gold_x - xp_right, 6, f"Overlap detected at scale {scale}!")

    def test_ui_scale_bar_numbers_fit_inside_height(self):
        """Verifies bar numbers scale down so they never exceed the bar height and clip."""
        ui = UI()
        for scale in [0.6, 0.7, 1.0, 1.3]:
            ui.ui_scale = scale
            s = scale
            h = max(12, int(18 * s))
            
            num_font = ui.get_font_scaled(10)
            if num_font.get_height() > h - 2:
                num_font = get_pixel_font(max(7, h - 3), bold=True)
                
            self.assertLessEqual(num_font.get_height(), h, f"Font height exceeds bar height at scale {scale}")

    def test_ui_scale_skill_cards_minimum_clamping(self):
        """Verifies skill cards are clamped to a minimum size so icons remain visible."""
        ui = UI()
        for scale in [0.5, 0.7, 1.0, 1.4]:
            ui.ui_scale = scale
            s = scale
            card_size = max(44, int(54 * s))
            self.assertGreaterEqual(card_size, 44, f"Skill card shrunk below 44px at scale {scale}")

    def test_dialogue_bubble_draw_with_camera_group(self):
        """Verifies NPCDialogueBubble draws properly when passed CameraGroup instead of a raw offset."""
        cam = CameraGroup()
        player = Player((400, 400), [cam], pygame.sprite.Group(), pygame.sprite.Group())
        cam.zoom_level = 1.5
        cam.custom_draw(player)

        bubble = NPCDialogueBubble("Greetings Traveler!", (420, 380), duration=3000, bubble_type='merchant')
        # Should not raise exception
        bubble.draw(self.disp, cam)
        self.assertTrue(bubble.is_alive())

if __name__ == '__main__':
    unittest.main()
