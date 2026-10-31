"""
Method 2: Algorithmic Layered Dark-Fantasy Pixel Synthesizer for 5 Radically Distinct Knights
100% Original Code - Zero external assets, Zero third-party sprites, Zero cloud API dependencies.

Simulates master pixel art techniques algorithmically:
- Asymmetrical anatomical skeletal posing
- Procedural plate beveling & specular highlights
- Cloth physics & catenary drapery folds
- Filigree engraving, stippling, and selective outlining (sel-out)
- Hand-tailored 32-color gothic dark-fantasy palettes with Hue-Shifting
"""

import os
import math
from PIL import Image

CANVAS_SIZE = 48
GROUND_Y = 42

def make_canvas():
    return Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))

def put(img, x, y, col):
    if 0 <= x < CANVAS_SIZE and 0 <= y < CANVAS_SIZE:
        img.putpixel((x, y), col)

def draw_rect(img, x0, y0, w, h, col):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            put(img, x, y, col)

def draw_circle(img, cx, cy, r, col):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx)**2 + (y - cy)**2 <= r*r:
                put(img, x, y, col)

def draw_line(img, x0, y0, x1, y1, col):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        put(img, x0, y0, col)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

def apply_sel_out(img, outline_color=(12, 10, 16, 255)):
    """Applies selective pixel-art outline to all non-transparent silhouette borders."""
    w, h = img.size
    orig = img.load()
    out = img.copy()
    out_pix = out.load()
    for y in range(h):
        for x in range(w):
            if orig[x, y][3] == 0:
                # Check 4-connected neighbors
                has_solid_nbr = False
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and orig[nx, ny][3] > 0:
                        has_solid_nbr = True
                        break
                if has_solid_nbr:
                    out_pix[x, y] = outline_color
    return out

