import unittest
import pygame
import os
import sys

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

sys.path.insert(0, os.path.abspath('.'))
from src.settings import TILE_SIZE

class TestDungeonDiversityAndTenMobs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((200, 200))

    def setUp(self):
        self.group = pygame.sprite.Group()

    def test_floor_tile_8_variations_loading(self):
        from src.map_manager import Tile
        for i in range(1, 9):
            sub = f'var{i}'
            t = Tile((0, 0), [self.group], 'floor', biome='dungeon', sub_type=sub)
            self.assertIsNotNone(t.image)
            self.assertEqual(t.image.get_size(), (TILE_SIZE, TILE_SIZE))

            t_crypt = Tile((0, 0), [self.group], 'floor', biome='crypt', sub_type=sub)
            self.assertIsNotNone(t_crypt.image)
            self.assertEqual(t_crypt.image.get_size(), (TILE_SIZE, TILE_SIZE))

    def test_three_interactive_altars(self):
        from src.entities import BloodAltar, WisdomFountain, AnvilShrine, Player

        obs_grp = pygame.sprite.Group()
        player = Player((100, 100), [self.group], obs_grp, pygame.sprite.Group())
        player.health = 100
        player.energy = 20

        class DummyLevel:
            def __init__(self, vis):
                self.visible_sprites = vis

        lvl = DummyLevel(self.group)

        # 1. Blood Altar
        ba = BloodAltar((100, 100), [self.group])
        self.assertEqual(ba.altar_type, 'blood')
        self.assertIn("35 HP", ba.prompt_str)
        self.assertTrue(ba.interact(player, lvl))
        self.assertTrue(ba.used)
        self.assertEqual(player.health, 65)

        # 2. Wisdom Fountain
        wf = WisdomFountain((100, 100), [self.group])
        self.assertEqual(wf.altar_type, 'wisdom')
        self.assertIn("MP", wf.prompt_str)
        self.assertTrue(wf.interact(player, lvl))
        self.assertTrue(wf.used)
        self.assertEqual(player.energy, getattr(player, 'max_energy', 100))

        # 3. Anvil Shrine
        shrine = AnvilShrine((100, 100), [self.group])
        self.assertEqual(shrine.altar_type, 'forge')
        self.assertIn("Заточка", shrine.prompt_str)
        init_bonus = getattr(player, 'sharpness_bonus', 0)
        self.assertTrue(shrine.interact(player, lvl))
        self.assertTrue(shrine.used)
        self.assertEqual(getattr(player, 'sharpness_bonus', 0), init_bonus + 4)

    def test_ten_new_mobs_instantiation_and_hp(self):
        from src.entities import Enemy, Player, ENEMY_HP_CONFIG

        player = Player((50, 50), [self.group], pygame.sprite.Group(), pygame.sprite.Group())
        new_mob_types = [
            'mimic', 'gargoyle', 'mosquito', 'cultist', 'skeleton_brute',
            'spore_creeper', 'banshee', 'lava_hound', 'sarcophagus', 'iron_maiden'
        ]

        for m_type in new_mob_types:
            self.assertIn(m_type, ENEMY_HP_CONFIG)
            e = Enemy((150, 150), [self.group], pygame.sprite.Group(), player, m_type, visible_sprites=self.group)
            self.assertEqual(e.enemy_type, m_type)
            self.assertEqual(e.max_hp, ENEMY_HP_CONFIG[m_type])
            self.assertEqual(e.hp, ENEMY_HP_CONFIG[m_type])
            self.assertIsNotNone(e.image)

    def test_mimic_sleep_and_ambush_activation(self):
        from src.entities import Enemy, Player

        player = Player((50, 50), [self.group], pygame.sprite.Group(), pygame.sprite.Group())
        mimic = Enemy((300, 300), [self.group], pygame.sprite.Group(), player, 'mimic', visible_sprites=self.group)

        # Far away -> stays asleep
        mimic.move_towards_player()
        self.assertFalse(getattr(mimic, 'mimic_awake', False))
        self.assertEqual(mimic.direction.magnitude(), 0.0)

        # Player steps within 60px
        mimic.hitbox.center = (80, 50)
        mimic.rect.center = (80, 50)
        mimic.move_towards_player()
        self.assertTrue(getattr(mimic, 'mimic_awake', False), "Mimic must awaken and ambush when player approaches")
        self.assertEqual(mimic.anim_state, 'attack')

    def test_skeleton_death_shatters_into_bone_debris(self):
        from src.entities import Enemy, Player, DebrisParticle

        vis_group = pygame.sprite.Group()
        player = Player((50, 50), [vis_group], pygame.sprite.Group(), pygame.sprite.Group())
        skel = Enemy((100, 100), [vis_group], pygame.sprite.Group(), player, 'skeleton', visible_sprites=vis_group)

        # Deal fatal damage
        skel.take_damage(999, source='weapon')
        self.assertFalse(skel.alive())

        # Check bone debris spawned in group
        bone_debris = [s for s in vis_group if isinstance(s, DebrisParticle)]
        self.assertGreaterEqual(len(bone_debris), 5, "Skeleton death must shatter into 5-7 bone chunks")

    def test_taboo_preservation_for_zombie_goblin_spore_bomber_necromancer(self):
        from src.entities import Enemy, Player
        player = Player((50, 50), [self.group], pygame.sprite.Group(), pygame.sprite.Group())

        for tab_type in ['zombie', 'goblin', 'spore_bomber', 'necromancer']:
            e = Enemy((100, 100), [self.group], pygame.sprite.Group(), player, tab_type, visible_sprites=self.group)
            self.assertTrue(e.alive())
            self.assertIsNotNone(e.image)

if __name__ == '__main__':
    unittest.main()
