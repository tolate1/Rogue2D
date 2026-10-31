"""
Rogue2D Universal LPC (Liberated Pixel Cup) Modular Compositor
Standard modular sprite compositor for 2D/2.5D RPGs.

Standard LPC Specs:
- Cell Size: 64x64 pixels (supports downsampling to 32x32 for Rogue2D)
- Layer Z-Ordering:
    1. background_layers (back cloaks, quivers)
    2. base_body (human, skeleton, shadow lurker)
    3. eyes_and_head (features, glowing eyes)
    4. boots (leather, iron greaves, plate sabatons)
    5. legs (chainmail leggings, plate cuisses)
    6. torso (leather tunic, hauberk, steel breastplate)
    7. hands (gauntlets, leather gloves)
    8. headgear (iron helm, dark hood, crown)
    9. offhand (shield, buckler, magic orb)
    10. weapon (sword, spear, rapier, scythe)
    11. vfx (rune aura, weapon trail)
"""

import os
from typing import Dict, List, Optional, Tuple
from PIL import Image

# Canonical Z-ordering for LPC modular layer composition
LPC_LAYER_ORDER = [
    "cloak_back",
    "body",
    "eyes",
    "boots",
    "legs",
    "torso",
    "hands",
    "headgear",
    "offhand",
    "weapon",
    "vfx"
]

# Standard LPC Animation Row indices (Direction: 0=North, 1=West, 2=South, 3=East)
LPC_ANIM_ROWS = {
    "spellcast": {"start_row": 0,  "frames": 7,  "dirs": ["north", "west", "south", "east"]},
    "thrust":    {"start_row": 4,  "frames": 8,  "dirs": ["north", "west", "south", "east"]},
    "walk":      {"start_row": 8,  "frames": 9,  "dirs": ["north", "west", "south", "east"]},
    "slash":     {"start_row": 12, "frames": 6,  "dirs": ["north", "west", "south", "east"]},
    "shoot":     {"start_row": 16, "frames": 13, "dirs": ["north", "west", "south", "east"]},
    "hurt":      {"start_row": 20, "frames": 6,  "dirs": ["single"]}
}

class LPCCompositor:
    def __init__(self, cell_size: int = 64):
        self.cell_size = cell_size
        self.layer_cache = {}

    def composite_layers(self, layer_images: Dict[str, Image.Image], canvas_size: Tuple[int, int] = (832, 1344)) -> Image.Image:
        """
        Combines modular layers in canonical LPC Z-order.
        canvas_size defaults to standard 13-column x 21-row LPC sheet (832 x 1344).
        """
        canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

        for layer_key in LPC_LAYER_ORDER:
            img = layer_images.get(layer_key)
            if img:
                # Resize if necessary
                if img.size != canvas_size:
                    img = img.resize(canvas_size, Image.NEAREST)
                canvas.alpha_composite(img.convert("RGBA"))

        return canvas

    def extract_action_frames(self, sheet: Image.Image,
                              action: str = "walk",
                              direction: str = "south",
                              target_size: Optional[Tuple[int, int]] = (32, 32)) -> List[Image.Image]:
        """
        Extracts individual animation frames for a given action and direction.
        Optionally resizes each frame to target_size (e.g., 32x32 for Rogue2D).
        """
        anim_info = LPC_ANIM_ROWS.get(action)
        if not anim_info:
            raise ValueError(f"Unknown LPC action: {action}")

        dirs = anim_info["dirs"]
        dir_idx = dirs.index(direction) if direction in dirs else 0
        row_idx = anim_info["start_row"] + dir_idx
        frame_count = anim_info["frames"]

        frames = []
        cs = self.cell_size

        for f in range(frame_count):
            box = (f * cs, row_idx * cs, (f + 1) * cs, (row_idx + 1) * cs)
            frame = sheet.crop(box)
            if target_size and target_size != (cs, cs):
                frame = frame.resize(target_size, Image.NEAREST)
            frames.append(frame)

        return frames

    def recolor_layer(self, layer_img: Image.Image, color_multiplier: Tuple[float, float, float]) -> Image.Image:
        """
        Applies a RGB multiplier to tint/recolor armor and cloth
        (e.g., iron -> gold, blood red, shadow void).
        """
        img = layer_img.convert("RGBA")
        r_mult, g_mult, b_mult = color_multiplier
        pixels = img.load()
        w, h = img.size

        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                if a > 0:
                    nr = int(max(0, min(255, r * r_mult)))
                    ng = int(max(0, min(255, g * g_mult)))
                    nb = int(max(0, min(255, b * b_mult)))
                    pixels[x, y] = (nr, ng, nb, a)

        return img
