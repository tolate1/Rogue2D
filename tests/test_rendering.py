import unittest
import pygame
from unittest.mock import MagicMock

# Define simple mocks effectively behaving like Sprites
class MockSprite(pygame.sprite.Sprite):
    def __init__(self, rect_y, sprite_type='other'):
        super().__init__()
        self.rect = MagicMock()
        self.rect.centery = rect_y
        self.rect.colliderect.return_value = True # Always visible for test
        self.image = MagicMock()
        self.sprite_type = sprite_type
        # If sprite_type is 'other' (mimicking Entity), we might delete the attr to test getattr default
        if sprite_type == 'missing':
            del self.sprite_type

class TestRenderingOrder(unittest.TestCase):
    def test_sort_key_logic(self):
        # Setup Sprites
        # Floor (Y=100)
        floor_a = MockSprite(100, 'floor')
        floor_a.name = 'Floor A'
        
        # Enemy (Y=50) - Should be drawn AFTER Floor A despite lower Y
        enemy_b = MockSprite(50, 'missing') 
        enemy_b.name = 'Enemy B'
        
        # Floor (Y=200)
        floor_c = MockSprite(200, 'floor')
        floor_c.name = 'Floor C'
        
        # Enemy (Y=300)
        enemy_d = MockSprite(300, 'missing')
        enemy_d.name = 'Enemy D'
        
        sprites = [floor_a, enemy_b, floor_c, enemy_d]
        
        # The sort key used in the code:
        # key = lambda sprite: (0 if getattr(sprite, 'sprite_type', 'other') == 'floor' else 1, sprite.rect.centery)
        
        sort_key = lambda sprite: (0 if getattr(sprite, 'sprite_type', 'other') == 'floor' else 1, sprite.rect.centery)
        
        sorted_sprites = sorted(sprites, key=sort_key)
        
        print("\nOriginal Order: " + ", ".join([s.name for s in sprites]))
        print("Sorted Order:   " + ", ".join([s.name for s in sorted_sprites]))
        
        # Expected: floors first (sorted by Y), then others (sorted by Y)
        # Floors: A(100), C(200)
        # Others: B(50), D(300)
        # Result: A, C, B, D
        
        self.assertEqual(sorted_sprites[0], floor_a, "1st should be Floor A")
        self.assertEqual(sorted_sprites[1], floor_c, "2nd should be Floor C")
        self.assertEqual(sorted_sprites[2], enemy_b, "3rd should be Enemy B")
        self.assertEqual(sorted_sprites[3], enemy_d, "4th should be Enemy D")

if __name__ == '__main__':
    unittest.main()
