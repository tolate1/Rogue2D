"""
Rogue2D Normal-Mapped 2.5D Lighting Engine
Calculates physical diffuse (N·L) and Blinn-Phong specular (N·H) highlights
for 2D sprites using normal maps and dynamic light sources.
"""

import math
from PIL import Image

class NormalMappedLighting:
    def __init__(self):
        pass

    @staticmethod
    def render_lit_sprite(diffuse_img: Image.Image,
                          normal_img: Image.Image,
                          specular_img: Image.Image,
                          light_pos_rel: tuple,  # (lx, ly, lz) relative to sprite center in pixels
                          light_color: tuple = (255, 220, 150),
                          light_intensity: float = 1.3,
                          light_radius: float = 120.0,
                          ambient_color: tuple = (35, 30, 45),
                          shininess: float = 16.0) -> Image.Image:
        """
        Renders a diffuse sprite with 2.5D normal-mapped lighting.
        light_pos_rel: relative (x, y, z) coordinates where z is height off the 2D plane (>0).
        """
        diffuse = diffuse_img.convert("RGBA")
        normal = normal_img.convert("RGBA")
        spec = specular_img.convert("RGBA") if specular_img else None

        w, h = diffuse.size
        d_px = diffuse.load()
        n_px = normal.load()
        s_px = spec.load() if spec else None

        out_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        out_px = out_img.load()

        cx = w / 2.0
        cy = h / 2.0
        lx, ly, lz = light_pos_rel

        # Ambient color normalized
        amb_r = ambient_color[0] / 255.0
        amb_g = ambient_color[1] / 255.0
        amb_b = ambient_color[2] / 255.0

        # Light color normalized
        lc_r = light_color[0] / 255.0
        lc_g = light_color[1] / 255.0
        lc_b = light_color[2] / 255.0

        # View vector pointing straight out of screen (0, 0, 1)
        # Halfway vector H = normalize(L + V)

        for y in range(h):
            for x in range(w):
                dr, dg, db, da = d_px[x, y]
                if da < 10:
                    continue

                nr, ng, nb, _ = n_px[x, y]
                # Unpack normal from [0..255] to [-1..1]
                nx = (nr / 255.0) * 2.0 - 1.0
                ny = -((ng / 255.0) * 2.0 - 1.0) # OpenGL tangent space inversion
                nz = (nb / 255.0) * 2.0 - 1.0
                # Normalize N
                n_len = math.sqrt(nx * nx + ny * ny + nz * nz)
                if n_len > 0.0001:
                    nx /= n_len
                    ny /= n_len
                    nz /= n_len
                else:
                    nx, ny, nz = 0.0, 0.0, 1.0

                # Vector from pixel to light source
                px_rel_x = x - cx
                px_rel_y = y - cy
                dir_x = lx - px_rel_x
                dir_y = ly - px_rel_y
                dir_z = lz

                dist_3d = math.sqrt(dir_x * dir_x + dir_y * dir_y + dir_z * dir_z)
                if dist_3d > 0.0001:
                    lx_norm = dir_x / dist_3d
                    ly_norm = dir_y / dist_3d
                    lz_norm = dir_z / dist_3d
                else:
                    lx_norm, ly_norm, lz_norm = 0.0, 0.0, 1.0

                # Distance attenuation (smooth falloff)
                dist_2d = math.hypot(dir_x, dir_y)
                attenuation = max(0.0, min(1.0, 1.0 - (dist_2d / light_radius)))
                attenuation = attenuation * attenuation # Quadratic decay

                # Diffuse term (N · L)
                n_dot_l = nx * lx_norm + ny * ly_norm + nz * lz_norm
                diffuse_factor = max(0.0, n_dot_l) * light_intensity * attenuation

                # Blinn-Phong Specular (N · H)
                # V = (0, 0, 1) -> H = normalize(L + V)
                hx = lx_norm
                hy = ly_norm
                hz = lz_norm + 1.0
                h_len = math.sqrt(hx * hx + hy * hy + hz * hz)
                if h_len > 0.0001:
                    hx /= h_len
                    hy /= h_len
                    hz /= h_len
                n_dot_h = max(0.0, nx * hx + ny * hy + nz * hz)

                spec_intensity = 0.0
                if s_px:
                    sr, sg, sb, _ = s_px[x, y]
                    spec_strength = (sr / 255.0)
                    spec_intensity = spec_strength * math.pow(n_dot_h, shininess) * light_intensity * attenuation

                # Combine ambient + diffuse + specular
                base_r = dr / 255.0
                base_g = dg / 255.0
                base_b = db / 255.0

                final_r = base_r * amb_r + base_r * lc_r * diffuse_factor + lc_r * spec_intensity
                final_g = base_g * amb_g + base_g * lc_g * diffuse_factor + lc_g * spec_intensity
                final_b = base_b * amb_b + base_b * lc_b * diffuse_factor + lc_b * spec_intensity

                final_r = int(max(0.0, min(1.0, final_r)) * 255.0)
                final_g = int(max(0.0, min(1.0, final_g)) * 255.0)
                final_b = int(max(0.0, min(1.0, final_b)) * 255.0)

                out_px[x, y] = (final_r, final_g, final_b, da)

        return out_img
