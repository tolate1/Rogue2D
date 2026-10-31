# Architectural Blueprint: Developer Room Topology & Interaction Matrix

> **Council Protocol Rule 6 Standard**: Every entity, boss, hero archetype, mechanic, shrine, and hazard in Rogue2D must be cataloged here, mapped in `src/map_manager.py:create_dev_room()`, registered in `get_showcase_anim_data()`, and validated by `tools/council/validator.py`.

---

## 1. Developer Room Topology & Wing Coordinates

The Developer Room is an expansive Grand Pantheon Hall measuring **48×46 tiles** ($1920 \times 1840$ pixels). It allows real-time inspection, combat testing, and asset verification across 9 specialized wings:

```
+-----------------------------------------------------------------------+
|  WING 1 (y=4):  5 Core Hero Archetypes (60-74px Native Silhouettes)   |
|  WING 2 (y=7):  5 Alternative Hero Paladins & Class Colorways         |
|                                                                       |
|  [CENTRAL PLAZA (x=24, y=8): Hero Spawn Point & Loadout Hub]          |
|                                                                       |
|  WING 3 (y=11): Undead & Crypt Bestiary (7 Mobs)                      |
|  WING 4 (y=16): Caverns, Underworld & Beasts (7 Mobs)                 |
|  WING 5 (y=21): Swamps, Spores, Slimes & Mutants (8 Mobs)             |
|  WING 6 (y=26): Grand Boss Pantheon (4 Bosses, 1.5x Giant Scale)     |
|  WING 7 (y=31): Interactive Altars, Shrines, Chests & Breakables      |
|  WING 8 (y=36): Services, Arsenal Pedestals, Forge & Merchant Kelvin  |
|  WING 9 (y=41): Hazards, Traps, Floor Decals, Bones & Exit Portal     |
+-----------------------------------------------------------------------+
```

### Detailed Wing Breakdown & Entity Registry

| Wing | Y-Coord | Entities | Scale / Type | Interactive Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Wing 1: Hero Archetypes** | `y = 4` | `hero_slayer` (70px), `hero_wanderer` (66px), `hero_crusader` (74px), `hero_champion_redux` (60px), `player_default` (48px) | ShowcaseEntity | Proximity (<65px) reveals `[E] ЭКИПИРОВАТЬ: <Имя>`. Pressing `[E]` immediately hot-swaps player sprite sheets, hitboxes, and weapon trails. |
| **Wing 2: Hero Skins** | `y = 7` | `player_default`, `player_paladin`, `player_dark_knight`, `player_penitent`, `player_champion` | ShowcaseEntity | Distinct colorways, pauldrons, and visors. Equippable via `[E]`. |
| **Wing 3: Crypt Bestiary** | `y = 11` | `zombie`, `skeleton`, `skeleton_brute`, `necromancer`, `phantom`, `banshee`, `sarcophagus` | ShowcaseEntity | Cycles through states: *Ожидание $\to$ Замах $\to$ Удар $\to$ Восстановление / Призыв*. Can be struck for damage numbers and hitstop. |
| **Wing 4: Cavern Bestiary** | `y = 16` | `goblin`, `lurker`, `imp`, `bat`, `yeti`, `lava_hound`, `gargoyle` | ShowcaseEntity | Agile behaviors, flanking tactics, aerial flight, ground slam telegraphed frames. |
| **Wing 5: Swamp Aberrations** | `y = 21` | `toxic_slime`, `mini_slime`, `spore_bomber`, `spore_creeper`, `mosquito`, `cultist`, `mimic`, `iron_maiden` | ShowcaseEntity | Slime stretch/squash cycles, explosive detonation telegraphed states, mimic awakening jaws. |
| **Wing 6: Boss Pantheon** | `y = 26` | `boss_void_knight`, `boss_bone_golem`, `boss_frost_revenant`, `boss_necro_lord` | ShowcaseEntity (1.5×, 72px) | Multi-cell sweeping cleaves, orbital projectiles, summoning rituals, void bursts. |
| **Wing 7: Shrines & Altars** | `y = 31` | `BloodAltar`, `WisdomFountain`, `AnvilShrine`, `Chest`, `Breakable`, `Gold` | Interactive World Entity | `[E]` Interaction: Modulates stats, spends gold/HP, springs UI, plays `altar.wav`/`anvil.wav`. |
| **Wing 8: Services & Arsenal** | `y = 36` | `Blacksmith`, `Anvil`, `Trader (Kelvin)`, Weapon Display Pedestals | NPC & Service Entities | Opens Blacksmith Forge modal and Kelvin Shop modal with buy/sell and tabbed inventory. |
| **Wing 9: Hazards & Decals** | `y = 41` | 5 `FloorDecal` (cracks, moss, blood, puddle, rune), 3 `InteractiveDebris` bone piles, `GroundMist`, `Torch`, Exit Portal | Environmental / Decal | Stepping on bone piles crunches (`debris_crunch.wav`) and scatters shards. Dash parts mist. Exit portal returns to hub/menu. |

---

## 2. Comprehensive System Interaction Matrix

This matrix defines exact data flows, collision masks, physics responses, and audio-visual feedback when entities encounter one another:

