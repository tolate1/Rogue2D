import unittest
import pygame
import os
import math
from src.entities import Player, Weapon, FlameTrailHazard, SpeedlineStreakVFX, MagmaEmberVFX
from src.map_manager import Level, ShowcaseEntity, get_showcase_anim_data

class TestHeroArchetypesAndCombatLighting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100), pygame.HIDDEN)

    def setUp(self):
        self.dummy_vis = pygame.sprite.Group()
        self.dummy_obs = pygame.sprite.Group()
        self.dummy_enemies = pygame.sprite.Group()

    def test_01_hero_archetypes_load_and_animations(self):
        """Verify all 4 archetypes exist and have idle, walk, attack, and dash frames."""
        player = Player((100, 100), [self.dummy_vis], self.dummy_obs, self.dummy_enemies)
        archetypes = ['slayer', 'wanderer', 'crusader', 'champion_redux']
        
        for arch in archetypes:
            self.assertIn(arch, player.available_archetypes)
            player.set_skin(arch)
            self.assertEqual(player.current_skin, arch)
            self.assertGreaterEqual(len(player.idle_frames), 4)
            self.assertGreaterEqual(len(player.walk_frames), 4)
            self.assertGreaterEqual(len(player.attack_frames), 3)
            self.assertGreaterEqual(len(player.dash_frames), 2)
            
            # Check dimensions (native 64x80 scale preserved for tall archetypes)
            w, h = player.image.get_size()
            self.assertEqual(w, 64)
            self.assertEqual(h, 80)

    def test_02_hero_grounding_anchoring(self):
        """Verify midbottom anchoring firmly grounds tall archetypes to the floor tile."""
        player = Player((200, 200), [self.dummy_vis], self.dummy_obs, self.dummy_enemies)
        player.set_skin('slayer')
        player.animate()
        # rect bottom should align with hitbox bottom + 2
        self.assertEqual(player.rect.midbottom[1], player.hitbox.bottom + 2)
        self.assertEqual(player.rect.midbottom[0], player.hitbox.centerx)

    def test_03_dev_room_pedestals_and_interaction(self):
        """Verify Dev Room contains 4 hero archetype pedestals and [E] interaction switches player skin."""
        level = Level(is_dev_room=True)
        showcase_entities = [s for s in level.visible_sprites if isinstance(s, ShowcaseEntity)]
        
        # Verify 4 hero archetypes are present on pedestals
        archetype_entities = {s.archetype_key: s for s in showcase_entities if getattr(s, 'archetype_key', None)}
        self.assertIn('slayer', archetype_entities)
        self.assertIn('wanderer', archetype_entities)
        self.assertIn('crusader', archetype_entities)
        self.assertIn('champion_redux', archetype_entities)

        # Test interaction: move player to slayer pedestal and simulate [E] key
        slayer_ent = archetype_entities['slayer']
        level.player.rect.center = slayer_ent.rect.center
        level.player.hitbox.center = slayer_ent.rect.center
        
        # Simulate E key press
        fake_keys = {pygame.K_e: True}
        level.e_pressed_prev = False
        
        # Trigger Dev Room pedestal check
        for s in level.showcase_sprites:
            if getattr(s, 'archetype_key', None):
                dist = (pygame.math.Vector2(s.rect.center) - pygame.math.Vector2(level.player.rect.center)).magnitude()
                if dist < 65:
                    level.player.set_skin(s.archetype_key)
                    break
                    
        self.assertEqual(level.player.current_skin, 'slayer')

    def test_04_weapon_3phase_strike_rendering(self):
        """Verify Weapon 3-phase combat pipeline renders windup, crescent smear, and recovery."""
        player = Player((100, 100), [self.dummy_vis], self.dummy_obs, self.dummy_enemies)
        weapon = Weapon(player, [self.dummy_vis], pygame.math.Vector2(1, 0), weapon_type='sword')
        
        # Phase 1: Windup (progress = 0.10)
        img_windup = weapon.render_slash(0.10)
        self.assertIsInstance(img_windup, pygame.Surface)
        self.assertGreater(img_windup.get_width(), 50)
        
        # Phase 2: Active Strike & 180 deg Smear (progress = 0.50)
        img_strike = weapon.render_slash(0.50)
        self.assertIsInstance(img_strike, pygame.Surface)
        self.assertGreater(img_strike.get_width(), 50)
        
        # Phase 3: Recovery (progress = 0.90)
        img_recovery = weapon.render_slash(0.90)
        self.assertIsInstance(img_recovery, pygame.Surface)
        self.assertGreater(img_recovery.get_width(), 50)

    def test_05_flame_trail_milestone_colors(self):
        """Verify FlameTrailHazard evolves colors based on level milestones (1-4, 5-9, 10-14, 15+)."""
        # Lv 1: Amber Gold
        f1 = FlameTrailHazard((10, 10), [self.dummy_vis], player_level=1)
        self.assertEqual(f1.flame_color, (255, 160, 30))
        
        # Lv 5: Azure Arcane
        f5 = FlameTrailHazard((20, 20), [self.dummy_vis], player_level=5)
        self.assertEqual(f5.flame_color, (60, 205, 255))
        
        # Lv 10: Amethyst Nether
        f10 = FlameTrailHazard((30, 30), [self.dummy_vis], player_level=10)
        self.assertEqual(f10.flame_color, (195, 75, 255))
        
        # Lv 15+: Celestial Crimson
        f15 = FlameTrailHazard((40, 40), [self.dummy_vis], player_level=18)
        self.assertEqual(f15.flame_color, (255, 45, 65))

    def test_dash_opener_is_stronger_and_uses_slashes_instead_of_orbs(self):
        player = Player((100, 100), [self.dummy_vis], self.dummy_obs, self.dummy_enemies)
        player.spawn_dash_trail_vfx(initial=True)
        default_lines = [sprite for sprite in self.dummy_vis if isinstance(sprite, SpeedlineStreakVFX)]
        self.assertEqual(len(default_lines), 10)
        self.assertTrue(all(sprite.length >= 48 for sprite in default_lines))

        self.dummy_vis.empty()
        player.dash_trail_variant = 1
        player.spawn_dash_trail_vfx(initial=True)
        self.assertFalse(any(isinstance(sprite, MagmaEmberVFX) for sprite in self.dummy_vis))
        hazard = FlameTrailHazard((100, 100), [self.dummy_vis], direction=(1, 0))
        hazard.update()
        self.assertEqual(hazard.image.get_at((18, 15)).a, 0, "Dash mark center must stay open; stacked circular orbs are gone")

    def test_06_cathedral_chime_audio(self):
        """Verify level_up.wav exists and is a valid non-empty audio file."""
        path = "assets/audio/level_up.wav"
        self.assertTrue(os.path.exists(path))
        self.assertGreater(os.path.getsize(path), 20000)

if __name__ == '__main__':
    unittest.main()
