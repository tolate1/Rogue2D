---
name: procedural-gen
description: Procedural generation principles, random walks, room stitching, and collision-free object placement.
---

# Procedural Generation Guidelines for Rogue2

## 1. Random Walk Generation
- Start at origin `(0, 0)` and step randomly in 4 cardinal directions.
- Keep a `set` of floor coordinates.
- Ensure minimum number of unique tiles (`steps >= 350-400`).

## 2. Wall Surrounding
- For every floor tile, inspect its 8 neighbors (including diagonals).
- Any neighboring tile not in the floor set becomes a wall tile with collision.

## 3. Safe Entity Placement
- Calculate Euclidean or Manhattan distance from player spawn `(0, 0)`.
- Never place stairs, chests, or high-tier enemies adjacent to player spawn.
- Maintain an `occupied_positions` set during map generation to prevent overlapping stairs, chests, and breakables.
- Exit stairs placed at furthest point from player spawn: `points.sort(key=lambda p: p[0]**2 + p[1]**2, reverse=True)`.
