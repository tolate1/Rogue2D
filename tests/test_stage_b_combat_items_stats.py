import unittest
import sys
import os
import pygame

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.entities import Player, Enemy, Weapon, RadiantBarrierVFX
from src.items import Item
from src.settings import TILE_SIZE

class TestStageBCombatItemsStats(unittest.TestCase):
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

    def test_shield_vfx_is_a_translucent_sphere(self):
        self.player.is_shielded = True
        vfx = RadiantBarrierVFX(self.player, [self.visible_sprites])
        vfx.update()
        cx = cy = vfx.image.get_width() // 2
        center_alpha = vfx.image.get_at((cx, cy)).a

        self.assertGreaterEqual(vfx.image.get_width(), self.player.rect.width * 1.5)
        self.assertGreater(center_alpha, 0)
        self.assertLess(center_alpha, 100)
        self.assertEqual(vfx.image.get_at((0, 0)).a, 0)

    def test_shield_vfx_is_not_duplicated_by_player_updates(self):
        self.player.is_shielded = True
        first = self.player._ensure_barrier_vfx()
        second = self.player._ensure_barrier_vfx()

        self.assertIs(first, second)
        self.assertEqual(sum(isinstance(s, RadiantBarrierVFX) for s in self.visible_sprites), 1)

    def test_b1_enemy_hp_and_take_damage(self):
        """Enemies have HP pools, survive non-lethal hits, and die cleanly upon lethal damage."""
        zombie = Enemy((100, 100), [self.visible_sprites, self.enemy_sprites],
                       self.obstacle_sprites, self.player, 'zombie', visible_sprites=self.visible_sprites)
        self.assertEqual(zombie.max_hp, 45)
        self.assertEqual(zombie.hp, 45)

        # Non-lethal hit
        killed = zombie.take_damage(20)
        self.assertFalse(killed)
        self.assertEqual(zombie.hp, 25)
        self.assertTrue(zombie.alive())

        # Lethal hit
        initial_kills = self.player.kills
        initial_gold = self.player.gold
        killed = zombie.take_damage(25)
        self.assertTrue(killed)
        self.assertEqual(zombie.hp, 0)
        self.assertFalse(zombie.alive())
        self.assertEqual(self.player.kills, initial_kills + 1)

    def test_b1_weapon_single_hit_per_swing(self):
        """A single sword swing only deals damage once to the same enemy across multiple frames."""
        zombie = Enemy((130, 100), [self.visible_sprites, self.enemy_sprites],
                       self.obstacle_sprites, self.player, 'zombie', visible_sprites=self.visible_sprites)
        self.assertEqual(zombie.hp, 45)

        weapon = Weapon(self.player, [self.visible_sprites], pygame.math.Vector2(1, 0))
        weapon.rect.center = zombie.rect.center # ensure overlap

        # Frame 1: damages zombie by 10 (45 -> 35)
        weapon.update()
        self.assertEqual(zombie.hp, 35)

        # Frame 2: should NOT re-damage the same zombie
        weapon.update()
        self.assertEqual(zombie.hp, 35, "Same weapon swing must not hit enemy twice!")

    def test_b2_multi_level_exp_gain(self):
        """gain_exp handles large XP amounts correctly advancing levels without losing excess XP."""
        self.assertEqual(self.player.level, 1)
        self.assertEqual(self.player.exp, 0)

        # 250 XP at lvl 1 (requires 100 to reach lvl 2)
        self.player.gain_exp(250)
        self.assertEqual(self.player.level, 2)
        self.assertEqual(self.player.exp, 150)
        self.assertEqual(self.player.stats['health'], 110)
        self.assertEqual(self.player.stats['attack'], 12)

    def test_b3_use_potion_from_inventory(self):
        """Drinking a potion restores HP by its heal value and removes it from inventory."""
        self.player.health = 40.0
        potion = Item("Health Potion", "rare", {'heal': 40}, 20, 'assets/sprites/item_heart.png')
        self.player.inventory.append(potion)

        used = self.player.use_potion()
        self.assertTrue(used)
        self.assertEqual(self.player.health, 80.0)
        self.assertNotIn(potion, self.player.inventory)

        # Full health rejection
        self.player.health = 100.0
        potion2 = Item("Health Potion", "common", {'heal': 20}, 10, 'assets/sprites/item_heart.png')
        self.player.inventory.append(potion2)
        used = self.player.use_potion()
        self.assertFalse(used)
        self.assertIn(potion2, self.player.inventory)

    def test_b4_equipment_stat_recalculation(self):
        """Equipped gear dynamically improves attack, max health, speed, and attack speed."""
        sword = Item("Epic Sword", "epic", {'attack': 6}, 30, 'assets/sprites/item_sword.png', slot='weapon')
        armor = Item("Rare Armor", "rare", {'health': 20}, 20, 'assets/sprites/item_armor.png', slot='armor')
        boots = Item("Boots", "common", {'speed': 1}, 10, 'assets/sprites/item_boots.png', slot='boots')
        gloves = Item("Gloves", "common", {'attack_speed': 10}, 10, 'assets/sprites/item_gloves.png', slot='offhand')

        for itm in [sword, armor, boots, gloves]:
            self.player.equip_item(itm)
        self.player.recalculate_stats()

        self.assertEqual(self.player.stats['attack'], 16) # 10 base + 6
        self.assertEqual(self.player.stats['health'], 120) # 100 base + 20
        self.assertEqual(self.player.stats['speed'], 6) # 5 base + 1
        self.assertEqual(self.player.attack_cooldown, 360) # 400 - 10*4

    def test_b5_energy_costs_and_shield_block(self):
        """Dash and Shield consume energy, and Shield blocks 100% of damage while active."""
        self.assertEqual(self.player.energy, 60.0)

        # Simulate Dash input
        keys_mock = [0] * 323
        keys_mock[pygame.K_z] = 1
        from unittest.mock import patch
        with patch('pygame.key.get_pressed', return_value=keys_mock):
            self.player.input()

        self.assertEqual(self.player.energy, 45.0, "Dash must consume 15 energy")

        # Invest through the Dash root to open the defensive branch.
        self.player.skill_points = 2
        ok, _ = self.player.upgrade_skill('dash')
        self.assertTrue(ok)
        ok, _ = self.player.upgrade_skill('shield')
        self.assertTrue(ok)
        keys_mock[pygame.K_z] = 0
        keys_mock[pygame.K_x] = 1
        with patch('pygame.key.get_pressed', return_value=keys_mock):
            self.player.input()

        self.assertEqual(self.player.energy, 20.0, "Shield must consume 25 energy")
        self.assertTrue(self.player.is_shielded)

        # Test Shield damage immunity: zombie hits shielded player
        zombie = Enemy((100, 100), [self.visible_sprites, self.enemy_sprites],
                       self.obstacle_sprites, self.player, 'zombie', visible_sprites=self.visible_sprites)
        self.player.health = 100.0
        zombie.hitbox.center = self.player.hitbox.center
        zombie.move_towards_player()
        self.assertEqual(self.player.health, 100.0, "Shield must block 100% of incoming damage!")

if __name__ == '__main__':
    unittest.main()