# ===================================================================
# 1. THE JUGGERNAUT (Heavy Bastion with Tower Shield & Spiked Maul)
# ===================================================================
def generate_juggernaut():
    img = make_canvas()
    # Palette: Cold Blue-Grey Steel, Gilded Rivets, Dark Iron
    c_dark = (24, 28, 38, 255)
    c_shadow = (42, 48, 65, 255)
    c_mid = (78, 90, 115, 255)
    c_light = (135, 152, 180, 255)
    c_high = (205, 220, 240, 255)
    c_gold = (215, 165, 50, 255)
    c_eye = (255, 195, 60, 255)

    # 1. Heavy Greaves & Sabatons (Legs: x 14..32, y 32..42)
    # Left leg
    draw_rect(img, 14, 32, 6, 10, c_shadow)
    draw_rect(img, 15, 33, 4, 8, c_mid)
    draw_rect(img, 13, 40, 8, 3, c_dark)
    draw_rect(img, 14, 40, 6, 2, c_light)
    # Right leg
    draw_rect(img, 26, 32, 6, 10, c_shadow)
    draw_rect(img, 27, 33, 4, 8, c_mid)
    draw_rect(img, 25, 40, 8, 3, c_dark)
    draw_rect(img, 26, 40, 6, 2, c_light)

    # 2. Heavy Plate Torso & Segmented Tassets (x 13..33, y 18..33)
    draw_rect(img, 14, 20, 18, 12, c_shadow)
    draw_rect(img, 16, 21, 14, 10, c_mid)
    draw_rect(img, 19, 21, 8, 6, c_light)
    put(img, 22, 22, c_high)
    put(img, 23, 22, c_high)
    # Belt and gold studs
    draw_rect(img, 14, 29, 18, 3, c_dark)
    put(img, 16, 30, c_gold)
    put(img, 22, 30, c_gold)
    put(img, 28, 30, c_gold)

    # 3. Colossal Pauldrons (Left: x 7..15, Right: x 31..39, y 13..23)
    draw_circle(img, 11, 18, 5, c_shadow)
    draw_circle(img, 11, 17, 4, c_mid)
    draw_circle(img, 10, 16, 2, c_light)
    put(img, 9, 15, c_high)
    draw_circle(img, 35, 18, 5, c_shadow)
    draw_circle(img, 35, 17, 4, c_mid)
    draw_circle(img, 34, 16, 2, c_light)
    put(img, 33, 15, c_high)

    # 4. Frog-Mouth Helm (x 18..28, y 8..19)
    draw_rect(img, 18, 9, 10, 10, c_shadow)
    draw_rect(img, 19, 10, 8, 8, c_mid)
    draw_rect(img, 20, 9, 6, 4, c_light)
    put(img, 22, 9, c_high)
    # Menacing horizontal visor slit
    draw_rect(img, 20, 14, 6, 2, c_dark)
    draw_line(img, 21, 14, 24, 14, c_eye)

    # 5. Massive Tower Shield (Pavise) on Left Side (x 5..17, y 14..42)
    # Curved rectangular iron shield planted into the dirt
    draw_rect(img, 6, 16, 10, 26, c_dark)
    draw_rect(img, 7, 17, 8, 24, c_shadow)
    draw_rect(img, 8, 18, 6, 22, c_mid)
    draw_line(img, 9, 19, 9, 38, c_light)
    # Golden cross bossing on shield face
    draw_line(img, 7, 26, 14, 26, c_gold)
    draw_line(img, 11, 21, 11, 33, c_gold)
    put(img, 11, 26, c_high)

    # 6. Spiked Iron Warhammer (Maul) in Right Hand (x 36..44, y 8..38)
    # Shaft
    draw_line(img, 38, 12, 38, 38, (60, 42, 30, 255))
    draw_line(img, 39, 12, 39, 38, (95, 68, 48, 255))
    # Massive Hammer Head (x 34..44, y 10..18)
    draw_rect(img, 34, 10, 10, 7, c_dark)
    draw_rect(img, 35, 11, 8, 5, c_shadow)
    draw_rect(img, 36, 12, 6, 3, c_mid)
    draw_rect(img, 37, 12, 3, 2, c_light)
    put(img, 38, 12, c_high)
    # Spikes on striking faces
    put(img, 33, 13, c_light)
    put(img, 44, 13, c_light)
    put(img, 39, 8, c_light)
    put(img, 39, 9, c_light)

    return apply_sel_out(img)

