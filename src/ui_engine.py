"""
Production-grade Sprite-based UI Engine for Rogue 2D.
Eliminates procedural flat-box "AI slop" and delivers authentic, tactile,
textured pixel-art interfaces using 9-slice sprites, tactile buttons,
recessed inlays, and crisp Cyrillic typography.
"""

import os
import pygame

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_ASSET_DIR = os.path.join(BASE_DIR, 'assets', 'sprites', 'ui_kenney')
FONT_PATH = os.path.join(BASE_DIR, 'assets', 'fonts', 'pixel_font.ttf')

_RAW_TEXTURES = {}
_NINESLICE_CACHE = {}
_FONT_CACHE = {}


def get_font(size=14, bold=False, font_name=None):
    """Retrieve cached font with full Cyrillic support."""
    key = (size, bold, font_name)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    font = None
    if font_name == 'pixel' and os.path.exists(FONT_PATH):
        try:
            font = pygame.font.Font(FONT_PATH, size)
        except Exception:
            font = None

    if font is None:
        if not pygame.font.get_init():
            pygame.font.init()
        # Clean retro typography with crisp Cyrillic support
        for name in ['tahoma', 'consolas', 'cascadiamono', 'segoeui', 'arial']:
            try:
                font = pygame.font.SysFont(name, size, bold=bold)
                if font:
                    break
            except Exception:
                continue
        if font is None:
            font = pygame.font.SysFont('arial', size, bold=bold)

    _FONT_CACHE[key] = font
    return font


def _load_raw_texture(filename):
    """Load and cache raw UI texture."""
    if filename not in _RAW_TEXTURES:
        full_path = os.path.join(UI_ASSET_DIR, filename)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"UI texture not found: {full_path}")
        surf = pygame.image.load(full_path)
        if pygame.display.get_surface():
            try:
                surf = surf.convert_alpha()
            except Exception:
                pass
        _RAW_TEXTURES[filename] = surf
    return _RAW_TEXTURES[filename]


def get_nineslice(texture_name, width, height, corner=16, tint=None):
    """
    Generate or retrieve a cached 9-slice rendered surface of given dimensions.
    Supports color tinting (e.g. dark gothic stone, aged bronze, molten gold).
    """
    width = max(corner * 2, int(width))
    height = max(corner * 2, int(height))
    cache_key = (texture_name, width, height, corner, tint)
    if cache_key in _NINESLICE_CACHE:
        return _NINESLICE_CACHE[cache_key]

    src = _load_raw_texture(texture_name)
    sw, sh = src.get_size()
    cw = min(corner, sw // 3)
    ch = min(corner, sh // 3)

    out = pygame.Surface((width, height), pygame.SRCALPHA)

    # 9 Slices from source
    tl = src.subsurface((0, 0, cw, ch))
    t  = src.subsurface((cw, 0, sw - 2 * cw, ch))
    tr = src.subsurface((sw - cw, 0, cw, ch))

    l  = src.subsurface((0, ch, cw, sh - 2 * ch))
    c  = src.subsurface((cw, ch, sw - 2 * cw, sh - 2 * ch))
    r  = src.subsurface((sw - cw, ch, cw, sh - 2 * ch))

    bl = src.subsurface((0, sh - ch, cw, ch))
    b  = src.subsurface((cw, sh - ch, sw - 2 * cw, ch))
    br = src.subsurface((sw - cw, sh - ch, cw, ch))

    # Corners
    out.blit(tl, (0, 0))
    out.blit(tr, (width - cw, 0))
    out.blit(bl, (0, height - ch))
    out.blit(br, (width - cw, height - ch))

    # Edges
    edge_w = width - 2 * cw
    edge_h = height - 2 * ch

    if edge_w > 0:
        out.blit(pygame.transform.scale(t, (edge_w, ch)), (cw, 0))
        out.blit(pygame.transform.scale(b, (edge_w, ch)), (cw, height - ch))

    if edge_h > 0:
        out.blit(pygame.transform.scale(l, (cw, edge_h)), (0, ch))
        out.blit(pygame.transform.scale(r, (cw, edge_h)), (width - cw, ch))

    if edge_w > 0 and edge_h > 0:
        out.blit(pygame.transform.scale(c, (edge_w, edge_h)), (cw, ch))

    if tint is not None:
        tint_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        tint_surf.fill((*tint, 255))
        out.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    _NINESLICE_CACHE[cache_key] = out
    return out


def draw_panel(surface, rect, texture='brown.png', corner=16, tint=None, shadow=True, shadow_offset=(4, 6), shadow_alpha=130):
    """Draw a textured 9-slice panel with an optional ambient drop shadow."""
    r = pygame.Rect(rect)
    if shadow:
        shadow_surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, shadow_alpha))
        surface.blit(shadow_surf, (r.x + shadow_offset[0], r.y + shadow_offset[1]))

    slice_surf = get_nineslice(texture, r.width, r.height, corner=corner, tint=tint)
    surface.blit(slice_surf, r.topleft)


