import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pygame
from PIL import Image, ImageDraw, ImageFont

# Headless setup
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
pygame.init()
screen = pygame.display.set_mode((1280, 720))

from src.map_manager import Level
from src.entities import Player
from src.ui import UI

OUT_DIR = "Critic/visual critic"
os.makedirs(OUT_DIR, exist_ok=True)

def generate_acceptance_pack():
    print("=== Generating Pilot Knight Acceptance Pack ===")
    
    # 1. Level in dungeon biome (floor 1)
    lvl = Level(current_floor=1, floor_seed=777)
    lvl.create_map()
    player = lvl.player
    player.set_skin('knight')
    
    # 2. Capture 6 attack frames in game room
    in_game_frames = []
    for i in range(6):
        player.attack()
        player.attack_time = pygame.time.get_ticks() - int((i / 6.0) * 240)
        player.animate()
        lvl.visible_sprites.update()
        
        screen.fill((12, 10, 16))
        lvl.draw()
        
        raw_bytes = pygame.image.tostring(screen, 'RGBA')
        im = Image.frombytes('RGBA', (1280, 720), raw_bytes)
        
        # Center crop around player
        cx, cy = 640, 360
        crop = im.crop((cx - 160, cy - 140, cx + 160, cy + 140))
        in_game_frames.append(crop)
        
    gif_path = os.path.join(OUT_DIR, "pilot_knight_in_game_attack.gif")
    in_game_frames[0].save(gif_path, save_all=True, append_images=in_game_frames[1:], duration=90, loop=0)
    print(f"[1/4] In-Game Attack GIF: {gif_path}")
    
    # 3. Capture 4 directional attacks (Right, Left, Up, Down)
    dir_crops = []
    directions = [
        ('Right (Восток)', pygame.math.Vector2(1, 0), False),
        ('Left (Запад)', pygame.math.Vector2(-1, 0), True),
        ('Down (Юг)', pygame.math.Vector2(0, 1), False),
        ('Up (Север)', pygame.math.Vector2(0, -1), False)
    ]
    
    for label, dir_vec, flip_left in directions:
        player.direction = dir_vec
        player.facing_left = flip_left
        player.attack()
        player.attack_time = pygame.time.get_ticks() - 120 # Frame 3 (contact)
        player.animate()
        lvl.visible_sprites.update()
        
        screen.fill((12, 10, 16))
        lvl.draw()
        
        raw_bytes = pygame.image.tostring(screen, 'RGBA')
        im = Image.frombytes('RGBA', (1280, 720), raw_bytes)
        crop = im.crop((640 - 100, 360 - 100, 640 + 100, 360 + 100))
        dir_crops.append((label, crop))
        
    # Assemble Directional Board
    board_w = 4 * 220 + 40
    board_h = 280
    dir_board = Image.new('RGB', (board_w, board_h), (16, 18, 24))
    draw = ImageDraw.Draw(dir_board)
    try:
        font_title = ImageFont.truetype('arialbd.ttf', 16)
        font_lbl = ImageFont.truetype('arial.ttf', 13)
    except Exception:
        font_title = font_lbl = ImageFont.load_default()
        
    draw.text((20, 12), "PILOT KNIGHT: КОНТРОЛЬ АТАКИ В 4 НАПРАВЛЕНИЯХ (ФАЗА КОНТАКТА)", fill=(245, 220, 70), font=font_title)
    
    for idx, (lbl, crop_im) in enumerate(dir_crops):
        bx = 20 + idx * 220
        by = 45
        draw.rectangle([(bx, by), (bx + 200, by + 200)], fill=(10, 12, 16), outline=(45, 52, 68))
        dir_board.paste(crop_im, (bx, by))
        draw.text((bx + 10, by + 210), lbl, fill=(200, 215, 235), font=font_lbl)
        
    dir_path = os.path.join(OUT_DIR, "pilot_knight_4_directions_combat.png")
    dir_board.save(dir_path)
    print(f"[2/4] Directional Combat Board: {dir_path}")
    
    # 4. Raw Sprite vs Scaled 3x Side-by-Side Strip
    sprites_dir = "assets/sprites"
    filmstrip_w = 6 * 192 + 50
    filmstrip_h = 240 + 80
    filmstrip = Image.new('RGB', (filmstrip_w, filmstrip_h), (14, 16, 22))
    f_draw = ImageDraw.Draw(filmstrip)
    f_draw.text((20, 12), "PILOT KNIGHT: ПОКАДРОВАЯ АТАКА (1x64x80 и 3x УВЕЛИЧЕНИЕ, БЕЗ ОБРЕЗКИ И ТЕНЕВЫХ ПАРАЗИТОВ)", fill=(245, 220, 70), font=font_title)
    
    for i in range(6):
        p_frame = os.path.join(sprites_dir, f"player_knight_attack_{i}.png")
        if os.path.exists(p_frame):
            f_im = Image.open(p_frame)
            fx = 20 + i * (192 + 8)
            fy = 45
            f_draw.rectangle([(fx, fy), (fx + 192, fy + 240)], fill=(8, 10, 14), outline=(40, 48, 64))
            f_3x = f_im.resize((192, 240), Image.NEAREST)
            filmstrip.paste(f_3x, (fx, fy), f_3x)
            f_draw.text((fx + 10, fy + 245), f"Кадр {i+1}/6 (t={i*40}ms)", fill=(180, 195, 220), font=font_lbl)
            
    filmstrip_path = os.path.join(OUT_DIR, "pilot_knight_lossless_filmstrip_3x.png")
    filmstrip.save(filmstrip_path)
    print(f"[3/4] Lossless Filmstrip 3x: {filmstrip_path}")
    
    print("=== Acceptance Pack Generated Successfully ===")

if __name__ == '__main__':
    generate_acceptance_pack()
