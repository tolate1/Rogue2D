"""
Rogue2D Dual-Grid Tilemap & Autotiling System
Based on the Dual-Grid algorithm (Oskar Stalberg / Ondrej-K Dual-Grid Tilemap System).

Reduces 47 complex Wang autotiles down to 16 elegant corner-sampled tiles
by rendering on a half-tile shifted grid: (x - TILE_SIZE/2, y - TILE_SIZE/2).
Every dual cell samples 4 neighboring primary grid points:
    TL (Top-Left), TR (Top-Right), BL (Bottom-Left), BR (Bottom-Right)
giving exactly 2^4 = 16 seamless tile configurations.
"""

from typing import List, Dict, Tuple, Optional

# Bitmask values for the 4 corners
CORNER_TL = 1  # 0001
CORNER_TR = 2  # 0010
CORNER_BR = 4  # 0100
CORNER_BL = 8  # 1000

# Canonical 16 Dual-Grid Tile Configurations:
# Index is bitmask = (TL * 1) + (TR * 2) + (BR * 4) + (BL * 8)
TILE_NAMES = {
    0:  "empty_or_base",         # 0000: All 4 corners Base (e.g., pure Floor)
    1:  "outer_corner_tl",       # 0001: Wall only in Top-Left
    2:  "outer_corner_tr",       # 0010: Wall only in Top-Right
    3:  "edge_top",              # 0011: Wall along Top edge (TL + TR)
    4:  "outer_corner_br",       # 0100: Wall only in Bottom-Right
    5:  "diagonal_inverted",     # 0101: Wall at TL + BR (Saddle point A)
    6:  "edge_right",            # 0110: Wall along Right edge (TR + BR)
    7:  "inner_corner_bl",       # 0111: Wall everywhere except Bottom-Left
    8:  "outer_corner_bl",       # 1000: Wall only in Bottom-Left
    9:  "edge_left",             # 1001: Wall along Left edge (TL + BL)
    10: "diagonal_standard",     # 1010: Wall at TR + BL (Saddle point B)
    11: "inner_corner_br",       # 1011: Wall everywhere except Bottom-Right
    12: "edge_bottom",           # 1100: Wall along Bottom edge (BL + BR)
    13: "inner_corner_tr",       # 1101: Wall everywhere except Top-Right
    14: "inner_corner_tl",       # 1110: Wall everywhere except Top-Left
    15: "solid_foreground"       # 1111: All 4 corners Wall (pure Wall / Fill)
}

# 4x4 Sheet Coordinates (column, row) for a standard 16-tile autotile sheet
# Standard layout:
# Row 0: [ 0,  1,  2,  3]
# Row 1: [ 4,  5,  6,  7]
# Row 2: [ 8,  9, 10, 11]
# Row 3: [12, 13, 14, 15]
TILE_SHEET_COORDS = {mask: (mask % 4, mask // 4) for mask in range(16)}


class DualGridTilemap:
    """
    Manages dual-grid autotiling for a 2D grid.
    World grid has dimensions (width, height).
    Dual rendered grid has dimensions (width + 1, height + 1) shifted by (-tileSize/2, -tileSize/2).
    """

    def __init__(self, width: int, height: int, default_value: int = 0):
        self.width = width
        self.height = height
        # Primary logical grid (0 = Floor/Base, 1 = Wall/Elevated)
        self.grid = [[default_value for _ in range(width)] for _ in range(height)]

    def set_cell(self, x: int, y: int, value: int):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = 1 if value else 0

    def get_cell(self, x: int, y: int) -> int:
        """Returns cell value with boundary clamping to 0 (floor) or 1 (wall boundary)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return 0

    def calculate_dual_bitmask(self, dual_x: int, dual_y: int) -> int:
        """
        Calculates the 4-bit mask for dual grid position (dual_x, dual_y).
        Corners in primary world coordinates:
            TL: (dual_x - 1, dual_y - 1)
            TR: (dual_x,     dual_y - 1)
            BL: (dual_x - 1, dual_y)
            BR: (dual_x,     dual_y)
        """
        tl = 1 if self.get_cell(dual_x - 1, dual_y - 1) else 0
        tr = 1 if self.get_cell(dual_x,     dual_y - 1) else 0
        bl = 1 if self.get_cell(dual_x - 1, dual_y)     else 0
        br = 1 if self.get_cell(dual_x,     dual_y)     else 0

        mask = (tl * CORNER_TL) | (tr * CORNER_TR) | (br * CORNER_BR) | (bl * CORNER_BL)
        return mask

    def generate_dual_tilemap(self) -> List[List[int]]:
        """
        Generates the full (height + 1) x (width + 1) dual tile matrix.
        Each entry is an integer bitmask [0..15].
        """
        dual_rows = self.height + 1
        dual_cols = self.width + 1
        dual_map = []
        for dy in range(dual_rows):
            row = []
            for dx in range(dual_cols):
                mask = self.calculate_dual_bitmask(dx, dy)
                row.append(mask)
            dual_map.append(row)
        return dual_map

    def get_tile_render_info(self, dual_x: int, dual_y: int, tile_size: int = 32) -> dict:
        """
        Returns rendering metadata for a dual tile:
        - world_x, world_y: screen/world coordinates shifted by -half_tile
        - bitmask: 0..15
        - name: descriptive string
        - sheet_col, sheet_row: position in 4x4 sprite sheet
        """
        mask = self.calculate_dual_bitmask(dual_x, dual_y)
        half_tile = tile_size // 2
        world_x = dual_x * tile_size - half_tile
        world_y = dual_y * tile_size - half_tile
        col, row = TILE_SHEET_COORDS[mask]

        return {
            "world_x": world_x,
            "world_y": world_y,
            "bitmask": mask,
            "tile_name": TILE_NAMES.get(mask, "unknown"),
            "sheet_col": col,
            "sheet_row": row
        }
