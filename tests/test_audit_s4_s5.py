import unittest
import sys
import os
import tempfile
import pygame
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import src.save_manager
from src.map_manager import Level
from src.save_manager import save_game_state, load_game_state
from src.entities import Player, Enemy
from src.items import Item, Chest, Gold, Breakable
from main import Game

class TestAuditS4S5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.orig_save_file = src.save_manager.SAVE_FILE
        src.save_manager.SAVE_FILE = os.path.join(self.tmp_dir.name, "savegame.json")

    def tearDown(self):
        src.save_manager.SAVE_FILE = self.orig_save_file
        self.tmp_dir.cleanup()

    def test_shop_key_1_no_potion_drinking_and_honest_price(self):
        """Pressing 1 near trader buys heal and does NOT drink player's own potion."""
        level = Level(current_floor=1, floor_seed=123)
        p = level.player
        p.health = 20
        p.gold = 100
        # Add 1 healing potion to player inventory
        pot = Item("Health Potion", "common", {'heal': 25}, 10, 'assets/sprites/item_heart.png')
        p.inventory.append(pot)
        self.assertEqual(len([i for i in p.inventory if 'heal' in getattr(i, 'effects', {})]), 1)

        # Place a mock trader right by player
        trader = pygame.sprite.Sprite([level.visible_sprites, level.trader_sprites])
        trader.rect = pygame.Rect(p.rect.x + 30, p.rect.y, 32, 32)
        
        # Simulate update when key 1 is pressed
        keys = {pygame.K_1: True, pygame.K_2: False, pygame.K_3: False, pygame.K_4: False, pygame.K_e: False,
                pygame.K_w: False, pygame.K_s: False, pygame.K_a: False, pygame.K_d: False, pygame.K_q: False,
                pygame.K_z: False, pygame.K_x: False, pygame.K_c: False}
        
        from unittest.mock import patch
        with patch('pygame.key.get_pressed', return_value=keys):
            level.update()

        # Trader healed player from 20 -> 70, deducted 50g
        self.assertEqual(p.gold, 50, "Option 1 must deduct 50g")
        self.assertEqual(p.health, 70, "Health restored by trader +50")
        # Personal potion must NOT have been consumed!
        self.assertEqual(len([i for i in p.inventory if 'heal' in getattr(i, 'effects', {})]), 1,
                         "Personal potion must not be consumed when interacting with merchant")

    def test_shop_speed_cap_rejection(self):
        """Trader option 4 rejects boots purchase without deducting gold when speed cap is reached."""
        level = Level(current_floor=1, floor_seed=123)
        level.player.gold = 100
        level.player.stats['speed'] = 8.0 # Already at max cap
        
        success, msg = level.interact_trader(4)
        self.assertFalse(success)
        self.assertEqual(level.player.gold, 100, "Gold must not be deducted when speed cap is already reached")

    def test_r10_chest_animation_ownership(self):
        """Chest.open() owns opened state and sets open_time to current ticks."""
        chest = Chest((100, 100), [])
        self.assertFalse(chest.opened)
        self.assertEqual(chest.open_time, 0)

        now = 123456
        with patch('pygame.time.get_ticks', return_value=now):
            opened = chest.open()
            self.assertTrue(opened)
            self.assertTrue(chest.opened)
            self.assertEqual(chest.open_time, now)

            # Second call returns False
            self.assertFalse(chest.open())

    def test_r12_boss_cleave_damage_angle_cone(self):
        """Boss cleave damages targets in frontal 120-degree cone, but does NOT damage targets behind boss."""
        visible_sprites = pygame.sprite.Group()
        obstacle_sprites = pygame.sprite.Group()
        enemy_sprites = pygame.sprite.Group()

        player = Player((0, 100), [visible_sprites], obstacle_sprites, enemy_sprites)
        player.hitbox.center = (0, 100)
        boss = Enemy((100, 100), [visible_sprites, enemy_sprites], obstacle_sprites, player, 'boss_void_knight', visible_sprites=visible_sprites)
        boss.hitbox.center = (100, 100)
        
        # Boss aims right (1, 0). Player is to the LEFT (0, 100), i.e. 100px behind the boss!
        boss.cleave_dir = pygame.math.Vector2(1, 0)
        boss.boss_attack_state = 'telegraph'
        boss.boss_telegraph_start = 1000
        initial_hp = player.health

        with patch('pygame.time.get_ticks', return_value=2000):
            boss.update()

        self.assertEqual(player.health, initial_hp, "Player behind boss must not take frontal cleave damage")

        # Now place player in front of boss (160, 100), inside cleave cone
        player.hitbox.center = (160, 100)
        boss.boss_attack_state = 'telegraph'
        boss.boss_telegraph_start = 3000
        with patch('pygame.time.get_ticks', return_value=4000):
            boss.update()

        self.assertLess(player.health, initial_hp, "Player in front of boss within cone must take cleave damage")

    def test_r06_world_state_persistence(self):
        """Saving and loading restores destroyed obstacles, killed enemies, and ground gold."""
        level = Level(current_floor=1, floor_seed=456)
        
        # Count initial breakables and enemies
        initial_breakables = [s for s in level.obstacle_sprites if hasattr(s, 'destroy')]
        self.assertGreater(len(initial_breakables), 0)
        target_brk = initial_breakables[0]
        brk_pos = (target_brk.rect.x, target_brk.rect.y)
        
        # Destroy one breakable
        target_brk.destroy()
        
        # Kill one enemy
        initial_enemies = list(level.enemy_sprites)
        self.assertGreater(len(initial_enemies), 0)
        target_enemy = initial_enemies[0]
        target_enemy.kill()

        # Drop 1 gold coin on the floor
        gold_coin = Gold((200, 200), [level.visible_sprites], 15, level.player)
        
        # Save game
        save_game_state(level.current_floor, level.player, level=level)

        # Create game instance and continue saved run
        game = Game()
        game.continue_saved_run()

        # Verify destroyed breakable was not revived
        loaded_breakables = [s for s in game.level.obstacle_sprites if hasattr(s, 'destroy')]
        self.assertFalse(any(b.rect.x == brk_pos[0] and b.rect.y == brk_pos[1] for b in loaded_breakables),
                         "Destroyed crate must remain destroyed upon continue")

        # Verify killed enemy was not revived
        self.assertEqual(len(game.level.enemy_sprites), len(initial_enemies) - 1,
                         "Killed enemy must remain dead upon continue")

        # Verify dropped coin is still on the ground
        loaded_gold = [s for s in game.level.visible_sprites if s.__class__.__name__ == 'Gold']
        self.assertTrue(any(g.rect.centerx == 200 and g.rect.centery == 200 for g in loaded_gold),
                        "Dropped gold coin must persist on the ground upon continue")

    def test_r08_pause_compensation_timers(self):
        """Pausing the game shifts player regen tick and boss burst timer so free energy / instant bursts do not occur."""
        game = Game()
        game.start_new_run()
        p = game.level.player
        p.last_regen_tick = 1000
        
        boss = Enemy((200, 200), [game.level.visible_sprites, game.level.enemy_sprites],
                     game.level.obstacle_sprites, p, 'boss_void_knight', visible_sprites=game.level.visible_sprites)
        boss.boss_burst_time = 2000

        # Simulate 3000ms pause
        game.on_resume(3000)

        self.assertEqual(p.last_regen_tick, 4000, "Player regen tick must be shifted by pause duration")
        self.assertEqual(boss.boss_burst_time, 5000, "Boss burst timer must be shifted by pause duration")

if __name__ == '__main__':
    unittest.main()
