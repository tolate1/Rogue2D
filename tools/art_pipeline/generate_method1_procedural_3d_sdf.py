"""
Method 1: Procedural 3D SDF & Raymarching Sculptor for 5 Radically Distinct Knights
100% Original Mathematical Code - Zero external assets, Zero API tokens.

5 Radically Distinct Archetypes:
1. JUGGERNAUT (Джаггернаут) - Ultra-wide silhouette, frog-mouth helm, massive tower shield (pavise) + brutal warhammer.
2. WINGED DRAGOON (Крылатый гусар) - Tall heroic posture, towering twin feathered wings, long halberd/polearm with fluttering pennant.
3. DREAD LORD (Рогатый лорд скверны) - Wide curving demonic horns, serrated gothic plate, massive flamberge zweihander over shoulder.
4. DUELIST TEMPLAR (Рыцарь-дуэлянт) - Slim side fencing stance, feathered sallet, forward thrusting rapier with basket hilt + parrying dagger.
5. PENITENT INQUISITOR (Кающийся инквизитор) - Tall conical capirote hood (46px apex), flowing floor-length cassock, chained spiked flail + censer.
"""

import os
import math
from PIL import Image

CANVAS_SIZE = 48
GROUND_Y = 42

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def length2(x, y):
    return math.hypot(x, y)

def length3(x, y, z):
    return math.sqrt(x*x + y*y + z*z)

def smin(a, b, k=2.0):
    """Polynomial smooth minimum for fusing 3D anatomical parts without seams."""
    h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1.0 - h) + a * h - k * h * (1.0 - h)

# 3D Primitive Distance Functions
def sd_sphere(p, r):
    return length3(p[0], p[1], p[2]) - r

def sd_ellipsoid(p, r):
    k0 = length3(p[0]/r[0], p[1]/r[1], p[2]/r[2])
    k1 = length3(p[0]/(r[0]*r[0]), p[1]/(r[1]*r[1]), p[2]/(r[2]*r[2]))
    return k0 * (k0 - 1.0) / max(0.0001, k1)

def sd_box(p, b):
    dx = abs(p[0]) - b[0]
    dy = abs(p[1]) - b[1]
    dz = abs(p[2]) - b[2]
    outside = length3(max(dx, 0.0), max(dy, 0.0), max(dz, 0.0))
    inside = min(max(dx, max(dy, dz)), 0.0)
    return outside + inside

def sd_round_box(p, b, r):
    q = (abs(p[0]) - b[0], abs(p[1]) - b[1], abs(p[2]) - b[2])
    outside = length3(max(q[0], 0.0), max(q[1], 0.0), max(q[2], 0.0))
    inside = min(max(q[0], max(q[1], q[2])), 0.0)
    return outside + inside - r

def sd_capsule(p, a, b, r):
    pa = (p[0] - a[0], p[1] - a[1], p[2] - a[2])
    ba = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    h = clamp((pa[0]*ba[0] + pa[1]*ba[1] + pa[2]*ba[2]) / (ba[0]*ba[0] + ba[1]*ba[1] + ba[2]*ba[2]), 0.0, 1.0)
    return length3(pa[0] - ba[0]*h, pa[1] - ba[1]*h, pa[2] - ba[2]*h) - r

def sd_cone(p, h, r):
    """Vertical cone pointing upward, apex at (0, -h, 0), base at (0, 0, 0)."""
    q = length2(p[0], p[2])
    if p[1] < -h or p[1] > 0.0:
        return 10.0
    return q - (r * (p[1] + h) / h)