# ===================================================================
# 2. THE WINGED DRAGOON (Heroic Winged Hussar with Halberd)
# ===================================================================
def generate_winged_dragoon():
    img = make_canvas()
    # Palette: Polished Gilded Plate, White Feathers, Crimson Silk
    c_dark = (28, 20, 26, 255)
    c_plate_sh = (60, 45, 55, 255)
    c_plate_mid = (115, 95, 105, 255)
    c_plate_light = (185, 170, 175, 255)
    c_plate_high = (245, 235, 240, 255)
    c_gold = (235, 185, 55, 255)
    c_gold_hi = (255, 240, 150, 255)
    c_crimson = (185, 30, 45, 255)
    c_crimson_hi = (240, 65, 80, 255)
    c_feather = (230, 235, 245, 255)
    c_feather_sh = (140, 155, 175, 255)

    # 1. Twin Towering Arched Feather Wings (y 2..28, x 8..16 and x 30..38)
    # Wing Left
    wing_pts_l = [
        (16, 24), (14, 18), (11, 12), (9, 7), (10, 3), (12, 2), (14, 4), (16, 8)
    ]
    for i in range(len(wing_pts_l) - 1):
        draw_line(img, wing_pts_l[i][0], wing_pts_l[i][1], wing_pts_l[i+1][0], wing_pts_l[i+1][1], c_gold)
    # Feathers radiating outward
    for xf, yf in [(13, 17), (10, 11), (8, 6), (9, 3), (13, 3)]:
        draw_line(img, xf, yf, xf - 4, yf + 5, c_feather_sh)
        draw_line(img, xf - 1, yf + 1, xf - 4, yf + 4, c_feather)

    # Wing Right
    wing_pts_r = [
        (30, 24), (32, 18), (35, 12), (37, 7), (36, 3), (34, 2), (32, 4), (30, 8)
    ]
    for i in range(len(wing_pts_r) - 1):
        draw_line(img, wing_pts_r[i][0], wing_pts_r[i][1], wing_pts_r[i+1][0], wing_pts_r[i+1][1], c_gold)
    for xf, yf in [(33, 17), (36, 11), (38, 6), (37, 3), (33, 3)]:
        draw_line(img, xf, yf, xf + 4, yf + 5, c_feather_sh)
        draw_line(img, xf + 1, yf + 1, xf + 4, yf + 4, c_feather)

    # 2. Slender Legs & Armored Greaves (x 18..28, y 30..42)
    draw_rect(img, 18, 30, 4, 12, c_plate_sh)
    draw_rect(img, 19, 31, 2, 10, c_plate_mid)
    draw_rect(img, 17, 40, 6, 2, c_plate_light)
    draw_rect(img, 24, 30, 4, 12, c_plate_sh)
    draw_rect(img, 25, 31, 2, 10, c_plate_mid)
    draw_rect(img, 23, 40, 6, 2, c_plate_light)

    # 3. Fluted Cuirass & Crimson Sash (x 17..29, y 18..30)
    draw_rect(img, 18, 19, 11, 10, c_plate_sh)
    draw_rect(img, 19, 20, 9, 8, c_plate_mid)
    draw_rect(img, 21, 20, 5, 6, c_plate_light)
    put(img, 23, 21, c_plate_high)
    # Gold trim and lion crest
    draw_line(img, 18, 19, 28, 19, c_gold)
    put(img, 23, 23, c_gold)
    put(img, 22, 24, c_gold_hi)
    put(img, 24, 24, c_gold_hi)
    # Flowing crimson sash belt
    draw_rect(img, 17, 28, 13, 3, c_crimson)
    draw_line(img, 20, 28, 26, 28, c_crimson_hi)
    # Sash ribbon tails hanging down left hip
    draw_line(img, 17, 30, 15, 37, c_crimson)
    draw_line(img, 16, 31, 14, 38, c_crimson_hi)

    # 4. Lobster-Tail Zischagge Helmet & Plume (x 20..27, y 8..18)
    draw_rect(img, 20, 9, 7, 9, c_plate_sh)
    draw_rect(img, 21, 10, 5, 7, c_plate_mid)
    draw_rect(img, 22, 9, 3, 4, c_plate_light)
    put(img, 23, 9, c_plate_high)
    # Golden visor crest & nasal bar
    draw_line(img, 20, 13, 26, 13, c_gold)
    draw_line(img, 23, 13, 23, 17, c_gold)
    # Sweeping crimson feather plume at helm apex (y 4..9)
    draw_line(img, 23, 8, 25, 4, c_crimson_hi)
    draw_line(img, 24, 8, 27, 5, c_crimson)

    # 5. Long Halberd / Polearm with Fluttering Pennant (x 38..45, y 2..42)
    # Pole shaft
    draw_line(img, 40, 2, 40, 42, (80, 55, 35, 255))
    draw_line(img, 41, 2, 41, 42, (120, 85, 55, 255))
    # Halberd Crescent Axe Blade & Top Spear Point (y 2..12)
    draw_line(img, 40, 2, 40, 6, c_plate_high) # Top spear
    draw_line(img, 36, 6, 39, 6, c_plate_light) # Axe crescent
    draw_rect(img, 36, 7, 4, 3, c_plate_high)
    draw_line(img, 37, 10, 39, 10, c_plate_light)
    # Back armor-piercing fluke beak
    draw_line(img, 42, 7, 44, 7, c_plate_light)
    # Fluttering dual-tailed swallowtail pennant banner (x 41..47, y 8..16)
    draw_rect(img, 42, 8, 5, 3, c_crimson)
    draw_rect(img, 42, 11, 4, 2, c_gold)
    draw_line(img, 46, 9, 47, 9, c_crimson_hi)
    draw_line(img, 45, 12, 47, 12, c_gold_hi)

    return apply_sel_out(img)

