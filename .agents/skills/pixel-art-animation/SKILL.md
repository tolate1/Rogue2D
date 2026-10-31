---
name: pixel-art-animation
description: Standard operating procedure and quality guidelines for 2D top-down pixel art, dark-fantasy character design, sprite animation cycles, combat VFX, and environmental lighting in Rogue 2D.
---

# Pixel Art & Animation Quality System (Rogue 2D)

This skill serves as the permanent aesthetic benchmark, animation standard, and quality-control manual for **Rogue 2D: Dungeon Descent**. It codifies player feedback, approved visual benchmarks, and strict anti-patterns.

---

## 1. Player Feedback & Benchmark Register

Always cross-reference new character models and animation cycles against the player's explicit feedback:

### 🌟 Approved Benchmarks (What the Player Praised)
1. **Таящийся (Lurker) — The Stealth Assassin Benchmark**:
   - *Why Approved*: Distinct hunched stalking silhouette, dynamic opacity drop (alpha 70%) for cloaking, glowing cyan eye glints, and sudden lethal scissor cross-slash with dual obsidian daggers.
   - *Rule*: Every rogue, shadow mob, or humanoid creature must feature expressive posture, clear eye glints, and unique weapon grips.
2. **Слизни (Slimes) — The Organic Squash & Stretch Benchmark**:
   - *Why Approved*: 7-phase organic deformation cycle. Deep charging squish down to 14px height, explosive launch stretched tall to 38px, parabolic ground-shadow separation (z-height up to 32px), and juicy impact splat with radial toxic splash droplets.
   - *Rule*: All non-rigid monsters must deform dynamically during windup, movement, and landing.
3. **Скелет-Лучник (Skeleton Archer) — The Recurve Archer Benchmark**:
   - *Why Approved*: Prominent forward-extended recurve bow (`x >= 28`), taut triangular bowstring pulled back to cheekbone (`x=14`), and distinct anticipation hold before release.
   - *Rule*: Ranged units must clearly telegraph arrow nocking, string tension, and projectile release.
4. **Спецэффект Повышения Уровня (Key L) — The Sacred Celestial Benchmark**:
   - *Why Approved*: Sacred rotating rune mandala on the dungeon floor, volumetric vertical pillar of light, 7 angled divine god rays, ascending gold spark motes, and **physical illumination of dungeon tiles in `self.light_surf`** running at a locked 60 FPS.
5. **Developer Showcase Screen — The Testing Grounds**:
   - *Why Approved*: Structured exhibit rows allowing live state toggling and side-by-side inspection of all monsters and hero skins.

### 🚫 Strictly Forbidden Anti-Patterns (What the Player Rejected)
1. **The Recolor Trap (Запрещено: Перекраска скинов)**:
   - *Issue*: Applying palette swaps to the exact same 32x38 silhouette mask.
   - *Mandate*: Every skin MUST be a genuinely different 3D/pixel model with distinct geometry:
     - `paladin`: Winged angelic bascinet flaring to `y=0`, glowing solar halo, white-and-gold surcoat.
     - `dark_knight`: Curved demonic obsidian horns to `y=0`, spiked shoulders, burning red eye slit.
     - `champion`: Down-curving ram horns, nasal barbute, shaggy wolf fur mantle, barbarian war-skirt.
2. **The Shrinking Dash Bug (Запрещено: Уменьшение персонажа при дэше)**:
   - *Issue*: Character shrinking down to a miniature size during dash or dodge rolls.
   - *Mandate*: Maintain consistent 38–40px character height across ALL frames (idle, walk, attack, dash).
3. **Mismatched / Oversized Pixels (Запрещено: Гигантские пиксели)**:
   - *Issue*: Mixing 2x2 or 3x3 pixel blocks with 1x1 sub-pixel details.
   - *Mandate*: All sprites on 48x48 or 32x32 canvases must adhere to a unified 1x1 sub-pixel grid.
4. **Flat Minecraft Boxes (Запрещено: Плоские коробки)**:
   - *Issue*: Solid rectangular blocks without muscle tone, torn cloth, exposed bones, or silhouette cuts.
   - *Mandate*: Add broken ribs, ragged burial hems, clawed fingers, and drooping jaws (as seen in the overhauled Zombie and Goblin).
5. **Frozen Tilted Sprites (Запрещено: Застывший повернутый меч)**:
   - *Issue*: Spawning a static pre-rotated sprite that sits in the air.
   - *Mandate*: Melee attacks must be dynamic sweeping crescents (`Weapon.render_slash`) that rotate fluidly around the hero.
6. **Duplicate Limb / Prop Bug (Запрещено: Двойные посохи/оружие)**:
   - *Issue*: Drawing a raised casting staff while forgetting to erase the idle staff on the other shoulder.
   - *Mandate*: When an action pose draws a raised prop, always erase or adjust the resting prop.
7. **Detached Lighting Layers (Запрещено: Оторванное освещение)**:
   - *Issue*: Drawing glowing VFX solely on top of the screen without writing into the environment lightmap.
   - *Mandate*: Every radiant flash, torch, or spell aura must blit directly into `self.light_surf` to physically light up dungeon bricks and floors.

---

## 2. Canvas & Anatomy Standards

