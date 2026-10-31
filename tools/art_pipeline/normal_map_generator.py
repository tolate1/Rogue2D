"""
Rogue2D Art Pipeline: Normal, Height, and Specular Map Generator
Inspired by Laigter (Open Source 2D Normal Map Generator).

Converts 2D pixel-art sprites into:
1. Tangent-Space Normal Maps (_normal.png) for physical N·L diffuse & specular lighting
2. Specular / Roughness Maps (_specular.png) for metallic highlights
3. Height / Bump Maps (_height.png) for parallax and relief depth
"""

import os
import math
from PIL import Image, ImageFilter

class NormalMapGenerator:
    def __init__(self, strength: float = 2.5, bevel_radius: int = 2, invert_y: bool = True):
        self.strength = float(strength)
        self.bevel_radius = int(bevel_radius)
        self.invert_y = bool(invert_y)

    def generate_height_map(self, img: Image.Image) -> Image.Image:
        """
        Synthesizes a height map combining luminance and edge bevels.
        Internal pixels further from sprite boundaries rise higher.
        """
        img = img.convert("RGBA")
        width, height = img.size
        pixels = img.load()

        # Step 1: Base luminance
        lum_map = []
        for y in range(height):
            row = []
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a < 10:
                    row.append(0.0)
                else:
                    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
                    row.append(lum)
            lum_map.append(row)

        # Step 2: Distance bevel from transparent boundary
        dist_map = []
        for y in range(height):
            row = []
            for x in range(width):
                _, _, _, a = pixels[x, y]
                if a < 10:
                    row.append(0.0)
                else:
                    # Sample neighbors within bevel radius
                    min_edge_dist = self.bevel_radius
                    for dy in range(-self.bevel_radius, self.bevel_radius + 1):
                        for dx in range(-self.bevel_radius, self.bevel_radius + 1):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < width and 0 <= ny < height:
                                if pixels[nx, ny][3] < 10:
                                    d = math.hypot(dx, dy)
                                    if d < min_edge_dist:
                                        min_edge_dist = d
                            else:
                                min_edge_dist = min(min_edge_dist, 1.0)
                    bevel_norm = min_edge_dist / float(max(1, self.bevel_radius))
                    row.append(bevel_norm)
            dist_map.append(row)

        # Step 3: Combine luminance (40%) and shape bevel (60%)
        height_img = Image.new("L", (width, height), 0)
        h_pixels = height_img.load()
        for y in range(height):
            for x in range(width):
                _, _, _, a = pixels[x, y]
                if a >= 10:
                    combined = 0.45 * lum_map[y][x] + 0.55 * dist_map[y][x]
                    h_pixels[x, y] = int(max(0.0, min(1.0, combined)) * 255.0)

        # Subtle Gaussian smoothing to prevent harsh single-pixel spikes
        smoothed_height = height_img.filter(ImageFilter.GaussianBlur(radius=0.6))
        return smoothed_height

    def generate_normal_map(self, img: Image.Image) -> Image.Image:
        """
        Generates an RGB/RGBA tangent-space normal map using a 3x3 Sobel slope operator.
        R = Nx (-1..1 -> 0..255)
        G = Ny (-1..1 -> 0..255)
        B = Nz ( 0..1 -> 128..255, pointing outward toward viewer)
        A = Original sprite alpha
        """
        img = img.convert("RGBA")
        width, height = img.size
        src_pixels = img.load()

        height_img = self.generate_height_map(img)
        h_pixels = height_img.load()

        normal_img = Image.new("RGBA", (width, height), (128, 128, 255, 0))
        n_pixels = normal_img.load()

        for y in range(height):
            for x in range(width):
                _, _, _, a = src_pixels[x, y]
                if a < 10:
                    n_pixels[x, y] = (128, 128, 255, 0)
                    continue

                # 3x3 Sobel kernel sampling with boundary clamping
                def get_h(ix, iy):
                    cx = max(0, min(width - 1, ix))
                    cy = max(0, min(height - 1, iy))
                    return h_pixels[cx, cy] / 255.0

                tl = get_h(x - 1, y - 1)
                t  = get_h(x    , y - 1)
                tr = get_h(x + 1, y - 1)
                l  = get_h(x - 1, y    )
                r  = get_h(x + 1, y    )
                bl = get_h(x - 1, y + 1)
                b  = get_h(x    , y + 1)
                br = get_h(x + 1, y + 1)

                # Horizontal and vertical gradients
                dx = (tr + 2.0 * r + br) - (tl + 2.0 * l + bl)
                dy = (bl + 2.0 * b + br) - (tl + 2.0 * t + tr)

                # Tangent normal components
                nx = -dx * self.strength
                ny = -dy * self.strength if not self.invert_y else dy * self.strength
                nz = 1.0

                # Normalization
                length = math.sqrt(nx * nx + ny * ny + nz * nz)
                if length > 0.00001:
                    nx /= length
                    ny /= length
                    nz /= length
                else:
                    nx, ny, nz = 0.0, 0.0, 1.0

                # Map [-1, 1] to [0, 255]
                red   = int((nx * 0.5 + 0.5) * 255.0)
                green = int((ny * 0.5 + 0.5) * 255.0)
                blue  = int((nz * 0.5 + 0.5) * 255.0)

                red   = max(0, min(255, red))
                green = max(0, min(255, green))
                blue  = max(0, min(255, blue))

                n_pixels[x, y] = (red, green, blue, a)

        return normal_img

    def generate_specular_map(self, img: Image.Image, metallic_boost: float = 1.2) -> Image.Image:
        """
        Generates a specular map indicating surface reflectivity.
        Brighter/high-contrast areas (steel, gems, gold trims) receive high specular response.
        """
        img = img.convert("RGBA")
        width, height = img.size
        src_pixels = img.load()

        spec_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        s_pixels = spec_img.load()

        for y in range(height):
            for x in range(width):
                r, g, b, a = src_pixels[x, y]
                if a < 10:
                    continue
                # Calculate saturation and brightness
                max_c = max(r, g, b)
                min_c = min(r, g, b)
                delta = max_c - min_c
                lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0

                # Metallic surfaces: high luminance or high saturation highlights
                spec = math.pow(lum, 1.6) * metallic_boost
                val = int(max(0.0, min(1.0, spec)) * 255.0)
                s_pixels[x, y] = (val, val, val, a)

        return spec_img

    def process_file(self, input_path: str, output_dir: str = None) -> dict:
        """Processes a single sprite file and writes _normal.png, _specular.png, and _height.png."""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Source file not found: {input_path}")

        if output_dir is None:
            output_dir = os.path.dirname(input_path)
        os.makedirs(output_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(input_path))[0]
        src_img = Image.open(input_path)

        normal_img = self.generate_normal_map(src_img)
        spec_img = self.generate_specular_map(src_img)
        height_img = self.generate_height_map(src_img)

        norm_path = os.path.join(output_dir, f"{base_name}_normal.png")
        spec_path = os.path.join(output_dir, f"{base_name}_specular.png")
        hgt_path = os.path.join(output_dir, f"{base_name}_height.png")

        normal_img.save(norm_path, "PNG")
        spec_img.save(spec_path, "PNG")
        height_img.save(hgt_path, "PNG")

        return {
            "normal": norm_path,
            "specular": spec_path,
            "height": hgt_path
        }

    def batch_process(self, input_dir: str, output_dir: str, pattern_includes: list = None) -> list:
        """Batch processes multiple sprites in an input folder."""
        results = []
        for root, _, files in os.walk(input_dir):
            for file in files:
                if not file.lower().endswith((".png", ".jpg", ".webp")):
                    continue
                if any(x in file for x in ["_normal", "_specular", "_height"]):
                    continue
                if pattern_includes and not any(p in file for p in pattern_includes):
                    continue

                full_in = os.path.join(root, file)
                rel_dir = os.path.relpath(root, input_dir)
                target_out = os.path.join(output_dir, rel_dir) if rel_dir != "." else output_dir
                res = self.process_file(full_in, target_out)
                results.append(res)
        return results

if __name__ == "__main__":
    import sys
    print("NormalMapGenerator ready. Use as a library or pass image path as argument.")