# -------------------------------------------------------------------
# Archetype 1: JUGGERNAUT (Heavy Bastion)
# -------------------------------------------------------------------
def juggernaut_sdf(p):
    x, y, z = p
    # Heavy squat torso
    d_torso = sd_round_box((x, y - 22, z), (10.0, 8.0, 6.0), 3.0)
    # Frog-mouth helm
    d_head = sd_sphere((x, y - 10, z), 6.5)
    d_visor = sd_box((x, y - 9.5, z - 6.0), (4.5, 0.6, 1.5))
    d_head = max(d_head, -d_visor)
    # Colossal spherical pauldrons
    d_p_left = sd_sphere((x + 14.0, y - 15, z), 7.5)
    d_p_right = sd_sphere((x - 14.0, y - 15, z), 7.5)
    # Heavy trunk legs
    d_leg_l = sd_capsule(p, (-7.0, 28.0, 0.0), (-8.0, 41.0, 0.0), 4.5)
    d_leg_r = sd_capsule(p, (7.0, 28.0, 0.0), (8.0, 41.0, 0.0), 4.5)
    # Giant rectangular Tower Shield (Pavise) on left arm (x: 10..22, y: 14..42)
    d_shield = sd_round_box((x + 14.0, y - 28.0, z - 5.0), (6.0, 14.0, 2.0), 1.0)
    d_shield_boss = sd_sphere((x + 14.0, y - 28.0, z - 7.5), 3.0)
    d_shield = min(d_shield, d_shield_boss)
    # Warhammer on right arm (x: -16, y: 18)
    d_shaft = sd_capsule(p, (-15.0, 8.0, -2.0), (-15.0, 36.0, -2.0), 1.2)
    d_hammer = sd_box((x + 15.0, y - 12.0, z + 2.0), (3.5, 4.0, 5.0))
    d_weapon = min(d_shaft, d_hammer)

    d_body = smin(d_torso, d_head, 2.0)
    d_body = smin(d_body, d_p_left, 1.8)
    d_body = smin(d_body, d_p_right, 1.8)
    d_body = min(d_body, d_leg_l)
    d_body = min(d_body, d_leg_r)
    d_body = min(d_body, d_shield)
    d_body = min(d_body, d_weapon)
    return d_body

# -------------------------------------------------------------------
# Archetype 2: WINGED DRAGOON (Hussar)
# -------------------------------------------------------------------
def winged_dragoon_sdf(p):
    x, y, z = p
    # Tall sleek torso
    d_torso = sd_ellipsoid((x, y - 22, z), (6.5, 9.0, 4.5))
    # Lobster-tail helm with plume
    d_head = sd_sphere((x, y - 9, z), 4.5)
    d_plume = sd_capsule(p, (0.0, 5.0, 2.0), (0.0, 1.0, 6.0), 2.2)
    # Slender legs
    d_leg_l = sd_capsule(p, (-4.5, 29.0, 0.0), (-5.0, 42.0, 0.0), 2.8)
    d_leg_r = sd_capsule(p, (4.5, 29.0, 0.0), (5.0, 42.0, 0.0), 2.8)
    # Twin Arched Wings curving up behind shoulders (y: 2..28, x: +-7..18)
    # Wing ribs approximated via angled capsules
    d_wing_l1 = sd_capsule(p, (-5.0, 20.0, 5.0), (-14.0, 4.0, 4.0), 1.8)
    d_wing_l2 = sd_capsule(p, (-14.0, 4.0, 4.0), (-16.0, 14.0, 5.0), 2.0)
    d_wing_r1 = sd_capsule(p, (5.0, 20.0, 5.0), (14.0, 4.0, 4.0), 1.8)
    d_wing_r2 = sd_capsule(p, (14.0, 4.0, 4.0), (16.0, 14.0, 5.0), 2.0)
    d_wings = min(min(d_wing_l1, d_wing_l2), min(d_wing_r1, d_wing_r2))
    # Long Polearm / Halberd with pennant
    d_pole = sd_capsule(p, (12.0, 2.0, -1.0), (12.0, 42.0, -1.0), 0.9)
    d_blade = sd_box((x - 12.0, y - 6.0, z + 1.0), (3.0, 4.0, 0.4))
    d_pennant = sd_box((x - 15.0, y - 12.0, z + 1.0), (3.0, 2.0, 0.3))

    d_body = smin(d_torso, d_head, 2.0)
    d_body = min(d_body, d_plume)
    d_body = min(d_body, d_leg_l)
    d_body = min(d_body, d_leg_r)
    d_body = min(d_body, d_wings)
    d_body = min(d_body, d_pole)
    d_body = min(d_body, d_blade)
    d_body = min(d_body, d_pennant)
    return d_body

