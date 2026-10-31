import os
import sys
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1, 1))

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sprites_dir = os.path.join(base_dir, 'assets', 'sprites')

print("=== ENEMY SPRITE INVENTORY & FRAME AUDIT ===")
keywords = ['slime', 'zombie', 'skeleton', 'goblin', 'imp', 'bat', 'lurker', 'yeti', 'necro', 'boss', 'phantom', 'spore']

sprites = {}
for f in sorted(os.listdir(sprites_dir)):
    if any(k in f.lower() for k in keywords) and f.endswith('.png'):
        path = os.path.join(sprites_dir, f)
        img = pygame.image.load(path)
        base_name = f.rsplit('_', 1)[0] if ('_0' in f or '_1' in f or '_2' in f) else f.replace('.png', '')
        if base_name not in sprites:
            sprites[base_name] = []
        sprites[base_name].append((f, img.get_size(), img.get_width() * img.get_height()))

for name, frames in sprites.items():
    frame_names = [fr[0] for fr in frames]
    sizes = [fr[1] for fr in frames]
    print(f"[{name}] {len(frames)} frames: {frame_names} - Sizes: {set(sizes)}")
