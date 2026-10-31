---
name: pygame-core
description: Best practices and patterns for Pygame architecture, game loops, event handling, physics, sprite groups, and collision management.
---

# Pygame Core Architecture Guidelines for Rogue2

## 1. Game Loop & Clock
- Fixed timestep logic: `clock.tick(FPS)` to stabilize at 60 FPS.
- Separate `events()`, `update()`, and `draw()` cleanly.
- Never mix input processing inside drawing functions.

## 2. Sub-pixel Physics and Collisions
- Pygame `Rect` only stores integers. For smooth movement, always maintain float coordinates using `pygame.math.Vector2`:
  ```python
  self.pos.x += self.velocity.x
  self.hitbox.x = round(self.pos.x)
  self.collision('horizontal')
  self.pos.x = self.hitbox.x # Sync float with resolved hitbox
  ```
- Use smaller `hitbox` (`rect.inflate(-w, -h)`) for entities rather than the visual `rect` to prevent awkward wall-snagging.

## 3. Sprite Groups & Rendering
- Do not recreate groups every frame.
- Use layer sorting: floors first, then Y-sort (`centery`) for depth illusion.
- Use culling (skip drawing sprites whose rects do not intersect camera view).