# -------------------------------------------------------------------
# Archetype 3: DREAD LORD (Horned Abyssal Knight)
# -------------------------------------------------------------------
def dread_lord_sdf(p):
    x, y, z = p
    # Heavy athletic torso
    d_torso = sd_round_box((x, y - 21, z), (7.5, 8.5, 5.0), 2.0)
    # Menacing horned helmet
    d_head = sd_sphere((x, y - 9, z), 5.0)
    # Sweeping curved demonic horns (span 34px)
    d_horn_l1 = sd_capsule(p, (-4.0, 10.0, 0.0), (-12.0, 5.0, -1.0), 1.6)
    d_horn_l2 = sd_capsule(p, (-12.0, 5.0, -1.0), (-16.0, 8.0, 1.0), 1.0)
    d_horn_r1 = sd_capsule(p, (4.0, 10.0, 0.0), (12.0, 5.0, -1.0), 1.6)
    d_horn_r2 = sd_capsule(p, (12.0, 5.0, -1.0), (16.0, 8.0, 1.0), 1.0)
    d_horns = min(min(d_horn_l1, d_horn_l2), min(d_horn_r1, d_horn_r2))
    # Spiked gothic pauldrons
    d_p_l = sd_box((x + 11.0, y - 14.0, z), (3.5, 3.5, 4.0))
    d_p_r = sd_box((x - 11.0, y - 14.0, z), (3.5, 3.5, 4.0))
    # Serrated Zweihander held diagonally across shoulder
    d_blade = sd_box((x - (20.0 - y * 0.4), y - 16.0, z + 2.0), (1.5, 14.0, 0.5))
    d_cross = sd_box((x + 7.0, y - 27.0, z + 2.0), (5.0, 1.0, 1.0))
    # Tattered cape
    d_cape = sd_box((x, y - 28.0, z + 5.0), (8.5, 12.0, 0.8))
    # Legs
    d_leg_l = sd_capsule(p, (-5.0, 28.0, 0.0), (-6.0, 42.0, 0.0), 3.2)
    d_leg_r = sd_capsule(p, (5.0, 28.0, 0.0), (6.0, 42.0, 0.0), 3.2)

    d_body = smin(d_torso, d_head, 2.0)
    d_body = min(d_body, d_horns)
    d_body = min(d_body, d_p_l)
    d_body = min(d_body, d_p_r)
    d_body = min(d_body, d_blade)
    d_body = min(d_body, d_cross)
    d_body = min(d_body, d_cape)
    d_body = min(d_body, d_leg_l)
    d_body = min(d_body, d_leg_r)
    return d_body

# -------------------------------------------------------------------
# Archetype 4: DUELIST TEMPLAR (Fencer Knight)
# -------------------------------------------------------------------
def duelist_sdf(p):
    x, y, z = p
    # Slender side fencing profile (angled torso)
    d_torso = sd_ellipsoid((x + 1.0, y - 21, z), (4.5, 8.5, 4.5))
    # Feathered sallet
    d_head = sd_sphere((x, y - 8, z), 4.2)
    d_feather = sd_capsule(p, (-1.0, 7.0, 1.0), (-8.0, 2.0, 2.0), 1.5)
    # Side stance legs (one forward, one bent back)
    d_leg_front = sd_capsule(p, (3.0, 28.0, -1.0), (6.0, 42.0, -2.0), 2.2)
    d_leg_back = sd_capsule(p, (-4.0, 28.0, 2.0), (-8.0, 41.0, 3.0), 2.2)
    # Thrusting Rapier pointing forward (x: 6..24, y: 19..20)
    d_rapier = sd_capsule(p, (7.0, 20.0, -4.0), (22.0, 17.0, -4.0), 0.6)
    d_basket = sd_sphere((x - 7.0, y - 20.0, z + 4.0), 2.8)
    # Half-cape over left shoulder
    d_halfcape = sd_box((x + 5.0, y - 22.0, z + 3.0), (3.0, 8.0, 1.5))

    d_body = smin(d_torso, d_head, 1.8)
    d_body = min(d_body, d_feather)
    d_body = min(d_body, d_leg_front)
    d_body = min(d_body, d_leg_back)
    d_body = min(d_body, d_rapier)
    d_body = min(d_body, d_basket)
    d_body = min(d_body, d_halfcape)
    return d_body

