---
name: game-ui-ux
description: HUD design, menus, inventory tooltip interaction, and scale responsiveness for Pygame.
---

# Game UI / UX Guidelines for Rogue2

## 1. Text Surface Caching
- Never call `font.render()` every frame with the same string.
- Cache rendered text surfaces and re-render only when underlying data (health, level, gold) changes.

## 2. Click & Hover Interaction
- `Button` instances must check hover via `pygame.mouse.get_pos()`.
- Process clicks strictly in `MOUSEBUTTONDOWN` events with `event.button == 1`.
- Keep button labels clean: action text only (e.g. "Start Game", "Resume", "Settings"), avoid cluttering with key hints.

## 3. Inventory HUD & Tooltips
- Display item icons in horizontal or grid slots.
- When cursor hovers over a slot, display a compact tooltip panel showing item name, rarity color, and stat modifications.
- Hotkey for drinking health potion (e.g. `Q` or `1`) with HUD icon cooldown feedback.
