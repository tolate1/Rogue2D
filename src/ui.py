import random
from src.ui_engine import get_nineslice, draw_panel, draw_inlay, draw_text, get_font, SpriteButton
import pygame
import math
from functools import lru_cache
from src.settings import *

RARITY_COLORS = {
    'common': (175, 180, 195),
    'rare': (60, 160, 255),
    'epic': (190, 80, 255),
    'legendary': (255, 205, 40)
}

def _group_inventory_for_hud(items):
    groups = []
    for item in items:
        for group in groups:
            can_stack = getattr(group[0], 'can_stack_with', None)
            if callable(can_stack) and can_stack(item):
                group.append(item)
                break
        else:
            groups.append([item])
    return [
        (group[0], sum(max(1, int(getattr(item, 'count', 1))) for item in group), group)
        for group in groups
    ]

def compute_spring_scale(open_time, duration_ms=90):
    if not open_time:
        return 1.0
    now = pygame.time.get_ticks()
    elapsed = now - open_time
    if elapsed >= duration_ms or elapsed < 0:
        return 1.0
    p = max(0.0, min(1.0, elapsed / float(duration_ms)))
    # Spring overshoot curve (0.90 -> 1.05 -> 1.00)
    scale = 1.0 - 0.10 * (1.0 - p) + 0.15 * math.sin(p * math.pi) * p
    return scale


def draw_with_spring_easing(modal, surface, render_fn):
    open_t = getattr(modal, 'open_time', 0)
    scale = compute_spring_scale(open_t, duration_ms=90)
    if scale < 0.999:
        sw, sh = surface.get_size()
        temp_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        render_fn(temp_surf)
        r = getattr(modal, 'rect', None)
        if r:
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((5, 5, 9, 210))
            surface.blit(overlay, (0, 0))
            box_surf = temp_surf.subsurface(r).copy()
            scaled_w = max(10, int(r.width * scale))
            scaled_h = max(10, int(r.height * scale))
            scaled_box = pygame.transform.scale(box_surf, (scaled_w, scaled_h))
            surface.blit(scaled_box, (r.centerx - scaled_w // 2, r.centery - scaled_h // 2))
            return
    render_fn(surface)


def get_pixel_font(size, bold=True):
    if not pygame.font.get_init():
        pygame.font.init()
    # Highly legible clean typography with crisp rendering & 100% Cyrillic support
    for name in ['consolas', 'tahoma', 'cascadiamono', 'segoeui', 'arial']:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f: return f
        except Exception:
            continue
    return pygame.font.SysFont('arial', size, bold=bold)


@lru_cache(maxsize=512)
def _service_text(text, color, size, bold):
    return get_pixel_font(size, bold).render(text, True, color)


def draw_pixel_frame(surface, rect, accent=(153, 118, 71)):
    """Gothic 9-slice multi-bevel frame with carved brass corners and relief shadow."""
    shadow = pygame.Surface((rect.width + 12, rect.height + 12), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 125))
    surface.blit(shadow, (rect.x + 4, rect.y + 6))
    pygame.draw.rect(surface, (15, 13, 20), rect)
    pygame.draw.line(surface, (68, 58, 75), (rect.left, rect.top), (rect.right - 1, rect.top), 1)
    pygame.draw.line(surface, (68, 58, 75), (rect.left, rect.top), (rect.left, rect.bottom - 1), 1)
    pygame.draw.line(surface, (8, 6, 12), (rect.left, rect.bottom - 1), (rect.right - 1, rect.bottom - 1), 1)
    pygame.draw.line(surface, (8, 6, 12), (rect.right - 1, rect.top), (rect.right - 1, rect.bottom - 1), 1)
    pygame.draw.rect(surface, (28, 24, 34), rect.inflate(-4, -4))
    pygame.draw.rect(surface, (19, 16, 25), rect.inflate(-10, -10))
    pygame.draw.rect(surface, accent, rect.inflate(-6, -6), 1)
    inner_accent = (min(255, accent[0] + 40), min(255, accent[1] + 35), min(255, accent[2] + 25))
    corner_len = min(16, max(8, rect.width // 18))
    for x, dx in ((rect.x + 3, 1), (rect.right - 4, -1)):
        for y, dy in ((rect.y + 3, 1), (rect.bottom - 4, -1)):
            pygame.draw.line(surface, inner_accent, (x, y), (x + corner_len * dx, y), 2)
            pygame.draw.line(surface, inner_accent, (x, y), (x, y + corner_len * dy), 2)
            pygame.draw.rect(surface, (245, 215, 120), (x - 1, y - 1, 3, 3))
            pygame.draw.rect(surface, (45, 28, 12), (x, y, 1, 1))


def draw_dialog_frame(surface, rect, accent=(190, 154, 90)):
    """Dark layered gothic frame with 9-slice bevels and carved chevrons."""
    shadow = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 135))
    surface.blit(shadow, (rect.x + 6, rect.y + 8))
    pygame.draw.rect(surface, (15, 13, 21), rect)
    inner = rect.inflate(-8, -8)
    pygame.draw.rect(surface, (28, 25, 35), inner)
    pygame.draw.line(surface, (75, 65, 82), (rect.left, rect.top), (rect.right - 1, rect.top), 1)
    pygame.draw.line(surface, (75, 65, 82), (rect.left, rect.top), (rect.left, rect.bottom - 1), 1)
    pygame.draw.line(surface, (8, 6, 12), (rect.left, rect.bottom - 1), (rect.right - 1, rect.bottom - 1), 1)
    pygame.draw.line(surface, (8, 6, 12), (rect.right - 1, rect.top), (rect.right - 1, rect.bottom - 1), 1)
    header = pygame.Rect(inner.x, inner.y, inner.width, 53)
    pygame.draw.rect(surface, (37, 31, 41), header)
    pygame.draw.line(surface, accent, (inner.x + 4, header.bottom), (inner.right - 4, header.bottom), 1)
    pygame.draw.rect(surface, accent, rect, 2)
    pygame.draw.rect(surface, (72, 61, 75), rect.inflate(-10, -10), 1)
    for x, dx in ((rect.left + 4, 1), (rect.right - 5, -1)):
        for y, dy in ((rect.top + 4, 1), (rect.bottom - 5, -1)):
            pygame.draw.line(surface, accent, (x, y), (x + 18 * dx, y), 2)
            pygame.draw.line(surface, accent, (x, y), (x, y + 18 * dy), 2)
            pygame.draw.rect(surface, (255, 220, 120), (x - 1, y - 1, 3, 3))


def draw_workbench(surface, rect, title, subtitle, accent):
    """Draw the common stone-and-brass shell of a service screen."""
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((5, 5, 9, 220))
    surface.blit(overlay, (0, 0))
    shadow = pygame.Surface((rect.w + 20, rect.h + 20), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 130))
    surface.blit(shadow, (rect.x + 8, rect.y + 9))
    draw_pixel_frame(surface, rect, accent)
    pygame.draw.rect(surface, (29, 26, 29), (rect.x + 8, rect.y + 8, rect.w - 16, 75))
    pygame.draw.line(surface, accent, (rect.x + 26, rect.y + 83), (rect.right - 26, rect.y + 83))
    name = get_pixel_font(25).render(title, True, (239, 221, 191))
    caption = get_pixel_font(13, False).render(subtitle, True, (169, 153, 139))
    surface.blit(name, (rect.x + 30, rect.y + 19))
    surface.blit(caption, (rect.x + 31, rect.y + 51))


def service_label(surface, text, pos, color=(208, 193, 172), size=15, bold=True):
    surface.blit(_service_text(str(text), tuple(color), size, bold), pos)


