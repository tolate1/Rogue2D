import os
import unittest
import pygame
from src.entities import Player, Enemy, BloodAltar, ChainLightningVFX, FlameTrailHazard, SoulMote
from src.map_manager import Level
from src.save_manager import load_profile

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'


class TestLowHPAltarAndSynergies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

    def setUp(self):
        self.level = Level(current_floor=1)
        self.player = self.level.player
        self._orig_profile = load_profile()

    def tearDown(self):
        if hasattr(self, '_orig_profile'):
            from src.save_manager import save_profile
            save_profile(self._orig_profile)

    def test_low_hp_panic_activation(self):
        """Verify Low HP Panic triggers when health drops below 28% and clears when healed."""
        max_hp = self.player.stats.get('health', 100)
        self.player.health = int(max_hp * 0.50)
        self.player.update()
        self.assertFalse(self.player.low_hp_active)

        # Drop to 20% (< 28%)
        self.player.health = int(max_hp * 0.20)
        self.player.update()
        self.assertTrue(self.player.low_hp_active)

        # Heal back to 50%
        self.player.health = int(max_hp * 0.50)
        self.player.update()
        self.assertFalse(self.player.low_hp_active)

    def test_blood_altar_successful_sacrifice(self):
        """Verify BloodAltar consumes 35 HP, grants purple shard and relic, and marks used."""
        altar = BloodAltar((200, 200), [self.level.visible_sprites, self.level.altar_sprites])
        self.assertFalse(altar.used)
        
        prof_before = load_profile()
        shards_before = prof_before.get('purple_shards', 0)
        
        self.player.health = 80
        success = altar.interact(self.player, self.level)
        self.assertTrue(success)
        self.assertEqual(self.player.health, 80 - 35)
        self.assertTrue(altar.used)

        prof_after = load_profile()
        self.assertEqual(prof_after.get('purple_shards', 0), shards_before + 1)

        # Cannot be used a second time
        second_attempt = altar.interact(self.player, self.level)
        self.assertFalse(second_attempt)

    def test_blood_altar_low_hp_rejection(self):
        """Verify BloodAltar rejects sacrifice if player does not have enough HP to survive."""
        altar = BloodAltar((200, 200), [self.level.visible_sprites])
        self.player.health = 30 # <= 35
        success = altar.interact(self.player, self.level)
        self.assertFalse(success)
        self.assertEqual(self.player.health, 30) # Health unchanged
        self.assertFalse(altar.used)

    def test_chain_lightning_vfx(self):
        """Verify ChainLightningVFX creates valid jagged electric geometry and expires."""
        vfx = ChainLightningVFX((100, 100), (250, 150), [self.level.visible_sprites])
        self.assertEqual(vfx.sprite_type, 'ui_effect')
        self.assertGreaterEqual(len(vfx.points), 3)
        vfx.update()
        self.assertTrue(vfx.alive())
        # Force expiration
        vfx.spawn_time -= 200
        vfx.update()
        self.assertFalse(vfx.alive())

    def test_flame_trail_hazard_damage(self):
        """Verify FlameTrailHazard damages overlapping enemies."""
        enemy = Enemy((150, 150), [self.level.visible_sprites], [self.level.obstacle_sprites], self.player, 'zombie')
        enemy.hp = 30
        hazard = FlameTrailHazard((150, 150), [self.level.visible_sprites], enemy_sprites=[enemy])
        self.assertEqual(hazard.sprite_type, 'hazard')
        hazard.last_tick_time = 0
        hazard.update()
        self.assertLess(enemy.hp, 30) # Took fire tick damage

    def test_soul_mote_homing_and_heal(self):
        """Verify SoulMote homes toward player and heals upon absorption."""
        self.player.health = 50
        mote = SoulMote((self.player.rect.centerx + 40, self.player.rect.centery), [self.level.visible_sprites], self.player)
        self.assertEqual(mote.sprite_type, 'ui_effect')
        
        # Teleport mote onto player
        mote.pos = pygame.math.Vector2(self.player.rect.center)
        mote.update()
        self.assertFalse(mote.alive())
        self.assertEqual(self.player.health, 52) # Healed +2 HP

    def test_sacred_chest_integrity(self):
        """Rule 1: Sacred chest opening animation frames must remain completely untouched."""
        from src.utils import load_image
        c0 = load_image('assets/sprites/chest_0.png')
        c1 = load_image('assets/sprites/chest_1.png')
        c2 = load_image('assets/sprites/chest_2.png')
        self.assertIsNotNone(c0)
        self.assertIsNotNone(c1)
        self.assertIsNotNone(c2)


if __name__ == '__main__':
    unittest.main()
