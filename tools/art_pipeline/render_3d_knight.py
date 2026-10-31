"""
Rogue2D 3D-to-2D Pixel Art Knight Generator & Renderer
Creates true 3D voxel/box-model meshes of 5 distinct Knight archetypes,
applies skeletal kinematics (idle, walk, attack, dash),
and renders them via 2.5D orthographic camera with 3D normals, depth-buffering,
directional lighting, and dark fantasy palette quantization.
"""

import math
from typing import Dict, List, Tuple
from PIL import Image

# 3D Box / Voxel primitive
class Box3D:
    def __init__(self, cx, cy, cz, sx, sy, sz, color, normal_bias=(0, 0, 1), name="part"):
        self.cx, self.cy, self.cz = cx, cy, cz  # Center in 3D world space
        self.sx, self.sy, self.sz = sx, sy, sz  # Width (X), Depth (Y), Height (Z)
        self.color = color                      # RGB tuple
        self.normal_bias = normal_bias          # Facing bias
        self.name = name

class Knight3DModel:
    """Parametric 3D Knight with skeletal kinematics."""
    def __init__(self, archetype: str = "iron_crusader"):
        self.archetype = archetype
        self.parts: List[Box3D] = []
        self._build_mesh()

    def _build_mesh(self):
        """Constructs 3D anatomy for the selected archetype."""
        self.parts.clear()

        # Archetype Palettes
        palettes = {
            "iron_crusader": {
                "plate_dark": (45, 48, 58),
                "plate_mid": (80, 85, 100),
                "plate_light": (145, 155, 175),
                "plate_spec": (210, 220, 235),
                "gold_trim": (185, 145, 55),
                "cape": (135, 32, 42),
                "cape_shadow": (75, 18, 26),
                "visor_glow": (60, 210, 240),
                "leather": (60, 42, 32),
                "blade": (195, 205, 225),
                "blade_edge": (240, 245, 255),
                "helm_type": "great_helm"
            },
            "sunlight_paladin": {
                "plate_dark": (70, 68, 65),
                "plate_mid": (130, 128, 120),
                "plate_light": (195, 190, 175),
                "plate_spec": (255, 250, 230),
                "gold_trim": (230, 185, 45),
                "cape": (220, 215, 195),
                "cape_shadow": (140, 135, 120),
                "visor_glow": (255, 230, 80),
                "leather": (85, 60, 40),
                "blade": (230, 215, 140),
                "blade_edge": (255, 250, 210),
                "helm_type": "winged_helm"
            },
            "dark_knight": {
                "plate_dark": (22, 22, 28),
                "plate_mid": (42, 40, 52),
                "plate_light": (75, 70, 90),
                "plate_spec": (130, 125, 160),
                "gold_trim": (120, 40, 150),
                "cape": (28, 20, 38),
                "cape_shadow": (14, 10, 20),
                "visor_glow": (190, 45, 245),
                "leather": (32, 28, 36),
                "blade": (110, 95, 140),
                "blade_edge": (215, 80, 255),
                "helm_type": "horned_helm"
            },
            "penitent_knight": {
                "plate_dark": (52, 45, 38),
                "plate_mid": (95, 80, 65),
                "plate_light": (155, 135, 110),
                "plate_spec": (215, 195, 165),
                "gold_trim": (160, 115, 45),
                "cape": (115, 75, 45),
                "cape_shadow": (60, 38, 22),
                "visor_glow": (255, 210, 120),
                "leather": (70, 48, 35),
                "blade": (165, 155, 145),
                "blade_edge": (235, 225, 215),
                "helm_type": "pointed_spire"
            },
            "astral_champion": {
                "plate_dark": (30, 42, 60),
                "plate_mid": (60, 85, 120),
                "plate_light": (110, 155, 210),
                "plate_spec": (195, 230, 255),
                "gold_trim": (80, 210, 255),
                "cape": (32, 55, 125),
                "cape_shadow": (16, 28, 68),
                "visor_glow": (80, 240, 255),
                "leather": (45, 40, 55),
                "blade": (150, 210, 255),
                "blade_edge": (240, 250, 255),
                "helm_type": "crown_visor"
            }
        }
        pal = palettes.get(self.archetype, palettes["iron_crusader"])
        self.pal = pal

    def get_pose_parts(self, state: str = "idle", frame_idx: int = 0) -> List[Box3D]:
        """Calculates 3D box coordinates for state and animation frame."""
        pal = self.pal
        parts: List[Box3D] = []

        # Kinematic Parameters
        torso_z_bob = 0.0
        leg_l_angle = 0.0
        leg_r_angle = 0.0
        cape_sway_y = 0.0
        cape_sway_x = 0.0
        weapon_angle = 0.0
        weapon_dx = 0.0
        weapon_dy = 0.0
        weapon_dz = 0.0
        arm_r_angle = 0.0
        shield_dx = 0.0

        if state == "idle":
            # Subtle breathing cycle (4 frames: 0, 1, 2, 3)
            cycle = math.sin(frame_idx * math.pi / 2.0)
            torso_z_bob = cycle * 0.7
            cape_sway_x = cycle * 0.4
            cape_sway_y = cycle * 0.3
            weapon_angle = -0.15 + cycle * 0.03
            arm_r_angle = cycle * 0.04

        elif state == "walk":
            # Grounded 4-frame stride
            cycle = frame_idx * (math.pi / 2.0)
            torso_z_bob = math.cos(cycle * 2.0) * 0.6
            leg_l_angle = math.sin(cycle) * 0.45
            leg_r_angle = -math.sin(cycle) * 0.45
            cape_sway_x = math.sin(cycle) * 0.8
            cape_sway_y = -abs(math.cos(cycle)) * 0.6
            weapon_angle = -0.15 + math.sin(cycle) * 0.08
            shield_dx = -math.sin(cycle) * 0.5

        elif state == "attack":
            # 3-Frame Attack:
            # Frame 0: Anticipation / Windup (coiling back, blade raised high)
            # Frame 1: Slash Impact (blade swept forward, wide 180 deg horizontal arc)
            # Frame 2: Recovery / Follow-through (weight leaning forward)
            if frame_idx == 0:
                torso_z_bob = -0.4
                weapon_angle = 1.35   # Raised back over shoulder
                weapon_dx = -3.0
                weapon_dy = -2.5
                weapon_dz = 4.0
                arm_r_angle = 1.1
                cape_sway_x = -1.2
            elif frame_idx == 1:
                torso_z_bob = -0.8
                weapon_angle = -1.55  # Full forward swing
                weapon_dx = 5.5
                weapon_dy = 2.0
                weapon_dz = -1.0
                arm_r_angle = -1.3
                cape_sway_x = 2.2
            else: # frame 2
                torso_z_bob = -0.3
                weapon_angle = -0.7   # Follow-through rest
                weapon_dx = 4.0
                weapon_dy = 1.0
                weapon_dz = -2.0
                arm_r_angle = -0.6
                cape_sway_x = 0.8

        elif state == "dash":
            # Aerodynamic 2-frame lean
            torso_z_bob = -1.2
            cape_sway_x = -3.0 if frame_idx == 0 else -3.8
            cape_sway_y = -1.0
            weapon_angle = -0.9
            weapon_dx = 3.0
            arm_r_angle = -0.8

        # --- 3D PART ASSEMBLY (Coordinates in mm/units, center=(0,0,0) at waist) ---

        # 1. Cape (Behind body: Y < 0)
        c_x = -0.5 + cape_sway_x
        c_y = -3.5 + cape_sway_y
        c_z = 2.0 + torso_z_bob
        parts.append(Box3D(c_x, c_y, c_z - 3.5, 9.5, 1.6, 12.0, pal["cape"], normal_bias=(0, -1, 0), name="cape"))
        parts.append(Box3D(c_x, c_y - 0.3, c_z - 8.0, 10.5, 1.2, 5.0, pal["cape_shadow"], normal_bias=(0, -1, 0), name="cape_trim"))

        # 2. Legs & Sabatons (Z = -13 to -1)
        # Left Leg
        ll_y = math.sin(leg_l_angle) * 3.0
        ll_z = -math.cos(leg_l_angle) * 3.0
        parts.append(Box3D(-2.5, ll_y, -6.5 + ll_z, 3.2, 3.4, 7.5, pal["plate_mid"], normal_bias=(0, 1, 0), name="leg_l"))
        parts.append(Box3D(-2.5, ll_y + 0.8, -11.0 + ll_z, 3.4, 4.4, 3.0, pal["plate_dark"], normal_bias=(0, 1, 0), name="boot_l"))

        # Right Leg
        lr_y = math.sin(leg_r_angle) * 3.0
        lr_z = -math.cos(leg_r_angle) * 3.0
        parts.append(Box3D(2.5, lr_y, -6.5 + lr_z, 3.2, 3.4, 7.5, pal["plate_mid"], normal_bias=(0, 1, 0), name="leg_r"))
        parts.append(Box3D(2.5, lr_y + 0.8, -11.0 + lr_z, 3.4, 4.4, 3.0, pal["plate_dark"], normal_bias=(0, 1, 0), name="boot_r"))

        # 3. Torso / Breastplate (Z = -1 to 8)
        tz = torso_z_bob
        parts.append(Box3D(0.0, 0.0, 1.5 + tz, 7.6, 5.2, 7.5, pal["plate_light"], normal_bias=(0, 1, 0.3), name="torso"))
        # Gold/Accent Gorget & Crest
        parts.append(Box3D(0.0, 1.8, 4.2 + tz, 5.0, 1.8, 3.0, pal["gold_trim"], normal_bias=(0, 1, 0.5), name="crest"))
        parts.append(Box3D(0.0, 0.2, -1.8 + tz, 7.8, 5.4, 2.0, pal["leather"], normal_bias=(0, 1, 0), name="belt"))

        # 4. Spaulders / Shoulders (Z = 5 to 8)
        parts.append(Box3D(-4.8, 0.0, 6.0 + tz, 3.4, 4.8, 3.6, pal["plate_spec"], normal_bias=(-1, 0, 1), name="spaulder_l"))
        parts.append(Box3D(4.8, 0.0, 6.0 + tz, 3.4, 4.8, 3.6, pal["plate_spec"], normal_bias=(1, 0, 1), name="spaulder_r"))

        # 5. Head / Helmet (Z = 8 to 17)
        hz = 11.2 + tz
        helm_type = pal.get("helm_type", "great_helm")

        if helm_type == "great_helm":
            # Solid steel bucket helm with T-slit
            parts.append(Box3D(0.0, 0.0, hz, 6.2, 6.0, 7.2, pal["plate_mid"], normal_bias=(0, 1, 0.3), name="helm"))
            # T-Visor slit with cyan glow
            parts.append(Box3D(0.0, 2.8, hz + 0.4, 4.2, 0.8, 0.9, pal["visor_glow"], normal_bias=(0, 1, 0), name="visor_h"))
            parts.append(Box3D(0.0, 2.8, hz - 1.0, 0.9, 0.8, 2.2, pal["visor_glow"], normal_bias=(0, 1, 0), name="visor_v"))
            # Golden Crest on top
            parts.append(Box3D(0.0, -0.4, hz + 3.8, 1.2, 5.4, 1.6, pal["gold_trim"], normal_bias=(0, 0, 1), name="crest_ridge"))

        elif helm_type == "winged_helm":
            # Corinthian / Winged Paladin Helmet
            parts.append(Box3D(0.0, 0.0, hz, 6.0, 5.8, 7.0, pal["plate_spec"], normal_bias=(0, 1, 0.3), name="helm"))
            parts.append(Box3D(0.0, 2.6, hz + 0.2, 4.0, 0.8, 1.2, pal["visor_glow"], normal_bias=(0, 1, 0), name="visor"))
            # Left & Right Golden Wings
            parts.append(Box3D(-3.8, -0.5, hz + 3.0, 1.4, 4.2, 4.8, pal["gold_trim"], normal_bias=(-1, 0, 1), name="wing_l"))
            parts.append(Box3D(3.8, -0.5, hz + 3.0, 1.4, 4.2, 4.8, pal["gold_trim"], normal_bias=(1, 0, 1), name="wing_r"))

        elif helm_type == "horned_helm":
            # Jagged Dark Knight Horns & Violet Visor
            parts.append(Box3D(0.0, 0.0, hz, 6.4, 6.2, 7.4, pal["plate_dark"], normal_bias=(0, 1, 0.3), name="helm"))
            parts.append(Box3D(0.0, 2.8, hz + 0.4, 4.6, 0.8, 1.0, pal["visor_glow"], normal_bias=(0, 1, 0), name="visor"))
            # Swept obsidian horns
            parts.append(Box3D(-4.2, -1.0, hz + 3.5, 1.5, 3.0, 4.5, pal["gold_trim"], normal_bias=(-1, 0, 1), name="horn_l"))
            parts.append(Box3D(4.2, -1.0, hz + 3.5, 1.5, 3.0, 4.5, pal["gold_trim"], normal_bias=(1, 0, 1), name="horn_r"))

        elif helm_type == "pointed_spire":
            # Blasphemous Penitent High Spire
            parts.append(Box3D(0.0, 0.0, hz - 1.0, 5.8, 5.6, 5.5, pal["plate_mid"], normal_bias=(0, 1, 0.3), name="helm_base"))
            parts.append(Box3D(0.0, 0.0, hz + 4.5, 3.6, 3.6, 7.0, pal["gold_trim"], normal_bias=(0, 0, 1), name="spire_mid"))
            parts.append(Box3D(0.0, 0.0, hz + 9.0, 1.8, 1.8, 5.0, pal["gold_trim"], normal_bias=(0, 0, 1), name="spire_tip"))
            # Face veil / eye slit
            parts.append(Box3D(0.0, 2.6, hz - 0.8, 3.6, 0.8, 0.8, pal["visor_glow"], normal_bias=(0, 1, 0), name="visor"))

        elif helm_type == "crown_visor":
            # Astral Runic Crown Visor with distinct tall crown points
            parts.append(Box3D(0.0, 0.0, hz, 6.0, 6.0, 6.8, pal["plate_mid"], normal_bias=(0, 1, 0.3), name="helm"))
            parts.append(Box3D(0.0, 2.6, hz + 0.4, 4.4, 0.8, 1.4, pal["visor_glow"], normal_bias=(0, 1, 0), name="visor"))
            # Crown base band
            parts.append(Box3D(0.0, 0.0, hz + 3.8, 6.6, 6.6, 1.4, pal["gold_trim"], normal_bias=(0, 0, 1), name="crown_band"))
            # Distinctive Crown Spires (Left, Center, Right)
            parts.append(Box3D(-3.4, -0.5, hz + 5.6, 1.4, 2.0, 4.4, pal["gold_trim"], normal_bias=(-1, 0, 1), name="crown_l"))
            parts.append(Box3D(3.4, -0.5, hz + 5.6, 1.4, 2.0, 4.4, pal["gold_trim"], normal_bias=(1, 0, 1), name="crown_r"))
            parts.append(Box3D(0.0, -0.5, hz + 6.6, 1.8, 2.2, 5.8, pal["gold_trim"], normal_bias=(0, 0, 1), name="crown_mid"))
            # Astral Runic Wings on Pauldrons
            parts.append(Box3D(-5.8, -0.5, 6.5 + tz, 2.0, 4.5, 5.0, pal["gold_trim"], normal_bias=(-1, 0, 1), name="astral_wing_l"))
            parts.append(Box3D(5.8, -0.5, 6.5 + tz, 2.0, 4.5, 5.0, pal["gold_trim"], normal_bias=(1, 0, 1), name="astral_wing_r"))

        # 6. Shield / Offhand (Left side: X < 0)
        sh_x = -5.5 + shield_dx
        parts.append(Box3D(sh_x, 1.5, 2.0 + tz, 1.8, 4.8, 7.0, pal["plate_dark"], normal_bias=(-1, 1, 0), name="shield"))
        parts.append(Box3D(sh_x - 0.2, 1.6, 2.0 + tz, 1.0, 2.8, 4.2, pal["gold_trim"], normal_bias=(-1, 1, 0), name="shield_boss"))

        # 7. Sword / Weapon (Right side: X > 0)
        # Handle & Crossguard
        wx = 5.2 + weapon_dx
        wy = 1.0 + weapon_dy
        wz = 1.5 + tz + weapon_dz

        # Weapon rotation
        parts.append(Box3D(wx, wy, wz, 1.4, 1.4, 3.2, pal["leather"], normal_bias=(0, 1, 0), name="sword_hilt"))
        parts.append(Box3D(wx, wy, wz + 2.0, 5.4, 1.6, 1.2, pal["gold_trim"], normal_bias=(0, 1, 0), name="sword_guard"))
        # Steel Blade extending along weapon_angle
        blade_len = 13.0
        bx = wx + math.sin(weapon_angle) * (blade_len * 0.5)
        by = wy + math.cos(weapon_angle) * 1.5
        bz = wz + 2.6 + math.cos(weapon_angle) * (blade_len * 0.5)
        parts.append(Box3D(bx, by, bz, 2.2, 0.8, blade_len, pal["blade"], normal_bias=(0, 1, 0.4), name="sword_blade"))
        parts.append(Box3D(bx, by + 0.3, bz, 1.0, 0.4, blade_len + 0.5, pal["blade_edge"], normal_bias=(0, 1, 0.6), name="sword_edge"))

        return parts