# -------------------------------------------------------------------
# Archetype 5: PENITENT INQUISITOR (Capirote Flagellant)
# -------------------------------------------------------------------
def penitent_sdf(p):
    x, y, z = p
    # Extremely tall cone capirote helmet (y: 2..16)
    d_cone = sd_cone((x, y - 16.0, z), 14.0, 5.0)
    # Monastic body & flowing floor-length cassock skirt (y: 16..42)
    d_torso = sd_ellipsoid((x, y - 22.0, z), (6.0, 7.0, 4.5))
    d_skirt = sd_cone((x, y - 42.0, z), 20.0, 11.0)
    # Heavy chained spiked flail on right arm
    d_chain = sd_capsule(p, (-10.0, 22.0, -2.0), (-16.0, 30.0, -2.0), 0.8)
    d_ball = sd_sphere((x + 16.0, y - 32.0, z + 2.0), 3.8)
    # Incense Censer in left hand
    d_censer = sd_cylinder = sd_box((x - 12.0, y - 28.0, z - 2.0), (2.0, 3.5, 2.0))

    d_body = min(d_cone, d_torso)
    d_body = smin(d_body, d_skirt, 2.0)
    d_body = min(d_body, d_chain)
    d_body = min(d_body, d_ball)
    d_body = min(d_body, d_censer)
    return d_body

# -------------------------------------------------------------------
# 3D Raymarching & Shading Pipeline
# -------------------------------------------------------------------
def compute_normal(sdf_func, p, eps=0.3):
    dx = sdf_func((p[0] + eps, p[1], p[2])) - sdf_func((p[0] - eps, p[1], p[2]))
    dy = sdf_func((p[0], p[1] + eps, p[2])) - sdf_func((p[0], p[1] - eps, p[2]))
    dz = sdf_func((p[0], p[1], p[2] + eps)) - sdf_func((p[0], p[1], p[2] - eps))
    mag = length3(dx, dy, dz)
    if mag == 0:
        return (0.0, 0.0, 1.0)
    return (dx / mag, dy / mag, dz / mag)