| Character Type | Canvas Size | Character Height | Center Anchor | Collision Hitbox |
| :--- | :--- | :--- | :--- | :--- |
| **Hero (Player)** | 48 x 48 px | 38 – 42 px | `(24, 24)` | `inflate(-10, -20)` |
| **Standard Mob (Skeleton, Zombie, Goblin, Lurker)** | 32 x 32 px | 24 – 28 px | `(16, 16)` | `inflate(-8, -10)` |
| **Slime (Toxic & Mini)** | 32 x 32 px (base) | 14 px (squish) – 38 px (stretch) | `(16, 20)` | `inflate(-4, -6)` |
| **Dungeon Boss (Void Knight, Golem, Necro Lord)** | 64 x 64 px | 52 – 58 px | `(32, 32)` | `inflate(-16, -14)` |

---

## 3. The 5-Phase Combat Animation State Machine

Every attack cycle must follow this cadence to maximize game feel and responsive combat:

```
[1. Windup / Telegraph] -> [2. Active Strike] -> [3. Impact Hitstop] -> [4. Follow-Through] -> [5. Recovery]
       (30-40% time)             (10-15% time)         (5-10% time)           (20-25% time)         (15-20% time)
```

1. **Windup / Telegraph (30–40% duration)**:
   - Hero pulls sword arm back; archer pulls bowstring taut; boss charges 140° red danger cone.
   - Gives the player visual clarity and reaction window.
2. **Active Strike / Release (10–15% duration)**:
   - High velocity acceleration.
   - Procedural crescent motion trail (`poly` with outer/inner radius and alpha decay).
   - Hitbox detection active (`hit_enemies` set prevents multi-hit bugs).
3. **Impact Hitstop (5–10% duration)**:
   - 1–2 frame micro hit-stop freeze on victim.
   - Red silhouette mask hurt flash (`setcolor=(235, 65, 65, 180)`).
   - Radial directional spark particles bursting away from strike angle.
4. **Follow-Through (20–25% duration)**:
   - Blade inertia completes arc; cape flutters forward.
   - Motion trail fades smoothly (`alpha * (1.0 - progress**1.8)`).
5. **Recovery (15–20% duration)**:
   - Smooth reset to walk or idle stance.

---

## 4. Procedural Weapon Slash Implementation

Never use static rotated bitmaps for melee weapons. Use the procedural crescent sweep formula:

```python
def render_slash(self, progress):
    t = progress ** 0.72 # Snappy ease-out
    sz = int((self.reach + 24) * 2)
    surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
    cx, cy = sz // 2, sz // 2

    swing_start = self.base_angle - self.arc_degrees * 0.5
    swing_end = self.base_angle + self.arc_degrees * 0.5
    cur_tip_ang = swing_start + (swing_end - swing_start) * t
    trail_span = min(self.arc_degrees * 0.65, self.arc_degrees * t)

    outer_pts, inner_pts = [], []
    for i in range(15):
        frac = i / 14.0
        a = cur_tip_ang - trail_span * (1.0 - frac)
        rad = math.radians(-a)
        r_out = self.reach + (1.0 - (1.0 - frac)**2) * 5
        r_in = max(8, self.reach - 14 + frac * 8)
        outer_pts.append((cx + math.cos(rad) * r_out, cy + math.sin(rad) * r_out))
        inner_pts.append((cx + math.cos(rad) * r_in, cy + math.sin(rad) * r_in))

    poly = outer_pts + list(reversed(inner_pts))
    if len(poly) >= 3:
        alpha = int(240 * (1.0 - progress ** 1.8))
        pygame.draw.polygon(surf, (*self.slash_col, max(0, min(255, alpha // 2))), poly)
        pygame.draw.lines(surf, (255, 255, 255, max(0, min(255, alpha))), False, outer_pts, 2)
        pygame.draw.circle(surf, (255, 255, 255, max(0, min(255, alpha))), (int(outer_pts[-1][0]), int(outer_pts[-1][1])), 3)
    return surf
```

---

## 5. Environmental Lighting Integration Rule

Whenever introducing a glowing aura, divine beam, or magical explosion:

1. **Lightmap Pass (`self.light_surf` in `Level.custom_draw`)**:
   - Draw the radial light burst or light beams directly onto `self.light_surf` BEFORE it is multiplied onto the screen (`disp.blit(self.light_surf, special_flags=BLEND_RGB_MULT)`).
   - This ensures dark dungeon floor tiles, stone bricks, and props physically illuminate.
2. **Foreground VFX Pass**:
   - Draw glowing volumetric motes, god rays, and sparkles on a cached scratch surface blitted with `BLEND_RGBA_ADD`.
   - Never allocate new surfaces inside the render loop every frame.

---

## 6. Automated Quality Verification Protocol

Before declaring any new model or animation complete, run:

1. **Silhouette Difference Test**:
   ```python
   overlap = m_base.overlap_mask(m_new, (0, 0)).count()
   diff = (m_base.count() - overlap) + (m_new.count() - overlap)
   assert diff > 30 # Proves it is a genuine model, not a recolor
   ```
2. **Height Consistency Test**:
   ```python
   assert 36 <= surf.get_bounding_rect().height <= 44 # Prevents shrinking dash bug
   ```
3. **Prop Integrity Test**:
   - Check that secondary weapon pixels are 0 when primary weapon is raised.
4. **Full Test Suite Validation**:
   - Execute `tools/council/validator.py` and ensure all unit tests pass with zero regressions.
