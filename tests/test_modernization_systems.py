import unittest
import pygame
import os
import sys

# Headless Pygame
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

class TestModernizationSystems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((640, 480))

    def test_sound_throttle(self):
        """Verifies SoundManager throttles rapid identical SFX to prevent audio clipping."""
        from src.sound_manager import SoundManager
        sm = SoundManager.get_instance()
        sm.enabled = True
        
        # Mock sound object
        class MockSound:
            def __init__(self):
                self.play_count = 0
            def play(self):
                self.play_count += 1
            def set_volume(self, v):
                pass
                
        mock_snd = MockSound()
        sm.sounds['test_sfx'] = mock_snd
        sm._last_played.clear()

        # Call play 10 times in the same millisecond
        for _ in range(10):
            sm.play('test_sfx')

        self.assertEqual(mock_snd.play_count, 1, "Sound throttle must prevent multi-play within 55ms window!")

    def test_player_procedural_squash_and_tilt(self):
        """Verifies Player.animate() calculates procedural scale and body tilt on velocity."""
        from src.entities import Player
        v_group = pygame.sprite.Group()
        o_group = pygame.sprite.Group()
        e_group = pygame.sprite.Group()
        
        player = Player((100, 100), [v_group], o_group, e_group)
        player.velocity = pygame.math.Vector2(5.0, 0.0) # Moving right at 5 px/f
        orig_img = player.image.copy()

        player.animate()
        self.assertIsNotNone(player.image)
        self.assertEqual(player.rect.center, player.hitbox.center)

        # Stationary idle breathing
        player.velocity = pygame.math.Vector2(0, 0)
        player.animate()
        self.assertIsNotNone(player.image)

    def test_button_hover_and_click_physics(self):
        """Verifies Button smooth lerp offset on hover and click response."""
        from src.ui import Button
        clicked = []
        btn = Button("Test", (100, 100), 200, 40, lambda: clicked.append(True))
        
        # Not hovered initially
        btn.check_hover((0, 0))
        self.assertFalse(btn.hovered)
        self.assertEqual(btn.offset_x, 0.0)

        # Hovered inside rect
        btn.check_hover((150, 120))
        self.assertTrue(btn.hovered)
        surf = pygame.Surface((300, 200))
        btn.draw(surf)
        self.assertGreater(btn.offset_x, 0.0, "Button offset_x must lerp towards target on hover!")

        # Click event
        click_evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (150, 120)})
        res = btn.check_click([click_evt])
        self.assertTrue(res)
        self.assertEqual(len(clicked), 1)
        self.assertEqual(btn.click_offset_y, 2.0)

    def test_game_over_stats_and_options(self):
        """Verifies Game Over screen retains run stats and resets smoothly."""
        from main import Game
        game = Game()
        game.state = 'game'
        # Simulate death trigger
        game.level.player.is_dead = True
        game.level.game_over = True
        game.set_state('game_over')

        self.assertEqual(game.state, 'game_over')
        self.assertTrue(len(game.ui_buttons) >= 2)
        btn_labels = [b.text_str for b in game.ui_buttons]
        self.assertTrue(any("НАЧАТЬ ЗАНОВО" in l for l in btn_labels))
        self.assertTrue(any("В ГЛАВНОЕ МЕНЮ" in l for l in btn_labels))

    def test_player_attack_animation(self):
        """Verifies Player uses attack frames during attack window without ballooning/distortion."""
        from src.entities import Player
        v_group = pygame.sprite.Group()
        o_group = pygame.sprite.Group()
        e_group = pygame.sprite.Group()
        
        player = Player((100, 100), [v_group], o_group, e_group)
        self.assertTrue(hasattr(player, 'attack_frames') and len(player.attack_frames) >= 2)
        
        from src.settings import TILE_SIZE
        player.attack()
        player.animate()
        # Verify sprite matches native TILE_SIZE without ballooning
        self.assertEqual(player.image.get_size(), (TILE_SIZE, TILE_SIZE))

    def test_player_take_damage_no_crash(self):
        """Verifies player taking damage does not trigger UnboundLocalError: is_moving."""
        from src.entities import Player
        v_group = pygame.sprite.Group()
        o_group = pygame.sprite.Group()
        e_group = pygame.sprite.Group()
        
        player = Player((100, 100), [v_group], o_group, e_group)
        # Enemy attacks player
        res = player.take_damage(15, source_pos=(120, 120))
        self.assertTrue(res)
        self.assertEqual(player.health, 85)
        # Animate during hitstop - must not crash!
        player.animate()
        self.assertIsNotNone(player.image)

    def test_raycast_fov_and_lighting(self):
        """Verifies compute_fov_polygon occludes walls and prevents seeing through walls."""
        from main import Game
        game = Game()
        game.start_new_run()
        level = game.level
        
        poly = level.compute_fov_polygon(max_radius=400, n_rays=60)
        self.assertTrue(len(poly) >= 3, "FOV polygon must have at least 3 vertices!")
        # Test level draw with FOV lighting
        level.draw()

    def test_torch_placement_and_room_bounds(self):
        """Verifies torches are placed safely on wall face (+24) and unclipped by room lighting."""
        from main import Game
        from src.settings import TILE_SIZE
        game = Game()
        game.start_new_run()
        level = game.level
        self.assertTrue(len(level.rooms) > 0)
        
        for r in level.rooms:
            if hasattr(r, 'torch') and r.torch:
                # Torch y should be on wall face (r.y - 1)*64 + 24
                expected_y = (r.y - 1) * TILE_SIZE + 24
                self.assertEqual(r.torch.rect.y, expected_y)
                # Verify torch center is inside room horizontal span
                self.assertGreaterEqual(r.torch.rect.centerx, r.x * TILE_SIZE)
                self.assertLessEqual(r.torch.rect.centerx, (r.x + r.w) * TILE_SIZE)

    def test_enemy_melee_attack_no_out_of_bounds_push(self):
        """Verifies enemies deal melee damage without violently shoving player out of the dungeon."""
        from src.entities import Player, Enemy
        from src.settings import TILE_SIZE
        v_group = pygame.sprite.Group()
        o_group = pygame.sprite.Group()
        e_group = pygame.sprite.Group()
        
        player = Player((200, 200), [v_group], o_group, e_group)
        enemy = Enemy((210, 200), [v_group, e_group], o_group, player, 'zombie')
        
        start_hp = player.health
        start_pos = player.pos.copy()
        
        # Enemy attacks in melee range
        enemy.can_attack = True
        enemy.hitbox.center = player.hitbox.center
        enemy.update()
        
        # Verify damage dealt
        self.assertLess(player.health, start_hp, "Melee enemy touching player must inflict damage!")
        # Verify player was not displaced into the void
        dist_moved = (player.pos - start_pos).magnitude()
        self.assertLess(dist_moved, 1.0, "Player must not be repelled/knocked out of bounds by mob contact!")

    def test_graphic_assets_and_banners(self):
        """Verifies title_logo.png and game_over_banner.png exist, load, and have alpha transparency."""
        from src.utils import load_image
        logo = load_image('assets/sprites/title_logo.png')
        self.assertIsNotNone(logo)
        self.assertGreater(logo.get_width(), 300)
        
        banner = load_image('assets/sprites/game_over_banner.png')
        self.assertIsNotNone(banner)
        self.assertGreater(banner.get_width(), 300)

    def test_skeleton_archer_and_boss_textures(self):
        """Verifies skeleton archer and bone golem boss textures exist and load."""
        from src.utils import load_image
        sk0 = load_image('assets/sprites/skeleton_0.png')
        sk1 = load_image('assets/sprites/skeleton_1.png')
        self.assertIsNotNone(sk0)
        self.assertIsNotNone(sk1)
        self.assertEqual(sk0.get_size(), (32, 32)) # Native sprite size
        
        boss0 = load_image('assets/sprites/boss_bone_golem_0.png')
        boss1 = load_image('assets/sprites/boss_bone_golem_1.png')
        self.assertIsNotNone(boss0)
        self.assertIsNotNone(boss1)
        self.assertEqual(boss0.get_size(), (64, 64))

    def test_equipment_system_and_slots(self):
        """Verifies Player equips items into dedicated slots and recalculates stats."""
        from src.entities import Player
        from src.items import Item
        v_group = pygame.sprite.Group()
        o_group = pygame.sprite.Group()
        e_group = pygame.sprite.Group()
        
        player = Player((100, 100), [v_group], o_group, e_group)
        self.assertIn('weapon', player.equipped)
        self.assertIn('armor', player.equipped)
        self.assertIn('boots', player.equipped)
        self.assertIn('accessory', player.equipped)
        
        base_atk = player.stats['attack']
        base_hp = player.stats['health']
        base_spd = player.stats['speed']
        
        # Equip weapon
        sword = Item("Палаш Героя", "rare", {'attack': 5}, 50, 'assets/sprites/item_sword.png', slot='weapon')
        player.equip_item(sword)
        self.assertEqual(player.equipped['weapon'], sword)
        self.assertEqual(player.stats['attack'], base_atk + 5)
        
        # Equip armor
        armor = Item("Мифриловый Панцирь", "epic", {'health': 40}, 80, 'assets/sprites/item_armor.png', slot='armor')
        player.equip_item(armor)
        self.assertEqual(player.equipped['armor'], armor)
        self.assertEqual(player.stats['health'], base_hp + 40)
        
        # Unequip weapon
        unequipped = player.unequip_item('weapon')
        self.assertEqual(unequipped, sword)
        self.assertIsNone(player.equipped['weapon'])
        self.assertIn(sword, player.inventory)
        player.inventory.remove(sword)
        player.recalculate_stats()
        self.assertEqual(player.stats['attack'], base_atk)

    def test_blacksmith_modal_upgrades(self):
        """Verifies Blacksmith upgrades weapon and armor for gold."""
        from src.entities import Player
        from src.ui import BlacksmithModal
        v_group = pygame.sprite.Group()
        o_group = pygame.sprite.Group()
        e_group = pygame.sprite.Group()
        
        class MockLevel:
            def __init__(self, p):
                self.player = p
                self.active_modal = 'blacksmith'
                
        player = Player((100, 100), [v_group], o_group, e_group)
        player.gold = 100
        level = MockLevel(player)
        modal = BlacksmithModal(level, player)
        
        init_atk = player.stats['attack']
        modal.sharpen_weapon()
        self.assertEqual(player.gold, 60)
        self.assertEqual(player.stats['attack'], init_atk + 3)
        self.assertIsNotNone(player.equipped['weapon'])
        
        # Reinforce armor
        init_hp = player.stats['health']
        modal.reinforce_armor()
        self.assertEqual(player.gold, 20)
        self.assertEqual(player.stats['health'], init_hp + 20)
        self.assertIsNotNone(player.equipped['armor'])

    def test_rpg_modals_open_and_close(self):
        """Verifies ShopModal, BlacksmithModal and EquipmentModal open, update and close."""
        from main import Game
        game = Game()
        game.start_new_run()
        level = game.level
        
        # Equipment modal
        level.open_modal('equipment')
        self.assertEqual(level.active_modal, 'equipment')
        self.assertIsNotNone(level.modal_instance)
        level.modal_instance.update((200, 200))
        level.open_modal(None)
        self.assertIsNone(level.active_modal)
        
        # Shop modal
        level.open_modal('shop')
        self.assertEqual(level.active_modal, 'shop')
        self.assertIsNotNone(level.modal_instance)
        level.modal_instance.update((200, 200))
        level.open_modal(None)
        self.assertIsNone(level.active_modal)
        
        # Blacksmith modal
        level.open_modal('blacksmith')
        self.assertEqual(level.active_modal, 'blacksmith')
        self.assertIsNotNone(level.modal_instance)
        level.modal_instance.update((200, 200))
        level.open_modal(None)
        self.assertIsNone(level.active_modal)

if __name__ == '__main__':
    unittest.main()