@lru_cache(maxsize=96)
def _forge_skin(filename, width, height, tint):
    """Build a nine-slice surface from Kenney's CC0 pixel UI sprites."""
    from src.utils import load_image
    src = load_image('assets/sprites/ui_kenney/' + filename).copy()
    src.fill((*tint, 255), special_flags=pygame.BLEND_RGBA_MULT)
    out = pygame.Surface((width, height), pygame.SRCALPHA)
    edge = 16
    dx = min(edge, width // 2)
    dy = min(edge, height // 2)
    sx = (0, edge, 32)
    sy = (0, edge, 32)
    widths = (dx, width - 2 * dx, dx)
    heights = (dy, height - 2 * dy, dy)
    xs = (0, dx, width - dx)
    ys = (0, dy, height - dy)
    for row in range(3):
        for col in range(3):
            if widths[col] and heights[row]:
                part = src.subsurface((sx[col], sy[row], edge, edge))
                out.blit(pygame.transform.scale(part, (widths[col], heights[row])), (xs[col], ys[row]))
    return out

class UI:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.font = get_pixel_font(12, bold=True)
        self.font_lg = get_pixel_font(18, bold=True)
        self.font_sm = get_pixel_font(10, bold=True)
        self.ui_scale = 1.0
        self.show_debug = False
        self.skill_plus_rects = {}
        self.skill_tree_open_rect = None
        self.skill_tree_panel_rect = None
        self.skill_tree_close_rect = None
        self.skill_tree_node_rects = {}
        self.skill_tree_feedback = ""
        self.skill_tree_feedback_time = 0
        self._skill_tree_text_cache = {}

    def _skill_tree_text(self, text, size, color, bold=True):
        key = (text, size, color, bold)
        surf = self._skill_tree_text_cache.get(key)
        if surf is None:
            surf = get_pixel_font(size, bold=bold).render(text, True, color)
            self._skill_tree_text_cache[key] = surf
        return surf

    def handle_skill_tree_click(self, pos, player):
        for skill_id, rect in self.skill_tree_node_rects.items():
            if not rect.collidepoint(pos):
                continue
            dash_level = player.skills.get('dash', {}).get('level', 1)
            if skill_id in ('shield', 'ult') and dash_level < 2:
                self.skill_tree_feedback = "Сначала вложи очко в РЫВОК до II ранга."
            elif getattr(player, 'skill_points', 0) <= 0:
                self.skill_tree_feedback = "Очки сохраняются. Получи следующий уровень."
            else:
                ok, message = player.upgrade_skill(skill_id)
                self.skill_tree_feedback = message if ok else message
            self.skill_tree_feedback_time = pygame.time.get_ticks()
            return True
        return False

    def draw_skill_tree(self, surface, player):
        sw, sh = surface.get_size()
        now = pygame.time.get_ticks()
        shade = pygame.Surface((sw, sh), pygame.SRCALPHA)
        shade.fill((5, 4, 9, 205))
        surface.blit(shade, (0, 0))

        panel_w, panel_h = min(960, sw - 32), min(570, sh - 32)
        panel = pygame.Rect((sw - panel_w) // 2, (sh - panel_h) // 2, panel_w, panel_h)
        self.skill_tree_panel_rect = panel
        pygame.draw.rect(surface, (14, 12, 19), panel)
        pygame.draw.rect(surface, (45, 37, 48), panel.inflate(-6, -6))
        pygame.draw.rect(surface, (184, 137, 61), panel, 2)
        pygame.draw.rect(surface, (82, 66, 62), panel.inflate(-8, -8), 1)
        for x, y in ((panel.left, panel.top), (panel.right - 8, panel.top),
                     (panel.left, panel.bottom - 8), (panel.right - 8, panel.bottom - 8)):
            pygame.draw.rect(surface, (238, 190, 72), (x, y, 8, 8))

        title = self._skill_tree_text("ДЕРЕВО НАВЫКОВ", 21, (255, 219, 113))
        surface.blit(title, (panel.left + 24, panel.top + 17))
        points = int(getattr(player, 'skill_points', 0))
        points_surf = self._skill_tree_text(f"СВОБОДНЫЕ ОЧКИ  {points}", 14,
                                            (255, 218, 99) if points else (166, 156, 151))
        surface.blit(points_surf, (panel.right - points_surf.get_width() - 58, panel.top + 22))
        self.skill_tree_close_rect = pygame.Rect(panel.right - 42, panel.top + 13, 28, 28)
        pygame.draw.rect(surface, (34, 27, 34), self.skill_tree_close_rect)
        pygame.draw.rect(surface, (168, 127, 68), self.skill_tree_close_rect, 1)
        close_surf = self._skill_tree_text("X", 15, (243, 213, 157))
        surface.blit(close_surf, (self.skill_tree_close_rect.centerx - close_surf.get_width() // 2,
                                  self.skill_tree_close_rect.centery - close_surf.get_height() // 2))
        pygame.draw.line(surface, (92, 72, 59), (panel.left + 22, panel.top + 57),
                         (panel.right - 22, panel.top + 57), 1)

        skills = getattr(player, 'skills', {})
        dash = skills.get('dash', {})
        shield = skills.get('shield', {})
        ult = skills.get('ult', {})
        dash_lvl = int(dash.get('level', 1))
        dash_max = int(dash.get('max', 3))
        shield_lvl = int(shield.get('level', 0))
        ult_lvl = int(ult.get('level', 0))
        unlocked = {'dash': True, 'shield': dash_lvl >= 2, 'ult': dash_lvl >= 2}

        compact = panel.height < 500
        root_w = min(360, panel.width - 48)
        node_w = max(150, (panel.width - 72) // 2)
        branch_offset = 215 if compact else 285
        node_h = min(150, panel.height - branch_offset - 84)
        root_h = 138 if compact else 150
        root_y = panel.top + (58 if compact else 70)
        root = pygame.Rect(panel.centerx - root_w // 2, root_y, root_w, root_h)
        branch_y = panel.top + branch_offset
        self.skill_tree_node_rects = {
            'dash': root,
            'shield': pygame.Rect(panel.left + 24, branch_y, node_w, node_h),
            'ult': pygame.Rect(panel.right - 24 - node_w, branch_y, node_w, node_h),
        }

        # Branch rails join at the second Dash rank; either branch can be levelled independently.
        rail = (193, 149, 72) if dash_lvl >= 2 else (77, 66, 57)
        root_bottom = root.bottom
        pygame.draw.line(surface, rail, (root.centerx, root_bottom), (root.centerx, branch_y - 18), 2)
        for branch_id in ('shield', 'ult'):
            node_rect = self.skill_tree_node_rects[branch_id]
            pygame.draw.line(surface, rail, (root.centerx, branch_y - 18),
                             (node_rect.centerx, branch_y), 2)
        pygame.draw.rect(surface, (235, 192, 91), (root.centerx - 3, branch_y - 21, 6, 6))

        definitions = {
            'dash': ('РЫВОК  /  МОБИЛЬНОСТЬ', 'assets/sprites/skill_dash.png', [
                'I    15 EN   •   откат 0.8 с', 'II   12 EN   •   откат 0.65 с', 'III   9 EN   •   откат 0.5 с']),
            'shield': ('БАРЬЕР  /  ЗАЩИТА', 'assets/sprites/skill_shield.png', [
                'I    3.0 с   •   откат 8.0 с   •   25 EN',
                'II   3.5 с   •   откат 6.5 с   •   21 EN',
                'III  4.0 с   •   откат 5.0 с   •   17 EN']),
            'ult': ('ВЗРЫВ БЕЗДНЫ  /  АТАКА', 'assets/sprites/skill_ult.png', [
                'I    ×2.5 урон   •   откат 15 с   •   45 EN',
                'II   ×3.5 урон   •   откат 12 с   •   40 EN',
                'III  ×4.5 урон   •   откат 9 с    •   35 EN']),
        }
        levels = {'dash': (dash_lvl, dash_max), 'shield': (shield_lvl, 3), 'ult': (ult_lvl, 3)}
        accents = {'dash': (120, 210, 235), 'shield': (80, 185, 240), 'ult': (197, 104, 247)}
        self.skill_tree_node_rects = {
            key: pygame.Rect(rect) for key, rect in self.skill_tree_node_rects.items()
        }
        mouse_pos = pygame.mouse.get_pos()
        for skill_id, rect in self.skill_tree_node_rects.items():
            lvl, maximum = levels[skill_id]
            is_unlocked = unlocked[skill_id]
            can_upgrade = is_unlocked and lvl < maximum and points > 0
            accent = (243, 196, 84) if can_upgrade else (accents[skill_id] if is_unlocked else (91, 82, 85))
            fill = (27, 23, 33) if is_unlocked else (20, 18, 25)
            pygame.draw.rect(surface, fill, rect)
            pygame.draw.rect(surface, (accent[0], accent[1], accent[2], 55), rect.inflate(8, 8), 1)
            pygame.draw.rect(surface, accent, rect, 2 if rect.collidepoint(mouse_pos) else 1)

            title_text, icon_path, rank_rows = definitions[skill_id]
            try:
                from src.utils import load_image
                icon = load_image(icon_path, scale=(40, 40))
                surface.blit(icon, (rect.x + 12, rect.y + 14))
            except Exception:
                pass
            text_x = rect.x + 62
            title_surf = self._skill_tree_text(title_text, 12, (242, 223, 193) if is_unlocked else (145, 137, 140))
            surface.blit(title_surf, (text_x, rect.y + 15))
            level_surf = self._skill_tree_text(f"РАНГ  {lvl} / {maximum}", 11, accent)
            surface.blit(level_surf, (text_x, rect.y + 38))
            pygame.draw.line(surface, (65, 56, 63), (rect.x + 12, rect.y + 57),
                             (rect.right - 12, rect.y + 57), 1)
            for rank_index, rank_text in enumerate(rank_rows):
                rank = rank_index + 1
                rank_color = (255, 222, 130) if rank == lvl else (
                    (167, 158, 162) if rank < lvl else (130, 123, 132))
                if not is_unlocked:
                    rank_color = (112, 107, 116)
                row_size = 10 if rect.width >= 340 else 8
                row_surf = self._skill_tree_text(rank_text, row_size, rank_color)
                surface.blit(row_surf, (rect.x + 12, rect.y + 62 + rank_index * 16))

            if not is_unlocked:
                action = "ЗАКРЫТО  •  НУЖЕН РЫВОК II"
                action_color = (150, 139, 130)
            elif lvl >= maximum:
                action = "МАКСИМАЛЬНЫЙ РАНГ"
                action_color = (177, 166, 145)
            elif points:
                action = "ВЛОЖИТЬ 1 ОЧКО"
                action_color = (255, 219, 113)
            else:
                action = "НЕТ ОЧКОВ  •  ОЧКИ СОХРАНЯЮТСЯ"
                action_color = (164, 154, 151)
            action_y = min(rect.y + 118, rect.bottom - 27)
            action_rect = pygame.Rect(rect.x + 10, action_y, rect.width - 20, 20)
            pygame.draw.rect(surface, (35, 29, 36), action_rect)
            pygame.draw.rect(surface, accent if can_upgrade else (91, 80, 76), action_rect, 1)
            action_surf = self._skill_tree_text(action, 10 if rect.width >= 340 else 8, action_color)
            surface.blit(action_surf, (action_rect.centerx - action_surf.get_width() // 2,
                                       action_rect.centery - action_surf.get_height() // 2))

        footer = "Обе ветви независимы. Очки остаются у тебя, пока не выберешь улучшение."
        if now - self.skill_tree_feedback_time < 2400:
            footer = self.skill_tree_feedback
        footer_surf = self._skill_tree_text(footer, 10 if panel.width >= 800 else 8, (214, 201, 177))
        surface.blit(footer_surf, (panel.centerx - footer_surf.get_width() // 2, panel.bottom - 43))
        hint = self._skill_tree_text("[ N ] / [ ESC ]  ЗАКРЫТЬ", 10, (150, 139, 130))
        surface.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 23))

    def handle_skill_click(self, pos, player):
        if hasattr(self, 'skill_plus_rects'):
            for sk_id, r in self.skill_plus_rects.items():
                if r.collidepoint(pos):
                    if hasattr(player, 'upgrade_skill'):
                        player.upgrade_skill(sk_id)
                        return True
        return False

    def get_font_scaled(self, base_size, bold=True):
        scaled_size = max(8, int(round(base_size * getattr(self, 'ui_scale', 1.0))))
        return get_pixel_font(scaled_size, bold=bold)

    def draw_bar(self, current, max_val, x, y, w, h, color, lag_val=None, label=""):
        s = self.ui_scale
        # Carved deep obsidian base with outer shadow
        pygame.draw.rect(self.display_surface, (10, 8, 14), (x - 2, y - 2, w + 4, h + 4))
        pygame.draw.rect(self.display_surface, (24, 22, 32), (x, y, w, h))

        # AAA Damage Burn Buffer (Visceral trailing chunk like Dark Souls / Hades)
        if lag_val is not None and lag_val > current and max_val > 0:
            lag_ratio = max(0.0, min(1.0, lag_val / max_val))
            burn_w = int(w * lag_ratio)
            if burn_w > 0:
                pygame.draw.rect(self.display_surface, (255, 205, 75), (x, y, burn_w, h))
                pygame.draw.rect(self.display_surface, (255, 255, 240), (x, y, burn_w, max(2, int(h * 0.35))))
                pygame.draw.rect(self.display_surface, (220, 125, 25), (x, y + h - max(2, int(2 * s)), burn_w, max(2, int(2 * s))))

        # Value bar with 3D gradient highlight
        if max_val > 0:
            ratio = max(0.0, min(1.0, current / max_val))
            fill_w = int(w * ratio)
            if fill_w > 0:
                pygame.draw.rect(self.display_surface, color, (x, y, fill_w, h))
                # Gloss highlight on top half
                hi_color = (min(255, color[0] + 65), min(255, color[1] + 65), min(255, color[2] + 65))
                pygame.draw.rect(self.display_surface, hi_color, (x, y, fill_w, max(2, int(h * 0.35))))
                # Dark shadow on bottom edge
                low_color = (max(0, color[0] - 50), max(0, color[1] - 50), max(0, color[2] - 50))
                pygame.draw.rect(self.display_surface, low_color, (x, y + h - max(2, int(2 * s)), fill_w, max(2, int(2 * s))))

        # Ornate beveled metallic border & corner notch
        pygame.draw.rect(self.display_surface, (185, 165, 115), (x - 1, y - 1, w + 2, h + 2), max(1, int(1.5 * s)))
        pygame.draw.rect(self.display_surface, (70, 60, 45), (x - 2, y - 2, w + 4, h + 4), 1)

        # Tactical Notch ticks at 25%, 50%, 75%
        for pct in (0.25, 0.5, 0.75):
            nx = x + int(w * pct)
            pygame.draw.line(self.display_surface, (15, 12, 20), (nx, y + 1), (nx, y + h - 2), 1)

        # Exact numeric text with drop shadow inside bar
        num_str = f"{label} {int(current)}/{int(max_val)}".strip()
        num_font = self.get_font_scaled(10)
        if num_font.get_height() > h - 2:
            num_font = get_pixel_font(max(7, h - 3), bold=True)
        num_surf = num_font.render(num_str, True, (255, 255, 255))
        num_shadow = num_font.render(num_str, True, (10, 10, 15))
        tx = x + (w - num_surf.get_width()) // 2
        ty = y + (h - num_surf.get_height()) // 2
        self.display_surface.blit(num_shadow, (tx + 1, ty + 1))
        self.display_surface.blit(num_surf, (tx, ty))

    def draw(self, player, level=None):
        s = self.ui_scale
        screen_w, screen_h = self.display_surface.get_size()
        mouse_pos = pygame.mouse.get_pos()
        now = pygame.time.get_ticks()

        # Low HP Panic Blood-Red Vignette Pulsing Screen Border (<28% HP)
        if getattr(player, 'low_hp_active', False) and not getattr(player, 'is_dead', False):
            hp_ratio = player.health / float(max(1, getattr(player, 'max_health', 100)))
            pulse_speed = 0.007 + (0.28 - max(0.0, hp_ratio)) * 0.02
            pulse = 0.5 + 0.5 * math.sin(now * pulse_speed)
            base_alpha = int(90 + pulse * 115)
            v_thick = int(min(screen_w, screen_h) * 0.16)
            v_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            steps = 8
            for st in range(steps):
                step_frac = (steps - st) / float(steps)
                step_alpha = int(base_alpha * (step_frac ** 1.6))
                inset = int(v_thick * (st / float(steps)))
                col = (185, 12, 22, max(0, min(255, step_alpha)))
                b_rect = pygame.Rect(inset, inset, screen_w - inset * 2, screen_h - inset * 2)
                pygame.draw.rect(v_surf, col, b_rect, max(1, v_thick // steps + 1))
            self.display_surface.blit(v_surf, (0, 0))

        # 1. Floor Plaque (Top Left Gothic Plaque)
        current_floor = getattr(level, 'current_floor', getattr(player, 'current_floor', 1))
        floor_font = getattr(self, 'font_md', self.font)
        floor_txt = f"ЭТАЖ {current_floor}"
        f_surf = floor_font.render(floor_txt, True, (255, 220, 80))
        f_shadow = floor_font.render(floor_txt, True, (15, 12, 20))
        bw = f_surf.get_width() + int(24 * s)
        bh = f_surf.get_height() + int(12 * s)
        bx, by = int(18 * s), int(16 * s)
        self.floor_plaque_rect = (bx, by, bw, bh)

        # Plaque background
        plaque_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        plaque_surf.fill((16, 14, 22, 235))
        self.display_surface.blit(plaque_surf, (bx, by))
        pygame.draw.rect(self.display_surface, (160, 135, 60), (bx, by, bw, bh), max(1, int(1.5 * s)))
        pygame.draw.rect(self.display_surface, (35, 30, 45), (bx + 2, by + 2, bw - 4, bh - 4), 1)
        # 4 Corner rivets
        for cr_x, cr_y in [(bx, by), (bx + bw - 3, by), (bx, by + bh - 3), (bx + bw - 3, by + bh - 3)]:
            pygame.draw.rect(self.display_surface, (230, 190, 50), (cr_x, cr_y, 3, 3))
        self.display_surface.blit(f_shadow, (bx + (bw - f_surf.get_width()) // 2 + 1, by + (bh - f_surf.get_height()) // 2 + 1))
        self.display_surface.blit(f_surf, (bx + (bw - f_surf.get_width()) // 2, by + (bh - f_surf.get_height()) // 2))

        # 2. Bottom-Right Framed RPG Status HUD Panel
        panel_w = max(195, int(230 * s))
        panel_h = max(92, int(102 * s))
        panel_x = screen_w - panel_w - int(20 * s)
        panel_y = screen_h - panel_h - int(16 * s)

        # Panel Background and Double Border
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((18, 16, 26, 235))
        self.display_surface.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.display_surface, (150, 140, 110), (panel_x, panel_y, panel_w, panel_h), max(1, int(2 * s)))
        pygame.draw.rect(self.display_surface, (45, 42, 55), (panel_x + 3, panel_y + 3, panel_w - 6, panel_h - 6), 1)

        # Corner gold brackets
        cw = int(6 * s)
        for cx, cy in [(panel_x, panel_y), (panel_x + panel_w - cw, panel_y),
                       (panel_x, panel_y + panel_h - cw), (panel_x + panel_w - cw, panel_y + panel_h - cw)]:
            pygame.draw.rect(self.display_surface, (235, 195, 50), (cx, cy, cw, cw))

        # Stats Header Row: LVL | XP | GOLD
        stats_y = panel_y + int(8 * s)
        
        # Level Badge
        lvl_font = self.get_font_scaled(10)
        lvl_str = f"LV {player.level}"
        lvl_surf = lvl_font.render(lvl_str, True, (255, 255, 255))
        lvl_bg_w = lvl_surf.get_width() + max(4, int(8 * s))
        lvl_bg_h = max(14, int(18 * s))
        lvl_x = panel_x + int(8 * s)
        pygame.draw.rect(self.display_surface, (40, 48, 70), (lvl_x, stats_y, lvl_bg_w, lvl_bg_h))
        pygame.draw.rect(self.display_surface, (100, 130, 180), (lvl_x, stats_y, lvl_bg_w, lvl_bg_h), 1)
        self.display_surface.blit(lvl_surf, (lvl_x + max(2, int(4 * s)), stats_y + (lvl_bg_h - lvl_surf.get_height()) // 2))

        # XP Counter
        xp_needed = player.level * 100
        xp_str = f"XP:{player.exp}/{xp_needed}"
        xp_surf = lvl_font.render(xp_str, True, (190, 200, 220))
        xp_x = lvl_x + lvl_bg_w + max(4, int(6 * s))
        self.display_surface.blit(xp_surf, (xp_x, stats_y + int(2 * s)))

        # Gold Counter - guaranteed non-overlapping
        gold_str = f"G:{player.gold}"
        gold_surf = lvl_font.render(gold_str, True, (255, 215, 50))
        gold_x = max(xp_x + xp_surf.get_width() + 6, panel_x + panel_w - gold_surf.get_width() - int(8 * s))
        self.display_surface.blit(gold_surf, (gold_x, stats_y + int(2 * s)))

        # Golden XP Progress Bar
        xp_ratio = max(0.0, min(1.0, player.exp / max(1, xp_needed)))
        xp_bar_w = panel_w - int(20 * s)
        xp_bar_h = max(3, int(4 * s))
        xp_bar_x = panel_x + int(10 * s)
        xp_bar_y = stats_y + int(20 * s)
        pygame.draw.rect(self.display_surface, (24, 20, 16), (xp_bar_x, xp_bar_y, xp_bar_w, xp_bar_h))
        pygame.draw.rect(self.display_surface, (255, 205, 45), (xp_bar_x, xp_bar_y, int(xp_bar_w * xp_ratio), xp_bar_h))
        pygame.draw.rect(self.display_surface, (120, 100, 40), (xp_bar_x - 1, xp_bar_y - 1, xp_bar_w + 2, xp_bar_h + 2), 1)

        # HP Bar
        bar_w = panel_w - int(20 * s)
        bar_h = int(18 * s)
        hp_x = panel_x + int(10 * s)
        hp_y = xp_bar_y + xp_bar_h + int(6 * s)

        # AAA Damage Burn Buffer (250ms hold, then smooth exponential drain)
        if not hasattr(player, 'burn_health') or not hasattr(player, 'last_health'):
            player.burn_health = float(player.health)
            player.last_health = float(player.health)
            player.burn_hold_until = 0

        if player.health < player.last_health:
            player.burn_hold_until = now + 250
            player.last_health = float(player.health)
        elif player.health > player.last_health:
            player.burn_health = float(player.health)
            player.last_health = float(player.health)

        if now >= getattr(player, 'burn_hold_until', 0):
            if player.burn_health > player.health:
                drain = max(0.4, (player.burn_health - player.health) * 0.12)
                player.burn_health = max(float(player.health), player.burn_health - drain)
            else:
                player.burn_health = float(player.health)

        player.display_health = player.burn_health
        self.draw_bar(player.health, player.stats['health'], hp_x, hp_y, bar_w, bar_h, (220, 35, 45), lag_val=player.burn_health, label="HP")

        # Energy Bar
        en_y = hp_y + bar_h + int(8 * s)
        en_h = int(16 * s)
        self.draw_bar(player.energy, player.stats['energy'], hp_x, en_y, bar_w, en_h, (45, 135, 245), label="MP")

        # 3. Bottom-Left Skills UI
        from src.utils import load_image
        potion_count = sum(1 for item in player.inventory if hasattr(item, 'effects') and 'heal' in item.effects or 'potion' in getattr(item, 'name', '').lower())
        
        dash_sk = getattr(player, 'skills', {}).get('dash', {'level': 1, 'max': 3})
        shield_sk = getattr(player, 'skills', {}).get('shield', {'level': 0, 'max': 3})
        ult_sk = getattr(player, 'skills', {}).get('ult', {'level': 0, 'max': 3})
        
        dash_lvl = dash_sk.get('level', 1)
        shield_lvl = shield_sk.get('level', 0)
        ult_lvl = ult_sk.get('level', 0)

        dash_cost = getattr(player, 'dash_energy_cost', 15)
        dash_cd_rem = max(0, player.dash_cooldown - (now - player.dash_time)) if not player.can_dash else 0
        dash_ready = player.can_dash and player.energy >= dash_cost
        
        shield_active = getattr(player, 'is_shielded', False)
        shield_locked = shield_lvl == 0
        shield_cost = getattr(player, 'shield_energy_cost', 25)
        shield_cd_rem = max(0, player.shield_cooldown - (now - getattr(player, 'shield_time', 0))) if not getattr(player, 'can_shield', True) else 0
        shield_ready = not shield_locked and getattr(player, 'can_shield', True) and not shield_active and player.energy >= shield_cost

        ult_locked = ult_lvl == 0
        ult_cost = getattr(player, 'ult_energy_cost', 45)
        ult_cd_rem = max(0, player.ult_cooldown - (now - getattr(player, 'ult_time', 0))) if not getattr(player, 'can_ult', True) else 0
        ult_ready = not ult_locked and getattr(player, 'can_ult', True) and player.energy >= ult_cost

        potion_ready = potion_count > 0 and player.health < player.stats['health']

        shield_lock_txt = None
        if shield_locked:
            shield_lock_txt = "ТРЕБ. РЫВ. 2" if dash_lvl < 2 else "ИЗУЧИ ВЕТКУ"

        ult_lock_txt = None
        if ult_locked:
            ult_lock_txt = "ТРЕБ. РЫВ. 2" if dash_lvl < 2 else "ИЗУЧИ ВЕТКУ"

        skill_deck = [
            ("Z", "DASH", f"{dash_cost} EN", dash_cd_rem, player.dash_cooldown, dash_ready, False, None, 'assets/sprites/skill_dash.png', (80, 220, 120),
             f"Стремительный рывок со шлейфом пламени.\nУровень: {dash_lvl}/3 | Энергия: {dash_cost} | КД: {player.dash_cooldown/1000.0:.1f}с", 'dash', dash_lvl, 3, dash_lvl < 3),
            ("X", "SHIELD", f"{shield_cost} EN", shield_cd_rem, player.shield_cooldown, shield_ready, shield_active, shield_lock_txt, 'assets/sprites/skill_shield.png', (60, 180, 255),
             f"Энергетический щит, поглощающий весь урон.\nУровень: {shield_lvl}/3 | Энергия: {shield_cost} | КД: {player.shield_cooldown/1000.0:.1f}с", 'shield', shield_lvl, 3, dash_lvl >= 2 and shield_lvl < 3),
            ("C", "VOID BLAST", f"{ult_cost} EN", ult_cd_rem, player.ult_cooldown, ult_ready, False, ult_lock_txt, 'assets/sprites/skill_ult.png', (210, 70, 255),
             f"Сокрушительная волна Бездны.\nУровень: {ult_lvl}/3 | Энергия: {ult_cost} | КД: {player.ult_cooldown/1000.0:.1f}с", 'ult', ult_lvl, 3, dash_lvl >= 2 and ult_lvl < 3),
            ("Q", "POTION", f"x{potion_count}", 0, 1, potion_ready, False, "ПУСТО" if potion_count == 0 else None, 'assets/sprites/skill_potion.png', (255, 80, 90),
             "Мгновенно восстанавливает здоровье.\nКлавиша Q или 1.", 'potion', None, None, False)
        ]

        card_size = max(44, int(54 * s))
        card_gap = max(4, int(12 * s))
        deck_x = int(20 * s)
        deck_y = screen_h - card_size - int(18 * s)
        hovered_skill_desc = None

        self.skill_plus_rects = {}
        sp_avail = getattr(player, 'skill_points', 0)
        sp_banner = f"ДЕРЕВО НАВЫКОВ [N]  •  ОЧКИ: {sp_avail}"
        sp_font = self.get_font_scaled(11, bold=True)
        sp_color = (255, 220, 80) if sp_avail else (190, 180, 177)
        sp_surf = sp_font.render(sp_banner, True, sp_color)
        sp_rect = pygame.Rect(deck_x, deck_y - int(38 * s), sp_surf.get_width() + 16, sp_surf.get_height() + 6)
        self.skill_tree_open_rect = sp_rect
        sp_bg = pygame.Surface(sp_rect.size, pygame.SRCALPHA)
        sp_bg.fill((20, 16, 26, 230))
        self.display_surface.blit(sp_bg, sp_rect.topleft)
        pygame.draw.rect(self.display_surface, (255, 200, 60) if sp_avail else (105, 96, 93), sp_rect, 1)
        self.display_surface.blit(sp_surf, (deck_x + 8, deck_y - int(35 * s)))

        for idx, item_data in enumerate(skill_deck):
            key, name, cost_lbl, cd_rem, cd_tot, is_ready, is_act, lock_txt, icon_path, glow_col, desc, sk_id, sk_l, sk_m, can_up = item_data
            cx = deck_x + idx * (card_size + card_gap)
            card_rect = pygame.Rect(cx, deck_y, card_size, card_size)

            # Ambient Soft Glow for Ready Skills
            if is_ready:
                glow_surf = pygame.Surface((card_size + 8, card_size + 8), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*glow_col, 55), [0, 0, card_size + 8, card_size + 8], border_radius=4)
                self.display_surface.blit(glow_surf, (cx - 4, deck_y - 4))

            # Base Card Frame (Carved Obsidian with Beveled Inner Plate)
            pygame.draw.rect(self.display_surface, (12, 10, 16), card_rect)
            pygame.draw.rect(self.display_surface, (28, 25, 36), (cx + 2, deck_y + 2, card_size - 4, card_size - 4))

            # 4 Corner Studs
            stud_col = (195, 170, 75) if is_ready else (70, 68, 80)
            for stx, sty in [(cx + 2, deck_y + 2), (cx + card_size - 4, deck_y + 2),
                             (cx + 2, deck_y + card_size - 4), (cx + card_size - 4, deck_y + card_size - 4)]:
                pygame.draw.rect(self.display_surface, stud_col, (stx, sty, 2, 2))

            # Icon
            try:
                icon_img = load_image(icon_path, scale=(int(34 * s), int(34 * s)))
                self.display_surface.blit(icon_img, (cx + (card_size - icon_img.get_width()) // 2, deck_y + (card_size - icon_img.get_height()) // 2))
            except Exception:
                pass

            # Cooldown Sweep Overlay
            if cd_rem > 0 and cd_tot > 0:
                ratio = max(0.0, min(1.0, cd_rem / cd_tot))
                sweep_h = int(card_size * ratio)
                sweep_surf = pygame.Surface((card_size, sweep_h), pygame.SRCALPHA)
                sweep_surf.fill((10, 8, 16, 215))
                self.display_surface.blit(sweep_surf, (cx, deck_y + (card_size - sweep_h)))

                sec_str = f"{cd_rem / 1000.0:.1f}s"
                sec_surf = self.font_sm.render(sec_str, True, (255, 255, 255))
                sec_shadow = self.font_sm.render(sec_str, True, (0, 0, 0))
                stx = cx + (card_size - sec_surf.get_width()) // 2
                sty = deck_y + (card_size - sec_surf.get_height()) // 2
                self.display_surface.blit(sec_shadow, (stx + 1, sty + 1))
                self.display_surface.blit(sec_surf, (stx, sty))

            # Lock Overlay with Golden Medieval Padlock
            if lock_txt:
                lock_surf = pygame.Surface((card_size, card_size), pygame.SRCALPHA)
                lock_surf.fill((10, 8, 16, 225))
                self.display_surface.blit(lock_surf, (cx, deck_y))
                try:
                    lock_img = load_image('assets/sprites/icon_lock.png', scale=(int(22 * s), int(22 * s)))
                    self.display_surface.blit(lock_img, (cx + (card_size - lock_img.get_width()) // 2, deck_y + int(7 * s)))
                except Exception:
                    pass
                lt_surf = self.font_sm.render(lock_txt, True, (255, 215, 60))
                self.display_surface.blit(lt_surf, (cx + (card_size - lt_surf.get_width()) // 2, deck_y + int(33 * s)))

            # Border State
            if is_act:
                b_pulse = max(0, min(255, 180 + int(70 * math.sin(now * 0.015))))
                pygame.draw.rect(self.display_surface, (60, b_pulse, 255), card_rect, max(1, int(2.5 * s)))
            elif is_ready:
                pygame.draw.rect(self.display_surface, glow_col, card_rect, max(1, int(2 * s)))
            else:
                pygame.draw.rect(self.display_surface, (65, 68, 80), card_rect, max(1, int(1.5 * s)))

            # Keybind Pill Badge [Z] (Tactile 3D button)
            key_surf = self.font_sm.render(key, True, (255, 245, 180) if is_ready else (180, 180, 195))
            pill_w = max(18, key_surf.get_width() + 6)
            pill_h = 16
            pygame.draw.rect(self.display_surface, (10, 8, 14), (cx + 3, deck_y + 3, pill_w, pill_h))
            pygame.draw.rect(self.display_surface, (215, 175, 50) if is_ready else (85, 80, 100), (cx + 3, deck_y + 3, pill_w, pill_h), 1)
            self.display_surface.blit(key_surf, (cx + 3 + (pill_w - key_surf.get_width()) // 2, deck_y + 3 + (pill_h - key_surf.get_height()) // 2))

            # Cost Badge (Bottom-Right)
            cost_surf = self.font_sm.render(cost_lbl, True, (255, 230, 120) if is_ready else (160, 160, 175))
            cp_w = cost_surf.get_width() + 6
            cp_h = 15
            c_pos_x = cx + card_size - cp_w - 3
            c_pos_y = deck_y + card_size - cp_h - 3
            pygame.draw.rect(self.display_surface, (12, 10, 16), (c_pos_x, c_pos_y, cp_w, cp_h))
            pygame.draw.rect(self.display_surface, (140, 120, 65) if is_ready else (65, 65, 80), (c_pos_x, c_pos_y, cp_w, cp_h), 1)
            self.display_surface.blit(cost_surf, (c_pos_x + 3, c_pos_y + (cp_h - cost_surf.get_height()) // 2))

            # Hover Check for Skill Tooltip
            if card_rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.display_surface, (255, 255, 255), card_rect, 1)
                hovered_skill_desc = (f"{name} [{key}]", desc, glow_col)

        # 4. Tactical Minimap (Top Right) with Fog of War & POI Icons
        if level and hasattr(level, 'floor_positions') and level.floor_positions:
            map_size = max(90, int(126 * s))
            map_x = screen_w - map_size - max(8, int(15 * s))
            map_y = max(8, int(15 * s))

            map_surf = pygame.Surface((map_size, map_size), pygame.SRCALPHA)
            map_surf.fill((14, 12, 20, 225))
            pygame.draw.rect(map_surf, (85, 90, 115), [0, 0, map_size, map_size], max(1, int(2 * s)))

            floors = level.floor_positions
            visited = getattr(level, 'visited_tiles', set())
            min_x = min(p[0] for p in floors)
            max_x = max(p[0] for p in floors)
            min_y = min(p[1] for p in floors)
            max_y = max(p[1] for p in floors)
            span_x = max(1, max_x - min_x)
            span_y = max(1, max_y - min_y)
            scale = (map_size - 20) / max(span_x, span_y)

            for fx_t, fy_t in floors:
                mx = 10 + int((fx_t - min_x) * scale)
                my = 10 + int((fy_t - min_y) * scale)
                if 0 <= mx < map_size and 0 <= my < map_size:
                    if (fx_t, fy_t) in visited or not visited:
                        map_surf.set_at((mx, my), (85, 95, 125, 255))
                    else:
                        map_surf.set_at((mx, my), (32, 28, 42, 130))

            # Stairs Exit Marker
            if hasattr(level, 'stairs_tile_pos'):
                sx, sy = level.stairs_tile_pos
                if (sx, sy) in visited or getattr(level, 'is_boss_level', False) or not visited:
                    smx = 10 + int((sx - min_x) * scale)
                    smy = 10 + int((sy - min_y) * scale)
                    if 0 <= smx < map_size and 0 <= smy < map_size:
                        pygame.draw.circle(map_surf, (255, 215, 50), (smx, smy), max(2, int(3 * s)))

            # Trader Marker [M] (Gold)
            for t in getattr(level, 'trader_sprites', []):
                tx = int(t.rect.centerx // TILE_SIZE)
                ty = int(t.rect.centery // TILE_SIZE)
                if (tx, ty) in visited or not visited:
                    tmx = 10 + int((tx - min_x) * scale)
                    tmy = 10 + int((ty - min_y) * scale)
                    if 0 <= tmx < map_size and 0 <= tmy < map_size:
                        pygame.draw.circle(map_surf, (255, 215, 60), (tmx, tmy), max(2, int(3.5 * s)))
                        pygame.draw.circle(map_surf, (15, 12, 20), (tmx, tmy), max(1, int(1.5 * s)))

            # Blood Altar Marker [A] (Crimson Circle)
            for altar in getattr(level, 'altar_sprites', []):
                ax = int(altar.rect.centerx // TILE_SIZE)
                ay = int(altar.rect.centery // TILE_SIZE)
                if (ax, ay) in visited or not visited:
                    amx = 10 + int((ax - min_x) * scale)
                    amy = 10 + int((ay - min_y) * scale)
                    if 0 <= amx < map_size and 0 <= amy < map_size:
                        a_col = (255, 30, 50) if not getattr(altar, 'used', False) else (120, 45, 55)
                        pygame.draw.circle(map_surf, a_col, (amx, amy), max(2, int(3.5 * s)))
                        pygame.draw.circle(map_surf, (20, 10, 15), (amx, amy), max(1, int(1.5 * s)))

            # Blacksmith Marker [B] (Orange/Steel)
            for bs in getattr(level, 'blacksmith_sprites', []):
                bx = int(bs.rect.centerx // TILE_SIZE)
                by = int(bs.rect.centery // TILE_SIZE)
                if (bx, by) in visited or not visited:
                    bmx = 10 + int((bx - min_x) * scale)
                    bmy = 10 + int((by - min_y) * scale)
                    if 0 <= bmx < map_size and 0 <= bmy < map_size:
                        pygame.draw.circle(map_surf, (255, 140, 45), (bmx, bmy), max(2, int(3.5 * s)))

            # Boss Marker [Skull/Red] (Crimson)
            if getattr(level, 'is_boss_level', False):
                for e in getattr(level, 'enemy_sprites', []):
                    if getattr(e, 'is_boss', False) and e.alive():
                        ex = int(e.rect.centerx // TILE_SIZE)
                        ey = int(e.rect.centery // TILE_SIZE)
                        emx = 10 + int((ex - min_x) * scale)
                        emy = 10 + int((ey - min_y) * scale)
                        if 0 <= emx < map_size and 0 <= emy < map_size:
                            pygame.draw.circle(map_surf, (255, 50, 70), (emx, emy), max(3, int(4.5 * s)))

            # Player Position (Cyan Dot with pulsing halo)
            px = player.rect.centerx // TILE_SIZE
            py = player.rect.centery // TILE_SIZE
            pmx = 10 + int((px - min_x) * scale)
            pmy = 10 + int((py - min_y) * scale)
            if 0 <= pmx < map_size and 0 <= pmy < map_size:
                halo_r = max(3, int((3.5 + 1.2 * math.sin(now * 0.008)) * s))
                pygame.draw.circle(map_surf, (70, 220, 255, 120), (pmx, pmy), halo_r)
                pygame.draw.circle(map_surf, (120, 245, 255), (pmx, pmy), max(2, int(3 * s)))

            self.display_surface.blit(map_surf, (map_x, map_y))

        # 5. Inventory Display (Top Center) with Stacking, Potions First, and xN Badges
        item_tooltip = None
        self.inv_slot_rects = []
        if hasattr(player, 'inventory') and player.inventory:
            # 1. Sort inventory: Potions ALWAYS first, then by rarity, then by name
            def item_sort_key(it):
                is_pot = 'potion' in getattr(it, 'name', '').lower() or 'heal' in getattr(it, 'effects', {})
                rarity_rank = {'legendary': 0, 'epic': 1, 'rare': 2, 'common': 3}.get(getattr(it, 'rarity', 'common'), 4)
                return (0 if is_pot else 1, rarity_rank, getattr(it, 'name', ''))

            sorted_items = sorted(player.inventory, key=item_sort_key)

            # 2. Stack only items that satisfy the game's actual stack contract.
            stacked_slots = _group_inventory_for_hud(sorted_items)

            # 3. Layout aligned directly below Floor Plaque (Top-Left)
            # Never floats in center void and never overlaps Boss HP Bar!
            inv_slot_size = int(32 * s)
            inv_gap = int(5 * s)
            max_per_row = 6
            num_stacks = len(stacked_slots)
            
            plaque_box = getattr(self, 'floor_plaque_rect', (int(18 * s), int(16 * s), int(110 * s), int(32 * s)))
            start_inv_x = plaque_box[0]
            start_inv_y = plaque_box[1] + plaque_box[3] + int(8 * s)

            for i, (item, count, all_items) in enumerate(stacked_slots):
                row = i // max_per_row
                col = i % max_per_row
                ix = start_inv_x + col * (inv_slot_size + inv_gap)
                iy = start_inv_y + row * (inv_slot_size + inv_gap)
                item_rect = pygame.Rect(ix, iy, inv_slot_size, inv_slot_size)
                self.inv_slot_rects.append((item_rect, item))

                rarity = getattr(item, 'rarity', 'common').lower()
                r_col = RARITY_COLORS.get(rarity, (175, 180, 195))

                # Slot Frame with sunken dark interior and 4 corner rivets
                pygame.draw.rect(self.display_surface, (12, 10, 16), item_rect)
                pygame.draw.rect(self.display_surface, (26, 23, 34), (ix + 2, iy + 2, inv_slot_size - 4, inv_slot_size - 4))
                pygame.draw.rect(self.display_surface, r_col, item_rect, max(1, int(1.5 * s)))
                for cr_x, cr_y in [(ix, iy), (ix + inv_slot_size - 3, iy), (ix, iy + inv_slot_size - 3), (ix + inv_slot_size - 3, iy + inv_slot_size - 3)]:
                    pygame.draw.rect(self.display_surface, r_col, (cr_x, cr_y, 3, 3))

                # Item Icon
                try:
                    if hasattr(item, 'image'):
                        scaled_icon = pygame.transform.scale(item.image, (int(28 * s), int(28 * s)))
                        self.display_surface.blit(scaled_icon, (ix + int(4 * s), iy + int(4 * s)))
                except Exception:
                    pass

                # Stack Count Badge (e.g. x3)
                if count > 1:
                    cnt_str = f"x{count}"
                    cnt_surf = self.font_sm.render(cnt_str, True, (255, 230, 90))
                    cnt_shadow = self.font_sm.render(cnt_str, True, (10, 8, 14))
                    cx_t = ix + inv_slot_size - cnt_surf.get_width() - 2
                    cy_t = iy + inv_slot_size - cnt_surf.get_height() - 2
                    self.display_surface.blit(cnt_shadow, (cx_t + 1, cy_t + 1))
                    self.display_surface.blit(cnt_surf, (cx_t, cy_t))

                # Hover Check
                if item_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(self.display_surface, (255, 255, 255), item_rect, 2)
                    effs = []
                    if hasattr(item, 'effects') and item.effects:
                        for k, v in item.effects.items():
                            effs.append(f"+{v} {k.capitalize()}")
                        buff_text = ", ".join(effs)
                    else:
                        buff_text = "Standard item"
                    if count > 1:
                        buff_text += f" (Кол-во: {count})"
                    item_tooltip = (getattr(item, 'name', 'Item'), rarity.upper(), buff_text, r_col)

        # 6. Render Tooltips (Inventory or Skill)
        if item_tooltip:
            name, r_name, buff_str, border_c = item_tooltip
            title_surf = self.font.render(f"{name} [{r_name}]", True, border_c)
            desc_surf = self.font_sm.render(buff_str, True, (220, 225, 240))
            tw = max(title_surf.get_width(), desc_surf.get_width()) + 20
            th = title_surf.get_height() + desc_surf.get_height() + 16
            tx = mouse_pos[0] + 15
            ty = mouse_pos[1] + 15
            if tx + tw > screen_w: tx = mouse_pos[0] - tw - 10
            if ty + th > screen_h: ty = mouse_pos[1] - th - 10

            tt_bg = pygame.Surface((tw, th), pygame.SRCALPHA)
            tt_bg.fill((16, 14, 24, 240))
            self.display_surface.blit(tt_bg, (tx, ty))
            pygame.draw.rect(self.display_surface, border_c, (tx, ty, tw, th), 2)
            self.display_surface.blit(title_surf, (tx + 10, ty + 8))
            self.display_surface.blit(desc_surf, (tx + 10, ty + 12 + title_surf.get_height()))

        elif hovered_skill_desc:
            s_name, s_desc, border_c = hovered_skill_desc
            lines = [s_name] + s_desc.split('\n')
            surfs = []
            for idx, line in enumerate(lines):
                f = self.font if idx == 0 else self.font_sm
                c = border_c if idx == 0 else (220, 225, 240)
                surfs.append(f.render(line, True, c))
            tw = max(sf.get_width() for sf in surfs) + 20
            th = sum(sf.get_height() + 4 for sf in surfs) + 12
            tx = mouse_pos[0] + 15
            ty = mouse_pos[1] - th - 10
            if tx + tw > screen_w: tx = mouse_pos[0] - tw - 10
            if ty < 10: ty = mouse_pos[1] + 15

            tt_bg = pygame.Surface((tw, th), pygame.SRCALPHA)
            tt_bg.fill((16, 14, 24, 240))
            self.display_surface.blit(tt_bg, (tx, ty))
            pygame.draw.rect(self.display_surface, border_c, (tx, ty, tw, th), 2)
            cur_y = ty + 8
            for sf in surfs:
                self.display_surface.blit(sf, (tx + 10, cur_y))
                cur_y += sf.get_height() + 4

        # 7. Item Pickup Notification Banner
        notif = getattr(level, 'pickup_notification', None)
        if notif and (now - notif.get('time', 0)) < 3500:
            elapsed = now - notif['time']
            alpha = 255 if elapsed < 2800 else int(255 * (1.0 - (elapsed - 2800) / 700.0))
            pw, ph = int(440 * s), int(64 * s)
            px = screen_w // 2 - pw // 2
            py = int(68 * s)

            r_col = RARITY_COLORS.get(notif.get('rarity', 'common'), (180, 185, 200))
            p_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
            p_surf.fill((16, 14, 24, min(240, alpha)))
            pygame.draw.rect(p_surf, r_col, [0, 0, pw, ph], max(1, int(2 * s)))
            self.display_surface.blit(p_surf, (px, py))

            if notif.get('icon'):
                try:
                    icon_img = pygame.transform.scale(notif['icon'], (int(36 * s), int(36 * s)))
                    self.display_surface.blit(icon_img, (px + int(12 * s), py + int(14 * s)))
                except Exception:
                    pass

            name_surf = self.font.render(f"Ты взял: {notif.get('name', 'Item')}", True, r_col)
            desc_surf = self.font_sm.render(notif.get('desc', ''), True, (255, 215, 60))
            self.display_surface.blit(name_surf, (px + int(56 * s), py + int(12 * s)))
            self.display_surface.blit(desc_surf, (px + int(56 * s), py + int(36 * s)))

        # 8. Level Up Grand Celebration Banner
        lvl_time = getattr(player, 'level_up_time', 0)
        if lvl_time > 0 and (now - lvl_time) < 3200:
            elapsed = now - lvl_time
            alpha = 255 if elapsed < 2500 else int(255 * (1.0 - (elapsed - 2500) / 700.0))
            bw, bh = int(490 * s), int(68 * s)
            bx = screen_w // 2 - bw // 2
            by = int(140 * s)
            b_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
            b_surf.fill((18, 14, 26, min(240, alpha)))
            pygame.draw.rect(b_surf, (255, 215, 60, alpha), [0, 0, bw, bh], max(1, int(2 * s)))
            for cx_b, cy_b in [(0, 0), (bw - 6, 0), (0, bh - 6), (bw - 6, bh - 6)]:
                pygame.draw.rect(b_surf, (255, 235, 100, alpha), [cx_b, cy_b, 6, 6])
            self.display_surface.blit(b_surf, (bx, by))

            t_surf = self.font_lg.render(f"НОВЫЙ УРОВЕНЬ! [LV {player.level}]", True, (255, 220, 60))
            sub_surf = self.font_sm.render("+10 Макс. HP | +2 Атака | Здоровье и Мана восстановлены!", True, (230, 235, 250))
            self.display_surface.blit(t_surf, (bx + (bw - t_surf.get_width()) // 2, by + int(12 * s)))
            self.display_surface.blit(sub_surf, (bx + (bw - sub_surf.get_width()) // 2, by + int(40 * s)))

        # 9. Grand Location Entrance Cinematic Banner
        if level and hasattr(level, 'floor_enter_time'):
            elapsed = now - level.floor_enter_time
            if elapsed < 3900:
                self.draw_location_banner(level, elapsed)

        # 7. Debug Overlay (F3)
        if self.show_debug:
            keys = pygame.key.get_pressed()
            debug_str = "KEYS: "
            if keys[pygame.K_w]: debug_str += "[W] "
            if keys[pygame.K_a]: debug_str += "[A] "
            if keys[pygame.K_s]: debug_str += "[S] "
            if keys[pygame.K_d]: debug_str += "[D] "
            debug_surf = self.font_sm.render(debug_str, True, (0, 255, 0))
            self.display_surface.blit(debug_surf, (screen_w - 300, 150))

            # Pilot Hero Animation & State Telemetry
            if player:
                p_skin = getattr(player, 'current_skin', 'default')
                controller = getattr(player, 'animation_controller', None)
                sample = getattr(controller, 'last_sample', None)
                if sample is not None:
                    p_state = sample.state
                    n_f = max(1, controller.frame_count(p_state))
                    cur_f = sample.frame_index
                else:
                    p_state = 'walk' if getattr(player, 'velocity', pygame.math.Vector2()).magnitude() > 0.2 else 'idle'
                    n_f = max(1, len(getattr(player, 'frames', [])))
                    cur_f = int(getattr(player, 'frame_index', 0)) % n_f
                is_baked = p_skin in ['knight', 'crusader']
                hero_txt = f"HERO: {p_skin} | {p_state} [{cur_f + 1}/{n_f}] | Pivot: center-ground | Weapon: {'baked' if is_baked else 'procedural'}"
                hero_s = self.font_sm.render(hero_txt, True, (255, 215, 60))
                self.display_surface.blit(hero_s, (screen_w - 440, 175))


    def draw_location_banner(self, level, elapsed):
        screen_w, screen_h = self.display_surface.get_size()
        s = self.ui_scale

        # Sound sting on entrance (played once)
        if not getattr(level, 'location_sting_played', False):
            level.location_sting_played = True
            try:
                from src.sound_manager import play_sfx
                play_sfx('stairs' if not getattr(level, 'is_boss_level', False) else 'boss_cleave')
            except Exception:
                pass

        # Smooth alpha envelope: 0..650ms fade-in, 650..2600ms hold, 2600..3900ms fade-out
        if elapsed < 650:
            alpha = int(255 * (elapsed / 650.0))
        elif elapsed < 2600:
            alpha = 255
        else:
            alpha = max(0, int(255 * (1.0 - (elapsed - 2600) / 1300.0)))

        if alpha <= 0:
            return

        # Cinematic Letterbox bars (film effect that smoothly retracts)
        lb_h = max(0, int(34 * (1.0 - min(1.0, elapsed / 1400.0))))
        if lb_h > 0:
            pygame.draw.rect(self.display_surface, (10, 8, 14), (0, 0, screen_w, lb_h))
            pygame.draw.rect(self.display_surface, (10, 8, 14), (0, screen_h - lb_h, screen_w, lb_h))

        # Main Gothic Title Banner Plate
        bw, bh = int(580 * s), int(86 * s)
        bx = (screen_w - bw) // 2
        by = int(88 * s)

        b_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        b_surf.fill((14, 12, 20, min(245, alpha)))

        # Ornate Gold / Ruby borders
        is_boss = getattr(level, 'is_boss_level', False)
        b_col = (255, 75, 85, alpha) if is_boss else (235, 195, 75, alpha)
        rim_col = (180, 30, 45, alpha) if is_boss else (140, 105, 45, alpha)
        pygame.draw.rect(b_surf, b_col, [0, 0, bw, bh], max(1, int(2 * s)))
        pygame.draw.rect(b_surf, rim_col, [int(3 * s), int(3 * s), bw - int(6 * s), bh - int(6 * s)], 1)

        # 4 Corner Runic Studs
        stud_sz = int(7 * s)
        for stx, sty in [(0, 0), (bw - stud_sz, 0), (0, bh - stud_sz), (bw - stud_sz, bh - stud_sz)]:
            pygame.draw.rect(b_surf, (255, 235, 120, alpha), (stx, sty, stud_sz, stud_sz))

        # Center top & bottom runic diamond crest
        cx, cy = bw // 2, 0
        pygame.draw.polygon(b_surf, (255, 220, 85, alpha), [(cx, 0), (cx + 8, 8), (cx, 16), (cx - 8, 8)])
        pygame.draw.polygon(b_surf, (255, 220, 85, alpha), [(cx, bh - 16), (cx + 8, bh - 8), (cx, bh), (cx - 8, bh - 8)])

        self.display_surface.blit(b_surf, (bx, by))

        # Text Content: Chapter Title & Floor Description
        ch_title = getattr(level, 'chapter_title', 'Верхние Катакомбы')
        fl_num = getattr(level, 'current_floor', 1)

        f_title = get_pixel_font(int(17 * s), bold=True)
        f_sub = get_pixel_font(int(12 * s), bold=True)

        if is_boss:
            title_text = "Л О Г О В О   В Л А Д Ы К И"
            sub_text = f"[ ВЛАДЫКА КАТАКОМБ : ЭТАЖ {fl_num} ]"
            t_col = (255, 230, 110)
            sub_col = (255, 90, 100)
        else:
            title_text = ch_title.upper()
            sub_text = f"—  ЭТАЖ {fl_num} : ИССЛЕДОВАНИЕ  —"
            t_col = (255, 225, 95)
            sub_col = (215, 220, 235)

        t_surf = f_title.render(title_text, True, t_col)
        t_shadow = f_title.render(title_text, True, (0, 0, 0))
        s_surf = f_sub.render(sub_text, True, sub_col)
        s_shadow = f_sub.render(sub_text, True, (0, 0, 0))

        tx = bx + (bw - t_surf.get_width()) // 2
        ty = by + int(14 * s)
        sx = bx + (bw - s_surf.get_width()) // 2
        sy = by + int(48 * s)

        # Drop shadow blit
        self.display_surface.blit(t_shadow, (tx + 1, ty + 1))
        self.display_surface.blit(t_surf, (tx, ty))
        self.display_surface.blit(s_shadow, (sx + 1, sy + 1))
        self.display_surface.blit(s_surf, (sx, sy))

        # Decorative heraldic diamonds next to title
        d_col = (255, 215, 60, alpha)
        for d_x in [tx - 20, tx + t_surf.get_width() + 20]:
            d_y = ty + t_surf.get_height() // 2
            pygame.draw.polygon(self.display_surface, d_col, [(d_x, d_y - 6), (d_x + 6, d_y), (d_x, d_y + 6), (d_x - 6, d_y)])



class Button(pygame.sprite.Sprite):
    def __init__(self, text, pos, width, height, callback):
        super().__init__()
        self.text_str = text
        self.base_pos = (pos[0], pos[1])
        self.rect = pygame.Rect(pos[0], pos[1], width, height)
        self.callback = callback
        self.font = get_pixel_font(13, bold=True)
        self.hovered = False
        self.was_hovered = False
        self.offset_x = 0.0
        self.click_offset_y = 0.0
        self.ui_selected = False
        self.ui_style = None
        self.hover_amount = 0.0
        self.last_draw_time = None
        self.pressed_until = 0
        self._label_cache = None

    @property
    def text(self):
        return self.text_str

    def draw(self, surface):
        if self.ui_style:
            now = pygame.time.get_ticks()
            elapsed = 16 if self.last_draw_time is None else min(50, max(0, now - self.last_draw_time))
            self.last_draw_time = now
            target = 1.0 if self.hovered or self.ui_selected else 0.0
            self.hover_amount += (target - self.hover_amount) * min(1.0, elapsed / 110.0)
            if self.ui_selected:
                self.hover_amount = max(.7, self.hover_amount)
            pressed = now < self.pressed_until
            rect = self.rect.move(0, 2 if pressed else 0)
            if self.ui_style in ('forge', 'forge_primary'):
                primary = self.ui_style == 'forge_primary'
                step = int(self.hover_amount * 5)
                tint = (125 + 14 * step, 112 + 12 * step, 112 + 8 * step) if primary else (112 + 12 * step, 103 + 10 * step, 125 + 9 * step)
                asset = ('brown' if primary else 'grey') + ('_pressed.png' if pressed else '.png')
                surface.blit(_forge_skin(asset, rect.w, rect.h, tint), rect)
                label_color = (255, 238, 202) if self.hovered or self.ui_selected else (229, 218, 204)
                cache_key = (self.text_str, rect.width, label_color)
                if not self._label_cache or self._label_cache[0] != cache_key:
                    font_size = 14
                    font = get_pixel_font(font_size, bold=True)
                    while font.size(self.text_str)[0] > rect.width - 20 and font_size > 10:
                        font_size -= 1
                        font = get_pixel_font(font_size, bold=True)
                    self._label_cache = (cache_key, font.render(self.text_str, True, label_color))
                old_clip = surface.get_clip()
                surface.set_clip(old_clip.clip(rect.inflate(-8, 0)))
                label = self._label_cache[1]
                surface.blit(label, label.get_rect(center=rect.center))
                surface.set_clip(old_clip)
                return
            primary = self.ui_style in ('primary', 'forge_primary')
            base = (59, 43, 39) if primary else (34, 30, 43)
            bright = (104, 70, 43) if primary else (65, 52, 62)
            fill = tuple(round(a + (b - a) * self.hover_amount) for a, b in zip(base, bright))
            border_base = (146, 113, 68) if primary else (105, 93, 104)
            border_hover = (239, 194, 104)
            border = tuple(round(a + (b - a) * self.hover_amount) for a, b in zip(border_base, border_hover))
            pygame.draw.rect(surface, (11, 9, 15), (rect.x, rect.y + 3, rect.w, rect.h))
            pygame.draw.rect(surface, (20, 17, 25), rect)
            pygame.draw.rect(surface, fill, rect.inflate(-4, -4))
            pygame.draw.rect(surface, border, rect, 1)
            pygame.draw.line(surface, (145, 119, 91), (rect.x + 4, rect.y + 3), (rect.right - 5, rect.y + 3))
            pygame.draw.line(surface, (17, 15, 22), (rect.x + 4, rect.bottom - 4), (rect.right - 5, rect.bottom - 4))
            for x in (rect.x + 2, rect.right - 4):
                for y in (rect.y + 2, rect.bottom - 4):
                    pygame.draw.rect(surface, border, (x, y, 2, 2))
            if self.ui_selected or self.hover_amount > .35:
                pygame.draw.rect(surface, border, (rect.x + 6, rect.centery - 2, 3, 4))
                pygame.draw.rect(surface, border, (rect.right - 9, rect.centery - 2, 3, 4))
            label_color = (248, 231, 201) if target else (219, 208, 194)
            cache_key = (self.text_str, rect.width, label_color)
            if not self._label_cache or self._label_cache[0] != cache_key:
                font_size = 14
                font = get_pixel_font(font_size, bold=True)
                while font.size(self.text_str)[0] > rect.width - 20 and font_size > 10:
                    font_size -= 1
                    font = get_pixel_font(font_size, bold=True)
                self._label_cache = (cache_key, font.render(self.text_str, True, label_color))
            label = self._label_cache[1]
            old_clip = surface.get_clip()
            surface.set_clip(old_clip.clip(rect.inflate(-8, 0)))
            surface.blit(label, label.get_rect(center=rect.center))
            surface.set_clip(old_clip)
            return
        # Smooth lerp offset on hover (juicy-ui-menu §1.2)
        target_x = 6.0 if self.hovered else 0.0
        self.offset_x += (target_x - self.offset_x) * 0.25
        if self.click_offset_y > 0.0:
            self.click_offset_y = max(0.0, self.click_offset_y - 0.4)

        d_x = int(self.base_pos[0] + self.offset_x)
        d_y = int(self.base_pos[1] + self.click_offset_y)
        d_rect = pygame.Rect(d_x, d_y, self.rect.width, self.rect.height)
        self.rect.x = d_x

        # Beveled gothic stone button
        if self.hovered or self.ui_selected:
            bg_col = (48, 38, 22)
            border_col = (255, 215, 60)
            inner_col = (75, 60, 35)
            text_col = (255, 245, 200)
            corner_col = (255, 235, 100)
        else:
            bg_col = (24, 22, 32)
            border_col = (145, 135, 115)
            inner_col = (38, 35, 48)
            text_col = (225, 220, 235)
            corner_col = (190, 175, 140)

        # Base Fill & Inner Bevel
        pygame.draw.rect(surface, bg_col, d_rect)
        pygame.draw.rect(surface, inner_col, (d_rect.x + 2, d_rect.y + 2, d_rect.width - 4, d_rect.height - 4))
        pygame.draw.rect(surface, border_col, d_rect, 2)

        # Metallic Corner Rivets
        rw = 4
        for cx, cy in [(d_rect.left, d_rect.top), (d_rect.right - rw, d_rect.top),
                       (d_rect.left, d_rect.bottom - rw), (d_rect.right - rw, d_rect.bottom - rw)]:
            pygame.draw.rect(surface, corner_col, (cx, cy, rw, rw))

        # Runic selection marker on hover (Gothic brass chevrons)
        if self.hovered and self.rect.width >= 100:
            marker_left = self.font.render("»", True, (255, 215, 60))
            marker_right = self.font.render("«", True, (255, 215, 60))
            surface.blit(marker_left, (d_rect.left + 8, d_rect.centery - marker_left.get_height() // 2))
            surface.blit(marker_right, (d_rect.right - 8 - marker_right.get_width(), d_rect.centery - marker_right.get_height() // 2))

        # Centered Text with Shadow and adaptive sizing
        f = self.font
        text_surf = f.render(self.text_str, True, text_col)
        if text_surf.get_width() > d_rect.width - 24:
            f = get_pixel_font(11, bold=True)
            text_surf = f.render(self.text_str, True, text_col)

        text_shadow = f.render(self.text_str, True, (10, 8, 14))
        tx = d_rect.centerx - text_surf.get_width() // 2
        ty = d_rect.centery - text_surf.get_height() // 2
        surface.blit(text_shadow, (tx + 1, ty + 1))
        surface.blit(text_surf, (tx, ty))

    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        if self.hovered and not self.was_hovered:
            try:
                from src.sound_manager import play_sfx
                play_sfx('step')
            except Exception:
                pass
        self.was_hovered = self.hovered

    def check_click(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.hovered:
                    self.click_offset_y = 2.0
                    self.pressed_until = pygame.time.get_ticks() + 140
                    try:
                        from src.sound_manager import play_sfx
                        play_sfx('sword_swing')
                    except Exception:
                        pass
                    if self.callback:
                        self.callback()
                    return True
        return False


# =============================================================================
# RPG MODAL WINDOWS: SHOP, BLACKSMITH FORGE, EQUIPMENT & CHARACTER SCREEN
# =============================================================================

def wrap_text(text, font, max_width):
    """Cleanly word-wraps text without cutting words."""
    words = text.split(' ')
    lines = []
    cur_line = []
    for word in words:
        test_line = ' '.join(cur_line + [word])
        if font.size(test_line)[0] <= max_width:
            cur_line.append(word)
        else:
            if cur_line:
                lines.append(' '.join(cur_line))
            cur_line = [word]
    if cur_line:
        lines.append(' '.join(cur_line))
    return lines

class NPCDialogueBubble:
    """
    AAA Gothic Pixel Speech Bubble for NPCs (Kelvin, Rodrik/Anvil).
    Features:
    - 9-slice dark slate frame with polished metallic border & corner rivets
    - Downward pointer notch pointing directly to the NPC
    - 90-120ms spring entrance overshoot (0.85 -> 1.05 -> 1.00)
    - Anti-tofu Cyrillic text rendering with word-wrapping
    - Smooth alpha fade-out over the final 400ms
    """
    def __init__(self, text, target_pos, duration=4200, bubble_type='merchant'):
        self.text = text
        self.target_pos = pygame.math.Vector2(target_pos)
        self.duration = duration
        self.bubble_type = bubble_type  # 'merchant', 'blacksmith'
        self.spawn_time = pygame.time.get_ticks()
        self.font = get_pixel_font(11, bold=True)
        self.max_text_width = 210
        self.lines = wrap_text(self.text, self.font, self.max_text_width)
        
        pad_x, pad_y = 10, 8
        line_height = self.font.get_linesize()
        text_w = max([self.font.size(l)[0] for l in self.lines]) if self.lines else 60
        text_h = len(self.lines) * line_height
        self.box_w = max(110, text_w + pad_x * 2)
        self.box_h = text_h + pad_y * 2
        self.pointer_h = 7
        self.pointer_w = 10
        self.total_h = self.box_h + self.pointer_h

    def is_alive(self):
        return (pygame.time.get_ticks() - self.spawn_time) < self.duration

    def get_alpha(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        if elapsed >= self.duration:
            return 0
        remain = self.duration - elapsed
        if remain < 400:
            return max(0, min(255, int(255 * (remain / 400.0))))
        return 255

    def get_scale(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        spring_dur = 110.0
        if elapsed >= spring_dur or elapsed < 0:
            return 1.0
        p = max(0.0, min(1.0, elapsed / spring_dur))
        return 0.85 + 0.15 * p + 0.12 * math.sin(p * math.pi)

    def draw(self, surface, camera_offset=None):
        if not self.is_alive():
            return
        
        alpha = self.get_alpha()
        if alpha <= 0:
            return

        scale = self.get_scale()
        if hasattr(camera_offset, 'world_to_screen'):
            screen_target = camera_offset.world_to_screen(self.target_pos)
        else:
            offset = pygame.math.Vector2(camera_offset) if camera_offset is not None else pygame.math.Vector2()
            screen_target = self.target_pos - offset
        
        bubble_surf = pygame.Surface((self.box_w, self.total_h), pygame.SRCALPHA)
        
        if self.bubble_type == 'merchant':
            border_col = (235, 195, 65)
            inner_col = (20, 17, 26)
            text_col = (255, 240, 190)
        elif self.bubble_type == 'blacksmith':
            border_col = (245, 150, 45)
            inner_col = (24, 18, 16)
            text_col = (255, 230, 200)
        else:
            border_col = (140, 180, 240)
            inner_col = (16, 20, 28)
            text_col = (220, 235, 255)

        box_rect = pygame.Rect(0, 0, self.box_w, self.box_h)
        
        # Shadow
        pygame.draw.rect(bubble_surf, (0, 0, 0, 140), box_rect.move(2, 3), border_radius=4)
        
        # Background slate
        pygame.draw.rect(bubble_surf, inner_col, box_rect, border_radius=4)
        
        # Inner relief highlight
        pygame.draw.rect(bubble_surf, (min(255, inner_col[0] + 25), min(255, inner_col[1] + 25), min(255, inner_col[2] + 25)), box_rect.inflate(-2, -2), 1, border_radius=3)
        
        # Metallic frame
        pygame.draw.rect(bubble_surf, border_col, box_rect, 1, border_radius=4)
        
        # Corner rivets
        for rx in (box_rect.left + 3, box_rect.right - 4):
            for ry in (box_rect.top + 3, box_rect.bottom - 4):
                pygame.draw.rect(bubble_surf, (255, 240, 160), (rx, ry, 1, 1))

        # Downward pointer notch
        pointer_cx = self.box_w // 2
        notch_poly = [
            (pointer_cx - self.pointer_w // 2, self.box_h - 1),
            (pointer_cx + self.pointer_w // 2, self.box_h - 1),
            (pointer_cx, self.box_h + self.pointer_h - 1)
        ]
        pygame.draw.polygon(bubble_surf, inner_col, notch_poly)
        pygame.draw.lines(bubble_surf, border_col, False, [notch_poly[0], notch_poly[2], notch_poly[1]], 1)

        # Text lines
        pad_x, pad_y = 10, 8
        line_h = self.font.get_linesize()
        curr_y = pad_y
        for line in self.lines:
            txt_s = self.font.render(line, True, text_col)
            txt_shadow = self.font.render(line, True, (8, 6, 12))
            bubble_surf.blit(txt_shadow, (pad_x + 1, curr_y + 1))
            bubble_surf.blit(txt_s, (pad_x, curr_y))
            curr_y += line_h

        # Spring scale
        if scale != 1.0:
            new_w = max(10, int(self.box_w * scale))
            new_h = max(10, int(self.total_h * scale))
            bubble_surf = pygame.transform.scale(bubble_surf, (new_w, new_h))
        else:
            new_w = self.box_w
            new_h = self.total_h

        # Alpha fade-out
        if alpha < 255:
            bubble_surf.set_alpha(alpha)

        # Position bubble
        draw_x = int(screen_target.x - new_w // 2)
        draw_y = int(screen_target.y - new_h - 12)
        
        sw, sh = surface.get_size()
        draw_x = max(10, min(sw - new_w - 10, draw_x))
        draw_y = max(10, min(sh - new_h - 10, draw_y))
        
        surface.blit(bubble_surf, (draw_x, draw_y))


def draw_enemy_status_badges(surface, enemy, offset_pos):
    """
    Renders micro animated pixel badges above enemy hitboxes/health bars for active status effects.
    - Burn: Animated dancing ember flame (ruby-orange gradient)
    - Chill / Freeze: Pulsing icy crystalline diamond/snowflake (glacial cyan)
    - Bleed: Rhythmic pulsing crimson teardrop droplet
    Zero font/unicode dependencies (100% Anti-Tofu proof).
    """
    effects = getattr(enemy, 'status_effects', None)
    if not effects:
        return

    # Filter active effects
    now = pygame.time.get_ticks()
    active_keys = [k for k, v in effects.items() if now < v.get('expires', 0)]
    if not active_keys:
        return

    badge_size = 14
    gap = 3
    total_w = len(active_keys) * badge_size + (len(active_keys) - 1) * gap
    ox = getattr(offset_pos, 'x', offset_pos[0])
    oy = getattr(offset_pos, 'y', offset_pos[1])
    base_x = ox + (enemy.rect.width - total_w) // 2
    base_y = oy - 22

    for i, effect_name in enumerate(active_keys):
        bx = int(base_x + i * (badge_size + gap))
        by = int(base_y)
        b_rect = pygame.Rect(bx, by, badge_size, badge_size)
        
        # 1. Shadow & Background Pill
        pygame.draw.rect(surface, (0, 0, 0, 150), b_rect.move(1, 1), border_radius=3)
        pygame.draw.rect(surface, (18, 14, 22), b_rect, border_radius=3)

        if effect_name == 'burn':
            # Border: Fiery amber
            pygame.draw.rect(surface, (255, 140, 30), b_rect, 1, border_radius=3)
            # Animated flickering flame tip: 3 frames
            flicker = (now // 80 + i) % 3
            tip_x = bx + 7 + (flicker - 1)
            tip_y = by + 2 + (1 if flicker == 1 else 0)
            flame_pts = [
                (bx + 4, by + 11),
                (bx + 3, by + 7),
                (tip_x, tip_y),
                (bx + 11, by + 7),
                (bx + 10, by + 11)
            ]
            pygame.draw.polygon(surface, (245, 90, 25), flame_pts)
            # Inner white-gold core
            core_pts = [
                (bx + 5, by + 10),
                (bx + 7, by + 5 + flicker),
                (bx + 9, by + 10)
            ]
            pygame.draw.polygon(surface, (255, 235, 120), core_pts)

        elif effect_name in ('chill', 'freeze'):
            # Border: Glacial frost cyan
            pulse = 1 if (now // 140 + i) % 2 == 0 else 0
            border_c = (80, 210, 255) if pulse else (50, 160, 225)
            pygame.draw.rect(surface, border_c, b_rect, 1, border_radius=3)
            # 6-point / diamond crystalline frost snowflake
            cx, cy = bx + 7, by + 7
            pygame.draw.line(surface, (140, 230, 255), (cx - 4, cy), (cx + 4, cy), 1)
            pygame.draw.line(surface, (140, 230, 255), (cx, cy - 4), (cx, cy + 4), 1)
            # Diagonal sparks
            pygame.draw.rect(surface, (180, 240, 255), (cx - 2, cy - 2, 1, 1))
            pygame.draw.rect(surface, (180, 240, 255), (cx + 2, cy - 2, 1, 1))
            pygame.draw.rect(surface, (180, 240, 255), (cx - 2, cy + 2, 1, 1))
            pygame.draw.rect(surface, (180, 240, 255), (cx + 2, cy + 2, 1, 1))
            # Center diamond core
            pygame.draw.rect(surface, (255, 255, 255), (cx - 1, cy - 1, 3, 3))

        elif effect_name == 'bleed':
            # Border: Crimson blood
            pygame.draw.rect(surface, (225, 40, 60), b_rect, 1, border_radius=3)
            # Teardrop droplet
            cx, cy = bx + 7, by + 7
            drop_pts = [
                (cx, cy - 4),
                (cx + 4, cy + 1),
                (cx + 3, cy + 4),
                (cx - 3, cy + 4),
                (cx - 4, cy + 1)
            ]
            pygame.draw.polygon(surface, (215, 25, 45), drop_pts)
            # Specular highlight
            pygame.draw.rect(surface, (255, 170, 185), (cx - 2, cy, 2, 2))


class ShopModal:
    """Production-grade Sprite-based Shop Modal with tactile buttons, sell pagination, and item stacking."""
    def __init__(self, level, player):
        self.level = level
        self.player = player
        self.tab = 'buy'
        self.sell_page = 0
        self.message = None
        self.message_time = 0
        self.message_color = (255, 215, 60)
        self.open_time = pygame.time.get_ticks()

        self.embers = [
            {
                'x': random.uniform(40, 260),
                'y': random.uniform(80, 500),
                'vx': random.uniform(-0.25, 0.25),
                'vy': random.uniform(-0.6, -0.2),
                'life': random.randint(30, 90),
                'max_life': 90,
                'size': random.uniform(1.5, 3.0),
                'col': random.choice([(255, 215, 60), (255, 160, 40), (255, 100, 30)])
            }
            for _ in range(16)
        ]

        self.reroll_count = 0
        self.items = []
        self.generate_stock()
        self.speech_text = self.get_reactive_greeting()
        self._init_layout()

    def get_reactive_greeting(self):
        hp = getattr(self.player, 'health', 100)
        max_hp = self.player.stats.get('health', 100) if hasattr(self.player, 'stats') else 100
        gold = getattr(self.player, 'gold', 0)
        fl = getattr(self.level, 'current_floor', 1) if self.level else 1
        wpn = self.player.equipped.get('weapon') if hasattr(self.player, 'equipped') else None
        wpn_name = getattr(wpn, 'name', '').lower()

        if hp < max_hp * 0.35:
            return "«Еле на ногах стоишь, путник! Вся броня в крови! Зелья на полке — пей, пока жив! Хочешь что-то купить?»"
        elif gold >= 200:
            return "«О-о, пухлый кошель и звон золота ласкают мой слух! Выбирай лучшее оружие! Хочешь что-то купить?»"
        elif any(k in wpn_name for k in ['паладин', 'клинок', 'меч', 'меч странника']):
            return "«Где ты раздобыл этот клинок?! От него веет древней сталью... Уважаю! Хочешь что-то купить?»"
        elif fl >= 5:
            return "«Тьма сгущается на нижних ярусах. Без хорошей брони там верная гибель! Хочешь что-то купить?»"
        else:
            return "«Добро пожаловать в лавку Кельвина! Всё честно, без обмана и гнилья. Хочешь что-то купить?»"

    def generate_stock(self):
        fl = getattr(self.level, 'current_floor', 1) if self.level else 1
        seed = getattr(self.level, 'floor_seed', 12345) if self.level else 12345
        reroll_offset = getattr(self, 'reroll_count', 0) * 1013
        rng = random.Random((seed ^ (fl * 733) ^ reroll_offset) & 0x7FFFFFFF)

        potion_pool = [
            {'name': 'Малое зелье жизни', 'desc': '+50 HP мгновенно', 'cost': 45, 'type': 'potion', 'icon': 'assets/sprites/item_heart.png', 'heal': 50, 'rarity': 'common'},
            {'name': 'Великий эликсир крови', 'desc': '+85 HP мгновенно', 'cost': 65, 'type': 'potion', 'icon': 'assets/sprites/item_potion.png', 'heal': 85, 'rarity': 'rare'},
            {'name': 'Заточка паладина', 'desc': '+6 к урону атаки', 'cost': 75, 'type': 'buff_atk', 'icon': 'assets/sprites/item_sword.png', 'bonus': 6, 'rarity': 'rare'},
            {'name': 'Укреплённые латы', 'desc': '+8 к защите брони', 'cost': 70, 'type': 'buff_def', 'icon': 'assets/sprites/item_armor.png', 'bonus': 8, 'rarity': 'rare'},
        ]

        weapon_pool = [
            {'name': 'Клинок Паладина', 'desc': '+14 урона / Размах', 'cost': 110, 'type': 'weapon', 'icon': 'assets/sprites/item_sword.png', 'atk': 14, 'rarity': 'rare'},
            {'name': 'Топор берсерка', 'desc': '+18 урона / Тяжёлый', 'cost': 140, 'type': 'weapon', 'icon': 'assets/sprites/item_warhammer.png', 'atk': 18, 'rarity': 'epic'},
            {'name': 'Кинжалы тени', 'desc': '+10 урона / Быстрый', 'cost': 95, 'type': 'weapon', 'icon': 'assets/sprites/item_daggers.png', 'atk': 10, 'rarity': 'rare'},
        ]

        armor_pool = [
            {'name': 'Латный доспех стража', 'desc': '+45 макс. HP', 'cost': 85, 'type': 'armor', 'icon': 'assets/sprites/item_armor.png', 'hp': 45, 'rarity': 'rare'},
            {'name': 'Мантия чародея', 'desc': '+30 HP / +5 Мана', 'cost': 75, 'type': 'armor', 'icon': 'assets/sprites/item_armor.png', 'hp': 30, 'rarity': 'common'},
        ]

        boots_pool = [
            {'name': 'Сапоги ветра', 'desc': '+1.5 к скорости шага', 'cost': 60, 'type': 'boots', 'icon': 'assets/sprites/item_boots.png', 'spd': 1.5, 'rarity': 'common'},
            {'name': 'Тяжёлые ботфорты', 'desc': '+1.0 скор. / +15 HP', 'cost': 70, 'type': 'boots', 'icon': 'assets/sprites/item_boots.png', 'spd': 1.0, 'rarity': 'rare'},
        ]

        special_pool = [
            {'name': 'Амулет полумесяца', 'desc': '+6% шанс крита', 'cost': 90, 'type': 'amulet', 'icon': 'assets/sprites/item_amulet.png', 'rarity': 'epic'},
            {'name': 'Кольцо свирепости', 'desc': '+8% шанс крита', 'cost': 105, 'type': 'ring', 'icon': 'assets/sprites/item_ring.png', 'rarity': 'epic'},
            {'name': 'Осколок Бездны', 'desc': '+1 фиолетовый шард', 'cost': 125, 'type': 'shard', 'icon': 'assets/sprites/item_star.png', 'rarity': 'legendary'},
            {'name': 'Связка бомб (x3)', 'desc': '3 взрывных заряда', 'cost': 50, 'type': 'bomb', 'icon': 'assets/sprites/item_potion.png', 'rarity': 'common'},
        ]

        if fl == 1:
            w_choice = weapon_pool[0]
        else:
            w_choice = rng.choice(weapon_pool)

        self.items = [
            rng.choice(potion_pool).copy(),
            w_choice.copy(),
            rng.choice(armor_pool).copy(),
            rng.choice(boots_pool).copy(),
            rng.choice(special_pool).copy(),
            rng.choice(special_pool).copy()
        ]

    def _init_layout(self):
        disp = pygame.display.get_surface()
        sw, sh = (960, 640) if disp is None else disp.get_size()
        self.rect = pygame.Rect((sw - 920) // 2, (sh - 580) // 2, 920, 580)
        r = self.rect

        self.btn_close_x = SpriteButton("X", (r.right - 36, r.y + 12), 24, 24, callback=self.close, style='red')

        # Mode Tab Buttons
        self.btn_tab_buy = SpriteButton("ТОВАРЫ КЕЛЬВИНА", (r.x + 284, r.y + 64), 180, 32,
                                        callback=lambda: self.set_tab('buy'),
                                        style='yellow' if self.tab == 'buy' else 'grey',
                                        tint=(120, 110, 130) if self.tab != 'buy' else None,
                                        hotkey="[1]")
        self.btn_tab_sell = SpriteButton("ПРОДАЖА ДОБЫЧИ", (r.x + 472, r.y + 64), 180, 32,
                                         callback=lambda: self.set_tab('sell'),
                                         style='yellow' if self.tab == 'sell' else 'grey',
                                         tint=(120, 110, 130) if self.tab != 'sell' else None,
                                         hotkey="[2]")
        self.btn_reroll = SpriteButton("ОБНОВИТЬ (25 G)", (r.x + 660, r.y + 64), 160, 32,
                                       callback=self.reroll_stock,
                                       style='brown',
                                       hotkey="[R]")

        # 6 Item Buy Buttons (2 cols x 3 rows)
        self.buttons = []
        for i, itm in enumerate(self.items):
            col = i % 2
            row = i // 2
            x = r.x + 284 + col * 314
            y = r.y + 104 + row * 142
            itm['rect'] = pygame.Rect(x, y, 304, 134)
            is_sold = itm.get('sold', False)
            affordable = self.player.gold >= itm['cost'] and not is_sold
            btn_txt = "РАСПРОДАНО" if is_sold else f"КУПИТЬ [{i+1}]  /  {itm['cost']} G"
            btn = SpriteButton(btn_txt, (x + 10, y + 92), 284, 32,
                               callback=(lambda idx=i: self.buy_item(idx)) if not is_sold else (lambda: None),
                               style='grey' if is_sold or not affordable else 'brown',
                               tint=(90, 85, 95) if is_sold else ((110, 105, 115) if not affordable else None),
                               hotkey=f"[{i+1}]" if not is_sold else "")
            self.buttons.append(btn)

        # Sell Buttons with Pagination & Stacking
        self.sell_buttons = []
        if hasattr(self.player, 'consolidate_inventory'):
            self.player.consolidate_inventory()
        inv = getattr(self.player, 'inventory', [])
        pages = max(1, (len(inv) + 5) // 6)
        self.sell_page = max(0, min(self.sell_page, pages - 1))
        
        # Page buttons for sell mode
        self.btn_sell_prev = SpriteButton("<", (r.x + 660, r.y + 64), 30, 32,
                                          callback=lambda: self.change_sell_page(-1), style='grey')
        self.btn_sell_next = SpriteButton(">", (r.x + 786, r.y + 64), 30, 32,
                                          callback=lambda: self.change_sell_page(1), style='grey')

        start_idx = self.sell_page * 6
        page_items = inv[start_idx : start_idx + 6]
        for i, itm in enumerate(page_items):
            col = i % 2
            row = i // 2
            x = r.x + 284 + col * 314
            y = r.y + 104 + row * 142
            val = max(10, int(getattr(itm, 'value', 30) * 0.45))
            global_idx = start_idx + i
            btn = SpriteButton(f"ПРОДАТЬ  +{val} G", (x + 10, y + 92), 284, 32,
                               callback=lambda g_idx=global_idx: self.sell_item(g_idx),
                               style='brown',
                               hotkey=f"[{i+1}]")
            self.sell_buttons.append(btn)

        self.close_btn = SpriteButton("ВЫХОД [ESC]", (r.right - 150, r.bottom - 42), 136, 30,
                                      callback=self.close, style='grey', tint=(130, 120, 135), hotkey="[ESC]")

    def change_sell_page(self, delta):
        inv = getattr(self.player, 'inventory', [])
        pages = max(1, (len(inv) + 5) // 6)
        self.sell_page = max(0, min(self.sell_page + delta, pages - 1))
        self._init_layout()

    def set_tab(self, new_tab):
        self.tab = new_tab
        if new_tab == 'sell':
            if hasattr(self.player, 'consolidate_inventory'):
                self.player.consolidate_inventory()
            self.sell_page = 0
            self.speech_text = "«О, трофеи из глубин подземелья? Показывай, что добыл! Плачу чеканным золотом! Хочешь что-то купить?»"
        else:
            self.speech_text = self.get_reactive_greeting()
        self._init_layout()

    def reroll_stock(self):
        if self.player.gold < 25:
            self.message = "Недостаточно золота для обновления!"
            self.message_color = (255, 90, 90)
            self.speech_text = "«У тебя нет даже 25 монет на обновление полок! Зарабатывай честно, путник!»"
            self.message_time = pygame.time.get_ticks()
            return
        self.player.gold -= 25
        self.reroll_count = getattr(self, 'reroll_count', 0) + 1
        self.generate_stock()
        self._init_layout()
        try:
            from src.sound_manager import play_sfx
            play_sfx('coin')
        except Exception:
            pass
        self.message = "Товары обновлены!"
        self.message_color = (120, 240, 255)
        self.speech_text = "«Свежий завоз из тайного каравана! Оружие ещё тёплое!»"
        self.message_time = pygame.time.get_ticks()

    def close(self):
        if self.level:
            self.level.active_modal = None

    def buy_item(self, idx):
        now = pygame.time.get_ticks()
        if idx >= len(self.items):
            return
        itm = self.items[idx]
        if itm.get('sold', False):
            self.message = "Этот товар уже распродан!"
            self.message_color = (255, 160, 60)
            self.message_time = now
            return
        if self.player.gold < itm['cost']:
            self.message = "Недостаточно золота!"
            self.speech_text = "«Эй, постой! У тебя не хватает золота! В долг не отпускаю — даже героям!»"
            self.message_color = (255, 90, 90)
            self.message_time = now
            return

        from src.items import Item
        if itm['type'] == 'potion':
            if self.player.health >= self.player.stats.get('health', 100):
                self.message = "Здоровье уже полно!"
                self.speech_text = "«Твои раны уже затянулись! Прибереги монеты на оружие!»"
                self.message_color = (255, 140, 80)
                self.message_time = now
                return
            self.player.gold -= itm['cost']
            heal_amt = itm.get('heal', 50)
            self.player.health = min(self.player.stats.get('health', 100), self.player.health + heal_amt)
            itm['sold'] = True
            self.message = f"Куплено {itm['name']}! (+{heal_amt} HP)"
            self.speech_text = "«Пей до дна! Силы вернутся вмиг!»"
            self.message_color = (100, 240, 120)
            self._init_layout()
        elif itm['type'] == 'buff_atk':
            self.player.gold -= itm['cost']
            bonuses = getattr(self.player, 'shop_stat_bonuses', None)
            if not isinstance(bonuses, dict):
                bonuses = self.player.shop_stat_bonuses = {'attack': 0, 'defense': 0}
            bonuses['attack'] = bonuses.get('attack', 0) + itm.get('bonus', 6)
            self.player.recalculate_stats()
            itm['sold'] = True
            self.message = f"Куплена {itm['name']}! (+{itm.get('bonus', 6)} к атаке)"
            self.speech_text = "«Клинок стал острее бритвы! Режь монстров на куски!»"
            self.message_color = (255, 120, 80)
        elif itm['type'] == 'buff_def':
            self.player.gold -= itm['cost']
            bonuses = getattr(self.player, 'shop_stat_bonuses', None)
            if not isinstance(bonuses, dict):
                bonuses = self.player.shop_stat_bonuses = {'attack': 0, 'defense': 0}
            bonuses['defense'] = bonuses.get('defense', 0) + itm.get('bonus', 8)
            self.player.recalculate_stats()
            itm['sold'] = True
            self.message = f"Куплены {itm['name']}! (+{itm.get('bonus', 8)} к защите)"
            self.speech_text = "«Крепкая сталь спасёт от подлого удара в спину!»"
            self.message_color = (120, 220, 255)
        elif itm['type'] == 'weapon':
            self.player.gold -= itm['cost']
            wpn = Item(itm['name'], itm.get('rarity', 'rare'), {'attack': itm.get('atk', 14)}, itm['cost'], itm['icon'], slot='weapon')
            itm['sold'] = True
            self.player.equip_item(wpn)
            self.message = f"Экипирован {itm['name']}!"
            self.speech_text = "«Острый клинок! Славный выбор — разрубает кости как масло!»"
            self.message_color = (255, 215, 60)
        elif itm['type'] == 'armor':
            self.player.gold -= itm['cost']
            arm = Item(itm['name'], itm.get('rarity', 'rare'), {'health': itm.get('hp', 45)}, itm['cost'], itm['icon'], slot='armor')
            itm['sold'] = True
            self.player.equip_item(arm)
            self.message = f"Экипирован {itm['name']}!"
            self.speech_text = "«Добротная броня! Теперь клыки некромантов не страшны!»"
            self.message_color = (120, 210, 255)
        elif itm['type'] == 'boots':
            self.player.gold -= itm['cost']
            bts = Item(itm['name'], itm.get('rarity', 'rare'), {'speed': itm.get('spd', 1.5)}, itm['cost'], itm['icon'], slot='boots')
            itm['sold'] = True
            self.player.equip_item(bts)
            self.message = f"Экипированы {itm['name']}!"
            self.speech_text = "«Легки как перышко! Будешь порхать сквозь ловушки!»"
            self.message_color = (180, 240, 160)
        elif itm['type'] in ('amulet', 'ring'):
            self.player.gold -= itm['cost']
            acc = Item(itm['name'], itm.get('rarity', 'epic'), {'crit_rate': 6.0}, itm['cost'], itm['icon'], slot=itm['type'])
            itm['sold'] = True
            self.player.equip_item(acc)
            self.message = f"Надет {itm['name']}!"
            self.speech_text = "«Магическая реликвия! Удары станут сокрушительными!»"
            self.message_color = (220, 160, 255)
        elif itm['type'] == 'shard':
            self.player.gold -= itm['cost']
            itm['sold'] = True
            from src.save_manager import load_profile, save_profile
            profile = load_profile()
            shards = max(int(getattr(self.player, 'purple_shards', 0)), int(profile.get('purple_shards', 0))) + 1
            self.player.purple_shards = shards
            profile['purple_shards'] = shards
            save_profile(profile)
            self.message = "Куплен Осколок Бездны! (+1 Shard)"
            self.speech_text = "«Пульсирует чистой энергией Бездны... Осторожнее с ним!»"
            self.message_color = (200, 100, 255)
        else:
            self.player.gold -= itm['cost']
            itm['sold'] = True
            self.player.bombs = getattr(self.player, 'bombs', 0) + 3
            self.message = "Куплено 3 бомбы!"
            self.speech_text = "«Бабах! Разноси стены и тайники в пыль!»"
            self.message_color = (255, 180, 60)

        self.message_time = now
        try:
            from src.sound_manager import play_sfx
            play_sfx('coin')
        except Exception:
            pass
        self._init_layout()

    def sell_item(self, global_idx):
        now = pygame.time.get_ticks()
        if hasattr(self.player, 'consolidate_inventory'):
            self.player.consolidate_inventory()
        inv = getattr(self.player, 'inventory', [])
        if global_idx >= len(inv):
            return
        itm = inv[global_idx]
        val = max(10, int(getattr(itm, 'value', 30) * 0.45))
        self.player.gold += val

        count = getattr(itm, 'count', 1)
        if count > 1:
            itm.count = count - 1
            rem_str = f" (Осталось: {itm.count} шт.)"
        else:
            self.player.inventory.pop(global_idx)
            rem_str = ""

        self.message = f"Продано: {getattr(itm, 'name', 'Предмет')} (+{val} G)!{rem_str}"
        self.message_color = (255, 215, 60)
        self.speech_text = f"«Отличная вещь! Держи свои {val} золотых. Хочешь продать ещё что-то?»"
        self.message_time = now
        try:
            from src.sound_manager import play_sfx
            play_sfx('coin')
        except Exception:
            pass
        self._init_layout()

    def update(self, mouse_pos):
        self.btn_tab_buy.check_hover(mouse_pos)
        self.btn_tab_sell.check_hover(mouse_pos)
        self.btn_reroll.check_hover(mouse_pos)
        self.close_btn.check_hover(mouse_pos)
        self.btn_close_x.check_hover(mouse_pos)

        if self.tab == 'buy':
            for btn in self.buttons:
                btn.check_hover(mouse_pos)
        elif self.tab == 'sell':
            if hasattr(self, 'btn_sell_prev'): self.btn_sell_prev.check_hover(mouse_pos)
            if hasattr(self, 'btn_sell_next'): self.btn_sell_next.check_hover(mouse_pos)
            for s_btn in getattr(self, 'sell_buttons', []):
                s_btn.check_hover(mouse_pos)

        for eb in self.embers:
            eb['x'] += eb['vx']
            eb['y'] += eb['vy']
            eb['life'] -= 1
            if eb['life'] <= 0:
                eb['x'] = random.uniform(self.rect.x + 30, self.rect.x + 250)
                eb['y'] = random.uniform(self.rect.y + 80, self.rect.y + 480)
                eb['life'] = eb['max_life']

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_e, pygame.K_i, pygame.K_c]:
                self.close()
                return True
            elif event.key == pygame.K_TAB:
                self.set_tab('sell' if self.tab == 'buy' else 'buy')
                return True
            elif event.key == pygame.K_r:
                self.reroll_stock()
                return True
            elif event.key in [pygame.K_LEFT, pygame.K_q, pygame.K_PAGEUP]:
                if self.tab == 'sell':
                    self.change_sell_page(-1)
                    return True
            elif event.key in [pygame.K_RIGHT, pygame.K_PAGEDOWN]:
                if self.tab == 'sell':
                    self.change_sell_page(1)
                    return True
            elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]:
                num = event.key - pygame.K_1
                if self.tab == 'buy' and num < len(self.items):
                    self.buy_item(num)
                    return True
                elif self.tab == 'sell':
                    g_idx = self.sell_page * 6 + num
                    if g_idx < len(getattr(self.player, 'inventory', [])):
                        self.sell_item(g_idx)
                        return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mpos = event.pos
            if not self.rect.collidepoint(mpos):
                self.close()
                return True
            if self.btn_close_x.rect.collidepoint(mpos):
                self.close()
                return True
            if self.btn_tab_buy.rect.collidepoint(mpos):
                self.set_tab('buy')
                return True
            if self.btn_tab_sell.rect.collidepoint(mpos):
                self.set_tab('sell')
                return True
            if self.btn_reroll.rect.collidepoint(mpos):
                self.reroll_stock()
                return True
            if self.close_btn.rect.collidepoint(mpos):
                self.close()
                return True

            if self.tab == 'buy':
                for btn in self.buttons:
                    if btn.rect.collidepoint(mpos):
                        btn._play_click_sound()
                        if btn.callback: btn.callback()
                        return True
            elif self.tab == 'sell':
                if hasattr(self, 'btn_sell_prev') and self.btn_sell_prev.rect.collidepoint(mpos):
                    self.change_sell_page(-1)
                    return True
                if hasattr(self, 'btn_sell_next') and self.btn_sell_next.rect.collidepoint(mpos):
                    self.change_sell_page(1)
                    return True
                for s_btn in getattr(self, 'sell_buttons', []):
                    if s_btn.rect.collidepoint(mpos):
                        s_btn._play_click_sound()
                        if s_btn.callback: s_btn.callback()
                        return True
        return False

    def draw(self, surface):
        r = self.rect
        now = pygame.time.get_ticks()

        # 1. Dark vignette backdrop
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((6, 5, 9, 230))
        surface.blit(overlay, (0, 0))

        # 2. Outer Window: Ancient Oak Carved Frame with deep shadow
        draw_panel(surface, r, texture='brown.png', corner=16, shadow=True, shadow_offset=(8, 10), shadow_alpha=175)

        # 3. Top Decorative Header Bar
        header_rect = pygame.Rect(r.x + 10, r.y + 10, r.w - 20, 48)
        draw_inlay(surface, header_rect, texture='brown_inlay.png', corner=12)
        draw_text(surface, "ЛАВКА СТРАННИКА КЕЛЬВИНА", (r.x + 28, r.y + 18), font_size=17, color=(255, 220, 110), bold=True)
        draw_text(surface, "ПОДЗЕМНЫЙ КАРАВАН И РЕДКИЕ ДИВОВИНЫ", (r.x + 28, r.y + 38), font_size=11, color=(195, 180, 160), bold=False)

        # Close X Button
        self.btn_close_x.draw(surface)

        # 4. Left Kelvin Booth Area
        booth_rect = pygame.Rect(r.x + 14, r.y + 64, 256, 458)
        draw_inlay(surface, booth_rect, texture='grey_inlay.png', corner=14, tint=(70, 65, 78))

        # Ambient floating embers inside booth
        for eb in self.embers:
            es = int(eb['size'])
            alpha = int(255 * (eb['life'] / eb['max_life']))
            esurf = pygame.Surface((es * 2, es * 2), pygame.SRCALPHA)
            pygame.draw.circle(esurf, (*eb['col'], alpha), (es, es), es)
            surface.blit(esurf, (int(eb['x']), int(eb['y'])))

        # Portrait Wood Frame
        port_frame = pygame.Rect(r.x + 24, r.y + 74, 236, 150)
        draw_panel(surface, port_frame, texture='brown.png', corner=14, shadow=True)
        port_socket = pygame.Rect(r.x + 32, r.y + 82, 220, 134)
        draw_inlay(surface, port_socket, texture='brown_inlay.png', corner=10)

        # Merchant Portrait with breathing animation
        try:
            from src.utils import load_image
            merchant_raw = load_image('assets/sprites/merchant.png')
            m_scaled = pygame.transform.scale(merchant_raw, (108, 108))
            bounce = int(2.5 * math.sin(now * 0.003))
            surface.blit(m_scaled, (port_socket.centerx - 54, port_socket.centery - 54 + bounce))
        except Exception:
            pass

        # Speaker Badge
        draw_text(surface, "КЕЛЬВИН", (r.x + 142, r.y + 232), font_size=15, color=(255, 230, 160), bold=True, center=True)
        draw_text(surface, "БРОДЯЧИЙ СКУПЩИК", (r.x + 142, r.y + 250), font_size=10, color=(175, 165, 150), center=True)

        # Dialogue Speech Bubble (Parchment tan.png)
        bubble_rect = pygame.Rect(r.x + 24, r.y + 270, 236, 140)
        draw_panel(surface, bubble_rect, texture='tan.png', corner=14, shadow=True)

        font_speech = get_font(12, bold=False)
        lines = wrap_text(self.speech_text, font_speech, 208)
        for idx, line in enumerate(lines[:6]):
            draw_text(surface, line, (bubble_rect.x + 14, bubble_rect.y + 14 + idx * 19),
                      font_size=12, color=(50, 40, 30), shadow=False, bold=False)

        # Player Wallet Inlay
        wallet_rect = pygame.Rect(r.x + 24, r.y + 420, 236, 92)
        draw_inlay(surface, wallet_rect, texture='brown_inlay.png', corner=12)

        try:
            from src.utils import load_image
            gold_ico = load_image('assets/sprites/item_gold.png')
            gold_ico = pygame.transform.scale(gold_ico, (28, 28))
            surface.blit(gold_ico, (wallet_rect.x + 14, wallet_rect.y + 14))
        except Exception:
            pass
        draw_text(surface, f"ЗОЛОТО: {self.player.gold} G", (wallet_rect.x + 50, wallet_rect.y + 20),
                  font_size=15, color=(255, 215, 60), bold=True)

        try:
            star_ico = load_image('assets/sprites/item_star.png')
            star_ico = pygame.transform.scale(star_ico, (24, 24))
            surface.blit(star_ico, (wallet_rect.x + 16, wallet_rect.y + 52))
        except Exception:
            pass
        shards = getattr(self.player, 'purple_shards', 0)
        draw_text(surface, f"ОСКОЛКИ: {shards} SH", (wallet_rect.x + 50, wallet_rect.y + 56),
                  font_size=14, color=(210, 140, 255), bold=True)

        # 5. Right Content Area: Tabs
        self.btn_tab_buy.style = 'yellow' if self.tab == 'buy' else 'grey'
        self.btn_tab_buy.tint = None if self.tab == 'buy' else (120, 110, 130)
        self.btn_tab_sell.style = 'yellow' if self.tab == 'sell' else 'grey'
        self.btn_tab_sell.tint = None if self.tab == 'sell' else (120, 110, 130)

        self.btn_tab_buy.draw(surface)
        self.btn_tab_sell.draw(surface)

        if self.tab == 'buy':
            self.btn_reroll.draw(surface)
            mpos = pygame.mouse.get_pos()
            for i, itm in enumerate(self.items):
                cr = itm['rect']
                is_hovered = cr.collidepoint(mpos)

                draw_inlay(surface, cr, texture='brown_inlay.png', corner=14)

                if is_hovered:
                    glow_surf = get_nineslice('yellow.png', cr.width, cr.height, corner=14)
                    glow_surf.set_alpha(75)
                    surface.blit(glow_surf, cr.topleft)

                # Icon socket
                icon_socket = pygame.Rect(cr.x + 10, cr.y + 10, 68, 68)
                draw_inlay(surface, icon_socket, texture='grey_inlay.png', corner=10, tint=(85, 80, 95))

                try:
                    from src.utils import load_image
                    ico = load_image(itm['icon'])
                    ico_scaled = pygame.transform.scale(ico, (44, 44))
                    surface.blit(ico_scaled, (icon_socket.centerx - 22, icon_socket.centery - 22))
                except Exception:
                    pass

                rarity = itm.get('rarity', 'common')
                title_col = (255, 255, 255)
                if rarity == 'rare': title_col = (110, 205, 255)
                elif rarity == 'epic': title_col = (210, 130, 255)
                elif rarity == 'legendary': title_col = (255, 220, 70)

                draw_text(surface, itm['name'], (cr.x + 88, cr.y + 14), font_size=13, color=title_col, bold=True)
                draw_text(surface, itm['desc'], (cr.x + 88, cr.y + 36), font_size=11, color=(195, 185, 175), bold=False)
                draw_text(surface, f"ЦЕНА: {itm['cost']} G", (cr.x + 88, cr.y + 56), font_size=12, color=(255, 215, 60), bold=True)

                affordable = self.player.gold >= itm['cost']
                self.buttons[i].style = 'yellow' if (affordable and self.buttons[i].hovered) else ('brown' if affordable else 'grey')
                self.buttons[i].tint = None if affordable else (115, 110, 120)
                self.buttons[i].enabled = affordable
                self.buttons[i].draw(surface)

        elif self.tab == 'sell':
            # Sell tab with pagination
            inv = getattr(self.player, 'inventory', [])
            pages = max(1, (len(inv) + 5) // 6)
            self.sell_page = max(0, min(self.sell_page, pages - 1))

            if pages > 1:
                self.btn_sell_prev.draw(surface)
                draw_text(surface, f"СТР {self.sell_page + 1} / {pages}", (r.x + 723, r.y + 73),
                          font_size=12, color=(255, 220, 120), center=True)
                self.btn_sell_next.draw(surface)

            start_idx = self.sell_page * 6
            page_items = inv[start_idx : start_idx + 6]

            if not inv:
                empty_rect = pygame.Rect(r.x + 284, r.y + 104, 618, 416)
                draw_inlay(surface, empty_rect, texture='grey_inlay.png', corner=14, tint=(75, 70, 85))
                draw_text(surface, "У ВАС НЕТ ПРЕДМЕТОВ НА ПРОДАЖУ", empty_rect.center,
                          font_size=16, color=(190, 180, 170), bold=True, center=True)
                draw_text(surface, "Исследуйте подземелье и побеждайте монстров, чтобы добыть сокровища!",
                          (empty_rect.centerx, empty_rect.centery + 30), font_size=12, color=(150, 140, 130), center=True)
            else:
                for i, itm in enumerate(page_items):
                    cr = pygame.Rect(r.x + 284 + (i % 2) * 314, r.y + 104 + (i // 2) * 142, 304, 134)
                    draw_inlay(surface, cr, texture='brown_inlay.png', corner=14)

                    icon_socket = pygame.Rect(cr.x + 10, cr.y + 10, 68, 68)
                    draw_inlay(surface, icon_socket, texture='grey_inlay.png', corner=10, tint=(85, 80, 95))

                    try:
                        from src.utils import load_image
                        ico = getattr(itm, 'image_path', None) or getattr(itm, 'icon', None) or 'assets/sprites/item_sword.png'
                        ico_surf = load_image(ico)
                        ico_scaled = pygame.transform.scale(ico_surf, (44, 44))
                        surface.blit(ico_scaled, (icon_socket.centerx - 22, icon_socket.centery - 22))
                    except Exception:
                        pass

                    # Stack count badge on item icon socket
                    c_count = getattr(itm, 'count', 1)
                    if c_count > 1:
                        draw_text(surface, f"x{c_count}", (icon_socket.right - 4, icon_socket.bottom - 4),
                                  font_size=12, color=(255, 230, 90), right=True, bold=True)

                    itm_name = getattr(itm, 'name', 'Предмет')
                    rarity = getattr(itm, 'rarity', 'common')
                    title_col = (255, 255, 255)
                    if rarity == 'rare': title_col = (110, 205, 255)
                    elif rarity == 'epic': title_col = (210, 130, 255)
                    elif rarity == 'legendary': title_col = (255, 220, 70)

                    val = max(10, int(getattr(itm, 'value', 30) * 0.45))
                    draw_text(surface, itm_name, (cr.x + 88, cr.y + 14), font_size=13, color=title_col, bold=True)
                    
                    count_desc = f"Количество: {c_count} шт." if c_count > 1 else f"Редкость: {rarity.capitalize()}"
                    draw_text(surface, count_desc, (cr.x + 88, cr.y + 36), font_size=11, color=(185, 175, 165), bold=False)
                    draw_text(surface, f"Выкуп: +{val} G за шт.", (cr.x + 88, cr.y + 56), font_size=12, color=(255, 215, 60), bold=True)

                    if i < len(self.sell_buttons):
                        self.sell_buttons[i].draw(surface)

        # 7. Bottom Status & Controls Bar
        if self.message and now - self.message_time < 3000:
            status_box = pygame.Rect(r.x + 284, r.bottom - 44, 460, 30)
            draw_inlay(surface, status_box, texture='brown_inlay.png', corner=10)
            draw_text(surface, self.message, (status_box.x + 14, status_box.y + 7), font_size=12, color=self.message_color, bold=True)
        else:
            controls_text = "[1-6] ДЕЙСТВИЕ   |   [TAB] СМЕНИТЬ РЕЖИМ   |   [Q/E] СТРАНИЦЫ   |   [ESC] ВЫХОД"
            draw_text(surface, controls_text, (r.x + 288, r.bottom - 36), font_size=11, color=(185, 175, 160), bold=False)

        self.close_btn.draw(surface)


class BlacksmithModal:
    def __init__(self, level, player):
        self.level = level
        self.player = player
        self.font_title = get_pixel_font(18, bold=True)
        self.font_sub = get_pixel_font(12, bold=True)
        self.font_sm = get_pixel_font(11, bold=False)
        self.font_tiny = get_pixel_font(10, bold=False)
        self.message = None
        self.message_time = 0
        self.message_color = (255, 215, 60)
        self.tab = 0  # 0: Прокачка (Genshin), 1: Астральная кузница (Фиолетовые осколки)
        self.sparks = []
        self.item_page = 0
        self.item_slots = []
        self.upgrade_effect_start = -1000

        # Select initial item to upgrade (default: weapon)
        self.selected_item = self.player.equipped.get('weapon')
        if not self.selected_item:
            for s in ['armor', 'offhand', 'boots', 'amulet', 'ring']:
                if self.player.equipped.get(s):
                    self.selected_item = self.player.equipped[s]
                    break

        self.open_time = pygame.time.get_ticks()
        self.buttons = []
        self._init_layout()

    @property
    def current_tab(self):
        return self.tab

    @current_tab.setter
    def current_tab(self, val):
        self.set_tab(val)

    def _init_layout(self):
        disp = pygame.display.get_surface()
        sw, sh = disp.get_size() if disp else (1280, 720)
        self.rect = pygame.Rect((sw - 1000) // 2, (sh - 600) // 2, 1000, 600)
        self.close_x_rect = pygame.Rect(self.rect.right - 38, self.rect.y + 19, 24, 24)
        self._rebuild_buttons()

    def _rebuild_buttons(self):
        self.buttons = []
        self.item_slots = []
        r = self.rect
        for tab, label in enumerate(("1  ПЕРЕКОВКА", "2  АСТРАЛЬНЫЙ ГОРН")):
            btn = Button(label, (r.x + 26 + tab * 260, r.y + 79), 250, 38, lambda t=tab: self.set_tab(t))
            btn.ui_selected = self.tab == tab
            btn.ui_style = 'forge'
            self.buttons.append(btn)
        if self.tab == 0:
            items = self.get_available_items()
            pages = max(1, (len(items) + 11) // 12)
            self.item_page = max(0, min(self.item_page, pages - 1))
            for idx, (itm, is_eq, slot_label) in enumerate(items[self.item_page * 12:self.item_page * 12 + 12]):
                slot = pygame.Rect(r.x + 51 + (idx % 4) * 60, r.y + 193 + (idx // 4) * 64, 54, 54)
                self.item_slots.append((slot, itm, is_eq, slot_label))
            if pages > 1:
                for dx, label, delta in ((0, '<', -1), (1, '>', 1)):
                    btn = Button(label, (r.x + 51 + dx * 184, r.y + 409), 46, 30, lambda d=delta: self.change_page(d))
                    btn.ui_style = 'forge'
                    self.buttons.append(btn)
            up = Button("УЛУЧШИТЬ  /  40 G", (r.x + 364, r.y + 503), 590, 42, self.upgrade_selected_item)
            up.ui_style = 'forge_primary'
            self.buttons.append(up)
        else:
            from src.items import ASTRAL_WEAPONS_CATALOGUE
            for idx, key in enumerate(ASTRAL_WEAPONS_CATALOGUE):
                btn = Button("ВЫКОВАТЬ  /  10 ОСКОЛКОВ", (r.x + 730, r.y + 190 + idx * 112),
                             220, 38, lambda wid=key: self.forge_astral_weapon(wid))
                btn.ui_style = 'forge_primary'
                self.buttons.append(btn)
        close_btn = Button("ЗАКРЫТЬ  /  ESC", (r.right - 200, r.bottom - 48), 165, 30, self.close)
        close_btn.ui_style = 'forge'
        self.buttons.append(close_btn)

    def change_page(self, delta):
        self.item_page += delta
        self._rebuild_buttons()

    def set_tab(self, tab_idx):
        self.tab = tab_idx
        self._rebuild_buttons()

    def select_item(self, itm):
        self.selected_item = itm
        self._spark_sfx()
        self._rebuild_buttons()

    def get_available_items(self):
        if hasattr(self.player, 'consolidate_inventory'):
            self.player.consolidate_inventory()
        result = []
        slots = [
            ('weapon', 'Оружие'),
            ('offhand', 'Вторая рука'),
            ('armor', 'Броня'),
            ('boots', 'Сапоги'),
            ('amulet', 'Амулет'),
            ('ring', 'Кольцо')
        ]
        for slot_k, label in slots:
            eq = self.player.equipped.get(slot_k)
            if eq:
                result.append((eq, True, label))
        inv_items = []
        for inv_it in getattr(self.player, 'inventory', []):
            if hasattr(inv_it, 'slot') and inv_it.slot in ['weapon', 'offhand', 'armor', 'boots', 'amulet', 'ring']:
                inv_items.append((inv_it, False, 'Рюкзак'))
        from src.items import item_sort_key
        inv_items.sort(key=lambda t: item_sort_key(t[0]))
        result.extend(inv_items)
        return result

    def close(self):
        self.level.active_modal = None

    def upgrade_selected_item(self):
        now = pygame.time.get_ticks()
        if not self.selected_item:
            self.message = "Сначала выберите предмет для прокачки!"
            self.message_color = (255, 90, 90)
            self.message_time = now
            return

        if self.player.gold < 40:
            self.message = "Недостаточно золота для прокачки (нужно 40 G)!"
            self.message_color = (255, 90, 90)
            self.message_time = now
            return

        target_item = self.selected_item
        is_stacked_inventory = (
            getattr(target_item, 'count', 1) > 1 and 
            target_item in getattr(self.player, 'inventory', [])
        )
        if is_stacked_inventory:
            target_item.count -= 1
            upgraded_copy = target_item.clone()
            upgraded_copy.count = 1
            success, msg = upgraded_copy.upgrade()
            if not success:
                target_item.count += 1
                self.message = msg
                self.message_color = (255, 140, 80)
                self.message_time = now
                return
            self.player.inventory.append(upgraded_copy)
            self.selected_item = upgraded_copy
        else:
            success, msg = target_item.upgrade()
            if not success:
                self.message = msg
                self.message_color = (255, 140, 80)
                self.message_time = now
                return

        self.player.gold -= 40
        self.player.recalculate_stats()
        self._rebuild_buttons()

        # Save to profile if in hub or updating persistent gear
        if getattr(self.level, 'is_hub', False):
            try:
                from src.save_manager import load_profile, save_profile
                prof = load_profile()
                for s in ['weapon', 'offhand', 'armor', 'boots', 'amulet', 'ring']:
                    it = self.player.equipped.get(s)
                    if it and hasattr(it, 'to_dict'):
                        prof.setdefault('equipped', {})[s] = it.to_dict()
                prof['permanent_gold'] = self.player.gold
                prof['armory'] = [it.to_dict() for it in getattr(self.player, 'inventory', []) if it and hasattr(it, 'to_dict')]
                save_profile(prof)
            except Exception:
                pass

        self.message = msg
        self.message_color = (255, 220, 60)
        self.message_time = now
        self._spark_sfx()
        self.upgrade_effect_start = now

        # Burst anvil spark particles
        import random
        for _ in range(25):
            self.sparks.append({
                'x': self.rect.x + 511 + random.uniform(-15, 15),
                'y': self.rect.y + 380 + random.uniform(-10, 10),
                'vx': random.uniform(-2.5, 2.5),
                'vy': random.uniform(-4.5, -1.0),
                'col': random.choice([(255, 235, 90), (255, 175, 40), (255, 120, 30), (255, 255, 200)]),
                'life': random.randint(20, 45),
                'max_life': 45
            })

    def forge_astral_weapon(self, weapon_id):
        now = pygame.time.get_ticks()
        p_shards = getattr(self.player, 'purple_shards', 0)
        from src.save_manager import load_profile, save_profile
        prof = load_profile()
        total_shards = max(p_shards, prof.get('purple_shards', 0))

        if total_shards < 10:
            self.message = "Недостаточно фиолетовых осколков (нужно 10)!"
            self.message_color = (255, 90, 90)
            self.message_time = now
            return

        from src.items import create_astral_weapon
        new_wpn = create_astral_weapon(weapon_id)
        if not new_wpn:
            return

        total_shards -= 10
        self.player.purple_shards = total_shards
        prof['purple_shards'] = total_shards
        self.player.equip_item(new_wpn)
        self.selected_item = new_wpn

        prof.setdefault('equipped', {})['weapon'] = new_wpn.to_dict()
        save_profile(prof)
        self.player.recalculate_stats()

        self.message = f"Выковано астральное оружие: {new_wpn.name}!"
        self.message_color = (215, 120, 255)
        self.message_time = now
        self._spark_sfx()
        self._rebuild_buttons()

        # Burst celestial purple spark particles
        import random
        for _ in range(30):
            self.sparks.append({
                'x': self.rect.centerx + random.uniform(-80, 80),
                'y': self.rect.y + 180 + random.uniform(-20, 20),
                'vx': random.uniform(-2.2, 2.2),
                'vy': random.uniform(-3.8, -0.8),
                'col': random.choice([(220, 130, 255), (170, 70, 255), (255, 220, 100)]),
                'life': random.randint(25, 50),
                'max_life': 50
            })

    # Compatibility methods for existing unit tests
    def sharpen_weapon(self):
        now = pygame.time.get_ticks()
        if self.player.gold < 40:
            self.message = "Недостаточно золота для заточки оружия!"
            self.message_color = (255, 90, 90)
            self.message_time = now
            return

        wpn = self.player.equipped.get('weapon')
        if not wpn:
            from src.items import Item
            wpn = Item("Клинок Оружейника", "common", {'attack': 3}, 40, 'assets/sprites/item_sword.png', slot='weapon')
            self.player.equip_item(wpn)
        else:
            wpn.effects['attack'] = wpn.effects.get('attack', 2) + 3
            wpn.base_effects['attack'] = wpn.effects['attack']
            if hasattr(wpn, 'main_stat') and wpn.main_stat and wpn.main_stat.get('id') == 'attack':
                wpn.main_stat['value'] = wpn.effects['attack']
            base_name = wpn.name.split(' +')[0]
            wpn.upgrade_level += 1
            wpn.name = f"{base_name} +{wpn.upgrade_level}"

        self.player.gold -= 40
        self.player.recalculate_stats()
        self._rebuild_buttons()
        if getattr(self.level, 'is_hub', False):
            try:
                from src.save_manager import load_profile, save_profile
                prof = load_profile()
                for s in ['weapon', 'offhand', 'armor', 'boots', 'amulet', 'ring']:
                    it = self.player.equipped.get(s)
                    if it and hasattr(it, 'to_dict'):
                        prof.setdefault('equipped', {})[s] = it.to_dict()
                save_profile(prof)
            except Exception:
                pass
        self.message = "Оружие успешно заточено! Урон увеличен (+3 Атака)"
        self.message_color = (255, 220, 60)
        self.message_time = now
        self._spark_sfx()
        self._rebuild_buttons()

    def reinforce_armor(self):
        now = pygame.time.get_ticks()
        if self.player.gold < 40:
            self.message = "Недостаточно золота для укрепления брони!"
            self.message_color = (255, 90, 90)
            self.message_time = now
            return

        arm = self.player.equipped.get('armor')
        if not arm:
            from src.items import Item
            arm = Item("Кольчуга Оружейника", "common", {'health': 20}, 40, 'assets/sprites/item_armor.png', slot='armor')
            self.player.equip_item(arm)
        else:
            arm.effects['health'] = arm.effects.get('health', 10) + 20
            arm.base_effects['health'] = arm.effects['health']
            if hasattr(arm, 'main_stat') and arm.main_stat and arm.main_stat.get('id') == 'health':
                arm.main_stat['value'] = arm.effects['health']
            base_name = arm.name.split(' +')[0]
            arm.upgrade_level += 1
            arm.name = f"{base_name} +{arm.upgrade_level}"

        self.player.gold -= 40
        self.player.recalculate_stats()
        self._rebuild_buttons()
        if getattr(self.level, 'is_hub', False):
            try:
                from src.save_manager import load_profile, save_profile
                prof = load_profile()
                for s in ['weapon', 'offhand', 'armor', 'boots', 'amulet', 'ring']:
                    it = self.player.equipped.get(s)
                    if it and hasattr(it, 'to_dict'):
                        prof.setdefault('equipped', {})[s] = it.to_dict()
                save_profile(prof)
            except Exception:
                pass
        self.message = "Броня закалена в горне! Макс. здоровье увеличено (+20 HP)"
        self.message_color = (120, 225, 255)
        self.message_time = now
        self._spark_sfx()
        self._rebuild_buttons()

    def reroll_runes(self):
        self.upgrade_selected_item()

    def _spark_sfx(self):
        try:
            from src.sound_manager import play_sfx
            play_sfx('anvil')
        except Exception:
            pass

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_e, pygame.K_i, pygame.K_TAB, pygame.K_c]:
                self.close()
                return True
            elif event.key == pygame.K_1: self.set_tab(0); return True
            elif event.key == pygame.K_2: self.set_tab(1); return True
            elif event.key in [pygame.K_RETURN, pygame.K_SPACE] and self.tab == 0:
                self.upgrade_selected_item()
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mpos = event.pos
            if not self.rect.collidepoint(mpos):
                self.close()
                return True
            if hasattr(self, 'close_x_rect') and self.close_x_rect.collidepoint(mpos):
                self.close()
                return True
            if self.tab == 0:
                for slot, itm, _, _ in self.item_slots:
                    if slot.collidepoint(mpos):
                        self.select_item(itm)
                        return True
            for btn in self.buttons:
                if btn.rect.collidepoint(mpos):
                    btn.check_hover(mpos)
                    if btn.check_click([event]):
                        return True
        return False

    def update(self, mouse_pos):
        for btn in self.buttons:
            btn.check_hover(mouse_pos)
        for sp in self.sparks:
            sp['x'] += sp['vx']
            sp['y'] += sp['vy']
            sp['vy'] += 0.12
            sp['life'] -= 1
        self.sparks = [sp for sp in self.sparks if sp['life'] > 0]

    def draw(self, surface):
        draw_with_spring_easing(self, surface, self._render_modal_body)

    def _render_modal_body(self, surface):
        from src.utils import load_image
        from src.save_manager import load_profile
        r = self.rect
        now = pygame.time.get_ticks()
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((10, 8, 14, 205))
        surface.blit(overlay, (0, 0))
        surface.blit(_forge_skin('brown.png', r.w, r.h, (132, 106, 106)), r)
        pygame.draw.rect(surface, (30, 26, 40), r.inflate(-20, -20))
        service_label(surface, "КУЗНИЦА И АСТРАЛЬНЫЙ ГОРН", (r.x + 26, r.y + 20), (255, 185, 75), 20)
        pygame.draw.line(surface, (130, 75, 30), (r.x + 24, r.y + 68), (r.right - 24, r.y + 68))
        shards = max(getattr(self.player, 'purple_shards', 0), load_profile().get('purple_shards', 0))
        resources = f"ЗОЛОТО  {self.player.gold} G    ОСКОЛКИ  {shards}"
        text = get_pixel_font(14).render(resources, True, (239, 195, 116))
        surface.blit(text, (r.right - text.get_width() - 52, r.y + 25))

        def panel(rect, border=(85, 68, 100)):
            surface.blit(_forge_skin('grey.png', rect.w, rect.h, (125, 108, 132)), rect)
            pygame.draw.rect(surface, (21, 18, 30), rect.inflate(-16, -16))
            pygame.draw.rect(surface, border, rect.inflate(-14, -14), 1)

        def clipped_label(text, x, y, width, color=(222, 211, 197), size=14, bold=True):
            old = surface.get_clip()
            surface.set_clip(old.clip(pygame.Rect(x, y, width, size + 7)))
            service_label(surface, text, (x, y), color, size, bold)
            surface.set_clip(old)

        if self.tab == 0:
            left = pygame.Rect(r.x + 26, r.y + 136, 290, 409)
            detail = pygame.Rect(r.x + 330, r.y + 136, 644, 351)
            panel(left)
            panel(detail)
            service_label(surface, "ВАШЕ СНАРЯЖЕНИЕ", (left.x + 20, left.y + 16), (232, 200, 151), 15)
            pygame.draw.line(surface, (106, 79, 55), (left.x + 20, left.y + 42), (left.right - 20, left.y + 42))
            for idx in range(12):
                slot = pygame.Rect(r.x + 51 + (idx % 4) * 60, r.y + 193 + (idx // 4) * 64, 54, 54)
                pygame.draw.rect(surface, (27, 25, 31), slot)
                pygame.draw.rect(surface, (72, 64, 71), slot, 1)
            mouse = pygame.mouse.get_pos()
            for slot, itm, is_eq, slot_label in self.item_slots:
                selected = itm is self.selected_item
                hover = slot.collidepoint(mouse)
                color = (247, 195, 96) if selected else ((200, 167, 110) if hover else RARITY_COLORS.get(itm.rarity, (100, 100, 100)))
                pygame.draw.rect(surface, (49, 38, 33) if selected else (30, 28, 33), slot)
                pygame.draw.rect(surface, color, slot, 2 if selected else 1)
                surface.blit(load_image(itm.image_path, scale=(44, 44)), (slot.x + 5, slot.y + 5))
                if getattr(itm, 'count', 1) > 1:
                    badge_surf = get_pixel_font(10, bold=True).render(f"x{itm.count}", True, (255, 235, 120))
                    bx = slot.right - badge_surf.get_width() - 4
                    by = slot.y + 3
                    bg_rect = pygame.Rect(bx - 2, by - 1, badge_surf.get_width() + 4, badge_surf.get_height() + 2)
                    pygame.draw.rect(surface, (15, 12, 20), bg_rect, border_radius=3)
                    pygame.draw.rect(surface, (140, 110, 50), bg_rect, 1, border_radius=3)
                    surface.blit(badge_surf, (bx, by))
                if itm.upgrade_level:
                    level_text = get_pixel_font(11).render(f"+{itm.upgrade_level}", True, (255, 229, 152))
                    surface.blit(level_text, (slot.right - level_text.get_width() - 3, slot.bottom - 15))
                if is_eq:
                    pygame.draw.rect(surface, (220, 178, 99), (slot.x + 3, slot.y + 3, 4, 4))
            if not self.item_slots:
                service_label(surface, "Нет предметов для улучшения", (left.x + 22, left.y + 263), (160, 150, 144), 13)
            pages = max(1, (len(self.get_available_items()) + 11) // 12)
            if pages > 1:
                service_label(surface, f"{self.item_page + 1} / {pages}", (left.x + 132, r.y + 415), (207, 185, 155), 13)
            service_label(surface, "Золотая метка: надето", (left.x + 22, left.bottom - 40), (155, 143, 131), 12, False)

            up = self.buttons[-2]
            if self.selected_item:
                itm = self.selected_item
                maximum = itm.upgrade_level >= itm.max_level
                can_upgrade = self.player.gold >= 40 and not maximum
                up.ui_style = 'forge_primary' if can_upgrade else 'forge'
                up.text_str = "МАКСИМАЛЬНЫЙ УРОВЕНЬ" if maximum else ("УЛУЧШИТЬ  /  40 G" if can_upgrade else f"НЕ ХВАТАЕТ {40 - self.player.gold} G")
                socket = pygame.Rect(detail.x + 23, detail.y + 20, 96, 96)
                pygame.draw.rect(surface, (29, 25, 40), socket)
                pygame.draw.rect(surface, RARITY_COLORS.get(itm.rarity, (139, 112, 76)), socket, 2)
                effect = max(0.0, 1.0 - (now - self.upgrade_effect_start) / 500.0)
                lift = int(5 * math.sin(effect * math.pi)) if effect else 0
                surface.blit(load_image(itm.image_path, scale=(72, 72)), (socket.x + 12, socket.y + 12 - lift))
                if effect:
                    flash = pygame.Surface(socket.size, pygame.SRCALPHA)
                    flash.fill((255, 211, 110, int(70 * effect)))
                    surface.blit(flash, socket.topleft)
                clipped_label(itm.name, detail.x + 141, detail.y + 27, 465, (240, 225, 202), 20)
                service_label(surface, f"УРОВЕНЬ  +{itm.upgrade_level} / {itm.max_level}", (detail.x + 141, detail.y + 59), (159, 203, 217), 14)
                for index in range(min(10, max(1, itm.max_level))):
                    marker = pygame.Rect(detail.x + 141 + index * 29, detail.y + 88, 22, 8)
                    pygame.draw.rect(surface, (205, 161, 66) if index < itm.upgrade_level else (50, 44, 58), marker)
                    pygame.draw.rect(surface, (124, 101, 70), marker, 1)
                pygame.draw.line(surface, (85, 68, 90), (detail.x + 23, detail.y + 130), (detail.right - 23, detail.y + 130))
                stat = itm.main_stat
                service_label(surface, "ОСНОВНАЯ ХАРАКТЕРИСТИКА", (detail.x + 23, detail.y + 145), (183, 151, 116), 12)
                clipped_label(stat.get('label', ''), detail.x + 23, detail.y + 171, 280, (221, 207, 187), 16)
                value = stat.get('value', 0)
                compare = str(value) if maximum else f"{value}   >   {round(value + stat.get('growth', 2), 1)}"
                clipped_label(compare, detail.x + 400, detail.y + 168, 210, (149, 223, 154), 20)
                pygame.draw.line(surface, (76, 60, 64), (detail.x + 23, detail.y + 205), (detail.right - 23, detail.y + 205))
                service_label(surface, "ДОПОЛНИТЕЛЬНЫЕ СВОЙСТВА", (detail.x + 23, detail.y + 217), (183, 151, 116), 12)
                for idx, sub in enumerate((itm.substats or [])[:4]):
                    x = detail.x + 23 + (idx % 2) * 300
                    y = detail.y + 244 + (idx // 2) * 35
                    pygame.draw.rect(surface, (31, 27, 38), (x, y - 3, 285, 27))
                    clipped_label(sub.get('label', ''), x + 8, y + 2, 185, (206, 197, 189), 13, False)
                    subvalue = f"+{sub.get('value', 0)}" + ('%' if sub.get('is_percent') else '')
                    val = get_pixel_font(13).render(subvalue, True, (165, 204, 220))
                    surface.blit(val, (x + 278 - val.get_width(), y + 2))
                service_label(surface, "Одно свойство улучшается случайно", (detail.x + 23, detail.y + 321), (149, 137, 127), 12, False)
            else:
                up.ui_style = 'forge'
                up.text_str = "ВЫБЕРИТЕ ПРЕДМЕТ"
                surface.blit(load_image('assets/sprites/anvil.png', scale=(96, 96)), (detail.centerx - 48, detail.y + 46))
                service_label(surface, "Выберите предмет слева", (detail.centerx - 105, detail.y + 172), (221, 206, 187), 17)
                service_label(surface, "Здесь появятся характеристики и стоимость", (detail.centerx - 154, detail.y + 202), (148, 138, 131), 12, False)
        else:
            from src.items import ASTRAL_WEAPONS_CATALOGUE
            for idx, data in enumerate(ASTRAL_WEAPONS_CATALOGUE.values()):
                self.buttons[idx + 2].ui_style = 'forge_primary' if shards >= 10 else 'forge'
                card = pygame.Rect(r.x + 26, r.y + 136 + idx * 112, 948, 100)
                panel(card, (120, 78, 132))
                surface.blit(load_image(data['image_path'], scale=(64, 64)), (card.x + 20, card.y + 18))
                clipped_label(data['name'], card.x + 104, card.y + 16, 530, (221, 188, 233), 17)
                for n, line in enumerate(wrap_text(data['description'], get_pixel_font(13, False), 490)[:2]):
                    clipped_label(line, card.x + 104, card.y + 42 + n * 16, 490, (185, 172, 186), 13, False)
                service_label(surface, f"АТАКА +{data['main_stat']['value']}   /   4 СВОЙСТВА", (card.x + 104, card.y + 75), (218, 183, 123), 12)
        if self.tab == 0:
            for sp in self.sparks:
                pygame.draw.rect(surface, sp['col'], (int(sp['x']), int(sp['y']), 3, 3))
        if self.message and now - self.message_time < 2800:
            clipped_label(self.message, r.x + 26, r.bottom - 42, 750, self.message_color, 13)
        else:
            service_label(surface, "1 / 2  ВКЛАДКИ    ENTER  УЛУЧШИТЬ", (r.x + 26, r.bottom - 41), (161, 146, 131), 12)
        for btn in self.buttons:
            btn.draw(surface)
        service_label(surface, "X", self.close_x_rect.topleft, (234, 203, 152), 19)



class ItemInspectModal:
    def __init__(self, parent_modal, item, player, level, source='inventory', slot_name=None):
        self.parent_modal = parent_modal
        self.item = item
        self.player = player
        self.level = level
        self.source = source
        self.slot_name = slot_name
        self.closed = False
        self.font_title = get_pixel_font(16, bold=True)
        self.font_sub = get_pixel_font(12, bold=True)
        self.font_sm = get_pixel_font(11, bold=False)
        self.font_tiny = get_pixel_font(10, bold=False)
        self.open_time = pygame.time.get_ticks()
        self.buttons = []
        self._init_layout()

    def _init_layout(self):
        disp = pygame.display.get_surface()
        sw, sh = disp.get_size() if disp else (1280, 720)
        mw, mh = 490, 440
        self.rect = pygame.Rect((sw - mw) // 2, (sh - mh) // 2, mw, mh)
        self.close_x_rect = pygame.Rect(self.rect.right - 28, self.rect.y + 12, 20, 20)

        r = self.rect
        self.buttons = []
        btn_y = r.bottom - 46
        if self.source == 'equipped':
            if self.slot_name != 'relic':
                eq_btn = Button("СНЯТЬ (E)", (r.x + 20, btn_y), 110, 32, self.action_unequip)
                self.buttons.append(eq_btn)
        else:
            if getattr(self.item, 'slot', '') == 'consumable' or 'heal' in getattr(self.item, 'effects', {}):
                use_btn = Button("ВЫПИТЬ (E)", (r.x + 20, btn_y), 110, 32, self.action_consume)
                self.buttons.append(use_btn)
            else:
                eq_btn = Button("НАДЕТЬ (E)", (r.x + 20, btn_y), 110, 32, self.action_equip)
                self.buttons.append(eq_btn)

        can_forge = getattr(self.level, 'is_hub', False) or getattr(self.player, 'near_blacksmith', False)
        if can_forge:
            forge_btn = Button("В КУЗНИЦУ (K)", (r.x + 145, btn_y), 150, 32, self.action_open_forge)
            self.buttons.append(forge_btn)

        close_btn = Button("ЗАКРЫТЬ (ESC)", (r.right - 145, btn_y), 125, 32, self.close)
        self.buttons.append(close_btn)

    def close(self):
        self.closed = True

    def action_equip(self):
        self.player.equip_item(self.item)
        if getattr(self.level, 'is_hub', False) and hasattr(self.parent_modal, '_sync_hub_profile'):
            self.parent_modal._sync_hub_profile()
        self.close()

    def action_unequip(self):
        if self.slot_name:
            self.player.unequip_item(self.slot_name)
            if getattr(self.level, 'is_hub', False) and hasattr(self.parent_modal, '_sync_hub_profile'):
                self.parent_modal._sync_hub_profile()
        self.close()

    def action_consume(self):
        self.player.consume_item(self.item)
        self.close()

    def action_open_forge(self):
        self.close()
        if hasattr(self.level, 'open_modal'):
            self.level.open_modal('blacksmith')
            if hasattr(self.level, 'modal_instance') and self.level.modal_instance:
                self.level.modal_instance.selected_item = self.item

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_i, pygame.K_TAB, pygame.K_c]:
                self.close()
                return True
            elif event.key == pygame.K_e:
                if self.source == 'equipped':
                    self.action_unequip()
                elif getattr(self.item, 'slot', '') == 'consumable' or 'heal' in getattr(self.item, 'effects', {}):
                    self.action_consume()
                else:
                    self.action_equip()
                return True
            elif event.key == pygame.K_k:
                self.action_open_forge()
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mpos = event.pos
            if not self.rect.collidepoint(mpos):
                self.close()
                return True
            if self.close_x_rect.collidepoint(mpos):
                self.close()
                return True
            for btn in self.buttons:
                if btn.check_click([event]):
                    return True
            return True
        return False

    def update(self, mouse_pos):
        for btn in self.buttons:
            btn.check_hover(mouse_pos)

    def draw(self, surface):
        draw_with_spring_easing(self, surface, self._render_modal_body)

    def _render_modal_body(self, surface):
        sw, sh = surface.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((8, 6, 12, 175))
        surface.blit(overlay, (0, 0))

        r = self.rect
        rarity = getattr(self.item, 'rarity', 'common')
        rarity_colors = {
            'common': (160, 155, 175),
            'rare': (75, 170, 255),
            'epic': (215, 110, 255),
            'legendary': (255, 215, 60)
        }
        frame_col = rarity_colors.get(rarity, (185, 145, 65))
        draw_dialog_frame(surface, r, accent=frame_col)

        from src.utils import load_image
        try:
            x_img = load_image('assets/sprites/btn_close_x.png', scale=(20, 20))
            surface.blit(x_img, self.close_x_rect.topleft)
        except Exception:
            pygame.draw.rect(surface, (45, 35, 55), self.close_x_rect)
            pygame.draw.line(surface, (255, 215, 60), (self.close_x_rect.left+4, self.close_x_rect.top+4), (self.close_x_rect.right-4, self.close_x_rect.bottom-4), 2)
            pygame.draw.line(surface, (255, 215, 60), (self.close_x_rect.left+4, self.close_x_rect.bottom-4), (self.close_x_rect.right-4, self.close_x_rect.top+4), 2)

        icon_box = pygame.Rect(r.x + 22, r.y + 20, 54, 54)
        pygame.draw.rect(surface, (16, 13, 22), icon_box)
        pygame.draw.rect(surface, frame_col, icon_box, 1)

        if hasattr(self.item, 'image') and self.item.image:
            scaled_img = pygame.transform.scale(self.item.image, (42, 42))
            surface.blit(scaled_img, (icon_box.x + 6, icon_box.y + 6))

        up_lvl = getattr(self.item, 'upgrade_level', 0)
        up_str = f" +{up_lvl}" if up_lvl > 0 else ""
        name_surf = self.font_title.render(f"{self.item.name}{up_str}", True, frame_col)
        surface.blit(name_surf, (r.x + 88, r.y + 20))

        count_val = getattr(self.item, 'count', 1)
        if count_val > 1:
            cnt_badge = self.font_tiny.render(f"x{count_val}", True, (255, 235, 120))
            cbx = icon_box.right - cnt_badge.get_width() - 3
            cby = icon_box.bottom - cnt_badge.get_height() - 2
            cbg = pygame.Rect(cbx - 2, cby - 1, cnt_badge.get_width() + 4, cnt_badge.get_height() + 2)
            pygame.draw.rect(surface, (16, 12, 22), cbg, border_radius=3)
            pygame.draw.rect(surface, (140, 110, 50), cbg, 1, border_radius=3)
            surface.blit(cnt_badge, (cbx, cby))

        slot_label = getattr(self.item, 'slot', 'предмет').upper()
        rarity_label = {'common': 'Обычный', 'rare': 'Редкий', 'epic': 'Эпический', 'legendary': 'Легендарный'}.get(rarity, rarity.capitalize())
        cnt_info = f"  |  Стопка: {count_val} шт." if count_val > 1 else ""
        sub_info = f"Слот: {slot_label}  |  Редкость: {rarity_label}{cnt_info}"
        surface.blit(self.font_sm.render(sub_info, True, (170, 165, 185)), (r.x + 88, r.y + 46))

        pygame.draw.line(surface, (80, 70, 95), (r.x + 20, r.y + 86), (r.right - 20, r.y + 86), 1)

        cur_y = r.y + 98
        main_stat = getattr(self.item, 'main_stat', None)
        if main_stat:
            m_box = pygame.Rect(r.x + 20, cur_y, r.width - 40, 42)
            pygame.draw.rect(surface, (25, 20, 34), m_box)
            pygame.draw.rect(surface, (90, 75, 115), m_box, 1)

            lbl = self.font_sub.render(f"ОСНОВНОЙ ПАРАМЕТР:  {main_stat.get('label', 'Атака')}", True, (255, 225, 90))
            val_str = f"+{main_stat.get('value', 0)}"
            val_surf = self.font_title.render(val_str, True, (120, 245, 150))
            surface.blit(lbl, (m_box.x + 12, m_box.y + 12))
            surface.blit(val_surf, (m_box.right - val_surf.get_width() - 14, m_box.y + 10))
            cur_y += 50

        substats = getattr(self.item, 'substats', [])
        s_hdr = self.font_sub.render("ДОПОЛНИТЕЛЬНЫЕ СВОЙСТВА (СУБСТАТЫ):", True, (215, 185, 255))
        surface.blit(s_hdr, (r.x + 20, cur_y))
        cur_y += 22

        if substats:
            for sub in substats[:4]:
                s_box = pygame.Rect(r.x + 20, cur_y, r.width - 40, 24)
                pygame.draw.rect(surface, (22, 18, 30), s_box)
                pygame.draw.rect(surface, (45, 38, 60), s_box, 1)

                s_val = f"+{sub['value']}%" if sub.get('is_percent') else f"+{sub['value']}"
                rolls = sub.get('rolls', 0)
                star_str = f"  [{rolls}+]" if rolls > 0 else ""
                col = (255, 215, 60) if rolls > 0 else (170, 215, 255)

                surface.blit(self.font_sm.render(f"- {sub.get('label', '')}", True, (210, 205, 220)), (s_box.x + 10, s_box.y + 4))
                surface.blit(self.font_sm.render(f"{s_val}{star_str}", True, col), (s_box.right - 95, s_box.y + 4))
                cur_y += 28
        else:
            eff_strs = [f"+{v} {k}" for k, v in getattr(self.item, 'effects', {}).items()]
            surface.blit(self.font_sm.render(", ".join(eff_strs) or "Нет особых свойств", True, (160, 210, 255)), (r.x + 20, cur_y))
            cur_y += 26

        cur_y += 6
        desc = getattr(self.item, 'description', '')
        if desc:
            pygame.draw.line(surface, (60, 52, 75), (r.x + 20, cur_y), (r.right - 20, cur_y), 1)
            cur_y += 8
            lore_surf = self.font_tiny.render(f"«{desc[:65]}»", True, (165, 155, 180))
            surface.blit(lore_surf, (r.x + 24, cur_y))

        for btn in self.buttons:
            btn.draw(surface)


class EquipmentModal:
    def __init__(self, level, player):
        self.level = level
        self.player = player
        self.font_title = get_pixel_font(18, bold=True)
        self.font_sub = get_pixel_font(12, bold=True)
        self.font_sm = get_pixel_font(11, bold=False)
        self.font_tiny = get_pixel_font(10, bold=False)
        self.inspect_modal = None
        self.inventory_page = 0
        self.open_time = pygame.time.get_ticks()
        self.hovered_item = None
        self.hovered_slot = None
        self.hovered_rect = None
        self.hovered_source = None
        self.hovered_mouse_pos = (0, 0)
        self._init_layout()

    def prev_inventory_page(self):
        inv = getattr(self.player, 'inventory', [])
        pages = max(1, (len(inv) + 15) // 16)
        self.inventory_page = (self.inventory_page - 1) % pages

    def next_inventory_page(self):
        inv = getattr(self.player, 'inventory', [])
        pages = max(1, (len(inv) + 15) // 16)
        self.inventory_page = (self.inventory_page + 1) % pages

    def _init_layout(self):
        disp = pygame.display.get_surface()
        sw, sh = disp.get_size() if disp else (1280, 720)
        mw, mh = min(920, sw - 20), min(580, sh - 20)
        self.rect = pygame.Rect((sw - mw) // 2, (sh - mh) // 2, mw, mh)
        self.close_x_rect = pygame.Rect(self.rect.right - 28, self.rect.y + 12, 20, 20)

        self.buttons = []
        r = self.rect
        close_btn = Button("ЗАКРЫТЬ (ESC / I)", (r.centerx - 80, r.bottom - 42), 160, 30, self.close)
        self.buttons.append(close_btn)

        # Backpack page navigation buttons
        self.btn_inv_prev = Button("<", (r.x + 785, r.y + 57), 24, 24, self.prev_inventory_page)
        self.btn_inv_next = Button(">", (r.x + 855, r.y + 57), 24, 24, self.next_inventory_page)
        self.buttons.extend([self.btn_inv_prev, self.btn_inv_next])

        # Flanking Anatomical Sockets (Left: weapon, offhand, boots | Right: armor, amulet, ring)
        self.slot_rects = {
            'weapon': pygame.Rect(r.x + 22, r.y + 68, 182, 54),
            'offhand': pygame.Rect(r.x + 22, r.y + 128, 182, 54),
            'boots': pygame.Rect(r.x + 22, r.y + 188, 182, 54),
            'armor': pygame.Rect(r.x + 456, r.y + 68, 182, 54),
            'amulet': pygame.Rect(r.x + 456, r.y + 128, 182, 54),
            'ring': pygame.Rect(r.x + 456, r.y + 188, 182, 54)
        }

        # Center Paperdoll & Radar Coordinates
        self.pedestal_cx = r.x + 330
        self.pedestal_cy = r.y + 168
        self.radar_cx = r.x + 330
        self.radar_cy = r.y + 328
        self.radar_radius = 62

        # 16-slot Backpack Grid (4x4) & Relics Rack
        grid_x = r.x + 658
        grid_y = r.y + 88
        self.backpack_rects = [
            pygame.Rect(grid_x + (i % 4) * 58, grid_y + (i // 4) * 58, 52, 52)
            for i in range(16)
        ]
        self.relic_rects = [
            pygame.Rect(grid_x + i * 58, r.y + 352, 52, 52)
            for i in range(4)
        ]

    def close(self):
        self.level.active_modal = None

    def handle_event(self, event):
        if self.inspect_modal is not None:
            handled = self.inspect_modal.handle_event(event)
            if self.inspect_modal.closed:
                self.inspect_modal = None
            return True

        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_i, pygame.K_TAB, pygame.K_c]:
                self.close()
                return True
            elif event.key in [pygame.K_LEFT, pygame.K_q]:
                self.prev_inventory_page()
                return True
            elif event.key in [pygame.K_RIGHT, pygame.K_e]:
                self.next_inventory_page()
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mpos = event.pos
            if not self.rect.collidepoint(mpos):
                self.close()
                return True
            if self.close_x_rect.collidepoint(mpos):
                self.close()
                return True
            for btn in self.buttons:
                if btn.rect.collidepoint(mpos):
                    btn.hovered = True
                    if btn.check_click([event]):
                        return True

            # Inspect equipped item
            for slot, s_rect in self.slot_rects.items():
                if s_rect.collidepoint(mpos):
                    itm = self.player.equipped.get(slot)
                    effective_slot = slot
                    if not itm and slot == 'offhand' and self.player.equipped.get('accessory'):
                        itm = self.player.equipped.get('accessory')
                        effective_slot = 'accessory'
                    if itm:
                        self.inspect_modal = ItemInspectModal(self, itm, self.player, self.level, source='equipped', slot_name=effective_slot)
                        return True

            # Inspect inventory backpack item (with pagination offset)
            inv = self.player.inventory
            for idx, box_rect in enumerate(self.backpack_rects):
                real_idx = self.inventory_page * 16 + idx
                if real_idx < len(inv) and box_rect.collidepoint(mpos):
                    self.inspect_modal = ItemInspectModal(self, inv[real_idx], self.player, self.level, source='inventory')
                    return True

            # Inspect relic
            relics = getattr(self.player, 'relics', [])
            for idx, r_rect in enumerate(self.relic_rects):
                if idx < len(relics) and r_rect.collidepoint(mpos):
                    self.inspect_modal = ItemInspectModal(self, relics[idx], self.player, self.level, source='equipped', slot_name='relic')
                    return True
        return False

    def _sync_hub_profile(self):
        from src.save_manager import load_profile, save_profile
        prof = load_profile()
        for s in ['weapon', 'offhand', 'armor', 'boots', 'amulet', 'ring']:
            it = self.player.equipped.get(s)
            prof.setdefault('equipped', {})[s] = it.to_dict() if it else None
        prof['armory'] = [it.to_dict() for it in getattr(self.player, 'inventory', []) if it and hasattr(it, 'to_dict')]
        save_profile(prof)

    def update(self, mouse_pos):
        if self.inspect_modal is not None:
            self.inspect_modal.update(mouse_pos)
            return
        for btn in self.buttons:
            btn.check_hover(mouse_pos)

        # Track hover for comparison tooltips
        self.hovered_item = None
        self.hovered_slot = None
        self.hovered_rect = None
        self.hovered_source = None
        self.hovered_mouse_pos = mouse_pos

        for slot, s_rect in self.slot_rects.items():
            if s_rect.collidepoint(mouse_pos):
                itm = self.player.equipped.get(slot)
                effective_slot = slot
                if not itm and slot == 'offhand' and self.player.equipped.get('accessory'):
                    itm = self.player.equipped.get('accessory')
                    effective_slot = 'accessory'
                if itm:
                    self.hovered_item = itm
                    self.hovered_slot = effective_slot
                    self.hovered_rect = s_rect
                    self.hovered_source = 'equipped'
                    return

        inv = self.player.inventory
        for idx, box_rect in enumerate(self.backpack_rects):
            real_idx = self.inventory_page * 16 + idx
            if real_idx < len(inv) and box_rect.collidepoint(mouse_pos):
                self.hovered_item = inv[real_idx]
                self.hovered_slot = getattr(inv[real_idx], 'slot', None)
                self.hovered_rect = box_rect
                self.hovered_source = 'inventory'
                return

        relics = getattr(self.player, 'relics', [])
        for idx, r_rect in enumerate(self.relic_rects):
            if idx < len(relics) and r_rect.collidepoint(mouse_pos):
                self.hovered_item = relics[idx]
                self.hovered_slot = 'relic'
                self.hovered_rect = r_rect
                self.hovered_source = 'relic'
                return

    def _calculate_stat_deltas(self, item):
        """Calculate stat deltas comparing item against currently equipped item in matching slot."""
        slot = getattr(item, 'slot', None)
        if not slot or slot not in self.player.equipped:
            return None
        curr_equipped = self.player.equipped.get(slot)
        stat_keys = [
            ('attack', 'Атака', ''),
            ('defense', 'Защита', ''),
            ('crit_rate', 'Крит. шанс', '%'),
            ('crit_dmg', 'Крит. урон', '%'),
            ('speed', 'Скорость', ''),
            ('health', 'Здоровье', ''),
            ('energy', 'Энергия', ''),
        ]
        deltas = []
        item_fx = getattr(item, 'effects', {}) or {}
        curr_fx = getattr(curr_equipped, 'effects', {}) or {} if curr_equipped else {}
        for k, label, suffix in stat_keys:
            new_val = item_fx.get(k, 0)
            old_val = curr_fx.get(k, 0)
            if new_val == 0 and old_val == 0:
                continue
            diff = new_val - old_val
            deltas.append({
                'key': k,
                'label': label,
                'new_val': new_val,
                'old_val': old_val,
                'diff': diff,
                'suffix': suffix
            })
        return deltas, curr_equipped

    def draw(self, surface):
        draw_with_spring_easing(self, surface, self._render_modal_body)

    def _draw_paperdoll_hero(self, surface, center_x, center_y):
        import math
        # 1. Runic glowing pedestal
        pygame.draw.ellipse(surface, (24, 20, 32), (center_x - 56, center_y - 2, 112, 24))
        pygame.draw.ellipse(surface, (185, 145, 65), (center_x - 56, center_y - 2, 112, 24), 2)
        pygame.draw.ellipse(surface, (120, 95, 45), (center_x - 44, center_y + 2, 88, 16), 1)
        # Runic gems on pedestal rim
        for gx in (center_x - 38, center_x - 14, center_x + 14, center_x + 38):
            pygame.draw.circle(surface, (255, 225, 100), (gx, center_y + 9), 2)

        # 2. Animated breathing hero sprite
        now = pygame.time.get_ticks()
        breath = 1.0 + 0.035 * math.sin(now / 320.0)
        hero_img = getattr(self.player, 'image', None)
        if hero_img:
            hw, hh = int(58 * breath), int(70 * breath)
            scaled_hero = pygame.transform.scale(hero_img, (hw, hh))
            surface.blit(scaled_hero, (center_x - hw // 2, center_y - hh + 12))

        # 3. Hero Level Badge
        badge_rect = pygame.Rect(center_x - 70, center_y - 78, 140, 20)
        pygame.draw.rect(surface, (20, 16, 26), badge_rect, border_radius=4)
        pygame.draw.rect(surface, (185, 145, 65), badge_rect, 1, border_radius=4)
        lvl_surf = self.font_tiny.render(f"ГЕРОЙ • УРОВЕНЬ {self.player.level}", True, (255, 225, 90))
        surface.blit(lvl_surf, (center_x - lvl_surf.get_width() // 2, badge_rect.y + 3))

    def _draw_stat_hexagon(self, surface, cx, cy, radius):
        import math
        max_hp = self.player.stats.get('health', 100) if hasattr(self.player, 'stats') else getattr(self.player, 'max_health', 100)
        max_en = self.player.stats.get('energy', 60) if hasattr(self.player, 'stats') else getattr(self.player, 'max_energy', 60)
        atk_val = getattr(self.player, 'attack_power', self.player.stats.get('attack', 10) if hasattr(self.player, 'stats') else 10)
        def_val = getattr(self.player, 'defense', self.player.stats.get('defense', 0) if hasattr(self.player, 'stats') else 0)
        crit_rate_val = getattr(self.player, 'crit_rate', 5.0)
        spd_val = getattr(self.player, 'speed', self.player.stats.get('speed', 4.0) if hasattr(self.player, 'stats') else 4.0)

        stats_meta = [
            ('HP', max_hp, 200.0, -90),
            ('ATK', atk_val, 50.0, -30),
            ('CRIT', crit_rate_val, 40.0, 30),
            ('ENG', max_en, 120.0, 90),
            ('DEF', def_val, 30.0, 150),
            ('SPD', spd_val, 8.0, 210),
        ]

        # 1. Concentric guide polygons
        for fraction in (0.33, 0.66, 1.0):
            ring_pts = [
                (cx + radius * fraction * math.cos(math.radians(ang)),
                 cy + radius * fraction * math.sin(math.radians(ang)))
                for _, _, _, ang in stats_meta
            ]
            pygame.draw.polygon(surface, (55, 48, 68), ring_pts, 1)

        # 2. Spokes radiating from center
        for _, _, _, ang in stats_meta:
            ex = cx + radius * math.cos(math.radians(ang))
            ey = cy + radius * math.sin(math.radians(ang))
            pygame.draw.line(surface, (65, 55, 80), (cx, cy), (ex, ey), 1)

        # 3. Translucent player stat polygon
        poly_pts = []
        for _, val, cap, ang in stats_meta:
            norm = max(0.18, min(1.0, float(val) / cap))
            px = cx + radius * norm * math.cos(math.radians(ang))
            py = cy + radius * norm * math.sin(math.radians(ang))
            poly_pts.append((px, py))

        poly_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(poly_surf, (80, 190, 255, 85), poly_pts)
        pygame.draw.polygon(poly_surf, (140, 230, 255, 235), poly_pts, 2)
        surface.blit(poly_surf, (0, 0))

        # 4. Vertices and Stat Labels
        for i, (label, val, _, ang) in enumerate(stats_meta):
            vx, vy = poly_pts[i]
            pygame.draw.circle(surface, (255, 225, 90), (int(vx), int(vy)), 3)
            lx = cx + (radius + 14) * math.cos(math.radians(ang))
            ly = cy + (radius + 14) * math.sin(math.radians(ang))
            lbl_surf = self.font_tiny.render(label, True, (255, 215, 60))
            surface.blit(lbl_surf, (lx - lbl_surf.get_width() // 2, ly - lbl_surf.get_height() // 2))

    def _draw_hover_comparison_tooltip(self, surface, item, mouse_pos):
        if not item:
            return
        res = self._calculate_stat_deltas(item)
        card_w = 230
        card_h = 175 if res and res[0] else 120
        mx, my = mouse_pos
        cx = min(surface.get_width() - card_w - 15, max(15, mx + 16))
        cy = min(surface.get_height() - card_h - 15, max(15, my - 20))

        # Card body
        t_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        t_surf.fill((16, 13, 22, 245))
        pygame.draw.rect(t_surf, (195, 155, 65), [0, 0, card_w, card_h], 1, border_radius=5)
        surface.blit(t_surf, (cx, cy))

        # Item title & rarity
        rarity_border = {
            'common': (150, 145, 165),
            'rare': (85, 180, 255),
            'epic': (225, 120, 255),
            'legendary': (255, 215, 60)
        }
        r_col = rarity_border.get(getattr(item, 'rarity', 'common'), (255, 215, 60))
        up_str = f" +{item.upgrade_level}" if getattr(item, 'upgrade_level', 0) > 0 else ""
        title_surf = self.font_sub.render(f"{item.name[:18]}{up_str}", True, r_col)
        surface.blit(title_surf, (cx + 10, cy + 8))

        slot_label = getattr(item, 'slot', 'предмет')
        tag_surf = self.font_tiny.render(f"[{slot_label.upper()} • {getattr(item, 'rarity', 'обычный').upper()}]", True, (150, 140, 165))
        surface.blit(tag_surf, (cx + 10, cy + 26))

        pygame.draw.line(surface, (60, 50, 75), (cx + 8, cy + 42), (cx + card_w - 8, cy + 42), 1)

        cur_y = cy + 48
        if res and res[0]:
            deltas, curr_equipped = res
            curr_name = curr_equipped.name if curr_equipped else "Пусто"
            sub_surf = self.font_tiny.render(f"Сравнение: vs {curr_name[:12]}", True, (215, 195, 140))
            surface.blit(sub_surf, (cx + 10, cur_y))
            cur_y += 16
            for d in deltas[:5]:
                diff = d['diff']
                diff_val_str = f"{diff:.1f}" if (isinstance(diff, float) and diff % 1 != 0) else f"{int(diff)}"
                if diff > 0:
                    diff_str = f"(+{diff_val_str}{d['suffix']})"
                    diff_col = (80, 245, 120)
                elif diff < 0:
                    diff_str = f"({diff_val_str}{d['suffix']})"
                    diff_col = (255, 95, 95)
                else:
                    diff_str = "(=)"
                    diff_col = (175, 170, 185)

                val_str = f"{d['label']}: {d['new_val']}{d['suffix']} "
                v_surf = self.font_tiny.render(val_str, True, (220, 215, 230))
                d_surf = self.font_tiny.render(diff_str, True, diff_col)
                surface.blit(v_surf, (cx + 10, cur_y))
                surface.blit(d_surf, (cx + 10 + v_surf.get_width(), cur_y))
                cur_y += 15
        else:
            desc = getattr(item, 'description', '') or "Предмет снаряжения или реликвия."
            d_surf = self.font_tiny.render(desc[:30], True, (175, 165, 185))
            surface.blit(d_surf, (cx + 10, cur_y))

        hint_surf = self.font_tiny.render("[ЛКМ] Осмотреть / Надеть", True, (140, 135, 155))
        surface.blit(hint_surf, (cx + 10, cy + card_h - 18))

    def _render_modal_body(self, surface):
        sw, sh = surface.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((10, 8, 14, 195))
        surface.blit(overlay, (0, 0))

        r = self.rect
        draw_dialog_frame(surface, r, accent=(185, 145, 65))

        # Close [X] button
        from src.utils import load_image
        try:
            x_img = load_image('assets/sprites/btn_close_x.png', scale=(20, 20))
            surface.blit(x_img, self.close_x_rect.topleft)
        except Exception:
            pygame.draw.rect(surface, (45, 35, 55), self.close_x_rect)
            pygame.draw.line(surface, (255, 215, 60), (self.close_x_rect.left+4, self.close_x_rect.top+4), (self.close_x_rect.right-4, self.close_x_rect.bottom-4), 2)
            pygame.draw.line(surface, (255, 215, 60), (self.close_x_rect.left+4, self.close_x_rect.bottom-4), (self.close_x_rect.right-4, self.close_x_rect.top+4), 2)

        # Header Title
        title_surf = self.font_title.render("СНАРЯЖЕНИЕ И ХАРАКТЕРИСТИКИ", True, (255, 215, 60))
        surface.blit(title_surf, (r.centerx - title_surf.get_width() // 2, r.y + 16))
        pygame.draw.line(surface, (120, 95, 45), (r.x + 20, r.y + 48), (r.right - 20, r.y + 48), 1)

        # Vertical Column Dividers
        pygame.draw.line(surface, (60, 50, 75), (r.x + 215, r.y + 55), (r.x + 215, r.bottom - 60), 1)
        pygame.draw.line(surface, (60, 50, 75), (r.x + 445, r.y + 55), (r.x + 445, r.y + 248), 1)
        pygame.draw.line(surface, (60, 50, 75), (r.x + 648, r.y + 55), (r.x + 648, r.bottom - 60), 1)

        slot_names = {
            'weapon': 'ОРУЖИЕ',
            'offhand': 'ЩИТ / ОФФХЭНД',
            'armor': 'ДОСПЕХ',
            'boots': 'ОБУВЬ',
            'amulet': 'АМУЛЕТ',
            'ring': 'КОЛЬЦО'
        }
        rarity_border = {
            'common': (120, 115, 135),
            'rare': (75, 170, 255),
            'epic': (215, 110, 255),
            'legendary': (255, 215, 60)
        }

        # 1. Draw Flanking Anatomical Sockets
        for slot, s_rect in self.slot_rects.items():
            itm = self.player.equipped.get(slot)
            if not itm and slot == 'offhand' and self.player.equipped.get('accessory'):
                itm = self.player.equipped.get('accessory')
            pygame.draw.rect(surface, (28, 24, 35), s_rect)
            b_col = rarity_border.get(getattr(itm, 'rarity', ''), (65, 55, 80)) if itm else (65, 55, 80)
            pygame.draw.rect(surface, b_col, s_rect, 1)

            s_label = self.font_tiny.render(slot_names.get(slot, slot.upper()), True, (150, 140, 165))
            surface.blit(s_label, (s_rect.x + 8, s_rect.y + 3))

            if itm:
                if hasattr(itm, 'image') and itm.image:
                    scaled_icon = pygame.transform.scale(itm.image, (34, 34))
                    surface.blit(scaled_icon, (s_rect.x + 8, s_rect.y + 15))
                n_col = rarity_border.get(getattr(itm, 'rarity', 'common'), (255, 225, 80))
                up_str = f" +{itm.upgrade_level}" if getattr(itm, 'upgrade_level', 0) > 0 else ""
                n_surf = self.font_sub.render(f"{itm.name[:13]}{up_str}", True, n_col)
                surface.blit(n_surf, (s_rect.x + 46, s_rect.y + 16))
                hint_surf = self.font_tiny.render("[ЛКМ] Осмотр статов", True, (120, 115, 135))
                surface.blit(hint_surf, (s_rect.x + 46, s_rect.y + 34))
            else:
                empty_surf = self.font_sm.render("<Пусто>", True, (95, 85, 110))
                surface.blit(empty_surf, (s_rect.x + 46, s_rect.y + 20))

        # 2. Draw Center Paperdoll Hero & Stat Radar
        self._draw_paperdoll_hero(surface, self.pedestal_cx, self.pedestal_cy)
        self._draw_stat_hexagon(surface, self.radar_cx, self.radar_cy, self.radar_radius)

        # 3. Draw Detailed Stat Sheet (Bottom Left Card)
        stat_card = pygame.Rect(r.x + 22, r.y + 252, 182, 252)
        pygame.draw.rect(surface, (22, 19, 28), stat_card)
        pygame.draw.rect(surface, (60, 50, 75), stat_card, 1)

        crit_rate_val = getattr(self.player, 'crit_rate', 5.0)
        crit_dmg_val = getattr(self.player, 'crit_dmg', 150.0)
        p_shards = getattr(self.player, 'purple_shards', 0)
        max_hp = self.player.stats.get('health', 100) if hasattr(self.player, 'stats') else getattr(self.player, 'max_health', 100)
        max_en = self.player.stats.get('energy', 60) if hasattr(self.player, 'stats') else getattr(self.player, 'max_energy', 60)
        atk_val = getattr(self.player, 'attack_power', self.player.stats.get('attack', 10) if hasattr(self.player, 'stats') else 10)
        def_val = getattr(self.player, 'defense', self.player.stats.get('defense', 0) if hasattr(self.player, 'stats') else 0)
        spd_val = getattr(self.player, 'speed', self.player.stats.get('speed', 4.0) if hasattr(self.player, 'stats') else 4.0)

        hdr_stat = self.font_tiny.render("ХАРАКТЕРИСТИКИ", True, (255, 215, 60))
        surface.blit(hdr_stat, (stat_card.x + 10, stat_card.y + 6))
        pygame.draw.line(surface, (60, 50, 75), (stat_card.x + 8, stat_card.y + 20), (stat_card.right - 8, stat_card.y + 20), 1)

        stat_lines = [
            ("Здоровье:", f"{int(self.player.health)}/{max_hp}", (255, 110, 110)),
            ("Энергия:", f"{int(self.player.energy)}/{max_en}", (90, 200, 255)),
            ("Атака:", f"{atk_val}", (255, 220, 80)),
            ("Защита:", f"{def_val}", (140, 200, 255)),
            ("Крит. Шанс:", f"{crit_rate_val:.1f}%", (255, 215, 60)),
            ("Крит. Урон:", f"{crit_dmg_val:.1f}%", (220, 140, 255)),
            ("Скорость:", f"{spd_val:.1f}", (140, 235, 140)),
            ("Золото:", f"{self.player.gold} G", (255, 235, 90)),
            ("Осколки:", f"{p_shards}", (215, 120, 255))
        ]
        for idx, (label, val, col) in enumerate(stat_lines):
            ly = stat_card.y + 26 + idx * 24
            surface.blit(self.font_tiny.render(label, True, (180, 175, 195)), (stat_card.x + 10, ly))
            surface.blit(self.font_tiny.render(val, True, col), (stat_card.x + 95, ly))

        # 4. Draw Backpack (4x4 Grid with pagination & stack badges)
        if hasattr(self.player, 'consolidate_inventory'):
            self.player.consolidate_inventory()
        inv = self.player.inventory
        total_pages = max(1, (len(inv) + 15) // 16)
        self.inventory_page = max(0, min(self.inventory_page, total_pages - 1))

        grid_x = r.x + 658
        inv_hdr = self.font_sub.render(f"РЮКЗАК ({len(inv)})", True, (255, 215, 60))
        surface.blit(inv_hdr, (grid_x, r.y + 62))

        # Page indicator between < and > buttons
        page_str = f"{self.inventory_page + 1}/{total_pages}"
        page_surf = self.font_tiny.render(page_str, True, (215, 195, 140))
        surface.blit(page_surf, (r.x + 825 - page_surf.get_width() // 2, r.y + 64))

        for idx in range(16):
            box_rect = self.backpack_rects[idx]
            pygame.draw.rect(surface, (28, 24, 35), box_rect)
            real_idx = self.inventory_page * 16 + idx

            if real_idx < len(inv):
                itm = inv[real_idx]
                r_col = rarity_border.get(getattr(itm, 'rarity', 'common'), (60, 50, 75))
                pygame.draw.rect(surface, r_col, box_rect, 1)
                if hasattr(itm, 'image') and itm.image:
                    scaled_itm = pygame.transform.scale(itm.image, (38, 38))
                    surface.blit(scaled_itm, (box_rect.x + 7, box_rect.y + 7))
                if getattr(itm, 'upgrade_level', 0) > 0:
                    badge_surf = self.font_tiny.render(f"+{itm.upgrade_level}", True, (255, 215, 60))
                    surface.blit(badge_surf, (box_rect.x + 32, box_rect.y + 4))
                if getattr(itm, 'count', 1) > 1:
                    cnt_surf = self.font_tiny.render(f"x{itm.count}", True, (255, 235, 120))
                    cbx = box_rect.right - cnt_surf.get_width() - 4
                    cby = box_rect.bottom - cnt_surf.get_height() - 3
                    cbg = pygame.Rect(cbx - 2, cby - 1, cnt_surf.get_width() + 4, cnt_surf.get_height() + 2)
                    pygame.draw.rect(surface, (16, 12, 22), cbg, border_radius=3)
                    pygame.draw.rect(surface, (140, 110, 50), cbg, 1, border_radius=3)
                    surface.blit(cnt_surf, (cbx, cby))
            else:
                pygame.draw.rect(surface, (45, 40, 55), box_rect, 1)

        # 5. Draw Relics Rack
        rel_hdr = self.font_sub.render("РЕЛИКВИИ ЗАБЕГА:", True, (255, 215, 60))
        surface.blit(rel_hdr, (grid_x, r.y + 328))
        relics = getattr(self.player, 'relics', [])

        for idx in range(4):
            r_rect = self.relic_rects[idx]
            pygame.draw.rect(surface, (28, 24, 35), r_rect)
            pygame.draw.rect(surface, (180, 100, 255) if idx < len(relics) else (45, 40, 55), r_rect, 1)
            if idx < len(relics):
                r_item = relics[idx]
                if hasattr(r_item, 'image') and r_item.image:
                    scaled_r = pygame.transform.scale(r_item.image, (38, 38))
                    surface.blit(scaled_r, (r_rect.x + 7, r_rect.y + 7))

        # 6. Buttons
        for btn in self.buttons:
            btn.draw(surface)

        # 7. Hover Comparison Tooltip (when inspect modal is not active)
        if self.hovered_item and self.inspect_modal is None:
            self._draw_hover_comparison_tooltip(surface, self.hovered_item, self.hovered_mouse_pos)

        # 8. Inspect Modal (top layer)
        if self.inspect_modal is not None:
            self.inspect_modal.draw(surface)