def draw_inlay(surface, rect, texture='brown_inlay.png', corner=14, tint=None):
    """Draw a recessed inlay socket for item cards, dialogue boxes, or slots."""
    r = pygame.Rect(rect)
    slice_surf = get_nineslice(texture, r.width, r.height, corner=corner, tint=tint)
    surface.blit(slice_surf, r.topleft)


def draw_text(surface, text, pos, font_size=13, color=(240, 230, 215), shadow=True,
              shadow_color=(12, 10, 16), center=False, right=False, bold=True, font_name=None):
    """Render crisp typography with an authentic 1px drop shadow for retro readability."""
    font = get_font(font_size, bold=bold, font_name=font_name)
    text_str = str(text)
    txt_surf = font.render(text_str, True, color)
    w, h = txt_surf.get_size()

    x, y = pos
    if center:
        x -= w // 2
        y -= h // 2
    elif right:
        x -= w

    if shadow:
        shd_surf = font.render(text_str, True, shadow_color)
        surface.blit(shd_surf, (x + 1, y + 1))

    surface.blit(txt_surf, (x, y))
    return pygame.Rect(x, y, w, h)


class SpriteButton:
    """
    Tactile, sprite-based button with 3 physical states:
    Normal -> Hover (gold glow + audio) -> Pressed (2px downward displacement + click audio).
    """
    def __init__(self, text, pos, width, height, callback=None, style='brown', hotkey=None, tint=None):
        self.text = text
        self.rect = pygame.Rect(pos[0], pos[1], width, height)
        self.callback = callback
        self.style = style  # 'brown', 'grey', 'yellow', 'blue', 'red'
        self.hotkey = hotkey
        self.tint = tint
        self.hovered = False
        self.was_hovered = False
        self.pressed = False
        self.enabled = True
        self.font_size = 13
        self.custom_data = None

    def check_hover(self, mouse_pos):
        if not self.enabled:
            self.hovered = False
            return False
        self.hovered = self.rect.collidepoint(mouse_pos)
        if self.hovered and not self.was_hovered:
            self._play_hover_sound()
        self.was_hovered = self.hovered
        return self.hovered

    def handle_event(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed:
                self.pressed = False
                if self.rect.collidepoint(event.pos):
                    self._play_click_sound()
                    if self.callback:
                        self.callback()
                    return True
        return False

    def check_click(self, events):
        """Compatibility with legacy check_click API."""
        for ev in events:
            if self.handle_event(ev):
                return True
        return False

    def _play_hover_sound(self):
        try:
            from src.sound_manager import play_sfx
            play_sfx('step_0')
        except Exception:
            pass

    def _play_click_sound(self):
        try:
            from src.sound_manager import play_sfx
            play_sfx('coin')
        except Exception:
            pass

    def draw(self, surface):
        r = self.rect
        tex_base = f"{self.style}.png"
        tex_pressed = f"{self.style}_pressed.png"
        
        tex = tex_pressed if (self.pressed and os.path.exists(os.path.join(UI_ASSET_DIR, tex_pressed))) else tex_base

        # Draw 9-slice button base
        btn_surf = get_nineslice(tex, r.width, r.height, corner=14, tint=self.tint)
        
        # Hover golden aura
        if self.hovered and self.enabled:
            aura = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
            aura.fill((255, 220, 80, 50))
            btn_surf = btn_surf.copy()
            btn_surf.blit(aura, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        dy = 2 if self.pressed else 0
        surface.blit(btn_surf, (r.x, r.y + dy))

        label_color = (255, 235, 195) if self.hovered else (230, 220, 205)
        if not self.enabled:
            label_color = (130, 125, 120)

        font = get_font(self.font_size, bold=True)
        t_surf = font.render(self.text, True, label_color)
        shd_surf = font.render(self.text, True, (14, 11, 16))
        
        cx = r.centerx
        cy = r.centery + dy
        shd_rect = shd_surf.get_rect(center=(cx + 1, cy + 1))
        t_rect = t_surf.get_rect(center=(cx, cy))
        
        surface.blit(shd_surf, shd_rect)
        surface.blit(t_surf, t_rect)

        if self.hotkey:
            hk_surf = get_font(10, bold=True).render(self.hotkey, True, (255, 215, 60))
            surface.blit(hk_surf, (r.x + 6, r.y + 4 + dy))
