---
name: game-feel
description: Guidelines for hit feedback, camera shake, damage indicators, i-frames, and responsive controls.
---

# Game Feel & Juice Guidelines for Rogue2

## 1. Hit Feedback & Multi-Hit Prevention
- When an attack lands on an enemy:
  - Do NOT allow the same weapon swing to damage the target every frame.
  - Track `hit_enemies = set()` inside the `Weapon` instance so each enemy takes damage only once per swing.
  - Flash enemy white or red for 2–3 frames upon hit (`flash_timer`).
  - Small knockback: push enemy back along attack vector by 5–10 pixels.

## 2. Floating Damage Numbers
- Spawn a floating text particle at the impact location:
  - Text: integer damage dealt.
  - Movement: float upwards while fading alpha over 400–600 ms, then remove.

## 3. Screen Shake
- Camera shake duration: 100–150 ms with random offset `(-3 to +3 px)` on major events (player taking damage, boss landing hits, explosive breaks).