```mermaid
flowchart TD
    subgraph Combat System
        P_ATK[Player Attack / Swing] -->|Hitbox Sweep| SWEEP[Arc Detection]
        SWEEP -->|Colliderect| MOB_HIT[Mob Hurtbox]
        MOB_HIT --> DMG[Apply Damage & Stats]
        MOB_HIT --> HS[110ms Hit-Stop Microfreeze]
        MOB_HIT --> CRIT{Crit Roll?}
        CRIT -->|Yes: Gold Pop| NUM_CRIT[DamageText Size 20 + Crit SFX]
        CRIT -->|No: White Pop| NUM_NORM[DamageText Size 16]
        MOB_HIT --> KNOCK[Knockback Impulse]
        MOB_HIT --> SPARK[Spark/Blood Particles in VisibleGroup]
    end

    subgraph Collision & Line of Sight
        AI_MOVE[Mob / Boss Pathfinding] --> LOS_CHECK[has_line_of_fire Raycast]
        LOS_CHECK -->|Filter non-obstacles| OBS_FILTER[Ignore Particle, Decal, Mist]
        OBS_FILTER -->|clipline| WALL_CHECK[Tile Wall Hitbox Check]
        WALL_CHECK -->|Clear Line| CHARGE_ATTACK[Execute Attack / Projectile]
        WALL_CHECK -->|Blocked| FLANK[A* Tangent Deviation]
    end

    subgraph Aerodynamics & Wind
        DASH[Player Dash [SPACE]] --> WIND_VEC[Generate Wind Vector]
        WIND_VEC -->|Radius 180px| TORCH[Torch Flame Flutter & Tilt]
        WIND_VEC -->|Displacement| MIST[Ground Mist Clearance Wake]
    end

    subgraph Environment & Altars
        E_PRESS[Interact Key [E]] --> ALTAR_PROX[Proximity < 65px Check]
        ALTAR_PROX -->|Blood Altar| HP_MOD[-25 HP -> +2 Permanent Atk]
        ALTAR_PROX -->|Wisdom Fountain| XP_MOD[-30 Gold -> +100 XP]
        ALTAR_PROX -->|Anvil Shrine| STAT_MOD[-20 Gold -> Random Stat +1]
        ALTAR_PROX -->|Bone Pile| DEBRIS_CRUNCH[Crunch Sound + Bone Chunks]
    end
```

### Detailed Interaction Specifications

#### A. Combat & Hitbox Resolution
1. **Swept Arc Detection**:
   - Weapons instantiate `Weapon(player, groups, weapon_type)` with directional offsets based on `player.status` (`up`, `down`, `left`, `right`).
   - `Claymore` has an expanded sweep radius ($52 \times 44$ px) with high stagger.
   - `Dagger` has a rapid forward thrust ($32 \times 24$ px) with $1.8\times$ crit multiplier.
2. **Hit-Stop Micro-Freeze**:
   - Both the player and struck entity store `took_damage_time = pygame.time.get_ticks()`.
   - During the 110ms window, position integration freezes while hit-flash mask ($RGB 255, 230, 230, 180$) blends over the sprite.
3. **Particle Group Isolation**:
   - **MANDATORY**: `Particle` instances MUST NEVER be placed into `obstacle_sprites`.
   - `Particle.__init__` enforces filtering of any group containing the string `"obstacle"`.
   - Particles have `hitbox = pygame.Rect(0, 0, 0, 0)` and `sprite_type = 'particle'`.

#### B. Line of Fire & Boss Collision Bulletproofing
1. **Raycasting Guarantee (`has_line_of_fire`)**:
   - Every raycast loops through `self.obstacle_sprites`.
   - Skips sprites where `sprite_type in ('particle', 'ui_effect', 'floor_overlay', 'decal', 'showcase_entity')`.
   - Accesses `hitbox = getattr(obstacle, 'hitbox', None) or getattr(obstacle, 'rect', None)`.
   - Verifies `hitbox is not None and hasattr(hitbox, 'clipline') and hitbox.width > 0`.
   - Protects against `AttributeError` on dynamic entities.
2. **Swept Wall Clamping**:
   - Movement splits into horizontal and vertical components.
   - Evaluates `prev_rect` vs obstacle boundaries to clamp position immediately without tunneling.

#### C. Environmental & Aerodynamic Coupling
1. **Ground Mist Dynamics**:
   - `GroundMist` motes wander at low velocity ($0.2$ to $0.5$ px/frame) inside dungeon boundaries.
   - When the player dashes, a repelling impulse is added to any mist mote within 90px, creating an authentic slipstream wake.
2. **Torch Flame Flutter**:
   - `Torch.update()` calculates `diff = player.rect.center - torch.rect.center`.
   - If player dashes within 160px, flame frames offset by $+3$ px in the dash direction for 250ms, mimicking realistic air displacement.
3. **Debris Restitution**:
   - Stepping on an `InteractiveDebris` bone pile triggers `trigger_crush()`.
   - Spawns 6 `Particle` shards with randomized radial velocity ($1.8$ to $4.5$ px/frame) and plays `debris_crunch.wav`.

---

## 3. Mandatory Council Protocol Rule 6

To prevent any team member or agent from leaving blind spots in the Developer Room, the Council Protocol now mandates:

1. **Simultaneous Dev Room Mapping**:
   Whenever a new entity is created in `src/entities.py`, it must be immediately added to:
   - `src/map_manager.py:create_dev_room()`
   - `src/map_manager.py:get_showcase_anim_data()`
   - `docs/DEV_ROOM_INTERACTION_MATRIX.md`
2. **Deterministic Validator Gate**:
   `tools/council/validator.py` includes `check_dev_room_entity_coverage()`.
   If any enemy or boss is detected in `src/entities.py` but absent from `create_dev_room()`, the test fails with:
   `FAIL: Entity '<entity_id>' is missing from Developer Room Pantheon!`
3. **Zero-Token Verification Requirement**:
   No PR or task is marked complete without a passing report from `validator.py`.
