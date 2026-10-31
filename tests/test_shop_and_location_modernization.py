import os
import unittest
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.items import Item
from src.entities import Player, Enemy, Particle
from src.ui import UI, ShopModal
from src.map_manager import Level, BossRunicCircle, BossArenaPillar

class TestShopAndLocationModernization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()
        pygame.display.set_mode((960, 640))

    def setUp(self):
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        if not pygame.display.get_surface():
            pygame.display.set_mode((960, 640))

        self.group = pygame.sprite.Group()
        self.obstacle_group = pygame.sprite.Group()
        self.player = Player((100, 100), [self.group], self.obstacle_group, self.group)
        self.level = Level(current_floor=5, floor_seed=12345)

    def test_1_line_of_fire_with_particles_resilience(self):
        """Line of fire must never crash when particles or non-obstacle sprites are in obstacle_sprites."""
        skeleton = Enemy((120, 100), [self.group], self.obstacle_group, self.player, 'skeleton', visible_sprites=self.group)
        # Intentionally inject Particle without hitbox into obstacle_group
        p = Particle((110, 100), [self.group])
        self.obstacle_group.add(p)
        
        # Must execute cleanly without AttributeError: 'Particle' object has no attribute 'hitbox'
        los_result = skeleton.has_line_of_fire()
        self.assertIsInstance(los_result, bool)

    def test_2_boss_arena_pillar_particle_safety(self):
        """BossArenaPillar updates flame motes into visible_group only, never obstacle group."""
        pillar = BossArenaPillar((100, 100), [self.group, self.obstacle_group], biome='void')
        self.assertEqual(pillar.visible_group, self.group)
        
        # Run updates to trigger flame embers
        for _ in range(20):
            pillar.update()
        
        # Verify no Particle ever leaked into obstacle_group
        for s in self.obstacle_group:
            self.assertNotIsInstance(s, Particle, "Particles must never be added to obstacle_group")

    def test_3_boss_runic_circle_visual_update(self):
        """BossRunicCircle updates alpha and spawns ambient ritual motes into visible_group without crash."""
        circle = BossRunicCircle((200, 200), [self.group], biome='void')
        self.assertEqual(circle.sz, 380)
        
        for _ in range(30):
            circle.update()
        self.assertTrue(circle.alive())

    def test_4_shop_modal_6_procedural_items(self):
        """ShopModal provides 6 varied procedural items."""
        shop = ShopModal(self.level, self.player)
        self.assertEqual(len(shop.items), 6)
        
        types = [itm['type'] for itm in shop.items]
        self.assertIn('potion', types)
        self.assertIn('weapon', types)
        self.assertIn('armor', types)
        self.assertIn('boots', types)

    def test_5_shop_modal_reroll_functionality(self):
        """Reroll refreshes shop stock with new items and deducts 25 gold."""
        self.player.gold = 100
        shop = ShopModal(self.level, self.player)
        initial_names = [itm['name'] for itm in shop.items]
        
        shop.reroll_stock()
        self.assertEqual(self.player.gold, 75, "Reroll must deduct exactly 25 gold")
        self.assertEqual(len(shop.items), 6)
        self.assertIn("обновлены", shop.message.lower())
        new_names = [itm['name'] for itm in shop.items]
        # Assert that the stock actually changed upon reroll (fixing defect E06)
        self.assertNotEqual(initial_names, new_names, "Reroll must generate distinct stock")

    def test_6_shop_modal_selling_items(self):
        """Player can sell unwanted inventory items for gold."""
        self.player.gold = 50
        junk_sword = Item("Старый Клинок", "common", {'attack': 2}, 40, slot='weapon')
        self.player.inventory.append(junk_sword)
        self.assertIn(junk_sword, self.player.inventory)
        
        shop = ShopModal(self.level, self.player)
        shop.set_tab('sell')
        self.assertEqual(shop.tab, 'sell')
        
        # Sell the item
        shop.sell_item(0)
        self.assertNotIn(junk_sword, self.player.inventory)
        self.assertGreater(self.player.gold, 50, "Gold must increase after selling")
        self.assertIn("продано", shop.message.lower())

    def test_7_shop_reactive_greetings(self):
        """Kelvin reacts to player's low health, wealth, and equipped weapons."""
        # Low health reaction
        self.player.stats['health'] = 100
        self.player.health = 20
        shop = ShopModal(self.level, self.player)
        self.assertIn("крови", shop.speech_text.lower())
        self.assertIn("Хочешь что-то купить?", shop.speech_text)

        # High wealth reaction
        self.player.health = 100
        self.player.gold = 350
        shop2 = ShopModal(self.level, self.player)
        self.assertIn("кошель", shop2.speech_text.lower())
        self.assertIn("Хочешь что-то купить?", shop2.speech_text)

    def test_8_minimap_fog_of_war(self):
        """Minimap renders visited tiles and tracks unexplored fog-of-war."""
        self.assertIsInstance(self.level.visited_tiles, set)
        self.level.update()
        self.assertGreater(len(self.level.visited_tiles), 0)
        
        ui = UI()
        # Draw UI without crashing
        ui.draw(self.player, self.level)

    def test_9_location_entrance_banner(self):
        """Location banner displays chapter title and boss danger badge smoothly."""
        ui = UI()
        self.level.floor_enter_time = pygame.time.get_ticks()
        
        # Draw at start of floor (t = 100ms)
        ui.draw(self.player, self.level)
        self.assertTrue(getattr(self.level, 'location_sting_played', False))

if __name__ == '__main__':
    unittest.main()
