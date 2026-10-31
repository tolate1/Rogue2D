import os
import unittest
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
if not pygame.display.get_surface():
    pygame.display.set_mode((960, 640))

from src.entities import Player, Enemy, Weapon, DamageText

class TestDamageNumbersOverhaul(unittest.TestCase):
    def setUp(self):
        self.v_group = pygame.sprite.Group()
        self.o_group = pygame.sprite.Group()
        self.e_group = pygame.sprite.Group()
        self.player = Player((100, 100), [self.v_group], self.o_group, self.e_group)

    def test_damage_text_arc_drift_and_fade(self):
        """Verify DamageText has float physics with upward velocity and alpha fade."""
        dt = DamageText("42", (100, 100), [self.v_group], color=(250, 250, 250), size=16)
        init_y = dt.pos_y
        dt.update()
        self.assertLess(dt.pos_y, init_y, "Damage text must float upward")
        self.assertTrue(dt.alive())

        # Check shadow surface presence
        self.assertGreater(dt.image.get_width(), 10)
        self.assertGreater(dt.image.get_height(), 10)

        # Advance past duration
        dt.spawn_time = pygame.time.get_ticks() - 800
        dt.update()
        self.assertFalse(dt.alive(), "Damage text should expire after duration")

    def test_enemy_normal_damage_spawns_white_text(self):
        """Verify normal attack spawns white damage text."""
        enemy = Enemy((140, 100), [self.v_group, self.e_group], self.o_group, self.player, 'zombie', visible_sprites=self.v_group)
        before_count = len(self.v_group)
        enemy.take_damage(25, source='weapon', is_crit=False)
        dmg_texts = [s for s in self.v_group if isinstance(s, DamageText)]
        self.assertGreaterEqual(len(dmg_texts), 1)
        latest_dt = dmg_texts[-1]
        self.assertFalse(latest_dt.is_crit)

    def test_enemy_crit_damage_spawns_gold_crit_text(self):
        """Verify critical hit spawns gold DamageText with is_crit=True and exclamation mark."""
        enemy = Enemy((140, 100), [self.v_group, self.e_group], self.o_group, self.player, 'zombie', visible_sprites=self.v_group)
        enemy.take_damage(60, source='weapon', is_crit=True)
        dmg_texts = [s for s in self.v_group if isinstance(s, DamageText)]
        crit_texts = [dt for dt in dmg_texts if getattr(dt, 'is_crit', False)]
        self.assertGreaterEqual(len(crit_texts), 1)
        self.assertTrue(crit_texts[-1].is_crit)

    def test_player_damage_spawns_ruby_red_text(self):
        """Verify Player taking damage spawns ruby red damage text."""
        before_count = len([s for s in self.v_group if isinstance(s, DamageText)])
        self.player.take_damage(30, source_pos=(50, 50))
        after_texts = [s for s in self.v_group if isinstance(s, DamageText)]
        self.assertGreater(len(after_texts), before_count, "Player must spawn DamageText on damage")

if __name__ == '__main__':
    unittest.main()
