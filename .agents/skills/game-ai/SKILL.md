---
name: game-ai
description: Enemy behaviors, state machines, line-of-sight checks, and combat AI for 2D roguelikes.
---

# Game AI Patterns for Rogue2

## 1. Staggered Raycasting (Line of Sight)
- Do not perform raycasts for all enemies every single frame (CPU bottleneck).
- Stagger checks using timer offsets:
  ```python
  self.los_timer += 1
  if self.los_timer < self.los_interval:
      return self.has_los
  self.los_timer = 0
  ```
- Fast path: check distance to player first (`distance < aggro_radius`), then step raycast through obstacles.

## 2. Enemy State Machine
- States: `IDLE`, `CHASE`, `ATTACK`, `COOLDOWN`, `HURT`, `DEAD`.
- Melee enemies: pursue until `hitbox.colliderect(player.hitbox)` and attack with cooldown.
- Ranged enemies (Skeleton, Imp): approach to firing range, stop or kite, shoot projectile with cooldown.
- Bosses: cycle through basic attack, charged rush, and radial projectile bursts.