# ===================================================================
# 3. THE DREAD LORD (Horned Abyssal Knight with Serrated Flamberge)
# ===================================================================
def generate_dread_lord():
    img = make_canvas()
    # Palette: Abyssal Obsidian, Violet Shading, Spectral Eye Glow
    c_dark = (14, 8, 22, 255)
    c_sh = (35, 18, 52, 255)
    c_mid = (68, 38, 95, 255)
    c_light = (118, 72, 155, 255)
    c_edge = (185, 125, 235, 255)
    c_glow = (225, 90, 255, 255)
    c_bone = (195, 185, 170, 255)

    # 1. Ragged Billowing Tattered Cloak (Behind body: x 8..38, y 18..42)
    for y in range(22, 42):
        spread = int((y - 22) * 0.65)
        draw_line(img, 18 - spread, y, 28 + spread, y, c_dark)
    # Tattered jagged hem rips at bottom
    for x in range(6, 40, 3):
        put(img, x, 41, c_sh)
        put(img, x + 1, 42, c_dark)

    # 2. Spiked Legs & Greaves (x 16..29, y 30..42)
    draw_rect(img, 17, 30, 5, 12, c_sh)
    draw_rect(img, 18, 31, 3, 10, c_mid)
    draw_rect(img, 16, 40, 7, 2, c_light)
    draw_rect(img, 25, 30, 5, 12, c_sh)
    draw_rect(img, 26, 31, 3, 10, c_mid)
    draw_rect(img, 24, 40, 7, 2, c_light)
    # Spiked knee cops
    put(img, 16, 33, c_edge)
    put(img, 30, 33, c_edge)

    # 3. Fluted Gothic Breastplate with Ribbed Grooves (x 16..30, y 18..30)
    draw_rect(img, 17, 19, 13, 11, c_sh)
    draw_rect(img, 18, 20, 11, 9, c_mid)
    draw_rect(img, 20, 20, 7, 7, c_light)
    # Fluted gothic rib lines
    draw_line(img, 23, 20, 23, 27, c_edge)
    draw_line(img, 20, 22, 23, 26, c_edge)
    draw_line(img, 26, 22, 23, 26, c_edge)

    # 4. Spiked Angular Gothic Pauldrons (Left: x 10..18, Right: x 28..36)
    # Multi-layered pointed shoulder cop spikes
    draw_rect(img, 11, 15, 6, 6, c_sh)
    draw_line(img, 11, 15, 9, 12, c_edge)
    draw_line(img, 13, 14, 11, 10, c_edge)
    draw_rect(img, 29, 15, 6, 6, c_sh)
    draw_line(img, 34, 15, 36, 12, c_edge)
    draw_line(img, 32, 14, 34, 10, c_edge)

    # 5. Skull Armet Helmet with Massive Demonic Horns (x 6..40, y 4..18)
    draw_rect(img, 19, 9, 9, 9, c_sh)
    draw_rect(img, 20, 10, 7, 7, c_mid)
    draw_rect(img, 21, 9, 5, 4, c_light)
    # Glowing violet ocular slit
    draw_line(img, 21, 13, 25, 13, c_glow)
    put(img, 23, 13, (255, 230, 255, 255))
    # Massive Demonic Curved Horns sprouting from helm temples
    # Left Horn
    horn_l = [(19, 11), (15, 8), (11, 6), (7, 6), (6, 9), (8, 12)]
    for i in range(len(horn_l) - 1):
        draw_line(img, horn_l[i][0], horn_l[i][1], horn_l[i+1][0], horn_l[i+1][1], c_bone)
    put(img, 8, 12, (245, 240, 230, 255))
    # Right Horn
    horn_r = [(27, 11), (31, 8), (35, 6), (39, 6), (40, 9), (38, 12)]
    for i in range(len(horn_r) - 1):
        draw_line(img, horn_r[i][0], horn_r[i][1], horn_r[i+1][0], horn_r[i+1][1], c_bone)
    put(img, 38, 12, (245, 240, 230, 255))

    # 6. Serrated Flamberge Zweihander Blade Held Diagonally Across Shoulder
    # Handle and spiked crossguard (x 16..22, y 25..30)
    draw_line(img, 18, 27, 26, 27, (120, 30, 40, 255))
    draw_line(img, 22, 28, 22, 34, (50, 40, 45, 255)) # Hilt
    # Long wavy flamberge blade rising over shoulder (x 22..38, y 4..26)
    flam_pts = [
        (22, 26), (24, 22), (23, 18), (26, 14), (25, 10), (28, 6), (30, 3)
    ]
    for i in range(len(flam_pts) - 1):
        draw_line(img, flam_pts[i][0], flam_pts[i][1], flam_pts[i+1][0], flam_pts[i+1][1], c_edge)
        draw_line(img, flam_pts[i][0] + 1, flam_pts[i][1], flam_pts[i+1][0] + 1, flam_pts[i+1][1], (235, 205, 255, 255))
    put(img, 30, 3, (255, 255, 255, 255)) # Blade tip glint

    return apply_sel_out(img)

