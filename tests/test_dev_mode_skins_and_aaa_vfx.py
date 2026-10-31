import os
import unittest
import pygame
from PIL import Image

os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.settings import WIDTH, HEIGHT, TILE_SIZE
from src.entities import Player, Weapon
from src.map_manager import Level, ShowcaseEntity

class TestDevModeSkinsAndAAAVFX(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()
        pygame.display.set_mode((WIDTH, HEIGHT))

    def setUp(self):
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        if not pygame.display.get_surface():
            pygame.display.set_mode((WIDTH, HEIGHT))

        self.visible = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player = Player((200, 200), [self.visible], self.obstacles, self.enemies)

    def test_1_dev_room_creation_and_exhibits(self):
        """Dev Room initializes properly with all exhibit wings and showcase entities."""
        dev_level = Level(is_dev_room=True)
        self.assertTrue(dev_level.is_dev_room)
        self.assertFalse(dev_level.is_hub)
        self.assertFalse(dev_level.is_boss_level)
        self.assertIsNotNone(dev_level.player)

        # Check showcase entities count
        showcase_entities = [s for s in dev_level.visible_sprites if isinstance(s, ShowcaseEntity)]
        self.assertGreaterEqual(len(showcase_entities), 18, "Dev Room must showcase all mobs, bosses, and hero variants")

        # Verify boss exhibits exist
        boss_ids = [s.entity_id for s in showcase_entities if 'boss' in s.entity_id]
        self.assertIn('boss_void_knight', boss_ids)
        self.assertIn('boss_bone_golem', boss_ids)
        self.assertIn('boss_frost_revenant', boss_ids)
        self.assertIn('boss_necro_lord', boss_ids)

        # Verify hero skin exhibits exist
        hero_ids = [s.entity_id for s in showcase_entities if 'player_' in s.entity_id]
        self.assertIn('player_default', hero_ids)
        self.assertIn('player_paladin', hero_ids)
        self.assertIn('player_dark_knight', hero_ids)
        self.assertIn('player_champion', hero_ids)

    def test_2_showcase_entity_animation_cycling_and_invulnerability(self):
        """Showcase entities cycle through their animation states without taking fatal damage."""
        anim_data = {
            'ожидание': [pygame.Surface((32, 32))],
            'атака': [pygame.Surface((32, 32))],
            'восстановление': [pygame.Surface((32, 32))]
        }
        showcase = ShowcaseEntity((100, 100), [self.visible], 'test_mob', 'Тестовый Моб', anim_data)
        self.assertEqual(showcase.current_state, 'ожидание')

        # Simulate state time advance
        showcase.state_start_time = pygame.time.get_ticks() - 3000
        showcase.update()
        self.assertEqual(showcase.current_state, 'атака', "Must advance to next showcased animation")

        # Player strikes showcase entity
        showcase.take_damage(999)
        self.assertTrue(showcase.alive(), "Showcase entity must not die from weapon strikes")
        self.assertGreaterEqual(pygame.time.get_ticks() - showcase.took_damage_time, 0)

    def test_3_hero_skin_switching_and_availability(self):
        """Player has 4 skins available and can switch cleanly via set_skin and cycle_skin."""
        expected_skins = ['default', 'paladin', 'dark_knight', 'champion']
        self.assertEqual(self.player.available_skins, expected_skins)
        self.assertEqual(self.player.current_skin, 'champion')
        default_idle = self.player._skin_cache['default']['idle'][0]
        self.assertNotEqual(pygame.image.tostring(self.player.idle_frames[0], 'RGBA'), pygame.image.tostring(default_idle, 'RGBA'))

        # The blue Champion is the default; cycling moves to Paladin.
        self.player.cycle_skin()
        self.assertEqual(self.player.current_skin, 'paladin')
        self.assertEqual(len(self.player.attack_frames), 3)

        # Cycle to Dark Knight
        self.player.cycle_skin()
        self.assertEqual(self.player.current_skin, 'dark_knight')

        # Cycle through the standard knight skin and back to the blue default.
        self.player.cycle_skin()
        self.assertEqual(self.player.current_skin, 'default')
        self.player.cycle_skin()
        self.assertEqual(self.player.current_skin, 'champion')

    def test_4_zero_deformation_guarantee_across_all_skins(self):
        """Hero core body pixels in x:9..32, y:5..43 must not deform between idle and attack."""
        skins = ['player', 'player_paladin', 'player_dark_knight', 'player_champion']
        for skin in skins:
            idle_path = os.path.join('assets', 'sprites', f'{skin}_idle_0.png')
            self.assertTrue(os.path.exists(idle_path), f"Idle sprite missing for {skin}")
            idle_im = Image.open(idle_path).convert('RGBA')
            self.assertEqual(idle_im.size, (48, 48))

            for atk_idx in [0, 1, 2]:
                atk_path = os.path.join('assets', 'sprites', f'{skin}_attack_{atk_idx}.png')
                self.assertTrue(os.path.exists(atk_path), f"Attack sprite {atk_idx} missing for {skin}")
                atk_im = Image.open(atk_path).convert('RGBA')
                self.assertEqual(atk_im.size, (48, 48))

                # Verify core body region has 0 coordinate distortion / shift
                for y in range(5, 43):
                    for x in range(9, 32):
                        p_idle = idle_im.getpixel((x, y))
                        p_atk = atk_im.getpixel((x, y))
                        self.assertEqual(p_idle, p_atk, f"Zero-deform violation in {skin} attack_{atk_idx} at ({x}, {y})")

    def test_5_aaa_level_up_vfx_trigger(self):
        """Player.trigger_level_up_vfx() updates level_up_time and triggers screen shake."""
        start_time = pygame.time.get_ticks()
        self.player.trigger_level_up_vfx()
        self.assertGreaterEqual(self.player.level_up_time, start_time)

        # Gain exp enough to level up also triggers it
        self.player.exp = 0
        self.player.gain_exp(100) # 100 exp = Level 2
        self.assertEqual(self.player.level, 2)
        self.assertGreaterEqual(self.player.level_up_time, start_time)

    def test_6_hero_skins_have_distinct_silhouettes(self):
        """Verify paladin, dark_knight, and champion have genuinely different silhouettes from default."""
        p0_path = os.path.join('assets', 'sprites', 'player_idle_0.png')
        p0_surf = pygame.image.load(p0_path)
        m0 = pygame.mask.from_surface(p0_surf)

        for sk in ['paladin', 'dark_knight', 'champion']:
            sk_path = os.path.join('assets', 'sprites', f'player_{sk}_idle_0.png')
            sk_surf = pygame.image.load(sk_path)
            m_sk = pygame.mask.from_surface(sk_surf)
            # Count overlapping vs non-overlapping pixels
            overlap = m0.overlap_mask(m_sk, (0, 0)).count()
            diff = (m0.count() - overlap) + (m_sk.count() - overlap)
            self.assertGreater(diff, 30, f"Skin {sk} has too few silhouette differences from default ({diff} <= 30)")

    def test_7_necromancer_cast_has_single_staff(self):
        """Verify necromancer_cast raises authentic bone skull staff and has no duplicate staff at x=22..28."""
        cast_path = os.path.join('assets', 'sprites', 'necromancer_cast.png')
        cast_surf = pygame.image.load(cast_path)
        # Verify right side has NO fake second wooden staff orb overhead
        for y in range(0, 8):
            for x in range(20, 31):
                c = cast_surf.get_at((x, y))
                self.assertEqual(c.a, 0, f"Duplicate second staff pixel found at ({x}, {y}): {c}")
        # Verify authentic bone skull staff exists on the left
        staff_pixel = cast_surf.get_at((6, 10))
        self.assertGreater(staff_pixel.a, 0, "Authentic staff must be present on the left")

    def test_8_skeleton_aim_bow_protrudes(self):
        """Verify skeleton_aim bow reaches forward past x >= 28."""
        aim_path = os.path.join('assets', 'sprites', 'skeleton_aim.png')
        aim_surf = pygame.image.load(aim_path)
        bb = aim_surf.get_bounding_rect()
        self.assertGreaterEqual(bb.right, 28, f"Skeleton bow does not protrude forward enough ({bb.right} < 28)")

    def test_9_weapon_slash_sweep_animation(self):
        """Verify Weapon.render_slash creates dynamic non-empty crescent frames."""
        from src.entities import Weapon
        direction = pygame.math.Vector2(1, 0)
        weapon = Weapon(self.player, [], direction, weapon_type='sword')
        mid_slash = weapon.render_slash(0.5)
        self.assertGreater(mid_slash.get_width(), 0)
        m = pygame.mask.from_surface(mid_slash)
        self.assertGreater(m.count(), 20)


    def test_10_dash_squash_and_stretch_and_ghost_trail(self):
        """Dash scales the full-body pose horizontally and spawns its chromatic GhostTrail."""
        from src.entities import GhostTrail
        self.player.dash_time = pygame.time.get_ticks() - 20
        self.player.animation_controller.start_action('dash', self.player.dash_time, self.player.dash_duration)
        self.player.last_ghost_trail_time = -1000
        self.player.animate()
        
        # In early dash (prog < 0.65), sprite is stretched horizontally
        self.assertGreater(self.player.image.get_width(), 48, "Dash must stretch sprite width during initial impulse")
        self.assertEqual(self.player.image.get_height(), self.player.dash_frames[0].get_height(), "Dash pose must preserve the skin's original frame height")
        
        # Player update spawns GhostTrail
        self.player.visible_sprites = self.visible
        self.player.update()
        ghosts = [s for s in self.visible if isinstance(s, GhostTrail)]
        self.assertGreaterEqual(len(ghosts), 1, "Dash must spawn GhostTrail sprite")
        ghost = ghosts[0]
        self.assertEqual(ghost.sprite_type, 'ghost_trail')
        self.assertTrue(ghost.chromatic)

    def test_11_camera_subpixel_lerp(self):
        """CameraGroup smoothly interpolates toward player with exponential lerp instead of hard snapping."""
        cam_group = self.player.visible_sprites
        if not hasattr(cam_group, 'custom_draw'):
            from src.map_manager import CameraGroup
            cam_group = CameraGroup()
            cam_group.add(self.player)
            self.player.visible_sprites = cam_group

        # First frame initializes camera directly
        cam_group.custom_draw(self.player)
        init_x = cam_group.offset.x

        # Teleport player 100 pixels to the right
        self.player.rect.x += 100
        cam_group.custom_draw(self.player)
        
        # Camera should move smoothly toward new target, not snap all 100 pixels in 1 frame
        expected_snap_x = init_x + 100
        self.assertGreater(cam_group.offset.x, init_x, "Camera must move towards player")
        self.assertLess(cam_group.offset.x, expected_snap_x - 10, "Camera must smoothly lerp instead of hard 100px snap")

    def test_12_floor_ambient_occlusion_applied(self):
        """Floor tiles adjacent to walls have 2.5D contact Ambient Occlusion (AO) baked into surface."""
        level = Level(is_dev_room=True)
        wall_set = level.wall_positions
        ao_found = False
        from src.utils import load_image
        raw_floor = load_image('assets/sprites/floor.png', scale=(TILE_SIZE, TILE_SIZE))
        
        for s in level.visible_sprites:
            if getattr(s, 'sprite_type', '') == 'floor':
                tx = int(s.rect.x // TILE_SIZE)
                ty = int(s.rect.y // TILE_SIZE)
                if (tx, ty - 1) in wall_set or (tx - 1, ty) in wall_set or (tx + 1, ty) in wall_set:
                    # Check top pixel row has darkening
                    top_pixel_floor = s.image.get_at((16, 1))
                    raw_pixel = raw_floor.get_at((16, 1))
                    if top_pixel_floor.r < raw_pixel.r:
                        ao_found = True
                        break
        self.assertTrue(ao_found, "Ambient occlusion gradient must darken floor tiles adjacent to walls")

    def test_13_fake_bloom_pass_execution(self):
        """Level.draw executes Fake Bloom Pass without crashes and initializes scratch buffers."""
        level = Level(is_dev_room=True)
        level.draw()
        self.assertTrue(hasattr(level, '_bloom_thresh'), "Level must allocate Fake Bloom threshold scratch buffer")
        self.assertEqual(level._bloom_thresh.get_size(), (WIDTH // 6, HEIGHT // 6))

if __name__ == '__main__':
    unittest.main()
