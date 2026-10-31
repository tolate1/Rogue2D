import unittest
import sys
import os
import pygame

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.entities import Player, Enemy, ToxicPuddle, EnemyProjectile
from src.map_manager import Level, BossArenaPillar, BossRunicCircle

class TestOverhaulMobsAndBosses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.visible_sprites = pygame.sprite.Group()
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.player = Player((100, 100), [self.visible_sprites], self.obstacle_sprites, self.enemy_sprites)

    def test_toxic_slime_leap_and_puddle(self):
        """Verifies toxic slime has leap state transitions and leaves damaging toxic puddles."""
        slime = Enemy((220, 100), [self.visible_sprites, self.enemy_sprites],
                      self.obstacle_sprites, self.player, 'toxic_slime', visible_sprites=self.visible_sprites)
        self.assertEqual(slime.enemy_type, 'toxic_slime')
        self.assertEqual(slime.hp, 60)
        self.assertTrue(hasattr(slime, 'slime_state'))

        # Force leap trigger
        slime.has_los = True
        slime.slime_leap_timer = 0
        slime.move_towards_player()
        self.assertEqual(slime.slime_state, 'charging')

        # Test ToxicPuddle hazard
        puddle = ToxicPuddle((100, 100), [self.visible_sprites], duration=3000, radius=20, damage=4)
        initial_hp = self.player.health
        puddle.update_hazard(self.player)
        self.assertLess(self.player.health, initial_hp, "Puddle should damage player on contact")
        self.assertEqual(getattr(self.player, 'speed_modifier', 1.0), 0.65, "Puddle should slow player")

        # Test Slime division on death
        pre_count = len([e for e in self.visible_sprites if isinstance(e, Enemy)])
        slime.take_damage(100)
        post_minis = [e for e in self.visible_sprites if isinstance(e, Enemy) and e.enemy_type == 'mini_slime']
        self.assertEqual(len(post_minis), 2, "Toxic slime should split into 2 mini slimes on death")

    def test_mob_teamwork_alert(self):
        """Verifies that an enemy spotting the player alerts nearby allies within 340px."""
        enemy1 = Enemy((200, 100), [self.visible_sprites, self.enemy_sprites],
                       self.obstacle_sprites, self.player, 'goblin', visible_sprites=self.visible_sprites)
        enemy2 = Enemy((280, 100), [self.visible_sprites, self.enemy_sprites],
                       self.obstacle_sprites, self.player, 'zombie', visible_sprites=self.visible_sprites)

        self.assertIsNone(enemy2.last_known_player_pos)
        enemy1.has_los = True
        enemy1.move_towards_player()
        enemy1.alert_nearby_allies()

        self.assertIsNotNone(enemy2.last_known_player_pos, "Nearby ally should receive alerted player position")

    def test_boss_projectile_types_and_bullet_hell(self):
        """Verifies new projectile types for boss bullet hell (frost, bone, void)."""
        frost_proj = EnemyProjectile((100, 100), [self.visible_sprites], pygame.math.Vector2(1, 0),
                                     self.obstacle_sprites, self.player, proj_type='frost_shard')
        self.assertEqual(frost_proj.proj_type, 'frost_shard')
        self.assertEqual(frost_proj.damage, 12)

        bone_proj = EnemyProjectile((100, 100), [self.visible_sprites], pygame.math.Vector2(1, 0),
                                    self.obstacle_sprites, self.player, proj_type='bone_spike')
        self.assertEqual(bone_proj.proj_type, 'bone_spike')
        self.assertEqual(bone_proj.damage, 11)

        void_proj = EnemyProjectile((100, 100), [self.visible_sprites], pygame.math.Vector2(1, 0),
                                    self.obstacle_sprites, self.player, proj_type='void_orb')
        self.assertEqual(void_proj.proj_type, 'void_orb')
        self.assertEqual(void_proj.damage, 14)

    def test_boss_arena_architecture(self):
        """Verifies boss arena creates 4 tactical pillars and centered occult mandala."""
        level = Level(current_floor=5)
        self.assertTrue(level.is_boss_level)

        pillars = [s for s in level.visible_sprites if isinstance(s, BossArenaPillar)]
        self.assertEqual(len(pillars), 4, "Boss arena must feature 4 tactical cover pillars")

        circles = [s for s in level.visible_sprites if isinstance(s, BossRunicCircle)]
        self.assertEqual(len(circles), 1, "Boss arena must feature a centered runic circle")

    def test_enemy_animation_state_transitions(self):
        """Verifies multi-state animation framework switches frames on telegraphs, charges, and attacks."""
        slime = Enemy((200, 100), [self.visible_sprites, self.enemy_sprites],
                      self.obstacle_sprites, self.player, 'toxic_slime', visible_sprites=self.visible_sprites)
        self.assertIn('charge', slime.anim_states)
        self.assertIn('leap', slime.anim_states)
        self.assertIn('land', slime.anim_states)

        # Test slime squash in charging state
        slime.slime_state = 'charging'
        slime.anim_state = 'charge'
        slime.animate()
        # Squashed flat: width is expanded (> 64), height is compressed (< 64)
        self.assertGreater(slime.image.get_width(), 64)
        self.assertLess(slime.image.get_height(), 64)

        # Test skeleton attack & aiming states
        skeleton = Enemy((200, 100), [self.visible_sprites, self.enemy_sprites],
                         self.obstacle_sprites, self.player, 'skeleton', visible_sprites=self.visible_sprites)
        self.assertIn('aim', skeleton.anim_states)
        self.assertIn('attack', skeleton.anim_states)
        skeleton.has_los = True
        skeleton.move_towards_player()
        self.assertEqual(skeleton.anim_state, 'attack')
        skeleton.can_attack = False
        skeleton.attack_anim_until = 0
        skeleton.move_towards_player()
        self.assertEqual(skeleton.anim_state, 'aim')

        # Test boss telegraph state
        boss = Enemy((200, 100), [self.visible_sprites, self.enemy_sprites],
                     self.obstacle_sprites, self.player, 'boss_void_knight', visible_sprites=self.visible_sprites)
        self.assertIn('telegraph', boss.anim_states)
        self.assertIn('cleave', boss.anim_states)
        self.assertIn('burst', boss.anim_states)
        boss.boss_attack_state = 'telegraph'
        boss.update()
        self.assertEqual(boss.anim_state, 'telegraph')

if __name__ == '__main__':
    unittest.main()