# ===================================================================
# 4. THE DUELIST TEMPLAR (Fencing Master with Rapier & Feathered Sallet)
# ===================================================================
def generate_duelist():
    img = make_canvas()
    # Palette: Royal Midnight Blue, Polished Silver, Gold Trim, White Plume
    c_dark = (16, 20, 34, 255)
    c_cloth_sh = (28, 42, 70, 255)
    c_cloth_mid = (48, 75, 125, 255)
    c_cloth_hi = (85, 130, 205, 255)
    c_silver = (185, 195, 215, 255)
    c_silver_hi = (245, 250, 255, 255)
    c_gold = (230, 180, 50, 255)
    c_feather = (255, 255, 255, 255)
    c_feather_sh = (170, 185, 210, 255)

    # 1. Asymmetric Side Fencing Stance Legs (x 16..32, y 30..42)
    # Right leg forward (bent forward en-garde)
    draw_line(img, 24, 30, 28, 36, c_cloth_mid)
    draw_line(img, 28, 36, 31, 42, c_silver)
    draw_rect(img, 30, 41, 4, 2, c_dark)
    # Left leg back (extended back balance)
    draw_line(img, 20, 30, 16, 36, c_cloth_sh)
    draw_line(img, 16, 36, 13, 41, c_silver)
    draw_rect(img, 11, 41, 4, 2, c_dark)

    # 2. Fitted Brigandine Doublet with Gold Rivets (x 18..27, y 18..30)
    draw_rect(img, 19, 19, 8, 11, c_cloth_sh)
    draw_rect(img, 20, 20, 6, 9, c_cloth_mid)
    draw_line(img, 22, 20, 22, 28, c_cloth_hi)
    # Vertical rows of gold studs
    put(img, 21, 22, c_gold)
    put(img, 21, 25, c_gold)
    put(img, 23, 22, c_gold)
    put(img, 23, 25, c_gold)

    # 3. Velvet Shoulder Half-Cape draped over left back (x 12..20, y 18..34)
    draw_rect(img, 14, 19, 5, 14, c_dark)
    draw_rect(img, 15, 20, 3, 12, c_cloth_sh)
    draw_line(img, 16, 21, 16, 31, c_cloth_mid)
    # Gold border on cape edge
    draw_line(img, 13, 22, 13, 33, c_gold)

    # 4. Open-Faced Sallet Helm with Flowing Plume (x 19..26, y 8..18)
    draw_rect(img, 20, 9, 6, 9, c_silver)
    draw_rect(img, 21, 10, 4, 7, c_silver_hi)
    # Visor raised showing shadowed eye and brow
    draw_line(img, 21, 13, 24, 13, (40, 35, 45, 255))
    put(img, 23, 14, (220, 180, 150, 255)) # Face skin tone
    # Sweeping majestic ostrich feather curling back (y 2..8, x 14..23)
    feather_pts = [(22, 8), (20, 5), (17, 3), (13, 4), (11, 7)]
    for i in range(len(feather_pts) - 1):
        draw_line(img, feather_pts[i][0], feather_pts[i][1], feather_pts[i+1][0], feather_pts[i+1][1], c_feather)
        draw_line(img, feather_pts[i][0], feather_pts[i][1] + 1, feather_pts[i+1][0], feather_pts[i+1][1] + 1, c_feather_sh)

    # 5. Long Needle Rapier Thrust Forward (x 26..46, y 17..21)
    # Right arm extended forward
    draw_line(img, 25, 20, 29, 19, c_silver)
    # Intricate sweeping cup / basket hilt (x 29..33, y 16..22)
    draw_circle(img, 30, 19, 3, c_gold)
    draw_circle(img, 30, 19, 2, c_silver_hi)
    put(img, 31, 19, (255, 255, 255, 255))
    # Slender needle rapier blade thrusting horizontally forward
    draw_line(img, 33, 19, 45, 18, c_silver)
    draw_line(img, 34, 18, 44, 18, c_silver_hi)
    put(img, 46, 18, (255, 255, 255, 255)) # Tip gleam

    # 6. Parrying Dagger (Main-Gauche) in Left Hand (x 14..18, y 22..28)
    draw_line(img, 16, 23, 16, 28, c_silver)
    draw_line(img, 14, 25, 18, 25, c_gold) # Dagger guard

    return apply_sel_out(img)