def render_sdf_knight(sdf_func, color_ramp, outline_color=(15, 12, 22)):
    """Renders a 48x48 pixel art sprite by raymarching the 3D SDF."""
    img = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    pixels = img.load()
    z_buffer = [[999.0 for _ in range(CANVAS_SIZE)] for _ in range(CANVAS_SIZE)]
    hit_mask = [[False for _ in range(CANVAS_SIZE)] for _ in range(CANVAS_SIZE)]
    shading_map = [[0.0 for _ in range(CANVAS_SIZE)] for _ in range(CANVAS_SIZE)]

    # Directional Key Light (from top-left, slightly forward)
    lx, ly, lz = -0.45, -0.65, 0.62
    l_mag = length3(lx, ly, lz)
    lx, ly, lz = lx / l_mag, ly / l_mag, lz / l_mag

    # Raymarch orthogonal parallel rays along Z
    for py in range(CANVAS_SIZE):
        for px in range(CANVAS_SIZE):
            wx = px - 24.0
            wy = py
            # Raymarch z from -20 to +20
            t = -20.0
            hit = False
            hit_z = 0.0
            for _ in range(28):
                p = (wx, wy, t)
                d = sdf_func(p)
                if d < 0.25:
                    hit = True
                    hit_z = t
                    break
                t += max(0.4, d * 0.75)
                if t > 20.0:
                    break

            if hit:
                z_buffer[py][px] = hit_z
                hit_mask[py][px] = True
                nx, ny, nz = compute_normal(sdf_func, (wx, wy, hit_z))
                # Diffuse term (N . L)
                diff = max(0.0, -(nx * lx + ny * ly + nz * lz))
                # Ambient + Rim light
                rim = max(0.0, 1.0 - abs(nz)) * 0.25
                shading = clamp(0.18 + diff * 0.72 + rim, 0.0, 1.0)
                shading_map[py][px] = shading

    # Apply Palette Ramping and Selective Outlining (Sel-out)
    for py in range(CANVAS_SIZE):
        for px in range(CANVAS_SIZE):
            if hit_mask[py][px]:
                val = shading_map[py][px]
                # Map to color ramp (ramp has [shadow, midtone, highlight, specular])
                n_colors = len(color_ramp)
                c_idx = int(val * (n_colors - 1))
                c_idx = clamp(c_idx, 0, n_colors - 1)
                pixels[px, py] = color_ramp[c_idx]

    # Edge detection for crisp pixel art outline
    outline_img = img.copy()
    out_pixels = outline_img.load()
    for py in range(1, CANVAS_SIZE - 1):
        for px in range(1, CANVAS_SIZE - 1):
            if not hit_mask[py][px]:
                # Check 4-connected neighbors
                if (hit_mask[py-1][px] or hit_mask[py+1][px] or 
                    hit_mask[py][px-1] or hit_mask[py][px+1]):
                    out_pixels[px, py] = outline_color

    return outline_img

def main():
    out_dir = os.path.join(os.path.abspath('.'), 'assets', 'method1_procedural_sdf')
    os.makedirs(out_dir, exist_ok=True)

    # 5 Completely Distinct Dark Fantasy Palette Ramps
    # 1. Juggernaut: Cold heavy forged steel & iron
    ramp_juggernaut = [
        (22, 24, 34, 255),
        (48, 54, 72, 255),
        (85, 98, 122, 255),
        (138, 154, 180, 255),
        (205, 218, 235, 255)
    ]
    # 2. Winged Dragoon: Gilded Brass, Crimson Sash & White Feathers
    ramp_dragoon = [
        (38, 22, 18, 255),
        (92, 45, 32, 255),
        (168, 110, 45, 255),
        (225, 175, 75, 255),
        (255, 235, 160, 255)
    ]
    # 3. Dread Lord: Abyssal Obsidian, Violet Shadows & Void Glow
    ramp_dread = [
        (16, 10, 26, 255),
        (42, 24, 60, 255),
        (75, 45, 95, 255),
        (135, 70, 160, 255),
        (210, 120, 245, 255)
    ]
    # 4. Duelist: Silver Filigree, Royal Indigo & Golden Rapier
    ramp_duelist = [
        (18, 20, 42, 255),
        (36, 48, 85, 255),
        (65, 95, 145, 255),
        (130, 170, 215, 255),
        (215, 235, 255, 255)
    ]
    # 5. Penitent: Monastic Sandstone, Blood-stained Capirote & Tarnished Bronze
    ramp_penitent = [
        (42, 28, 20, 255),
        (88, 56, 38, 255),
        (145, 102, 68, 255),
        (198, 155, 110, 255),
        (240, 215, 175, 255)
    ]

    configs = [
        ("m1_01_juggernaut.png", juggernaut_sdf, ramp_juggernaut),
        ("m1_02_winged_dragoon.png", winged_dragoon_sdf, ramp_dragoon),
        ("m1_03_dread_lord.png", dread_lord_sdf, ramp_dread),
        ("m1_04_duelist.png", duelist_sdf, ramp_duelist),
        ("m1_05_penitent.png", penitent_sdf, ramp_penitent)
    ]

    for filename, sdf_fn, ramp in configs:
        p = os.path.join(out_dir, filename)
        sprite = render_sdf_knight(sdf_fn, ramp)
        sprite.save(p)
        print(f"[Method 1 Generated] {filename} -> {p}")

if __name__ == '__main__':
    main()
