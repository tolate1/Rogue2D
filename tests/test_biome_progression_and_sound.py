import os
import unittest
import pygame
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.map_manager import Level, BossArenaPillar, BossRunicCircle
from src.entities import Player, Enemy, Weapon
from src.sound_manager import SoundManager, play_sfx
from src.items import Item, PERMANENT_GEAR_CATALOGUE

class TestBiomeProgressionAndSound(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_init():
            pygame.display.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((100, 100))

    def setUp(self):
        if not pygame.display.get_init():
            pygame.display.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((100, 100))
        self.visible_sprites = pygame.sprite.Group()
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.player = Player((100, 100), [self.visible_sprites], self.obstacle_sprites, self.enemy_sprites)

    def test_biome_chapter_progression(self):
        """Verifies 6 distinct 5-floor biome chapters."""
        expected_biomes = {
            1: 'dungeon',
            2: 'dungeon',
            5: 'dungeon',
            6: 'crypt',
            10: 'crypt',
            11: 'fungal',
            15: 'fungal',
            16: 'ice',
            20: 'ice',
            21: 'volcano',
            25: 'volcano',
            26: 'void',
            30: 'void'
        }
        for fl, exp_biome in expected_biomes.items():
            lvl = Level(current_floor=fl)
            self.assertEqual(lvl.biome_type, exp_biome, f"Floor {fl} should be in biome chapter {exp_biome}")

    def test_boss_rotation_by_chapter(self):
        """Verifies boss archetype by chapter end."""
        expected_bosses = {
            5: 'boss_void_knight',
            10: 'boss_necro_lord',
            15: 'boss_bone_golem',
            20: 'boss_frost_revenant'
        }
        for fl, exp_boss in expected_bosses.items():
            lvl = Level(current_floor=fl)
            self.assertTrue(lvl.is_boss_level)
            boss = next((e for e in lvl.enemy_sprites if getattr(e, 'is_boss', False)), None)
            self.assertIsNotNone(boss, f"Floor {fl} must spawn a boss")
            self.assertEqual(boss.enemy_type, exp_boss, f"Floor {fl} boss should be {exp_boss}")

    def test_new_sound_suite_registered(self):
        """Verifies all new sound effects are registered in SoundManager."""
        sm = SoundManager.get_instance()
        expected_sounds = [
            'spear_thrust', 'dagger_slash', 'spore_explode', 'necro_cast',
            'slime_leap', 'slime_land', 'zombie_attack', 'boss_cleave'
        ]
        for snd in expected_sounds:
            path = os.path.join('assets', 'sounds', f"{snd}.wav")
            self.assertTrue(os.path.exists(path), f"Audio file {path} must exist on disk")

    def test_player_weapon_sound_dispatch(self):
        """Verifies player plays correct SFX per weapon archetype."""
        with patch.object(SoundManager, 'play') as mock_play:
            # 1. Spear
            spear = Item.from_dict(PERMANENT_GEAR_CATALOGUE['spear_abyss'])
            self.player.equip_item(spear)
            self.player.attack(target_direction=(1, 0))
            mock_play.assert_called_with('spear_thrust')

            # 2. Daggers
            daggers = Item.from_dict(PERMANENT_GEAR_CATALOGUE['daggers_shadow'])
            self.player.equip_item(daggers)
            self.player.attack(target_direction=(1, 0))
            mock_play.assert_called_with('dagger_slash')

            # 3. Standard sword
            self.player.equipped['weapon'] = None
            self.player.attack(target_direction=(1, 0))
            mock_play.assert_called_with('sword_swing')

    def test_runic_circle_layer_separation(self):
        """Verifies runic circle uses floor_overlay layer, preventing occlusion by standard floor tiles."""
        lvl = Level(current_floor=5)
        circle = next((s for s in lvl.visible_sprites if isinstance(s, BossRunicCircle)), None)
        self.assertIsNotNone(circle)
        self.assertEqual(circle.sprite_type, 'floor_overlay')

if __name__ == '__main__':
    unittest.main()