class Orthographic25DRenderer:
    """Renders 3D boxes to 2.5D pixel-art with Z-buffer and 3D lighting."""
    def __init__(self, out_w: int = 48, out_h: int = 48, scale: float = 1.45):
        self.out_w = out_w
        self.out_h = out_h
        self.scale = scale
        # Camera angle: 2.5D axonometric projection
        self.cam_angle_x = math.radians(26.0) # Elevation angle

    def render(self, parts: List[Box3D]) -> Image.Image:
        w, h = self.out_w, self.out_h
        # Z-Buffer initialized to deep negative infinity
        z_buf = [[-999999.0 for _ in range(w)] for _ in range(h)]
        c_buf = [[(0, 0, 0, 0) for _ in range(w)] for _ in range(h)]

        cx_screen = w / 2.0
        cy_screen = h / 2.0 + 8.0 # Feet pinned near bottom

        cos_elev = math.cos(self.cam_angle_x)
        sin_elev = math.sin(self.cam_angle_x)

        # Light Vector (Key Light from Top-Left: lx=-0.5, ly=0.6, lz=0.8)
        light_dir = (-0.45, 0.55, 0.70)
        l_len = math.sqrt(sum(k*k for k in light_dir))
        lx, ly, lz = [k / l_len for k in light_dir]

        # Rasterize each box as dense point voxels
        step = 0.5
        for part in parts:
            half_x = part.sx * 0.5
            half_y = part.sy * 0.5
            half_z = part.sz * 0.5

            nx, ny, nz = part.normal_bias
            n_len = math.hypot(nx, math.hypot(ny, nz))
            if n_len > 0:
                nx, ny, nz = nx / n_len, ny / n_len, nz / n_len

            # Calculate diffuse light factor
            n_dot_l = max(0.0, nx * lx + ny * ly + nz * lz)
            light_mult = 0.45 + 0.55 * n_dot_l

            r, g, b = part.color
            lit_r = int(max(0, min(255, r * light_mult)))
            lit_g = int(max(0, min(255, g * light_mult)))
            lit_b = int(max(0, min(255, b * light_mult)))

            # Sample box volume
            vx = part.cx - half_x
            while vx <= part.cx + half_x + 0.001:
                vy = part.cy - half_y
                while vy <= part.cy + half_y + 0.001:
                    vz = part.cz - half_z
                    while vz <= part.cz + half_z + 0.001:
                        # 3D Orthographic Projection to (u, v, depth)
                        # Screen X is world X
                        u = int(cx_screen + vx * self.scale)
                        # Screen Y is combination of world Y and Z
                        v = int(cy_screen - (vz * cos_elev - vy * sin_elev) * self.scale)
                        # Depth for Z-buffer (higher depth = closer to camera)
                        depth = vz * sin_elev + vy * cos_elev

                        if 0 <= u < w and 0 <= v < h:
                            if depth > z_buf[v][u]:
                                z_buf[v][u] = depth
                                c_buf[v][u] = (lit_r, lit_g, lit_b, 255)
                        vz += step
                    vy += step
                vx += step

        # Build PIL Image
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        px = img.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = c_buf[y][x]

        # Add dark outline (1px gothic silhouette)
        outlined = self._apply_outline(img)
        return outlined

    def _apply_outline(self, src: Image.Image) -> Image.Image:
        """Adds crisp 1-pixel dark gothic outline around character silhouette."""
        w, h = src.size
        s_px = src.load()
        out = src.copy()
        o_px = out.load()

        outline_col = (18, 14, 24, 255)

        for y in range(h):
            for x in range(w):
                if s_px[x, y][3] == 0:
                    # Check 4 neighbors
                    has_solid = False
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            if s_px[nx, ny][3] > 100:
                                has_solid = True
                                break
                    if has_solid:
                        o_px[x, y] = outline_col

        return out