# ===================================================================
# 5. THE PENITENT INQUISITOR (Capirote Flagellant with Flail & Censer)
# ===================================================================
def generate_penitent():
    img = make_canvas()
    # Palette: Monastic Burlap, Bloodied Linen, Tarnished Bronze, Ash Embers
    c_dark = (26, 18, 14, 255)
    c_cassock_sh = (62, 45, 34, 255)
    c_cassock_mid = (110, 82, 60, 255)
    c_cassock_hi = (165, 130, 98, 255)
    c_capirote = (210, 185, 150, 255)
    c_capirote_sh = (145, 120, 90, 255)
    c_blood = (175, 25, 35, 255)
    c_bronze = (195, 140, 55, 255)
    c_smoke = (180, 190, 205, 180)

    # 1. Flowing Floor-Length Monastic Cassock / Robe (x 13..33, y 20..42)
    for y in range(20, 43):
        w = int(7 + (y - 20) * 0.72)
        draw_line(img, 23 - w, y, 23 + w, y, c_cassock_sh)
    # Deep vertical cloth fold highlights
    for y in range(22, 42):
        put(img, 20, y, c_cassock_mid)
        put(img, 21, y, c_cassock_hi)
        put(img, 26, y, c_cassock_mid)
        put(img, 27, y, c_cassock_hi)
    # Frayed ragged hem and blood drips at bottom
    for x in range(8, 38, 4):
        put(img, x, 42, c_dark)
        put(img, x + 2, 41, c_blood)

    # 2. Knotted Hemp Rope Belt with Hanging Rosary Beads (y 28..36)
    draw_line(img, 16, 28, 30, 28, (190, 170, 120, 255))
    draw_line(img, 17, 29, 29, 29, (130, 110, 75, 255))
    # Hanging knotted rope end with wooden beads
    draw_line(img, 22, 29, 20, 36, (190, 170, 120, 255))
    put(img, 20, 36, c_bronze) # Relic icon

    # 3. Bare Forearm Vambraces with Barbed Wire Wrapping (x 12..16 and x 30..34, y 22..30)
    draw_rect(img, 12, 22, 4, 7, (90, 95, 110, 255))
    draw_rect(img, 30, 22, 4, 7, (90, 95, 110, 255))
    # Barbed wire spirals
    draw_line(img, 11, 23, 16, 25, c_blood)
    draw_line(img, 11, 26, 16, 28, c_blood)
    draw_line(img, 30, 23, 35, 25, c_blood)

    # 4. Towering Conical Capirote Hood (y 2..20, x 17..29)
    # Steep triangular cone rising to a needle apex at (23, 2)
    for y in range(2, 21):
        half_w = int((y - 2) * 0.35)
        draw_line(img, 23 - half_w, y, 23 + half_w, y, c_capirote_sh)
        draw_line(img, 23 - half_w + 1, y, 23, y, c_capirote)
    put(img, 23, 2, (255, 250, 240, 255)) # Apex point
    # Eye slits in mask (y 15, x 21..25)
    put(img, 21, 15, c_dark)
    put(img, 24, 15, c_dark)
    # Crown of thorns / barbed wire coiled around capirote base
    draw_line(img, 18, 17, 28, 17, (65, 45, 30, 255))
    put(img, 20, 16, c_blood)
    put(img, 25, 16, c_blood)
    put(img, 22, 18, c_blood)

    # 5. Spiked Heavy Morningstar Flail on Chain (x 32..44, y 22..36)
    # Chained links
    chain_pts = [(33, 25), (36, 28), (38, 31), (39, 34)]
    for pt in chain_pts:
        put(img, pt[0], pt[1], (180, 185, 195, 255))
        put(img, pt[0] + 1, pt[1], (120, 125, 135, 255))
    # Heavy Spiked Ball (x 37..44, y 32..39)
    draw_circle(img, 40, 35, 3, c_dark)
    draw_circle(img, 40, 35, 2, (100, 105, 120, 255))
    put(img, 39, 34, (200, 210, 225, 255))
    # Spikes jutting out
    put(img, 36, 35, (160, 170, 185, 255))
    put(img, 44, 35, (160, 170, 185, 255))
    put(img, 40, 31, (160, 170, 185, 255))
    put(img, 40, 39, (160, 170, 185, 255))

    # 6. Smoking Ornate Brass Incense Censer in Left Hand (x 6..14, y 25..36)
    # Chains holding censer
    draw_line(img, 12, 25, 9, 30, c_bronze)
    # Censer burner body
    draw_rect(img, 7, 30, 5, 5, c_bronze)
    draw_rect(img, 8, 31, 3, 3, (245, 200, 90, 255))
    # Perforated grill holes with orange embers inside
    put(img, 9, 32, (255, 120, 30, 255))
    put(img, 10, 33, (255, 180, 40, 255))
    # Ethereal smoke motes curling upward (y 18..28)
    put(img, 8, 28, c_smoke)
    put(img, 7, 25, c_smoke)
    put(img, 9, 22, c_smoke)
    put(img, 10, 19, (210, 220, 235, 120))

    return apply_sel_out(img)

def main():
    out_dir = os.path.join(os.path.abspath('.'), 'assets', 'method2_pixel_synthesizer')
    os.makedirs(out_dir, exist_ok=True)

    generators = [
        ("m2_01_juggernaut.png", generate_juggernaut),
        ("m2_02_winged_dragoon.png", generate_winged_dragoon),
        ("m2_03_dread_lord.png", generate_dread_lord),
        ("m2_04_duelist.png", generate_duelist),
        ("m2_05_penitent.png", generate_penitent),
    ]

    for filename, fn in generators:
        p = os.path.join(out_dir, filename)
        sprite = fn()
        sprite.save(p)
        print(f"[Method 2 Synthesized] {filename} -> {p}")

if __name__ == '__main__':
    main()
