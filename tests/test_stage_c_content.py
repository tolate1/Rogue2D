import unittest
import sys
import os
import pygame

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.entities import Player, Enemy
from src.items import generate_random_item, Gold, Item
from src.map_manager import HazardTile

class TestStageCContent(unittest.TestCase):
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

    def test_c1_new_items_generation_and_magnet(self):
        """Random item generation produces new items and magnet pulls gold toward player."""
        item_names = set()
        for _ in range(100):
            item = generate_random_item()
            item_names.add(item.name.split()[-1].lower())

        self.assertTrue({'claymore', 'magnet', 'scroll', 'star', 'gear'}.issubset(item_names))

        # Test Magnet Pull
        magnet = Item("Rare Magnet", "rare", {'magnet': 2}, 20, 'assets/sprites/item_magnet.png')
        self.player.inventory.append(magnet)

        gold = Gold((180, 100), [self.visible_sprites], 5, self.player)
        initial_gold_x = gold.rect.x
        gold.update()
        self.assertLess(gold.rect.x, initial_gold_x, "Gold should be magnetized towards player")

    def test_c2_ice_biome_sliding(self):
        """Ice biome applies low friction (0.94) causing sliding when direction stops."""
        self.player.biome = 'ice'
        self.player.velocity = pygame.math.Vector2(5.0, 0)
        self.player.direction = pygame.math.Vector2(0, 0)

        self.player.move(self.player.speed)
        # Velocity should decay gradually (5.0 * 0.94 = ~4.7), not drop to 0
        self.assertGreater(self.player.velocity.x, 3.5)
        self.assertLess(self.player.velocity.x, 5.0)

    def test_c2_volcano_hazard_tile(self):
        """Volcano hazard tile deals damage unless shielded."""
        hazard = HazardTile((100, 100), [self.visible_sprites])
        self.player.health = 100.0
        hazard.hitbox.center = self.player.hitbox.center

        # Step on hazard
        hazard.update_hazard(self.player)
        self.assertEqual(self.player.health, 92.0)

        # Shielded step on hazard
        self.player.is_shielded = True
        hazard.last_damage_time = -1000 # allow trigger
        hazard.update_hazard(self.player)
        self.assertEqual(self.player.health, 92.0, "Shield must block hazard damage")

    def test_c3_boss_phases_and_burst(self):
        """Void Knight transitions from Phase 1 to Phase 2 (Enraged) below 100 HP, unleashing 8-dir bursts."""
        boss = Enemy((200, 200), [self.visible_sprites, self.enemy_sprites],
                     self.obstacle_sprites, self.player, 'boss_void_knight', visible_sprites=self.visible_sprites)
        self.assertEqual(boss.hp, 250)
        self.assertEqual(boss.boss_phase, 1)

        # Bring boss to Phase 2 (below 100 HP)
        boss.take_damage(160)
        self.assertEqual(boss.hp, 90)

        # Initial projectile count
        initial_projs = len([s for s in self.visible_sprites if 'projectile' in s.__class__.__name__.lower() or hasattr(s, 'has_hit')])

        # Update boss in phase 2
        boss.boss_burst_time = -5000 # force trigger burst
        boss.update()

        self.assertEqual(boss.boss_phase, 2)
        self.assertEqual(boss.speed, 3.2)

        final_projs = len([s for s in self.visible_sprites if 'projectile' in s.__class__.__name__.lower() or hasattr(s, 'has_hit')])
        self.assertEqual(final_projs - initial_projs, 8, "Phase 2 boss must spawn an 8-projectile circular burst")

if __name__ == '__main__':
    unittest.main()
