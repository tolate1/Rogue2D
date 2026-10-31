"""
Rogue2D Original Procedural Knight Sculptor & SDF Raymarched 2.5D Renderer
Generates 100% original, handcrafted-quality Dark Fantasy Knight models
using Signed Distance Fields (SDF), polynomial smooth blending (smin),
curved anatomical volumes, 3D surface normals, hue-shifted color ramps,
and sub-pixel cluster detailing.
"""

import math
from typing import Dict, List, Tuple
from PIL import Image

def v3_dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def v3_len(v):
    return math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])

def v3_norm(v):
    l = v3_len(v)
    return (v[0]/l, v[1]/l, v[2]/l) if l > 1e-6 else (0.0, 0.0, 1.0)

def v3_sub(a, b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def smin(a: float, b: float, k: float = 0.8) -> float:
    h = max(k - abs(a - b), 0.0) / k
    return min(a, b) - h * h * k * 0.25

def sd_sphere(p, r):
    return v3_len(p) - r

def sd_ellipsoid(p, r):
    k0 = v3_len((p[0]/r[0], p[1]/r[1], p[2]/r[2]))
    k1 = v3_len((p[0]/(r[0]*r[0]), p[1]/(r[1]*r[1]), p[2]/(r[2]*r[2])))
    return k0 * (k0 - 1.0) / k1 if k1 > 1e-6 else 0.0

def sd_capsule(p, a, b, r):
    pa = v3_sub(p, a)
    ba = v3_sub(b, a)
    ba_len_sq = v3_dot(ba, ba)
    h = max(0.0, min(1.0, v3_dot(pa, ba) / ba_len_sq)) if ba_len_sq > 1e-6 else 0.0
    diff = (pa[0] - ba[0]*h, pa[1] - ba[1]*h, pa[2] - ba[2]*h)
    return v3_len(diff) - r

def sd_cylinder_z(p, h, r):
    d_xy = math.hypot(p[0], p[1]) - r
    d_z = abs(p[2]) - h * 0.5
    outside = math.hypot(max(d_xy, 0.0), max(d_z, 0.0))
    inside = min(max(d_xy, d_z), 0.0)
    return outside + inside

def sd_round_box(p, b, r):
    q = (abs(p[0]) - b[0], abs(p[1]) - b[1], abs(p[2]) - b[2])
    outside = math.hypot(max(q[0], 0.0), max(q[1], 0.0), max(q[2], 0.0))
    inside = min(max(q[0], max(q[1], q[2])), 0.0)
    return outside + inside - r

# 5 Original Dark Fantasy Knight Palettes with Rich Hue-Shifting Ramps
KNIGHT_PALETTES = {
    "iron_crusader": {
        "title": "Железный Рыцарь (Iron Crusader)",
        "desc": "Тёмная готическая сталь, холодный лазурный визор, алый рыцарский плащ",
        "ramp_metal": [
            ( 24,  22,  36), # Deep indigo-black shadow
            ( 48,  52,  70), # Dark cold slate
            ( 82,  94, 118), # Midtone gothic steel
            (138, 154, 182), # Polished bright plate
            (198, 214, 238), # Specular highlight
            (255, 255, 255)  # Pure edge gleam
        ],
        "ramp_cloth": [
            ( 42,  12,  20), # Deep crimson crease
            ( 88,  24,  32), # Shadow red
            (152,  38,  44), # Rich gothic crimson
            (205,  68,  62), # Sunlit fabric
            (245, 125, 105)  # Edge highlight
        ],
        "gold_accent": (225, 180, 50),
        "visor_glow":  ( 55, 220, 250),
        "helm_ornament": "great_helm"
    },
    "sunlight_paladin": {
        "title": "Солнечный Паладин (Sunlight Paladin)",
        "desc": "Серебряные латы с чеканкой, золотые крылья на шлеме, сияющий плащ",
        "ramp_metal": [
            ( 38,  34,  40), # Warm dark shadow
            ( 90,  88,  94), # Silver shadow
            (155, 152, 160), # Polished silver
            (215, 212, 220), # Pure silver plate
            (255, 248, 230), # Sunlight glint
            (255, 255, 255)
        ],
        "ramp_cloth": [
            ( 50,  46,  40),
            (110, 100,  80),
            (175, 165, 138),
            (228, 218, 188),
            (255, 250, 230)
        ],
        "gold_accent": (245, 195, 45),
        "visor_glow":  (255, 230, 75),
        "helm_ornament": "winged_crest"
    },
    "dark_knight": {
        "title": "Тёмный Рыцарь (Dark Knight)",
        "desc": "Обсидиановая броня, изогнутые рога, фиолетовые щели визора",
        "ramp_metal": [
            ( 14,  10,  20), # Void black
            ( 30,  24,  44), # Obsidian shadow
            ( 62,  52,  84), # Dark purple steel
            (105,  90, 140), # Violet edge reflection
            (170, 140, 210), # Specular violet gleam
            (240, 215, 255)
        ],
        "ramp_cloth": [
            ( 16,   6,  24),
            ( 38,  16,  54),
            ( 74,  28, 100),
            (115,  50, 150),
            (170,  90, 210)
        ],
        "gold_accent": (160,  60, 200),
        "visor_glow":  (215,  45, 255),
        "helm_ornament": "curved_horns"
    },
    "penitent_knight": {
        "title": "Кающийся Рыцарь (Penitent Knight)",
        "desc": "Бронзовая кираса, терновый шпиль капирота, клинок Реликвия",
        "ramp_metal": [
            ( 32,  22,  16), # Bronze deep shadow
            ( 72,  48,  34), # Worn bronze
            (122,  88,  58), # Antique bronze
            (180, 138,  94), # Polished bronze
            (230, 190, 145), # Golden bronze gleam
            (255, 240, 215)
        ],
        "ramp_cloth": [
            ( 35,  12,  14),
            ( 70,  22,  24),
            (128,  35,  35),
            (178,  64,  58),
            (220, 110, 100)
        ],
        "gold_accent": (195, 135, 45),
        "visor_glow":  (255, 205, 95),
        "helm_ornament": "thorn_spire"
    },
    "astral_champion": {
        "title": "Астральный Чемпион (Astral Champion)",
        "desc": "Мифриловые латы, астральная корона, лазурный плащ, световой клинок",
        "ramp_metal": [
            ( 18,  26,  44), # Abyss navy shadow
            ( 42,  60,  98), # Dark mithril
            ( 80, 115, 172), # Midtone astral steel
            (140, 180, 235), # Bright mithril plate
            (210, 235, 255), # Luminous mana gleam
            (255, 255, 255)
        ],
        "ramp_cloth": [
            ( 10,  20,  48),
            ( 24,  44, 102),
            ( 42,  80, 175),
            ( 75, 130, 235),
            (135, 190, 255)
        ],
        "gold_accent": ( 80, 225, 255),
        "visor_glow":  ( 70, 245, 255),
        "helm_ornament": "runic_crown"
    }
}

class ProceduralKnightSculptor:
    def __init__(self, archetype: str = "iron_crusader"):
        self.archetype = archetype
        self.palette = KNIGHT_PALETTES.get(archetype, KNIGHT_PALETTES["iron_crusader"])

    def evaluate_sdf(self, p: Tuple[float, float, float], state: str = "idle", anim_prog: float = 0.0) -> Tuple[float, str]:
        x, y, z = p

        # Breathing / kinematic modulation
        bob_z = math.sin(anim_prog * math.pi * 2.0) * 0.4 if state == "idle" else 0.0
        cloth_sway = math.sin(anim_prog * math.pi * 2.0) * 0.6 if state == "idle" else 0.0
        z_adj = z - bob_z

        # 1. Torso / Breastplate (Curved V-shape with wasp waist)
        chest_d = sd_ellipsoid((x, y, z_adj - 20.0), (4.4, 3.8, 5.0))
        waist_d = sd_cylinder_z((x, y, z_adj - 14.0), 3.2, 3.2)
        torso_d = smin(chest_d, waist_d, 0.8)

        # 2. Helmet (Smooth rounded dome + frontal visor wedge)
        helm_dome = sd_ellipsoid((x, y, z_adj - 27.5), (3.6, 3.8, 4.2))
        prow = sd_round_box((x, y - 2.6, z_adj - 27.0), (2.6, 1.2, 2.2), 0.4)
        helmet_d = smin(helm_dome, prow, 0.6)

        # Eye Visor Slit
        eye_slit = sd_round_box((x, y - 3.8, z_adj - 27.2), (2.2, 0.4, 0.45), 0.1)

        # 3. Pauldrons (Curved spherical caps over shoulders)
        pauldron_l = sd_ellipsoid((x + 5.2, y + 0.2, z_adj - 22.0), (2.6, 3.0, 2.8))
        pauldron_r = sd_ellipsoid((x - 5.2, y + 0.2, z_adj - 22.0), (2.6, 3.0, 2.8))
        pauldrons_d = min(pauldron_l, pauldron_r)

        # 4. Limbs (Arms & Legs as smooth articulated capsules)
        arm_l = sd_capsule((x, y, z_adj), (-4.8, 0.0, 21.0), (-5.4, 1.2, 13.0), 1.5)
        arm_r = sd_capsule((x, y, z_adj), ( 4.8, 0.0, 21.0), ( 5.4, 1.2, 13.0), 1.5)
        arms_d = min(arm_l, arm_r)

        # Legs (Pelvis down to Sabatons landing at z = 1.0)
        leg_l = sd_capsule((x, y, z_adj), (-2.2, 0.2, 12.5), (-2.3, 0.4, 4.0), 1.7)
        leg_r = sd_capsule((x, y, z_adj), ( 2.2, 0.2, 12.5), ( 2.3, 0.4, 4.0), 1.7)
        boot_l = sd_round_box((x + 2.3, y - 1.0, z_adj - 2.5), (1.5, 2.4, 1.4), 0.3)
        boot_r = sd_round_box((x - 2.3, y - 1.0, z_adj - 2.5), (1.5, 2.4, 1.4), 0.3)
        legs_d = min(min(leg_l, leg_r), min(boot_l, boot_r))

        # 5. Weapon (Sword Handle & Blade at right hip)
        sword_guard = sd_round_box((x - 5.8, y - 1.0, z_adj - 13.0), (2.6, 0.8, 0.6), 0.2)
        sword_blade = sd_round_box((x - 5.8, y - 1.0, z_adj - 6.0), (1.0, 0.4, 7.0), 0.15)
        weapon_d = min(sword_guard, sword_blade)

        # 6. Flowing Cloth Cape (Draped behind back)
        cape_y_target = -3.2 + cloth_sway * 0.4
        cape_wave_x = math.sin((z_adj - 12.0) * 0.4) * 0.5
        cape_d = sd_round_box((x - cape_wave_x, y - cape_y_target, z_adj - 14.0), (5.2, 0.6, 9.5), 0.4)

        # 7. Archetype-specific ornaments
        ornament_d = 999.0
        orn_type = self.palette.get("helm_ornament", "great_helm")

        if orn_type == "winged_crest":
            wing_l = sd_round_box((x + 4.2, y + 0.2, z_adj - 29.5), (0.6, 2.2, 3.4), 0.2)
            wing_r = sd_round_box((x - 4.2, y + 0.2, z_adj - 29.5), (0.6, 2.2, 3.4), 0.2)
            ornament_d = min(wing_l, wing_r)

        elif orn_type == "curved_horns":
            horn_l = sd_capsule((x, y, z_adj), (-3.2, 0.0, 28.5), (-5.8, -1.5, 32.5), 0.8)
            horn_r = sd_capsule((x, y, z_adj), ( 3.2, 0.0, 28.5), ( 5.8, -1.5, 32.5), 0.8)
            ornament_d = min(horn_l, horn_r)

        elif orn_type == "thorn_spire":
            spire = sd_capsule((x, y, z_adj), (0.0, -0.4, 30.0), (0.0, -0.8, 38.5), 0.9)
            ornament_d = spire

        elif orn_type == "runic_crown":
            crown_mid = sd_capsule((x, y, z_adj), (0.0, -0.2, 30.0), (0.0, -0.5, 34.5), 0.8)
            crown_l   = sd_capsule((x, y, z_adj), (-2.8, 0.0, 29.5), (-3.2, -0.2, 33.0), 0.7)
            crown_r   = sd_capsule((x, y, z_adj), ( 2.8, 0.0, 29.5), ( 3.2, -0.2, 33.0), 0.7)
            ornament_d = min(crown_mid, min(crown_l, crown_r))

        metal_d = smin(smin(smin(torso_d, helmet_d, 0.6), pauldrons_d, 0.5), min(arms_d, min(legs_d, weapon_d)), 0.4)

        if eye_slit < 0.2:
            return (eye_slit, "glow")
        if ornament_d < 0.3:
            return (ornament_d, "gold")
        if cape_d < metal_d - 0.1:
            return (cape_d, "cloth")
        return (metal_d, "metal")

    def calc_normal(self, p: Tuple[float, float, float], eps: float = 0.05) -> Tuple[float, float, float]:
        x, y, z = p
        dx = self.evaluate_sdf((x + eps, y, z))[0] - self.evaluate_sdf((x - eps, y, z))[0]
        dy = self.evaluate_sdf((x, y + eps, z))[0] - self.evaluate_sdf((x, y - eps, z))[0]
        dz = self.evaluate_sdf((x, y, z + eps))[0] - self.evaluate_sdf((x, y, z - eps))[0]
        return v3_norm((dx, dy, dz))

    def render_orthographic_frame(self, state: str = "idle", anim_prog: float = 0.0,
                                  w: int = 48, h: int = 48) -> Image.Image:
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        px = img.load()

        cx_screen = w / 2.0
        cy_screen = 43.0 # Ground level at y=42
        scale_3d = 1.14

        light_dir = v3_norm((-0.55, 0.70, 0.65))
        rim_dir   = v3_norm(( 0.60, -0.60, 0.40))
        pal = self.palette

        for py in range(h):
            for px_idx in range(w):
                world_x = (px_idx - cx_screen) / scale_3d
                world_z = (cy_screen - py) / scale_3d

                hit = False
                hit_pos = (0.0, 0.0, 0.0)
                hit_mat = "metal"

                ray_y = 12.0
                while ray_y >= -10.0:
                    dist, mat = self.evaluate_sdf((world_x, ray_y, world_z), state, anim_prog)
                    if dist <= 0.05:
                        hit = True
                        hit_pos = (world_x, ray_y, world_z)
                        hit_mat = mat
                        break
                    ray_y -= max(dist * 0.7, 0.18)

                if not hit:
                    continue

                if hit_mat == "glow":
                    px[px_idx, py] = (pal["visor_glow"][0], pal["visor_glow"][1], pal["visor_glow"][2], 255)
                    continue

                norm = self.calc_normal(hit_pos)
                diffuse = max(0.0, v3_dot(norm, light_dir))
                rim = max(0.0, v3_dot(norm, rim_dir))

                half_v = v3_norm((light_dir[0], light_dir[1] + 1.0, light_dir[2]))
                spec = math.pow(max(0.0, v3_dot(norm, half_v)), 16.0)

                light_val = diffuse * 0.75 + rim * 0.25 + spec * 0.45
                shade_idx = int(max(0, min(5, light_val * 4.5)))

                if hit_mat == "cloth":
                    ramp = pal["ramp_cloth"]
                    c_idx = min(len(ramp) - 1, shade_idx)
                    col = ramp[c_idx]
                elif hit_mat == "gold":
                    col = pal["gold_accent"]
                    if shade_idx >= 4:
                        col = (min(255, col[0] + 45), min(255, col[1] + 45), min(255, col[2] + 45))
                    elif shade_idx <= 1:
                        col = (int(col[0] * 0.6), int(col[1] * 0.6), int(col[2] * 0.6))
                else:
                    ramp = pal["ramp_metal"]
                    c_idx = min(len(ramp) - 1, shade_idx)
                    col = ramp[c_idx]

                px[px_idx, py] = (col[0], col[1], col[2], 255)

        return self._apply_selective_outline(img)

    def _apply_selective_outline(self, src: Image.Image) -> Image.Image:
        w, h = src.size
        s_px = src.load()
        out = src.copy()
        o_px = out.load()
        outline_dark = (22, 18, 32, 255)

        for y in range(h):
            for x in range(w):
                if s_px[x, y][3] == 0:
                    has_solid = False
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            if s_px[nx, ny][3] > 100:
                                has_solid = True
                                break
                    if has_solid:
                        o_px[x, y] = outline_dark

        return out
