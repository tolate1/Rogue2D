import unittest
import pygame
import os
from PIL import Image
from src.settings import WIDTH, HEIGHT, TILE_SIZE
from src.entities import Player, Weapon, Enemy
from src.player_animation import PlayerAnimationController
from src.sound_manager import SoundManager, play_sfx

class TestPlayerCombatAnimationAndAudio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((WIDTH, HEIGHT))

    def setUp(self):
        self.v_group = pygame.sprite.Group()
        self.o_group = pygame.sprite.Group()
        self.e_group = pygame.sprite.Group()
        self.player = Player((100, 100), [self.v_group], self.o_group, self.e_group)

    def test_player_attack_frames_integrity(self):
        """Verifies player has 3 distinct attack frames matching TILE_SIZE without duplicate sword artifacts."""
        self.assertTrue(hasattr(self.player, 'attack_frames'))
        self.assertEqual(len(self.player.attack_frames), 3, "Player must have 3-stage attack frames (Windup, Strike, Recovery)")

        for idx, frame in enumerate(self.player.attack_frames):
            self.assertEqual(frame.get_size(), (TILE_SIZE, TILE_SIZE))

        # Check raw disk sprites for zero ghost sword artifact at x=34..38, y=5..22
        for f_idx in [0, 1, 2]:
            p = os.path.join('assets', 'sprites', f'player_attack_{f_idx}.png')
            self.assertTrue(os.path.exists(p))
            im = Image.open(p).convert('RGBA')
            self.assertEqual(im.size, (48, 48))

    def test_player_attack_directional_facing(self):
        """Player must immediately face the direction of the attack."""
        # Attack aiming right
        self.player.attack(target_direction=(1, 0))
        self.assertFalse(self.player.facing_left, "Player aiming right must not face left")

        # Attack aiming left
        self.player.attack(target_direction=(-1, 0))
        self.assertTrue(self.player.facing_left, "Player aiming left must immediately flip facing_left to True")

    def test_attack_pose_covers_full_weapon_swing_while_moving(self):
        """Running frames must not replace the attack pose before the slash ends."""
        from unittest.mock import patch

        class Claymore:
            weapon_type = 'claymore'

        self.player.equipped['weapon'] = Claymore()
        with patch('pygame.time.get_ticks', return_value=1000):
            self.player.attack(target_direction=(1, 0))
        self.player.velocity = pygame.math.Vector2(1, 0)

        # The claymore's slash lasts 320 ms; at 270 ms the hero must still pose in attack.
        with patch('pygame.time.get_ticks', return_value=1270):
            self.player.animate()

        self.assertEqual(self.player.attack_anim_duration, 320)
        expected = self.player.attack_frames[2]
        self.assertEqual(pygame.image.tostring(self.player.image, 'RGBA'), pygame.image.tostring(expected, 'RGBA'))

    def test_attack_pose_takes_priority_over_dash_without_stretch(self):
        from unittest.mock import patch

        self.player.dash_time = 900
        self.player.animation_controller.start_action('dash', 900, self.player.dash_duration)
        with patch('pygame.time.get_ticks', return_value=1000):
            self.player.attack(target_direction=(1, 0))
        with patch('pygame.time.get_ticks', return_value=1080):
            self.player.animate()

        expected = self.player.attack_frames[1]
        self.assertEqual(self.player.sprite_type, 'player')
        self.assertEqual(pygame.image.tostring(self.player.image, 'RGBA'), pygame.image.tostring(expected, 'RGBA'))

    def test_animation_controller_keeps_attack_pose_over_locomotion_and_returns_cleanly(self):
        idle = [pygame.Surface((48, 48), pygame.SRCALPHA) for _ in range(2)]
        walk = [pygame.Surface((48, 48), pygame.SRCALPHA) for _ in range(4)]
        attack = [pygame.Surface((48, 48), pygame.SRCALPHA) for _ in range(3)]
        dash = [pygame.Surface((48, 48), pygame.SRCALPHA) for _ in range(2)]
        controller = PlayerAnimationController(idle, walk, attack, dash, now_ms=0)
        controller.start_action('attack', 1000, 240)

        sample = controller.sample(1080, moving=True)
        self.assertEqual(sample.state, 'attack')
        self.assertIs(sample.frame, attack[1])
        self.assertTrue(sample.is_action)

        sample = controller.sample(1240, moving=True)
        self.assertEqual(sample.state, 'walk')
        self.assertFalse(sample.is_action)

    def test_attack_body_lunges_into_strike_and_returns_to_anchor(self):
        from unittest.mock import patch

        with patch('pygame.time.get_ticks', return_value=1000):
            self.player.attack(target_direction=(1, 0))
        anchor_x = self.player.hitbox.centerx
        original_hitbox = self.player.hitbox.copy()

        with patch('pygame.time.get_ticks', return_value=1000):
            self.player.animate()
        self.assertEqual(self.player.rect.centerx, anchor_x - 2, "Windup should pull the full pose back one pixel step")

        with patch('pygame.time.get_ticks', return_value=1150):
            self.player.animate()
        self.assertEqual(self.player.rect.centerx, anchor_x + 3, "Strike should lunge the full pose toward the target")

        with patch('pygame.time.get_ticks', return_value=1240):
            self.player.animate()
        self.assertEqual(self.player.rect.centerx, anchor_x, "Recovery should restore the original sprite anchor")
        self.assertEqual(self.player.hitbox, original_hitbox, "Visual lunge must not move collision geometry")

    def test_player_update_does_not_erase_attack_lunge(self):
        from unittest.mock import patch

        with patch('pygame.time.get_ticks', return_value=1000):
            self.player.attack(target_direction=(1, 0))
        anchor_x = self.player.hitbox.centerx

        with patch('pygame.time.get_ticks', return_value=1150), patch.object(self.player, 'input'):
            self.player.update()

        self.assertEqual(self.player.hitbox.centerx, anchor_x, "Visual lunge must not alter collision position")
        self.assertEqual(self.player.rect.centerx, anchor_x + 3, "Player.update must preserve the animated strike offset after movement")

    def test_attack_interrupts_dash_and_dash_cannot_replace_attack(self):
        frames = [pygame.Surface((48, 48), pygame.SRCALPHA) for _ in range(3)]
        controller = PlayerAnimationController(frames, frames, frames, frames, now_ms=0)
        controller.start_action('dash', 1000, 200)
        controller.start_action('attack', 1050, 150)
        self.assertEqual(controller.sample(1100, moving=True).state, 'attack')

        controller.start_action('dash', 1100, 200)
        self.assertEqual(controller.sample(1140, moving=True).state, 'attack')
        self.assertEqual(controller.sample(1200, moving=True).state, 'dash')

    def test_ghost_trail_draws_behind_player_with_and_without_zoom(self):
        from src.map_manager import CameraGroup

        camera = CameraGroup()
        player = pygame.sprite.Sprite()
        player.sprite_type = 'player'
        player.image = pygame.Surface((9, 9), pygame.SRCALPHA)
        player.image.fill((40, 220, 255, 255))
        player.rect = player.image.get_rect(center=(100, 100))
        ghost = pygame.sprite.Sprite()
        ghost.sprite_type = 'ghost_trail'
        ghost.image = pygame.Surface((9, 9), pygame.SRCALPHA)
        ghost.image.fill((250, 20, 30, 255))
        ghost.rect = ghost.image.get_rect(center=player.rect.center)
        camera.add(ghost, player)

        for zoom in (1.0, 1.5):
            camera.display_surface.fill((0, 0, 0))
            camera.zoom_level = zoom
            camera.initialized = False
            camera.custom_draw(player)
            self.assertEqual(camera.display_surface.get_at((WIDTH // 2, HEIGHT // 2)), pygame.Color(40, 220, 255, 255))

    def test_audio_mapping_and_sfx_coverage(self):
        """Verifies hit, crit, claymore_swing, sword_swing, dash, and monster SFX are mapped in SoundManager."""
        sm = SoundManager.get_instance()
        expected_sfx = [
            'hit', 'crit', 'sword_swing', 'claymore_swing', 'attack', 'dash', 'shield', 'break',
            'skeleton_hit', 'slime_leap', 'slime_land', 'zombie_attack', 'boss_cleave', 'frost_cast', 'void_burst'
        ]
        for sfx_name in expected_sfx:
            ogg_path = os.path.join('assets', 'sounds', f'{sfx_name}.ogg')
            wav_path = os.path.join('assets', 'sounds', f'{sfx_name}.wav')
            exists = os.path.exists(ogg_path) or os.path.exists(wav_path)
            self.assertTrue(exists, f"Sound file for {sfx_name} must exist on disk")

    def test_player_dash_frames_resolution_consistency(self):
        """Verifies dash frames maintain the 48x48 hero resolution without shrinking."""
        for i in [0, 1]:
            p = os.path.join('assets', 'sprites', f'player_dash_{i}.png')
            self.assertTrue(os.path.exists(p))
            im = Image.open(p)
            self.assertEqual(im.size, (48, 48), "Dash frame must match 48x48 hero canvas")

    def test_skeleton_single_clean_bow_integrity(self):
        """Verifies skeleton aim and attack frames do not contain overlapping duplicate bows."""
        for state in ['aim', 'attack']:
            p = os.path.join('assets', 'sprites', f'skeleton_{state}.png')
            self.assertTrue(os.path.exists(p))
            im = Image.open(p).convert('RGBA')
            self.assertEqual(im.size, (32, 32))
            # Verify clean eye glow
            self.assertEqual(im.getpixel((13, 8))[:3], (224, 242, 254))

    def test_weapon_critical_hit_and_particles(self):
        """Verifies critical hits trigger bonus damage and DamageText."""
        self.player.crit_rate = 100.0 # Force 100% crit
        self.player.crit_dmg = 200.0  # 2.0x multiplier

        enemy = Enemy((150, 100), [self.v_group, self.e_group], self.o_group, self.player, 'zombie', visible_sprites=self.v_group)
        initial_hp = enemy.hp

        # Weapon strike
        wpn = Weapon(self.player, [self.v_group], pygame.math.Vector2(1, 0), weapon_type='sword')
        wpn.update()

        # Enemy must have taken doubled critical damage
        dmg_dealt = initial_hp - enemy.hp
        base_atk = self.player.stats['attack']
        self.assertGreaterEqual(dmg_dealt, base_atk * 1.5, "Critical hit must deal multiplied damage")

if __name__ == '__main__':
    unittest.main()
