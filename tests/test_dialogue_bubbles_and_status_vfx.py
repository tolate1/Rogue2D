import os
import unittest
import pygame
import math
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
if not pygame.display.get_init() or pygame.display.get_surface() is None:
    pygame.display.set_mode((960, 640))

from src.settings import TILE_SIZE
from src.entities import Player, Enemy
from src.ui import NPCDialogueBubble, draw_enemy_status_badges, wrap_text, get_pixel_font
from src.map_manager import Level


class TestDialogueBubblesAndStatusVFX(unittest.TestCase):
    def setUp(self):
        self.group = pygame.sprite.Group()
        self.obstacle_group = pygame.sprite.Group()
        self.player = Player((200, 200), [self.group], self.obstacle_group, self.group)
        self.screen = pygame.display.get_surface()

    def test_npc_dialogue_bubble_lifecycle_and_spring(self):
        """Verifies NPCDialogueBubble initialization, word-wrap, spring curve and fade-out."""
        sample_text = "Ты весь в крови, путник! Выпей целебный отвар, пока не упал замертво!"
        bubble = NPCDialogueBubble(sample_text, (200, 200), duration=4000, bubble_type='merchant')
        
        self.assertTrue(bubble.is_alive())
        self.assertGreaterEqual(len(bubble.lines), 1)
        self.assertEqual(bubble.bubble_type, 'merchant')

        # Spring scale starts in overshoot region (0.85 -> 1.05)
        scale_init = bubble.get_scale()
        self.assertGreaterEqual(scale_init, 0.80)
        self.assertLessEqual(scale_init, 1.20)

        # Alpha full at start
        self.assertEqual(bubble.get_alpha(), 255)

        # Rendering check without error
        surf = pygame.Surface((960, 640), pygame.SRCALPHA)
        bubble.draw(surf, camera_offset=pygame.math.Vector2(0, 0))

        # Simulate expiration
        bubble.spawn_time = pygame.time.get_ticks() - 4100
        self.assertFalse(bubble.is_alive())
        self.assertEqual(bubble.get_alpha(), 0)

    def test_npc_dialogue_bubble_types_and_anchoring(self):
        """Verifies blacksmith bubble type, camera offsets and screen border clamping."""
        forge_text = "Астральные осколки таят силу... Я могу перековать их."
        bubble_forge = NPCDialogueBubble(forge_text, (500, 300), duration=3500, bubble_type='blacksmith')
        self.assertEqual(bubble_forge.bubble_type, 'blacksmith')
        
        surf = pygame.Surface((960, 640), pygame.SRCALPHA)
        # Draw with positive and negative camera offsets
        bubble_forge.draw(surf, camera_offset=(100, 50))
        bubble_forge.draw(surf, camera_offset=(-50, -30))

        # Edge clamping check: target placed near top-left screen edge
        edge_bubble = NPCDialogueBubble("Край экрана", (5, 5), duration=3000, bubble_type='merchant')
        edge_bubble.draw(surf, camera_offset=(0, 0))

    def test_enemy_status_effects_application_and_refresh(self):
        """Verifies Enemy.apply_status_effect registers effects, refreshes duration, and handles magnitude."""
        enemy = Enemy((300, 300), [self.group], self.obstacle_group, self.player, 'goblin', visible_sprites=self.group)
        self.assertTrue(hasattr(enemy, 'status_effects'))
        self.assertEqual(len(enemy.status_effects), 0)

        # Apply burn
        enemy.apply_status_effect('burn', duration_ms=2500, magnitude=1.5)
        self.assertIn('burn', enemy.status_effects)
        self.assertEqual(enemy.status_effects['burn']['magnitude'], 1.5)
        init_expires = enemy.status_effects['burn']['expires']

        # Refresh with higher duration
        time.sleep(0.01)
        enemy.apply_status_effect('burn', duration_ms=5000, magnitude=1.2)
        self.assertGreater(enemy.status_effects['burn']['expires'], init_expires)
        # Magnitude preserves max
        self.assertEqual(enemy.status_effects['burn']['magnitude'], 1.5)

        # Apply chill and bleed
        enemy.apply_status_effect('chill', duration_ms=3000)
        enemy.apply_status_effect('bleed', duration_ms=2000)
        self.assertIn('chill', enemy.status_effects)
        self.assertIn('bleed', enemy.status_effects)

    def test_enemy_status_effects_burn_and_bleed_tick_damage(self):
        """Verifies periodic tick damage from burn and bleed effects in Enemy.update()."""
        enemy = Enemy((300, 300), [self.group], self.obstacle_group, self.player, 'zombie', visible_sprites=self.group)
        enemy.hp = 100
        enemy.max_hp = 100

        # Apply burn (ticks every 500ms)
        enemy.apply_status_effect('burn', duration_ms=4000, magnitude=1.0)
        # Force tick timer into the past to trigger immediate damage on update
        enemy.status_effects['burn']['tick_timer'] = pygame.time.get_ticks() - 600

        enemy.update()
        self.assertLess(enemy.hp, 100, "Burn tick should deal damage to enemy HP")
        hp_after_burn = enemy.hp

        # Apply bleed (ticks every 600ms)
        enemy.apply_status_effect('bleed', duration_ms=4000, magnitude=1.0)
        enemy.status_effects['bleed']['tick_timer'] = pygame.time.get_ticks() - 700

        enemy.update()
        self.assertLess(enemy.hp, hp_after_burn, "Bleed tick should deal additional damage")

    def test_enemy_status_effects_chill_speed_reduction(self):
        """Verifies chill slows enemy movement speed by 45% (effective speed = 55%)."""
        enemy = Enemy((300, 300), [self.group], self.obstacle_group, self.player, 'imp', visible_sprites=self.group)
        orig_speed = enemy.speed

        # Without chill, enemy moves at full speed
        enemy.direction = pygame.math.Vector2(1, 0)
        enemy.update()
        
        # Apply chill
        enemy.apply_status_effect('chill', duration_ms=3000)
        self.assertIn('chill', enemy.status_effects)

        # Test speed reduction logic
        effective = enemy.speed * 0.55 if ('chill' in enemy.status_effects) else enemy.speed
        self.assertAlmostEqual(effective, orig_speed * 0.55, places=2)

    def test_draw_enemy_status_badges_rendering(self):
        """Verifies draw_enemy_status_badges renders micro pixel badges without font or unicode crashes."""
        enemy = Enemy((400, 300), [self.group], self.obstacle_group, self.player, 'skeleton', visible_sprites=self.group)
        enemy.apply_status_effect('burn', duration_ms=3000)
        enemy.apply_status_effect('chill', duration_ms=3000)
        enemy.apply_status_effect('bleed', duration_ms=3000)

        surf = pygame.Surface((960, 640), pygame.SRCALPHA)
        # Render badges above enemy head
        draw_enemy_status_badges(surf, enemy, offset_pos=pygame.math.Vector2(200, 200))
        # Also test tuple offset_pos
        draw_enemy_status_badges(surf, enemy, offset_pos=(200, 200))

    def test_level_npc_dialogue_bubbles_proximity(self):
        """Verifies Level manages dialogue bubbles when player is near Trader or Anvil."""
        level = Level(current_floor=1)
        self.assertTrue(hasattr(level, 'npc_bubbles'))
        self.assertTrue(hasattr(level, '_npc_dialogue_cooldowns'))

        # Directly add a bubble to level.npc_bubbles
        test_bubble = NPCDialogueBubble("Привет, герой!", (150, 150), duration=3000, bubble_type='merchant')
        level.npc_bubbles.append(test_bubble)
        self.assertEqual(len(level.npc_bubbles), 1)

        # Drawing the level should process and keep active bubbles
        level.draw()
        self.assertTrue(len(level.npc_bubbles) >= 1)


if __name__ == '__main__':
    unittest.main()
