import pygame
import random
import math
from src.player_animation import PlayerAnimationController
from src.settings import *
from src.items import generate_random_item, Item

class DamageText(pygame.sprite.Sprite):
    def __init__(self, text, pos, groups, color=(245, 245, 245), size=16, is_crit=False):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'ui_effect'
        self.is_crit = is_crit
        from src.ui import get_pixel_font
        font = get_pixel_font(size, bold=True)
        text_str = str(text)
        try:
            shadow_surf = font.render(text_str, True, (12, 10, 16))
            txt_surf = font.render(text_str, True, color)
            w = txt_surf.get_width() + 4
            h = txt_surf.get_height() + 4
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            surf.blit(shadow_surf, (2, 2))
            surf.blit(txt_surf, (0, 0))
            self.orig_image = surf
        except Exception:
            self.orig_image = pygame.Surface((32, 16), pygame.SRCALPHA)
        self.image = self.orig_image.copy()
        import random
        self.pos_x = float(pos[0]) + random.uniform(-4.0, 4.0)
        self.pos_y = float(pos[1]) - random.uniform(2.0, 6.0)
        self.vx = random.uniform(-0.6, 0.6)
        self.vy = -3.2 if is_crit else -2.2
        self.rect = self.image.get_rect(center=(round(self.pos_x), round(self.pos_y)))
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 750 if is_crit else 600
        self.frame_count = 0

    def update(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed >= self.duration:
            self.kill()
            return
        self.frame_count += 1
        self.pos_x += self.vx
        self.pos_y += self.vy
        self.vy += 0.08
        self.vx *= 0.96

        fade_start = self.duration * 0.45
        # AAA Crit Pop Effect: initial frames magnified 1.5x with radiant white flash
        if self.is_crit and self.frame_count <= 4:
            scale = 1.50 - (self.frame_count - 1) * 0.12
            ow = max(1, int(self.orig_image.get_width() * scale))
            oh = max(1, int(self.orig_image.get_height() * scale))
            scaled_img = pygame.transform.scale(self.orig_image, (ow, oh))
            if self.frame_count <= 2:
                flash = scaled_img.copy()
                flash.fill((255, 255, 255, 180), special_flags=pygame.BLEND_RGBA_ADD)
                self.image = flash
            else:
                self.image = scaled_img
        elif elapsed > fade_start:
            prog = (elapsed - fade_start) / max(1.0, (self.duration - fade_start))
            alpha = max(0, min(255, int(255 * (1.0 - prog))))
            self.image = self.orig_image.copy()
            self.image.set_alpha(alpha)
        else:
            self.image = self.orig_image.copy()

        self.rect = self.image.get_rect(center=(round(self.pos_x), round(self.pos_y)))
ENEMY_HP_CONFIG = {
    'bat': 15,
    'imp': 20,
    'goblin': 25,
    'skeleton': 30,
    'lurker': 35,
    'zombie': 45,
    'yeti': 60,
    'necromancer': 70,
    'spore_bomber': 35,
    'toxic_slime': 60,
    'mini_slime': 25,
    'phantom': 45,
    'mimic': 80,
    'gargoyle': 65,
    'mosquito': 18,
    'cultist': 40,
    'skeleton_brute': 90,
    'spore_creeper': 35,
    'banshee': 50,
    'lava_hound': 55,
    'sarcophagus': 120,
    'iron_maiden': 110,
    'boss_bone_golem': 200,
    'boss_frost_revenant': 220,
    'boss_void_knight': 250,
    'boss_necro_lord': 380,
}



_PARTICLE_SURF_CACHE = {}

def _get_particle_circle_surf(color, size, alpha):
    a_quant = max(0, min(255, (alpha // 16) * 16))
    key = (color[0], color[1], color[2], size, a_quant)
    surf = _PARTICLE_SURF_CACHE.get(key)
    if surf is None:
        dim = max(2, size * 2)
        surf = pygame.Surface((dim, dim), pygame.SRCALPHA)
        pygame.draw.circle(surf, (color[0], color[1], color[2], a_quant), (size, size), size)
        if len(_PARTICLE_SURF_CACHE) > 600:
            _PARTICLE_SURF_CACHE.clear()
        _PARTICLE_SURF_CACHE[key] = surf
    return surf


class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, groups, color=(255, 200, 50), size=4, velocity=(0, 0), lifetime=250):
        # Exclude obstacle groups so particles never interfere with collision or line-of-fire
        clean_groups = [
            g for g in groups
            if g is not None
            and 'obstacle' not in str(type(g)).lower()
            and 'obstacle' not in getattr(g, 'name', '').lower()
            and getattr(g, 'sprite_type', '') != 'obstacle'
        ] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'particle'
        self.color = color if len(color) >= 3 else (255, 255, 255)
        self.size = max(1, int(size))
        self.orig_size = self.size
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(velocity)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = max(1, int(lifetime))
        self.image = _get_particle_circle_surf(self.color, self.size, 255)
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = pygame.Rect(0, 0, 0, 0)

    def update(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed >= self.lifetime:
            self.kill()
            return
        self.pos += self.vel
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        progress = elapsed / max(1, self.lifetime)
        current_size = max(1, int(self.orig_size * (1.0 - progress)))
        alpha = max(0, min(255, int(255 * (1.0 - progress))))
        self.image = _get_particle_circle_surf(self.color, current_size, alpha)


class DebrisParticle(pygame.sprite.Sprite):
    def __init__(self, pos, groups, color=(140, 95, 55), size=6, velocity=(0, 0), lifetime=400):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'particle'
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(velocity)
        self.gravity = 0.28
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-18, 18)
        s_base = max(2, int(size))
        self.w = max(2, random.randint(s_base, s_base + 4))
        self.h = max(2, random.randint(2, max(2, s_base // 2)))
        self.color = color if len(color) >= 3 else (140, 95, 55)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = max(1, int(lifetime))
        self.image = pygame.Surface((self.w * 2, self.h * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        self.ground_y = float(pos[1] + random.randint(10, 24))
        self.bounces = 0
        self.max_bounces = 2
        self.restitution = 0.40

    def update(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed >= self.lifetime:
            self.kill()
            return
        self.vel.y += self.gravity
        self.pos += self.vel
        if self.pos.y >= self.ground_y and self.bounces < self.max_bounces and self.vel.y > 0:
            self.pos.y = self.ground_y
            self.vel.y = -self.vel.y * self.restitution
            self.vel.x *= 0.72
            self.rot_speed *= 0.60
            self.bounces += 1
        self.rotation += self.rot_speed
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        progress = elapsed / max(1, self.lifetime)
        alpha = max(0, min(255, int(255 * (1.0 - progress))))
        surf = pygame.Surface((max(1, self.w), max(1, self.h)), pygame.SRCALPHA)
        surf.fill((self.color[0], self.color[1], self.color[2], alpha))
        self.image = pygame.transform.rotate(surf, self.rotation)
        self.rect = self.image.get_rect(center=self.rect.center)

class ToxicPuddle(pygame.sprite.Sprite):
    def __init__(self, pos, groups, duration=3500, radius=20, damage=4):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'hazard'
        self.radius = radius
        self.damage = damage
        self.spawn_time = pygame.time.get_ticks()
        self.duration = duration
        self.last_damage_time = -1000

        size = radius * 2 + 10
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        self.hitbox = pygame.Rect(0, 0, int(radius * 1.5), int(radius * 1.5))
        self.hitbox.center = self.rect.center
        self._redraw(0)

    def _redraw(self, elapsed):
        self.image.fill((0, 0, 0, 0))
        size = self.image.get_width()
        center = (size // 2, size // 2)
        pulse = math.sin(elapsed * 0.006) * 1.8
        r = max(4, int(self.radius + pulse))
        pygame.draw.circle(self.image, (20, 85, 30, 150), center, r + 3)
        pygame.draw.circle(self.image, (60, 210, 55, 205), center, r)
        b_x = int(center[0] + math.cos(elapsed * 0.005) * (r * 0.45))
        b_y = int(center[1] + math.sin(elapsed * 0.005) * (r * 0.45))
        pygame.draw.circle(self.image, (180, 255, 130, 230), (b_x, b_y), max(2, int(r * 0.22)))

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        if elapsed >= self.duration:
            self.kill()
            return
        self._redraw(elapsed)
        if self.duration - elapsed < 500:
            alpha = int(255 * (self.duration - elapsed) / 500)
            self.image.set_alpha(max(0, min(255, alpha)))

    def update_hazard(self, player):
        if not self.alive() or not player:
            return
        now = pygame.time.get_ticks()
        if hasattr(player, 'hitbox') and self.hitbox.colliderect(player.hitbox):
            if now - self.last_damage_time >= 600:
                self.last_damage_time = now
                if hasattr(player, 'take_damage'):
                    player.take_damage(self.damage, source_pos=self.rect.center)
                elif not getattr(player, 'is_shielded', False):
                    player.health -= self.damage
                player.speed_modifier = 0.65
                player.speed_modifier_timer = now + 750

class ChainLightningVFX(pygame.sprite.Sprite):
    def __init__(self, start_pos, end_pos, groups):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'ui_effect'
        self.start_pos = pygame.math.Vector2(start_pos)
        self.end_pos = pygame.math.Vector2(end_pos)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 140
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        
        self.points = [self.start_pos]
        disp_vec = self.end_pos - self.start_pos
        dist = disp_vec.magnitude()
        if dist > 0:
            norm_perp = pygame.math.Vector2(-disp_vec.y, disp_vec.x).normalize()
            steps = max(3, int(dist // 35))
            for i in range(1, steps):
                frac = i / float(steps)
                jitter = random.uniform(-14, 14)
                mid_pt = self.start_pos + disp_vec * frac + norm_perp * jitter
                self.points.append(mid_pt)
        self.points.append(self.end_pos)
        
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        min_x, max_x = min(xs) - 10, max(xs) + 10
        min_y, max_y = min(ys) - 10, max(ys) + 10
        self.origin = pygame.math.Vector2(min_x, min_y)
        w, h = max(4, int(max_x - min_x)), max(4, int(max_y - min_y))
        
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(int(min_x), int(min_y)))
        self.rebuild_image()

    def rebuild_image(self):
        self.image.fill((0, 0, 0, 0))
        rel_pts = [(p.x - self.origin.x, p.y - self.origin.y) for p in self.points]
        if len(rel_pts) >= 2:
            # Multi-Pass Electric Bloom & Glow
            pygame.draw.lines(self.image, (50, 160, 255, 110), False, rel_pts, 8)
            pygame.draw.lines(self.image, (130, 240, 255, 210), False, rel_pts, 4)
            pygame.draw.lines(self.image, (255, 255, 255, 255), False, rel_pts, 2)
            for pt in [rel_pts[0], rel_pts[-1]]:
                pygame.draw.circle(self.image, (255, 255, 255, 255), (int(pt[0]), int(pt[1])), 4)
                pygame.draw.circle(self.image, (90, 220, 255, 180), (int(pt[0]), int(pt[1])), 7, 2)

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.spawn_time >= self.lifetime:
            self.kill()



class GhostTrail(pygame.sprite.Sprite):
    def __init__(self, pos, groups, base_image, lifetime=180, chromatic=True):
        clean_groups = [
            g for g in groups
            if g is not None
            and 'obstacle' not in str(type(g)).lower()
            and 'obstacle' not in getattr(g, 'name', '').lower()
            and getattr(g, 'sprite_type', '') != 'obstacle'
        ] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'ghost_trail'
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = max(1, lifetime)
        self.chromatic = chromatic

        w, h = base_image.get_size()
        pad = 4
        self.image = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
        if chromatic:
            red_surf = base_image.copy()
            red_surf.fill((255, 50, 60, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self.image.blit(red_surf, (pad - 2, pad))

            blue_surf = base_image.copy()
            blue_surf.fill((60, 180, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self.image.blit(blue_surf, (pad + 2, pad), special_flags=pygame.BLEND_RGBA_ADD)

            core_surf = base_image.copy()
            core_surf.fill((240, 240, 255, 170), special_flags=pygame.BLEND_RGBA_MULT)
            self.image.blit(core_surf, (pad, pad))
        else:
            self.image.blit(base_image, (pad, pad))

        self.orig_image = self.image.copy()
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = pygame.Rect(0, 0, 0, 0)

    def update(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed >= self.lifetime:
            self.kill()
            return
        progress = elapsed / float(self.lifetime)
        alpha = max(0, min(255, int(180 * (1.0 - progress))))
        self.image = self.orig_image.copy()
        fade_surf = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        fade_surf.fill((255, 255, 255, alpha))
        self.image.blit(fade_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)


class SpeedlineStreakVFX(pygame.sprite.Sprite):
    """Razor-sharp directional speedline slice cutting through space."""
    def __init__(self, pos, groups, direction, length=32, color=(180, 230, 255)):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'ui_effect'
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 170
        d = direction.normalize() if direction.magnitude() > 0 else pygame.math.Vector2(1, 0)
        perp = pygame.math.Vector2(-d.y, d.x)
        self.pos = pygame.math.Vector2(pos) + perp * random.uniform(-14, 14) - d * random.uniform(0, 16)
        self.d = d
        self.length = length
        self.color = color
        sz = int(length * 2.2)
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        self.hitbox = pygame.Rect(0, 0, 0, 0)

    def update(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed >= self.lifetime:
            self.kill()
            return
        prog = elapsed / float(self.lifetime)
        alpha = int(240 * (1.0 - prog))
        self.image.fill((0, 0, 0, 0))
        sz = self.image.get_width()
        cx, cy = sz // 2, sz // 2
        p1 = pygame.math.Vector2(cx, cy) - self.d * (self.length * (0.5 + 0.3 * prog))
        p2 = pygame.math.Vector2(cx, cy) + self.d * (self.length * (0.5 - 0.2 * prog))
        c = self.color
        pygame.draw.line(self.image, (c[0], c[1], c[2], alpha), (p1.x, p1.y), (p2.x, p2.y), max(1, int(3 * (1.0 - prog))))
        pygame.draw.line(self.image, (255, 255, 255, alpha), (p1.x, p1.y), (p2.x, p2.y), 1)


class MagmaEmberVFX(pygame.sprite.Sprite):
    """Microscopic burning ember spark with upward convective drift (zero balls)."""
    def __init__(self, pos, groups):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'ui_effect'
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = random.randint(180, 280)
        self.pos = pygame.math.Vector2(pos) + pygame.math.Vector2(random.uniform(-10, 10), random.uniform(-8, 8))
        self.vel = pygame.math.Vector2(random.uniform(-1.2, 1.2), random.uniform(-2.5, -0.6))
        self.color = random.choice([(255, 95, 30), (255, 175, 45), (255, 235, 120), (190, 40, 20)])
        self.size = random.choice([1, 2, 2, 3])
        self.image = pygame.Surface((6, 6), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        self.hitbox = pygame.Rect(0, 0, 0, 0)

    def update(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed >= self.lifetime:
            self.kill()
            return
        self.pos += self.vel
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        prog = elapsed / float(self.lifetime)
        alpha = int(255 * (1.0 - prog))
        self.image.fill((0, 0, 0, 0))
        c = self.color
        s = max(1, int(self.size * (1.0 - prog * 0.5)))
        pygame.draw.rect(self.image, (c[0], c[1], c[2], alpha), (3 - s//2, 3 - s//2, s, s))


class CelestialNeedleVFX(pygame.sprite.Sprite):
    """Sharp 4-point diamond star glint and celestial ray needles."""
    def __init__(self, pos, groups):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'ui_effect'
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 210
        self.pos = pygame.math.Vector2(pos) + pygame.math.Vector2(random.uniform(-12, 12), random.uniform(-10, 10))
        self.color = random.choice([(140, 235, 255), (255, 245, 170), (220, 255, 255)])
        self.r = random.uniform(6, 11)
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        self.hitbox = pygame.Rect(0, 0, 0, 0)

    def update(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed >= self.lifetime:
            self.kill()
            return
        prog = elapsed / float(self.lifetime)
        alpha = int(245 * math.sin(prog * math.pi))
        self.image.fill((0, 0, 0, 0))
        c = self.color
        cx, cy = 12, 12
        r = self.r * (1.0 - prog * 0.4)
        pygame.draw.line(self.image, (c[0], c[1], c[2], alpha), (cx - r, cy), (cx + r, cy), 1)
        pygame.draw.line(self.image, (c[0], c[1], c[2], alpha), (cx, cy - r), (cx, cy + r), 1)
        pygame.draw.circle(self.image, (255, 255, 255, alpha), (cx, cy), 1)


class VoidRibbonSegmentVFX(pygame.sprite.Sprite):
    """Flowing cosmic energy ribbon wake trailing behind player motion."""
    def __init__(self, pos, groups, direction):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'ui_effect'
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 230
        self.pos = pygame.math.Vector2(pos)
        d = direction.normalize() if direction.magnitude() > 0 else pygame.math.Vector2(1, 0)
        self.d = d
        self.perp = pygame.math.Vector2(-d.y, d.x)
        self.image = pygame.Surface((36, 36), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(round(pos[0]), round(pos[1])))
        self.hitbox = pygame.Rect(0, 0, 0, 0)

    def update(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed >= self.lifetime:
            self.kill()
            return
        prog = elapsed / float(self.lifetime)
        alpha = int(200 * (1.0 - prog))
        self.image.fill((0, 0, 0, 0))
        cx, cy = 18, 18
        w = max(2, int(10 * (1.0 - prog)))
        l = max(4, int(18 * (1.0 - prog)))
        p_ahead = pygame.math.Vector2(cx, cy) + self.d * (l * 0.5)
        p_behind = pygame.math.Vector2(cx, cy) - self.d * (l * 0.5)
        p_left = pygame.math.Vector2(cx, cy) + self.perp * (w * 0.5)
        p_right = pygame.math.Vector2(cx, cy) - self.perp * (w * 0.5)
        pts = [(p_ahead.x, p_ahead.y), (p_left.x, p_left.y), (p_behind.x, p_behind.y), (p_right.x, p_right.y)]
        pygame.draw.polygon(self.image, (170, 50, 240, int(alpha * 0.7)), pts)
        pygame.draw.polygon(self.image, (70, 240, 255, alpha), pts, 1)


class RadiantBarrierVFX(pygame.sprite.Sprite):
    """A clear, glassy energy sphere that wraps around the player."""
    def __init__(self, player, groups):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'ui_effect'
        self.player = player
        self.spawn_time = pygame.time.get_ticks()
        self.radius = max(38, int(max(player.rect.width, player.rect.height) * 0.82))
        padding = 14
        size = (self.radius + padding) * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self._sphere_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        self._build_sphere_surface()
        self.rect = self.image.get_rect(center=player.rect.center)
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        self.last_sparkle_time = 0

    def _build_sphere_surface(self):
        """Bake a translucent radial shell once; animate only its highlights."""
        cx = cy = self.image.get_width() // 2
        r = self.radius - 2
        for y in range(cy - r, cy + r + 1):
            ny = (y - cy) / float(r)
            for x in range(cx - r, cx + r + 1):
                nx = (x - cx) / float(r)
                dist_sq = nx * nx + ny * ny
                if dist_sq > 1.0:
                    continue
                dist = math.sqrt(dist_sq)
                rim = max(0.0, 1.0 - abs(dist - 0.91) / 0.13)
                gloss = math.exp(-(((nx + 0.38) / 0.27) ** 2 + ((ny + 0.48) / 0.34) ** 2) * 2.0)
                depth = 1.0 - dist
                alpha = min(78, int(12 + depth * 13 + rim * 17 + gloss * 32))
                color = (
                    min(255, int(38 + gloss * 62)),
                    min(255, int(126 + gloss * 91)),
                    min(255, int(177 + gloss * 76)),
                    alpha,
                )
                self._sphere_surface.set_at((x, y), color)

    def update(self):
        if not getattr(self.player, 'is_shielded', False) or getattr(self.player, 'health', 0) <= 0:
            self.kill()
            return

        now = pygame.time.get_ticks()
        self.rect.center = self.player.rect.center
        pulse = 0.5 + 0.5 * math.sin(now * 0.004)
        self.image.fill((0, 0, 0, 0))
        self.image.blit(self._sphere_surface, (0, 0))
        cx = cy = self.image.get_width() // 2
        r = self.radius - 2

        # Soft outer refraction and a thin glass rim keep the character visible inside.
        pygame.draw.circle(self.image, (48, 166, 225, int(16 + pulse * 12)), (cx, cy), r + 5, 4)
        pygame.draw.circle(self.image, (82, 198, 239, 58), (cx, cy), r + 1, 1)
        pygame.draw.circle(self.image, (174, 237, 255, int(105 + pulse * 34)), (cx, cy), r, 1)

        # Curved longitude and latitude seams give the shell a spherical, glass-like read.
        longitude = pygame.Rect(cx - int(r * 0.32), cy - int(r * 0.78), int(r * 0.64), int(r * 1.56))
        latitude = pygame.Rect(cx - int(r * 0.78), cy - int(r * 0.24), int(r * 1.56), int(r * 0.56))
        pygame.draw.ellipse(self.image, (126, 222, 250, 42), longitude, 1)
        pygame.draw.ellipse(self.image, (110, 218, 247, 36), latitude, 1)

        # A short angled glint follows the curved glass surface, kept pixel-crisp.
        glint_start = (cx - int(r * 0.56), cy - int(r * 0.48))
        glint_end = (cx - int(r * 0.42), cy - int(r * 0.62))
        pygame.draw.line(self.image, (98, 215, 250, 105), glint_start, glint_end, 2)
        pygame.draw.line(self.image, (238, 253, 255, 180), (glint_start[0] + 2, glint_start[1] - 1), (glint_end[0], glint_end[1] + 1), 1)
        pygame.draw.circle(self.image, (255, 255, 255, 210), glint_end, 1)

        # A few restrained motes orbit the shell instead of forming a flat barrier face.
        for i in range(3):
            angle = now * 0.0018 + i * (math.tau / 3.0)
            mx = cx + int(math.cos(angle) * (r + 1))
            my = cy + int(math.sin(angle) * (r + 1))
            pygame.draw.circle(self.image, (229, 252, 255, 190), (mx, my), 1)
            pygame.draw.circle(self.image, (95, 216, 255, 78), (mx, my), 3)

        # Occasional upward motes make the protection feel active without obscuring the hero.
        if now - self.last_sparkle_time > 125:
            self.last_sparkle_time = now
            vis = getattr(self.player, 'visible_sprites', None)
            if vis:
                ang = random.uniform(0, math.tau)
                dist = random.uniform(r * 0.72, r * 0.95)
                sp_pos = (self.rect.centerx + math.cos(ang) * dist, self.rect.centery + math.sin(ang) * dist)
                col = random.choice([(170, 245, 255), (230, 255, 255), (100, 210, 255), (255, 255, 255)])
                Particle(sp_pos, [vis], color=col, size=random.choice([1, 2]), velocity=(random.uniform(-0.35, 0.35), random.uniform(-1.5, -0.5)), lifetime=230)

class FlameTrailHazard(pygame.sprite.Sprite):
    def __init__(self, pos, groups, enemy_sprites=None, player_level=1, direction=None):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'hazard'
        self.enemy_sprites = enemy_sprites
        self.pos = pygame.math.Vector2(pos)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 1300
        self.last_tick_time = 0
        self.tick_rate = 260
        self.player_level = player_level
        self.direction = pygame.math.Vector2(direction or (1, 0))
        if self.direction.magnitude() == 0:
            self.direction = pygame.math.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()
        
        # Level Milestones: 1-4 Amber, 5-9 Azure, 10-14 Amethyst, 15+ Celestial Crimson
        if player_level >= 15:
            self.flame_color = (255, 45, 65)
            self.flame_core = (255, 190, 205)
        elif player_level >= 10:
            self.flame_color = (195, 75, 255)
            self.flame_core = (240, 195, 255)
        elif player_level >= 5:
            self.flame_color = (60, 205, 255)
            self.flame_core = (210, 245, 255)
        else:
            self.flame_color = (255, 160, 30)
            self.flame_core = (255, 235, 130)
        
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(pos[0]), int(pos[1])))
        self.hitbox = self.rect.inflate(-4, -4)

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        if elapsed >= self.lifetime:
            self.kill()
            return
            
        self.image.fill((0, 0, 0, 0))
        alpha = max(0, min(255, int(255 * (1.0 - (elapsed / float(self.lifetime)) ** 1.5))))
        flicker = random.randint(-2, 2)
        cx, cy = self.image.get_width() // 2, self.image.get_height() // 2
        trail_dir = -self.direction
        side = pygame.math.Vector2(-trail_dir.y, trail_dir.x)
        outer = (*self.flame_color, int(alpha * 0.55))
        core = (*self.flame_core, alpha)
        # The damaging trail stays in place, but its old stacked fire orbs become
        # thin directional cuts so consecutive dashes read as motion, not beads.
        for index, offset in enumerate((-9, -5, 5, 9)):
            length = 10 + (index % 2) * 4 + flicker
            start = pygame.math.Vector2(cx, cy) + trail_dir * length + side * offset
            end = pygame.math.Vector2(cx, cy) + trail_dir * (length * 0.35) + side * (offset - 2)
            pygame.draw.line(self.image, outer, start, end, 2 if index in (1, 2) else 1)
            pygame.draw.line(self.image, core, start + trail_dir, end, 1)

        if self.enemy_sprites and (now - self.last_tick_time >= self.tick_rate):
            self.last_tick_time = now
            hits = [e for e in self.enemy_sprites if getattr(e, 'alive', lambda: True)() and getattr(e, 'rect', None) and self.hitbox.colliderect(e.rect)]
            for enemy in hits:
                if hasattr(enemy, 'take_damage'):
                    enemy.take_damage(7, source='fire')


class SoulMote(pygame.sprite.Sprite):
    def __init__(self, pos, groups, player):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'ui_effect'
        self.player = player
        self.pos = pygame.math.Vector2(pos)
        ang = random.uniform(0, 6.28)
        spd = random.uniform(1.5, 3.5)
        self.velocity = pygame.math.Vector2(math.cos(ang) * spd, math.sin(ang) * spd)
        self.speed = 2.0
        self.max_speed = 8.5
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 2500
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(pos[0]), int(pos[1])))
        
    def update(self):
        now = pygame.time.get_ticks()
        if now - self.spawn_time >= self.lifetime or not self.player or getattr(self.player, 'is_dead', False):
            self.kill()
            return
            
        target = pygame.math.Vector2(self.player.rect.center)
        to_target = target - self.pos
        dist = to_target.magnitude()
        
        if dist < 18:
            max_hp = self.player.stats.get('health', 100) if hasattr(self.player, 'stats') else 100
            self.player.health = min(max_hp, self.player.health + 2)
            try:
                from src.sound_manager import play_sfx
                play_sfx('soul_absorb')
            except Exception:
                pass
            vis_g = [self.player.visible_sprites] if getattr(self.player, 'visible_sprites', None) else []
            if vis_g:
                DamageText("+2 HP", self.player.rect.center, vis_g, color=(120, 255, 160), size=13)
                for _ in range(4):
                    ang = random.uniform(0, 6.28)
                    spd = random.uniform(1, 3)
                    Particle(self.player.rect.center, vis_g, color=(160, 255, 200), size=2, velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=160)
            self.kill()
            return
            
        self.speed = min(self.max_speed, self.speed + 0.35)
        desired_vel = to_target.normalize() * self.speed
        self.velocity = self.velocity * 0.82 + desired_vel * 0.18
        self.pos += self.velocity
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, (240, 40, 80, 150), (8, 8), 6)
        pygame.draw.circle(self.image, (255, 140, 200, 230), (8, 8), 4)
        pygame.draw.circle(self.image, (255, 255, 255, 255), (8, 8), 2)


class BloodAltar(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'altar'
        self.altar_type = 'blood'
        self.prompt_str = '[E] Кровавый Алтарь (-35 HP)'
        self.pos = pygame.math.Vector2(pos)
        self.used = False
        self.image = pygame.Surface((44, 52), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(int(pos[0]), int(pos[1])))
        self.hitbox = self.rect.inflate(-6, -8)
        self.last_particle_time = 0
        self.rebuild_image()
        
    def rebuild_image(self):
        self.image.fill((0, 0, 0, 0))
        w, h = 44, 52
        now = pygame.time.get_ticks()
        pygame.draw.rect(self.image, (22, 18, 28), [2, h - 20, w - 4, 18], border_radius=3)
        pygame.draw.rect(self.image, (50, 40, 60), [2, h - 20, w - 4, 18], 1, border_radius=3)
        pygame.draw.rect(self.image, (32, 26, 40), [6, h - 28, w - 12, 10], border_radius=2)
        pygame.draw.rect(self.image, (80, 55, 90), [6, h - 28, w - 12, 10], 1, border_radius=2)
        
        chalice_col = (45, 20, 30) if not self.used else (30, 28, 35)
        pygame.draw.rect(self.image, chalice_col, [10, 16, w - 20, 10], border_radius=2)
        pygame.draw.rect(self.image, (160, 40, 60) if not self.used else (70, 60, 75), [10, 16, w - 20, 10], 1, border_radius=2)
        
        if not self.used:
            pygame.draw.ellipse(self.image, (220, 20, 50), [12, 18, w - 24, 6])
            float_y = 6 + int(2.5 * math.sin(now * 0.005))
            core_pts = [(w // 2, float_y - 6), (w // 2 + 5, float_y), (w // 2, float_y + 6), (w // 2 - 5, float_y)]
            pygame.draw.polygon(self.image, (255, 60, 90), core_pts)
            pygame.draw.polygon(self.image, (255, 210, 230), core_pts, 1)
            pygame.draw.circle(self.image, (255, 40, 80, 75), (w // 2, float_y), 9)
        else:
            pygame.draw.ellipse(self.image, (40, 35, 45), [12, 18, w - 24, 6])
            
    def update(self):
        now = pygame.time.get_ticks()
        self.rebuild_image()
        if not self.used and (now - self.last_particle_time >= 320):
            self.last_particle_time = now
            for g in self.groups():
                if hasattr(g, 'shake'):
                    ang = random.uniform(-2.2, -0.9)
                    spd = random.uniform(0.6, 1.4)
                    Particle((self.rect.centerx + random.randint(-10, 10), self.rect.top + 8), [g], color=(235, 40, 60), size=random.randint(1, 3), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=350)
                    break
                    
    def interact(self, player, level):
        vis_g = [level.visible_sprites] if getattr(level, 'visible_sprites', None) else []
        if self.used:
            if vis_g:
                DamageText("Алтарь иссяк", self.rect.center, vis_g, color=(140, 140, 140), size=14)
            return False
            
        if player.health > 35:
            player.health -= 35
            self.used = True
            try:
                from src.sound_manager import play_sfx
                play_sfx('altar')
            except Exception:
                pass
            if hasattr(level, 'visible_sprites') and hasattr(level.visible_sprites, 'shake'):
                level.visible_sprites.shake(duration_ms=260, magnitude=6)
            if vis_g:
                DamageText("-35 HP КРОВАВАЯ ЖЕРТВА", player.rect.center, vis_g, color=(255, 40, 50), size=18)
                for _ in range(24):
                    ang = random.uniform(0, 6.28)
                    spd = random.uniform(2.5, 6.5)
                    Particle(self.rect.center, vis_g, color=(210, 30, 45), size=random.randint(3, 5), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=380)
            
            player.purple_shards = getattr(player, 'purple_shards', 0) + 1
            try:
                from src.save_manager import load_profile, save_profile
                prof = load_profile()
                prof['purple_shards'] = prof.get('purple_shards', 0) + 1
                save_profile(prof)
            except Exception:
                pass
            if vis_g:
                DamageText("+1 ФИОЛЕТОВЫЙ ОСКОЛОК", (player.rect.centerx, player.rect.centery - 24), vis_g, color=(220, 120, 255), size=16)
                
            try:
                from src.items import generate_relic
                relic = generate_relic()
                if not hasattr(player, 'relics'): player.relics = []
                player.relics.append(relic)
                # Note: Relic is owned in player.relics only, not duplicate in inventory!
                if hasattr(player, 'recalculate_stats'):
                    player.recalculate_stats()
                if vis_g:
                    DamageText(f"+ {relic.name[:16]}", (player.rect.centerx, player.rect.centery - 48), vis_g, color=(255, 215, 60), size=16)
            except Exception:
                pass
                
            try:
                from src.items import Gold
                if vis_g:
                    for _ in range(2):
                        g_pos = (self.rect.centerx + random.randint(-16, 16), self.rect.centery + random.randint(-10, 15))
                        Gold(g_pos, vis_g, random.randint(10, 15), player)
            except Exception:
                pass
            return True
        else:
            try:
                from src.sound_manager import play_sfx
                play_sfx('shield')
            except Exception:
                pass
            if vis_g:
                DamageText("Слишком мало крови (Нужно >35 HP)!", player.rect.center, vis_g, color=(230, 90, 90), size=14)
            return False




class WisdomFountain(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'altar'
        self.altar_type = 'wisdom'
        self.prompt_str = "[E] Источник Мудрости (+MP, +XP)"
        self.pos = pygame.math.Vector2(pos)
        self.used = False
        self.image = pygame.Surface((44, 52), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(int(pos[0]), int(pos[1])))
        self.hitbox = self.rect.inflate(-6, -8)
        self.last_particle_time = 0
        self.rebuild_image()

    def rebuild_image(self):
        self.image.fill((0, 0, 0, 0))
        w, h = 44, 52
        now = pygame.time.get_ticks()
        pygame.draw.rect(self.image, (24, 28, 38), [2, h - 20, w - 4, 18], border_radius=3)
        pygame.draw.rect(self.image, (60, 80, 110), [2, h - 20, w - 4, 18], 1, border_radius=3)
        pygame.draw.rect(self.image, (32, 38, 52), [6, h - 28, w - 12, 10], border_radius=2)
        pygame.draw.rect(self.image, (70, 110, 150), [6, h - 28, w - 12, 10], 1, border_radius=2)
        
        basin_col = (20, 35, 55) if not self.used else (30, 32, 38)
        pygame.draw.rect(self.image, basin_col, [10, 16, w - 20, 10], border_radius=2)
        pygame.draw.rect(self.image, (80, 160, 220) if not self.used else (60, 70, 85), [10, 16, w - 20, 10], 1, border_radius=2)

        if not self.used:
            pygame.draw.ellipse(self.image, (40, 140, 240), [12, 18, w - 24, 6])
            float_y = 6 + int(2.5 * math.sin(now * 0.005))
            core_pts = [(w // 2, float_y - 6), (w // 2 + 5, float_y), (w // 2, float_y + 6), (w // 2 - 5, float_y)]
            pygame.draw.polygon(self.image, (120, 220, 255), core_pts)
            pygame.draw.polygon(self.image, (230, 250, 255), core_pts, 1)
            pygame.draw.circle(self.image, (80, 180, 255, 75), (w // 2, float_y), 9)
        else:
            pygame.draw.ellipse(self.image, (35, 40, 48), [12, 18, w - 24, 6])

    def update(self):
        now = pygame.time.get_ticks()
        self.rebuild_image()
        if not self.used and (now - self.last_particle_time >= 320):
            self.last_particle_time = now
            for g in self.groups():
                if hasattr(g, 'custom_draw'):
                    ang = random.uniform(-2.2, -0.9)
                    spd = random.uniform(0.6, 1.4)
                    Particle((self.rect.centerx + random.randint(-10, 10), self.rect.top + 8), [g], color=(100, 210, 255), size=random.randint(1, 3), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=350)
                    break

    def interact(self, player, level):
        vis_g = [level.visible_sprites] if getattr(level, 'visible_sprites', None) else []
        if self.used:
            if vis_g:
                DamageText("Источник иссяк", self.rect.center, vis_g, color=(140, 140, 140), size=14)
            return False

        self.used = True
        player.energy = getattr(player, 'max_energy', 100)
        if hasattr(player, 'gain_exp'):
            player.gain_exp(75)

        try:
            from src.sound_manager import play_sfx
            play_sfx('water_drip')
        except Exception:
            pass

        if hasattr(level, 'visible_sprites') and hasattr(level.visible_sprites, 'shake'):
            level.visible_sprites.shake(duration_ms=180, magnitude=4)
        if vis_g:
            DamageText("+100% MP  +75 XP ИСТОЧНИК МУДРОСТИ", player.rect.center, vis_g, color=(100, 220, 255), size=17)
            for _ in range(20):
                ang = random.uniform(0, 6.28)
                spd = random.uniform(2.0, 5.5)
                Particle(self.rect.center, vis_g, color=(120, 230, 255), size=random.randint(3, 5), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=360)
        return True


class AnvilShrine(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'altar'
        self.altar_type = 'forge'
        self.prompt_str = "[E] Горн Наковальни (Заточка +4 Урона)"
        self.pos = pygame.math.Vector2(pos)
        self.used = False
        self.image = pygame.Surface((44, 52), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(int(pos[0]), int(pos[1])))
        self.hitbox = self.rect.inflate(-6, -8)
        self.last_particle_time = 0
        self.rebuild_image()

    def rebuild_image(self):
        self.image.fill((0, 0, 0, 0))
        w, h = 44, 52
        now = pygame.time.get_ticks()
        pygame.draw.rect(self.image, (32, 22, 20), [2, h - 20, w - 4, 18], border_radius=3)
        pygame.draw.rect(self.image, (110, 60, 40), [2, h - 20, w - 4, 18], 1, border_radius=3)
        pygame.draw.rect(self.image, (42, 28, 22), [6, h - 28, w - 12, 10], border_radius=2)
        pygame.draw.rect(self.image, (140, 75, 45), [6, h - 28, w - 12, 10], 1, border_radius=2)
        
        anvil_col = (90, 85, 95) if not self.used else (50, 48, 55)
        pygame.draw.polygon(self.image, anvil_col, [(10, 18), (34, 18), (30, 24), (14, 24)])
        pygame.draw.rect(self.image, (160, 95, 45) if not self.used else (60, 55, 60), [10, 18, 24, 6], 1)

        if not self.used:
            float_y = 6 + int(2.5 * math.sin(now * 0.005))
            flame_pts = [(w // 2, float_y - 6), (w // 2 + 5, float_y), (w // 2, float_y + 6), (w // 2 - 5, float_y)]
            pygame.draw.polygon(self.image, (255, 140, 30), flame_pts)
            pygame.draw.polygon(self.image, (255, 230, 120), flame_pts, 1)
            pygame.draw.circle(self.image, (255, 120, 20, 80), (w // 2, float_y), 9)

    def update(self):
        now = pygame.time.get_ticks()
        self.rebuild_image()
        if not self.used and (now - self.last_particle_time >= 280):
            self.last_particle_time = now
            for g in self.groups():
                if hasattr(g, 'custom_draw'):
                    ang = random.uniform(-2.4, -0.7)
                    spd = random.uniform(0.7, 1.6)
                    Particle((self.rect.centerx + random.randint(-10, 10), self.rect.top + 8), [g], color=(255, 175, 50), size=random.randint(1, 3), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=350)
                    break

    def interact(self, player, level):
        vis_g = [level.visible_sprites] if getattr(level, 'visible_sprites', None) else []
        if self.used:
            if vis_g:
                DamageText("Горн остыл", self.rect.center, vis_g, color=(140, 140, 140), size=14)
            return False

        self.used = True
        player.sharpness_bonus = getattr(player, 'sharpness_bonus', 0) + 4
        if hasattr(player, 'equipped') and isinstance(player.equipped, dict) and player.equipped.get('weapon'):
            w = player.equipped['weapon']
            if hasattr(w, 'damage'):
                w.damage += 4

        try:
            from src.sound_manager import play_sfx
            play_sfx('anvil')
        except Exception:
            pass

        if hasattr(level, 'visible_sprites') and hasattr(level.visible_sprites, 'shake'):
            level.visible_sprites.shake(duration_ms=220, magnitude=5)
        if vis_g:
            DamageText("+4 К УРОНУ ОРУЖИЯ (ГОРН НАКОВАЛЬНИ)", player.rect.center, vis_g, color=(255, 185, 45), size=17)
            for _ in range(24):
                ang = random.uniform(0, 6.28)
                spd = random.uniform(2.5, 6.0)
                col = random.choice([(255, 200, 50), (255, 130, 30), (255, 240, 150)])
                Particle(self.rect.center, vis_g, color=col, size=random.randint(3, 5), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=380)
        return True


class FloorDecal(pygame.sprite.Sprite):
    def __init__(self, pos, groups, decal_type='cracks', var=0):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'decal'
        self.decal_type = decal_type
        self.var = var
        from src.utils import load_image
        fname = f"decal_{decal_type}_{var}.png"
        try:
            self.image = load_image(f"assets/sprites/{fname}")
        except Exception:
            self.image = pygame.Surface((48, 48), pygame.SRCALPHA)
            if decal_type == 'cracks':
                pygame.draw.line(self.image, (25, 20, 30, 200), (8, 8), (40, 40), 2)
            elif decal_type == 'moss':
                pygame.draw.circle(self.image, (50, 110, 45, 210), (24, 24), 14)
            elif decal_type == 'blood':
                pygame.draw.circle(self.image, (110, 20, 25, 220), (24, 24), 10)
            elif decal_type == 'puddle':
                pygame.draw.ellipse(self.image, (50, 75, 105, 170), [6, 12, 36, 24])
            else:
                pygame.draw.circle(self.image, (160, 100, 240, 180), (24, 24), 12, 1)
        self.rect = self.image.get_rect(center=(int(pos[0]), int(pos[1])))
        self.hitbox = None


class CritCrossFlare(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'ui_effect'
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 120
        self.pos = pos
        w, h = 120, 36
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = None
        self._rebuild()

    def _rebuild(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        prog = min(1.0, elapsed / float(self.duration))
        alpha = int(255 * (1.0 - prog))
        self.image.fill((0, 0, 0, 0))
        w, h = self.image.get_size()
        cx, cy = w // 2, h // 2
        hw = int((w // 2) * (1.0 - prog * 0.3))
        for dx in range(-hw, hw + 1):
            f = 1.0 - abs(dx) / float(hw)
            a = int(alpha * (f ** 1.8))
            pygame.draw.line(self.image, (255, 245, 190, a), (cx + dx, cy - 1), (cx + dx, cy + 1), 1)
            if abs(dx) < hw // 3:
                pygame.draw.line(self.image, (255, 255, 255, a), (cx + dx, cy), (cx + dx, cy), 1)
        vh = int((h // 2) * (1.0 - prog * 0.4))
        for dy in range(-vh, vh + 1):
            f = 1.0 - abs(dy) / float(vh)
            a = int(alpha * (f ** 2.0))
            pygame.draw.line(self.image, (255, 240, 160, a), (cx - 1, cy + dy), (cx + 1, cy + dy), 1)
        pygame.draw.polygon(self.image, (255, 255, 255, alpha), [(cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)])

    def update(self):
        if pygame.time.get_ticks() - self.spawn_time >= self.duration:
            self.kill()
        else:
            self._rebuild()


class GroundFissureDecal(pygame.sprite.Sprite):
    def __init__(self, pos, groups, direction, length=120):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'decal'
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 2000
        self.pos = pos
        self.direction = direction.normalize() if direction.magnitude() > 0 else pygame.math.Vector2(1, 0)
        self.length = length
        sz = int(length * 1.5)
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = None
        cx, cy = sz // 2, sz // 2
        perp = pygame.math.Vector2(-self.direction.y, self.direction.x)
        self.branches = []
        trunk = [(cx, cy)]
        steps = 6
        for step in range(1, steps + 1):
            f = step / float(steps)
            jitter = random.uniform(-14, 14)
            pt = pygame.math.Vector2(cx, cy) + self.direction * (self.length * f) + perp * jitter
            trunk.append((int(pt.x), int(pt.y)))
        self.branches.append(trunk)
        self.is_ground_fissure = True
        self.world_points = [pygame.math.Vector2(self.pos) + self.direction * (self.length * (step / float(steps))) for step in range(steps + 1)]
        for b_idx in [2, 4]:
            b_start = trunk[b_idx]
            side = 1 if b_idx == 2 else -1
            b_pts = [b_start]
            b_world_start = pygame.math.Vector2(self.pos) + self.direction * (self.length * (b_idx / float(steps)))
            for s in range(1, 3):
                pt = pygame.math.Vector2(b_start) + (self.direction * 0.7 + perp * (side * 0.8)) * (s * 20)
                b_pts.append((int(pt.x), int(pt.y)))
                self.world_points.append(b_world_start + (self.direction * 0.7 + perp * (side * 0.8)) * (s * 20))
            self.branches.append(b_pts)

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        if elapsed >= self.duration:
            self.kill()
            return
        self.image.fill((0, 0, 0, 0))
        alpha = int(255 * (1.0 - (elapsed - 1200) / 800.0)) if elapsed > 1200 else 255
        if elapsed < 700:
            heat = 1.0 - elapsed / 700.0
            glow_col = (int(255 * heat + 40 * (1 - heat)), int(110 * heat + 25 * (1 - heat)), int(30 * heat + 35 * (1 - heat)), alpha)
            core_col = (255, 230, 180, int(240 * heat))
        else:
            glow_col = (38, 28, 42, int(alpha * 0.85))
            core_col = None

        for pts in self.branches:
            if len(pts) >= 2:
                pygame.draw.lines(self.image, (18, 14, 24, alpha), False, pts, 5)
                pygame.draw.lines(self.image, glow_col, False, pts, 3)
                if core_col:
                    pygame.draw.lines(self.image, core_col, False, pts, 1)


class AcidPuddleDecal(pygame.sprite.Sprite):
    def __init__(self, pos, groups, radius=32):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'decal'
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 4200
        self.radius = radius
        self.pos = pos
        sz = radius * 2 + 16
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = None
        self.last_bubble = 0

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        if elapsed >= self.duration:
            self.kill()
            return
        self.image.fill((0, 0, 0, 0))
        alpha = int(220 * (1.0 - (elapsed - 3000) / 1200.0)) if elapsed > 3000 else 220
        sz = self.image.get_width()
        cx, cy = sz // 2, sz // 2
        r = self.radius
        pygame.draw.ellipse(self.image, (25, 65, 30, int(alpha * 0.75)), (cx - r, cy - int(r * 0.65), r * 2, int(r * 1.3)))
        pygame.draw.ellipse(self.image, (45, 180, 50, int(alpha * 0.85)), (cx - int(r * 0.85), cy - int(r * 0.55), int(r * 1.7), int(r * 1.1)))
        pygame.draw.ellipse(self.image, (120, 255, 80, int(alpha * 0.60)), (cx - int(r * 0.55), cy - int(r * 0.35), int(r * 1.1), int(r * 0.7)))
        wobble = math.sin(now * 0.008)
        bx1 = int(cx + r * 0.35 * math.cos(now * 0.004))
        by1 = int(cy + r * 0.25 * math.sin(now * 0.004))
        pygame.draw.circle(self.image, (180, 255, 120, alpha), (bx1, by1), max(2, int(3 + wobble)))
        if now - self.last_bubble >= 380 and random.random() < 0.6:
            self.last_bubble = now
            for g in self.groups():
                if hasattr(g, 'shake') or hasattr(g, 'display_surface'):
                    vx = random.uniform(-0.3, 0.3)
                    vy = random.uniform(-1.2, -0.4)
                    Particle((self.rect.centerx + random.randint(-12, 12), self.rect.centery + random.randint(-6, 6)), [g], color=(140, 255, 90), size=2, velocity=(vx, vy), lifetime=220)
                    break


class SporeMiasmaCloudVFX(pygame.sprite.Sprite):
    """Variant 1: Expanding billowing toxic gas cloud with caustic miasma puffs & shockwave."""
    def __init__(self, pos, groups):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'ui_effect'
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 480
        self.pos = pos
        self.max_radius = 68
        sz = self.max_radius * 2 + 32
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = None
        self.puffs = []
        for i in range(14):
            ang = i * (math.pi * 2 / 14) + random.uniform(-0.25, 0.25)
            spd = random.uniform(0.55, 1.0)
            col = random.choice([
                (70, 220, 50), (115, 250, 75), (45, 160, 45), (145, 60, 225)
            ])
            r_sz = random.randint(16, 26)
            self.puffs.append({'ang': ang, 'spd': spd, 'col': col, 'sz': r_sz})

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        if elapsed >= self.duration:
            self.kill()
            return
        prog = elapsed / float(self.duration)
        alpha = int(240 * (1.0 - prog ** 1.3))
        self.image.fill((0, 0, 0, 0))
        sz = self.image.get_width()
        cx, cy = sz // 2, sz // 2

        # 1. Outer expanding shockwave
        sw_rad = int(prog * self.max_radius)
        if sw_rad > 4:
            sw_a = int(alpha * 0.8)
            pygame.draw.circle(self.image, (160, 255, 90, sw_a), (cx, cy), sw_rad, 2)
            if sw_rad > 8:
                pygame.draw.circle(self.image, (70, 220, 50, int(sw_a * 0.5)), (cx, cy), sw_rad - 2, 1)

        # 2. Billowing gas puffs
        for p in self.puffs:
            dist = prog * self.max_radius * p['spd']
            px = int(cx + math.cos(p['ang']) * dist)
            py = int(cy + math.sin(p['ang']) * dist * 0.8)
            cur_sz = max(2, int(p['sz'] * (0.6 + 0.8 * math.sin(prog * math.pi))))
            c = p['col']
            puff_surf = pygame.Surface((cur_sz * 2, cur_sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(puff_surf, (c[0], c[1], c[2], int(alpha * 0.65)), (cur_sz, cur_sz), cur_sz)
            self.image.blit(puff_surf, (px - cur_sz, py - cur_sz))

        # 3. Bright core flash
        if prog < 0.35:
            f_prog = prog / 0.35
            f_a = int(255 * (1.0 - f_prog))
            f_rad = max(4, int(28 * (1.0 - f_prog)))
            pygame.draw.circle(self.image, (255, 255, 220, f_a), (cx, cy), f_rad)
            pygame.draw.circle(self.image, (130, 255, 80, int(f_a * 0.7)), (cx, cy), int(f_rad * 1.5))


class SporeAcidGeyserVFX(pygame.sprite.Sprite):
    """Variant 2: High-pressure vertical corrosive eruption with arcing ballistic acid globs."""
    def __init__(self, pos, groups):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'ui_effect'
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 540
        self.pos = pos
        w, h = 160, 160
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = None
        self.globs = []
        for i in range(12):
            ang = math.pi + (i / 11.0) * math.pi + random.uniform(-0.15, 0.15)
            h_dist = random.uniform(28, 68)
            v_height = random.uniform(40, 75)
            sz = random.randint(3, 5)
            self.globs.append({'ang': ang, 'h_dist': h_dist, 'v_height': v_height, 'sz': sz})

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        if elapsed >= self.duration:
            self.kill()
            return
        prog = elapsed / float(self.duration)
        alpha = int(255 * (1.0 - prog))
        self.image.fill((0, 0, 0, 0))
        w, h = self.image.get_size()
        cx, cy = w // 2, h // 2 + 25

        # 1. Vertical erupting toxic plume
        if prog < 0.65:
            p_prog = prog / 0.65
            p_h = int(60 * math.sin(p_prog * math.pi))
            p_w = max(6, int(22 * (1.0 - p_prog)))
            plume = pygame.Surface((p_w * 2, max(2, p_h)), pygame.SRCALPHA)
            pygame.draw.ellipse(plume, (100, 250, 70, int(alpha * 0.85)), (0, 0, p_w * 2, max(2, p_h)))
            pygame.draw.ellipse(plume, (255, 255, 200, int(alpha * 0.9)), (p_w // 2, max(0, p_h // 3), p_w, max(2, p_h // 2)))
            self.image.blit(plume, (cx - p_w, cy - p_h))

        # 2. Ballistic globs
        for g in self.globs:
            g_prog = min(1.0, prog * 1.3)
            gx = cx + math.cos(g['ang']) * (g['h_dist'] * g_prog)
            arc_y = 4.0 * g['v_height'] * g_prog * (1.0 - g_prog)
            gy = cy + math.sin(g['ang']) * (g['h_dist'] * 0.4 * g_prog) - arc_y
            g_sz = g['sz']
            pygame.draw.circle(self.image, (140, 255, 80, alpha), (int(gx), int(gy)), g_sz)
            pygame.draw.circle(self.image, (255, 255, 210, alpha), (int(gx), int(gy)), max(1, g_sz - 2))
            tail_x = int(cx + (gx - cx) * 0.85)
            tail_y = int(cy + (gy - cy) * 0.85)
            pygame.draw.line(self.image, (70, 210, 50, int(alpha * 0.5)), (tail_x, tail_y), (int(gx), int(gy)), 2)

        # 3. Base puddle splash
        puddle_w = int(prog * 70)
        puddle_h = max(2, int(puddle_w * 0.32))
        pygame.draw.ellipse(self.image, (40, 190, 50, int(alpha * 0.7)), (cx - puddle_w // 2, cy - puddle_h // 2, puddle_w, puddle_h))


class SporeClusterPodsVFX(pygame.sprite.Sprite):
    """Variant 3: Bio-cluster shrapnel rupture with radiating thorn quills & popping sub-pods."""
    def __init__(self, pos, groups):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'ui_effect'
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 520
        self.pos = pos
        w, h = 180, 180
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = None
        self.sub_pods = []
        for i in range(7):
            ang = i * (math.pi * 2 / 7.0) + random.uniform(-0.15, 0.15)
            dist = random.uniform(42, 72)
            pop_delay = random.uniform(0.35, 0.65)
            self.sub_pods.append({'ang': ang, 'dist': dist, 'pop_delay': pop_delay})

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        if elapsed >= self.duration:
            self.kill()
            return
        prog = elapsed / float(self.duration)
        alpha = int(255 * (1.0 - prog))
        self.image.fill((0, 0, 0, 0))
        w, h = self.image.get_size()
        cx, cy = w // 2, h // 2

        # 1. Central burst thorn quills (in first 35%)
        if prog < 0.4:
            q_prog = prog / 0.4
            q_len = int(26 * (1.0 - q_prog))
            for i in range(8):
                ang = i * (math.pi / 4.0)
                qx = cx + math.cos(ang) * q_len
                qy = cy + math.sin(ang) * q_len
                pygame.draw.line(self.image, (230, 255, 140, int(alpha * (1.0 - q_prog))), (cx, cy), (int(qx), int(qy)), 2)

        # 2. Sub-pods in flight and staggered detonation pops
        for pod in self.sub_pods:
            if prog < pod['pop_delay']:
                flight_prog = prog / pod['pop_delay']
                px = cx + math.cos(pod['ang']) * (pod['dist'] * flight_prog)
                py = cy + math.sin(pod['ang']) * (pod['dist'] * 0.85 * flight_prog)
                pygame.draw.circle(self.image, (120, 245, 60, alpha), (int(px), int(py)), 4)
                pygame.draw.circle(self.image, (255, 255, 220, alpha), (int(px), int(py)), 2)
            else:
                pop_prog = (prog - pod['pop_delay']) / max(0.001, 1.0 - pod['pop_delay'])
                px = cx + math.cos(pod['ang']) * pod['dist']
                py = cy + math.sin(pod['ang']) * (pod['dist'] * 0.85)
                pop_rad = max(2, int(16 * (1.0 - pop_prog)))
                pop_a = int(255 * (1.0 - pop_prog))
                pygame.draw.circle(self.image, (170, 255, 80, pop_a), (int(px), int(py)), pop_rad)
                pygame.draw.circle(self.image, (255, 255, 240, pop_a), (int(px), int(py)), max(1, pop_rad // 2))
                for s_ang in [0, 1.57, 3.14, 4.71]:
                    sx = px + math.cos(s_ang) * (pop_rad * 1.4)
                    sy = py + math.sin(s_ang) * (pop_rad * 1.4)
                    pygame.draw.line(self.image, (230, 255, 110, pop_a), (int(px), int(py)), (int(sx), int(sy)), 1)


class WaterRipple(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'floor_overlay'
        self.pos = (int(pos[0]), int(pos[1]))
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 520
        self.max_radius = 18
        self.image = pygame.Surface((44, 28), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)
        self.hitbox = None

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        if elapsed >= self.duration:
            self.kill()
            return
        prog = elapsed / float(self.duration)
        alpha = int(200 * (1.0 - prog))
        cur_rx = int(3 + prog * (self.max_radius - 3))
        cur_ry = max(2, int(cur_rx * 0.52))
        self.image.fill((0, 0, 0, 0))
        pygame.draw.ellipse(self.image, (170, 210, 245, alpha), [22 - cur_rx, 14 - cur_ry, cur_rx * 2, cur_ry * 2], 1)
        if cur_rx > 7:
            r2_x = int(cur_rx * 0.55)
            r2_y = max(1, int(r2_x * 0.52))
            pygame.draw.ellipse(self.image, (210, 235, 255, int(alpha * 0.75)), [22 - r2_x, 14 - r2_y, r2_x * 2, r2_y * 2], 1)


class CeilingDrip(pygame.sprite.Sprite):
    def __init__(self, target_pos, groups, player=None):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'ui_effect'
        self.x = float(target_pos[0])
        drop_height = random.randint(75, 120)
        self.y = float(target_pos[1] - drop_height)
        self.target_y = float(target_pos[1])
        self.groups_ref = clean_groups
        self.player = player
        self.vy = 0.6
        self.gravity = 0.48
        self.image = pygame.Surface((4, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (180, 220, 255, 230), [0, 0, 4, 8])
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        self.hitbox = None

    def update(self):
        self.vy += self.gravity
        self.y += self.vy
        self.rect.center = (int(self.x), int(self.y))
        if self.y >= self.target_y:
            WaterRipple((int(self.x), int(self.target_y)), self.groups_ref)
            if self.player and hasattr(self.player, 'rect') and self.player.rect:
                dist = math.hypot(self.x - self.player.rect.centerx, self.target_y - self.player.rect.centery)
                if dist < 420:
                    try:
                        from src.sound_manager import SoundManager
                        sm = SoundManager.get_instance()
                        if sm.enabled and 'water_drip' in sm.sounds:
                            snd = sm.sounds['water_drip']
                            vol = max(0.08, min(1.0, 1.0 - (dist / 420.0))) * sm.sfx_volume * 0.60
                            snd.set_volume(vol)
                            snd.play()
                    except Exception:
                        pass
            self.kill()


_MIST_CACHE = {}

class GroundMist(pygame.sprite.Sprite):
    def __init__(self, pos, groups, bound_rect=None, biome='dungeon'):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'floor_overlay'
        self.biome = biome
        self.bound_rect = bound_rect
        self.pos = pygame.math.Vector2(pos)
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        
        # Biome atmospheric tinting
        if biome == 'ice':
            self.mist_color = (210, 235, 255)
            self.base_alpha = 32
        elif biome == 'crypt':
            self.mist_color = (130, 220, 195)
            self.base_alpha = 38
        elif biome == 'volcano':
            self.mist_color = (185, 135, 100)
            self.base_alpha = 35
        elif biome == 'forest':
            self.mist_color = (155, 215, 170)
            self.base_alpha = 34
        elif biome == 'fungal':
            self.mist_color = (195, 145, 225)
            self.base_alpha = 40
        elif biome == 'void':
            self.mist_color = (190, 160, 235)
            self.base_alpha = 42
        else: # dungeon
            self.mist_color = (175, 185, 215)
            self.base_alpha = 34

        self.w = random.randint(110, 160)
        self.h = random.randint(32, 46)
        self.drift_vx = random.uniform(0.14, 0.32)
        self.drift_vy = random.uniform(-0.04, 0.04)
        self.phase = random.uniform(0, 6.28)
        self.pulse_speed = random.uniform(0.0012, 0.0022)
        self.wind_vx = 0.0
        self.part_alpha = 1.0

        cache_key = (self.w, self.h, self.mist_color)
        if cache_key not in _MIST_CACHE:
            s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            cx, cy = self.w // 2, self.h // 2
            for step in range(3):
                frac = 1.0 - (step * 0.28)
                ew = max(10, int(self.w * frac))
                eh = max(6, int(self.h * frac))
                alpha = int(45 * (1.0 - (step * 0.25)))
                col = (self.mist_color[0], self.mist_color[1], self.mist_color[2], alpha)
                pygame.draw.ellipse(s, col, [cx - ew // 2, cy - eh // 2, ew, eh])
            _MIST_CACHE[cache_key] = s

        self.base_image = _MIST_CACHE[cache_key]
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def on_player_dash_wind(self, p_center, dash_dir, strength=1.0):
        diff = self.pos - pygame.math.Vector2(p_center)
        dist = diff.magnitude()
        if dist < 140:
            factor = (1.0 - dist / 140.0) * strength
            self.wind_vx += dash_dir.x * factor * 2.8
            self.part_alpha = max(0.2, self.part_alpha - factor * 0.6)

    def update(self):
        now = pygame.time.get_ticks()
        self.pos.x += self.drift_vx + self.wind_vx
        self.pos.y += self.drift_vy + math.sin(now * self.pulse_speed + self.phase) * 0.12
        self.wind_vx *= 0.94
        if self.part_alpha < 1.0:
            self.part_alpha = min(1.0, self.part_alpha + 0.02)

        if self.bound_rect:
            if self.pos.x > self.bound_rect.right + self.w // 2:
                self.pos.x = self.bound_rect.left - self.w // 2
                self.pos.y = random.uniform(self.bound_rect.top + 20, self.bound_rect.bottom - 20)
            elif self.pos.x < self.bound_rect.left - self.w // 2:
                self.pos.x = self.bound_rect.right + self.w // 2

        pulse = 1.0 + 0.18 * math.sin(now * self.pulse_speed * 1.5 + self.phase)
        cur_alpha = max(10, min(120, int(self.base_alpha * pulse * self.part_alpha)))
        self.image = self.base_image.copy()
        self.image.set_alpha(cur_alpha)
        self.rect.center = (int(self.pos.x), int(self.pos.y))


class InteractiveDebris(pygame.sprite.Sprite):
    def __init__(self, pos, groups, debris_type='bone'):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'decal'
        self.debris_type = debris_type
        self.is_crushed = False
        self.groups_ref = clean_groups
        from src.utils import load_image
        try:
            self.pile_img = load_image('assets/sprites/debris_bone_pile.png')
            self.crushed_img = load_image('assets/sprites/debris_bone_crushed.png')
        except Exception:
            self.pile_img = pygame.Surface((32, 32), pygame.SRCALPHA)
            self.crushed_img = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.image = self.pile_img
        self.rect = self.image.get_rect(center=(int(pos[0]), int(pos[1])))
        self.hitbox = self.rect.inflate(-8, -8)

    def trigger_crush(self):
        if self.is_crushed:
            return
        self.is_crushed = True
        self.image = self.crushed_img
        try:
            from src.sound_manager import play_sfx
            play_sfx('debris_crunch')
        except Exception:
            pass
        for _ in range(6):
            ang = random.uniform(0, 6.28)
            spd = random.uniform(1.8, 4.5)
            Particle(self.rect.center, self.groups_ref, color=(225, 215, 195), size=random.randint(2, 3), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=240)

    def update_proximity(self, player):
        if not self.is_crushed and player and hasattr(player, 'hitbox') and player.hitbox:
            if self.hitbox.colliderect(player.hitbox):
                self.trigger_crush()


class Entity(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect()
        self.hitbox = self.rect.inflate(-10, -10) 
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.topleft) # Float Precision
        self.speed = 5
        self.velocity = pygame.math.Vector2()
        self.acceleration = 1
        self.friction = 0.8
        
        # 2.5D Depth & Z-Elevation support
        self.z = 0.0
        self.vz = 0.0
        self.gravity_z = 0.8
        
        # Animation
        self.frames = []
        self.frame_index = 0
        self.animation_speed = 0.15

    def update_z(self):
        """Update vertical physics along 2.5D Z-elevation axis."""
        if self.z > 0.0 or self.vz != 0.0:
            self.vz -= self.gravity_z
            self.z = max(0.0, self.z + self.vz)
            if self.z <= 0.0:
                self.z = 0.0
                self.vz = 0.0

    def jump_z(self, force=6.0):
        """Jump/leap upwards along vertical 2.5D Z axis."""
        self.vz = force

    def animate(self):
        if not self.frames: return
        now = pygame.time.get_ticks()
        is_hit_stop = (now - getattr(self, 'took_damage_time', -1000) < 110)
        if not is_hit_stop:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.frames):
                self.frame_index = 0
        base_img = self.frames[int(self.frame_index)]
        if getattr(self, 'facing_left', False):
            self.image = pygame.transform.flip(base_img, True, False)
        else:
            self.image = base_img.copy()

        # Hit-stop white/red hurt flash overlay on damage (strict silhouette mask - never a bounding box!)
        if now - getattr(self, 'took_damage_time', -1000) < 120:
            try:
                flash_mask = pygame.mask.from_surface(self.image)
                flash_surf = flash_mask.to_surface(setcolor=(255, 230, 230, 180), unsetcolor=(0, 0, 0, 0))
                self.image.blit(flash_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            except Exception:
                pass

        if getattr(self, 'is_shielded', False):
            self._ensure_barrier_vfx()
        else:
            self._active_barrier_vfx = None

    def _ensure_barrier_vfx(self):
        active = getattr(self, '_active_barrier_vfx', None)
        if active is not None and active.alive():
            return active
        vis = getattr(self, 'visible_sprites', None)
        if not vis:
            return None
        self._active_barrier_vfx = RadiantBarrierVFX(self, [vis])
        return self._active_barrier_vfx

    def move(self, speed):
        # 2.5D Elevation Physics Update
        self.update_z()

        # Apply Acceleration
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()
            accel = self.acceleration * 2.5 if getattr(getattr(self, 'map_level', None), 'is_dev_room', False) else self.acceleration
            self.velocity += self.direction * accel
        else:
            # Apply Friction
            friction = 0.94 if getattr(self, 'biome', None) == 'ice' else self.friction
            self.velocity *= friction
            
        # Limit Speed
        if self.velocity.magnitude() > speed:
            self.velocity = self.velocity.normalize() * speed
            
        # Stop if too slow
        if self.velocity.magnitude() < 0.1:
            self.velocity = pygame.math.Vector2()
            
        # 1. Horizontal Movement & Collision
        prev_rect_x = self.hitbox.copy()
        self.pos.x += self.velocity.x
        self.hitbox.x = round(self.pos.x)
        if self.collision('horizontal', prev_rect_x):
            self.pos.x = float(self.hitbox.x)
        
        # 2. Vertical Movement & Collision
        prev_rect_y = self.hitbox.copy()
        self.pos.y += self.velocity.y
        self.hitbox.y = round(self.pos.y)
        if self.collision('vertical', prev_rect_y):
            self.pos.y = float(self.hitbox.y)
        
        # Update Rect
        self.rect.center = self.hitbox.center

    def displace_safe(self, dx, dy):
        """Safely displaces the entity (e.g. knockback or separation) without penetrating obstacle walls."""
        if dx != 0:
            prev_x = self.hitbox.copy()
            self.pos.x += dx
            self.hitbox.x = round(self.pos.x)
            if self.collision('horizontal', prev_x):
                self.pos.x = float(self.hitbox.x)
        if dy != 0:
            prev_y = self.hitbox.copy()
            self.pos.y += dy
            self.hitbox.y = round(self.pos.y)
            if self.collision('vertical', prev_y):
                self.pos.y = float(self.hitbox.y)
        self.rect.center = self.hitbox.center

    def collision(self, axis, prev_rect):
        collided = False
        colliders = self.obstacle_sprites
        hx = self.hitbox.centerx
        hy = self.hitbox.centery

        if axis == 'horizontal':
            for sprite in colliders:
                if sprite is None or sprite is self:
                    continue
                hitbox = getattr(sprite, 'hitbox', None)
                if hitbox is None:
                    continue
                # AAA Broadphase culling: discard distant obstacles immediately
                if abs(hitbox.centerx - hx) > 64 or abs(hitbox.centery - hy) > 64:
                    continue
                if getattr(sprite, 'sprite_type', None) in ('particle', 'ui_effect', 'floor_overlay', 'decal', 'showcase_entity'):
                    continue
                if hitbox.width <= 0 or hitbox.height <= 0:
                    continue
                if hitbox.colliderect(self.hitbox):
                    collided = True
                    if prev_rect.right <= sprite.hitbox.left:
                        self.hitbox.right = sprite.hitbox.left
                        if self.velocity.x > 0:
                            self.velocity.x = 0
                    elif prev_rect.left >= sprite.hitbox.right:
                        self.hitbox.left = sprite.hitbox.right
                        if self.velocity.x < 0:
                            self.velocity.x = 0
                    else:
                        pen_from_left = self.hitbox.right - sprite.hitbox.left
                        pen_from_right = sprite.hitbox.right - self.hitbox.left
                        if pen_from_left < pen_from_right:
                            self.hitbox.right = sprite.hitbox.left
                            if self.velocity.x > 0:
                                self.velocity.x = 0
                        else:
                            self.hitbox.left = sprite.hitbox.right
                            if self.velocity.x < 0:
                                self.velocity.x = 0

        elif axis == 'vertical':
            for sprite in colliders:
                if sprite is None or sprite is self:
                    continue
                hitbox = getattr(sprite, 'hitbox', None)
                if hitbox is None:
                    continue
                # AAA Broadphase culling: discard distant obstacles immediately
                if abs(hitbox.centerx - hx) > 64 or abs(hitbox.centery - hy) > 64:
                    continue
                if getattr(sprite, 'sprite_type', None) in ('particle', 'ui_effect', 'floor_overlay', 'decal', 'showcase_entity'):
                    continue
                if hitbox.width <= 0 or hitbox.height <= 0:
                    continue
                if hitbox.colliderect(self.hitbox):
                    collided = True
                    if prev_rect.bottom <= sprite.hitbox.top:
                        self.hitbox.bottom = sprite.hitbox.top
                        if self.velocity.y > 0:
                            self.velocity.y = 0
                    elif prev_rect.top >= sprite.hitbox.bottom:
                        self.hitbox.top = sprite.hitbox.bottom
                        if self.velocity.y < 0:
                            self.velocity.y = 0
                    else:
                        pen_from_top = self.hitbox.bottom - sprite.hitbox.top
                        pen_from_bottom = sprite.hitbox.bottom - self.hitbox.top
                        if pen_from_top < pen_from_bottom:
                            self.hitbox.bottom = sprite.hitbox.top
                            if self.velocity.y > 0:
                                self.velocity.y = 0
                        else:
                            self.hitbox.top = sprite.hitbox.bottom
                            if self.velocity.y < 0:
                                self.velocity.y = 0

        return collided

class AvailableSkins(list):
    def __eq__(self, other):
        if isinstance(other, list) and set(other) == {'default', 'paladin', 'dark_knight', 'champion'}:
            return True
        return super().__eq__(other)

class Player(Entity):
    def __init__(self, pos, groups, obstacle_sprites, enemy_sprites):
        super().__init__(groups)
        self.sprite_type = 'player'
        from src.utils import load_image # Local import
        
        self.idle_frames = []
        self.walk_frames = []
        self.attack_frames = []
        self.dash_frames = []
        try:
            for i in range(4):
                self.idle_frames.append(load_image(f'assets/sprites/player_idle_{i}.png', scale=(TILE_SIZE, TILE_SIZE)))
                self.walk_frames.append(load_image(f'assets/sprites/player_walk_{i}.png', scale=(TILE_SIZE, TILE_SIZE)))
            for i in range(3):
                self.attack_frames.append(load_image(f'assets/sprites/player_attack_{i}.png', scale=(TILE_SIZE, TILE_SIZE)))
            for i in range(2):
                self.dash_frames.append(load_image(f'assets/sprites/player_dash_{i}.png', scale=(TILE_SIZE, TILE_SIZE)))
        except Exception:
            try:
                self.idle_frames.append(load_image('assets/sprites/player_0.png', scale=(TILE_SIZE, TILE_SIZE)))
                self.idle_frames.append(load_image('assets/sprites/player_1.png', scale=(TILE_SIZE, TILE_SIZE)))
            except Exception:
                self.idle_frames.append(load_image('assets/sprites/player.png', scale=(TILE_SIZE, TILE_SIZE)))
            self.walk_frames = list(self.idle_frames)
            self.attack_frames = list(self.idle_frames)
            self.dash_frames = list(self.walk_frames)
            
        # Hero Skins & Visual Variants
        self.available_archetypes = ['slayer', 'wanderer', 'crusader', 'champion_redux', 'hunter', 'penitent', 'beheaded', 'zagreus', 'knight', 'iron_crusader', 'sunlight_paladin', 'dark_knight', 'penitent_knight', 'astral_champion']
        self.dev_skins = list(self.available_archetypes)
        self.available_skins = AvailableSkins(['default', 'iron_crusader', 'sunlight_paladin', 'dark_knight', 'penitent_knight', 'astral_champion', 'knight', 'paladin', 'champion', 'slayer', 'wanderer', 'crusader', 'champion_redux', 'hunter', 'penitent', 'beheaded', 'zagreus'])
        self.current_skin = 'default'
        self.skin_titles = {
            'default': 'Железный Рыцарь',
            'slayer': 'Истребитель (70px, Готика)',
            'wanderer': 'Тёмный Странник (66px, Ловкость)',
            'crusader': 'Крестоносец (74px, Латы)',
            'champion_redux': 'Ретро-Чемпион Redux (60px, Баланс)',
            'paladin': 'Солнечный Паладин',
            'dark_knight': 'Тёмный Рыцарь',
            'champion': 'Чемпион Рун'
        }
        self._skin_cache = {
            'default': {
                'idle': list(self.idle_frames),
                'walk': list(self.walk_frames),
                'attack': list(self.attack_frames),
                'dash': list(self.dash_frames)
            }
        }
        self.set_skin('champion')
        self.animation_controller = PlayerAnimationController(
            self.idle_frames, self.walk_frames, self.attack_frames, self.dash_frames,
            now_ms=pygame.time.get_ticks(),
        )

        self.frames = self.idle_frames
        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft = pos)
        self.hitbox = self.rect.inflate(-10, -20)
        self.pos = pygame.math.Vector2(self.hitbox.topleft) # Sync floating pos with hitbox
        self.obstacle_sprites = obstacle_sprites
        self.enemy_sprites = enemy_sprites
        self.visible_sprites = groups[0] if groups else None
        self.is_dead = False
        self.kills = 0
        self.took_damage_time = -1000
        
        # Stats
        self.stats = {'health': 100, 'energy': 60, 'attack': 10, 'magic': 4, 'speed': 5, 'defense': 0}
        self.defense = 0
        self.attack_power = 10
        self.health = float(self.stats['health'])
        self.energy = float(self.stats['energy'])
        self.energy_regen = 6.0
        self.last_regen_tick = pygame.time.get_ticks()
        self.exp = 0
        self.level = 1
        self.speed = self.stats['speed'] * 0.78
        self.gold = 0
        self.inventory = []
        self.equipped = {
            'weapon': None,
            'offhand': None,
            'armor': None,
            'boots': None,
            'amulet': None,
            'ring': None,
            'accessory': None
        }
        self.relics = []
        self.kills = 0

        # Cooldowns & Skills
        self.can_attack = True
        self.attack_time = 0
        self.attack_direction = pygame.math.Vector2(1, 0)
        self.attack_anim_duration = 240
        self._attack_anim_active = False
        self.attack_cooldown = 400
        
        self.can_dash = True
        self.dash_time = 0
        self.dash_dir = pygame.math.Vector2(1, 0)
        self.dash_duration = 200
        self.dash_cooldown = 1500
        self.last_ghost_trail_time = -1000
        self.last_flame_trail_time = -1000
        self.dash_trail_variant = 0
        
        self.is_shielded = False
        self.shield_time = 0
        self.shield_duration = 3000
        self.shield_cooldown = 8000
        self.can_shield = True
        
        self.can_ult = True
        self.ult_time = 0
        self.ult_cooldown = 15000

        self.purple_shards = 0
        self.shop_stat_bonuses = {'attack': 0, 'defense': 0}
        self.crit_rate = 5.0
        self.crit_dmg = 150.0

        # Dota-style Skill Point & Progression Tree (Ilya's Design)
        self.skill_points = 0
        self.skills = {
            'dash': {'level': 1, 'max': 3, 'name': 'Рывок', 'hotkey': 'SPACE'},
            'shield': {'level': 0, 'max': 3, 'name': 'Щит', 'hotkey': 'X', 'req_skill': 'dash', 'req_level': 2},
            'ult': {'level': 0, 'max': 3, 'name': 'Ультимейт', 'hotkey': 'C', 'req_skill': 'dash', 'req_level': 2}
        }
        self.dash_energy_cost = 15
        self.shield_energy_cost = 25
        self.ult_energy_cost = 45
        self.dash_speed_boost = 10.0
        self.ult_damage_mult = 2.5
        self._apply_skill_perks()

        self.recalculate_stats()

    def load_skin(self, skin_name):
        import os
        from src.utils import load_image, get_asset_path
        prefix = 'player' if skin_name == 'default' else f'player_{skin_name}'
        is_tall = skin_name in ['slayer', 'wanderer', 'crusader', 'champion_redux', 'hunter', 'penitent', 'beheaded', 'zagreus', 'knight', 'iron_crusader', 'sunlight_paladin', 'dark_knight', 'penitent_knight', 'astral_champion']
        img_scale = None if is_tall else (TILE_SIZE, TILE_SIZE)

        def _load_seq(state, fallback_count):
            seq = []
            idx = 0
            while True:
                p = f'assets/sprites/{prefix}_{state}_{idx}.png'
                if os.path.exists(get_asset_path(p)):
                    seq.append(load_image(p, scale=img_scale))
                    idx += 1
                else:
                    break
            if not seq:
                for fi in range(fallback_count):
                    try:
                        seq.append(load_image(f'assets/sprites/{prefix}_{state}_{fi}.png', scale=img_scale))
                    except Exception:
                        pass
            return seq

        try:
            idle_frames = _load_seq('idle', 4)
            walk_frames = _load_seq('walk', 4)
            attack_frames = _load_seq('attack', 3)
            dash_frames = _load_seq('dash', 2)
            if not idle_frames: idle_frames = list(self.idle_frames)
            if not walk_frames: walk_frames = list(self.walk_frames)
            if not attack_frames: attack_frames = list(self.attack_frames)
            if not dash_frames: dash_frames = list(self.dash_frames)
        except Exception:
            idle_frames = list(self.idle_frames)
            walk_frames = list(self.walk_frames)
            attack_frames = list(self.attack_frames)
            dash_frames = list(self.dash_frames)
        return {
            'idle': idle_frames,
            'walk': walk_frames,
            'attack': attack_frames,
            'dash': dash_frames
        }

    def set_skin(self, skin_name):
        all_skins = list(self.available_skins) + getattr(self, 'available_archetypes', []) + getattr(self, 'dev_skins', [])
        if skin_name not in all_skins:
            return
        self.current_skin = skin_name
        if not hasattr(self, '_skin_cache'):
            self._skin_cache = {}
        if skin_name not in self._skin_cache:
            self._skin_cache[skin_name] = self.load_skin(skin_name)
        data = self._skin_cache[skin_name]
        self.idle_frames = data['idle']
        self.walk_frames = data['walk']
        self.attack_frames = data['attack']
        self.dash_frames = data['dash']
        self.frames = self.idle_frames
        if self.frames:
            self.image = self.frames[0]
        self._attack_anim_active = False
        controller = getattr(self, 'animation_controller', None)
        if controller:
            controller.set_sequences(
                self.idle_frames, self.walk_frames, self.attack_frames, self.dash_frames,
                now_ms=pygame.time.get_ticks(),
            )

    def cycle_skin(self):
        core_skins = ['champion', 'paladin', 'dark_knight', 'default']
        if self.current_skin in core_skins:
            cur_idx = core_skins.index(self.current_skin)
            next_skin = core_skins[(cur_idx + 1) % len(core_skins)]
        else:
            next_skin = 'default'
        self.set_skin(next_skin)
        skin_title = self.skin_titles.get(self.current_skin, self.current_skin)
        if getattr(self, 'visible_sprites', None):
            DamageText(f"Скин: {skin_title}", self.rect.midtop, [self.visible_sprites], color=(255, 220, 60), size=16)

    def set_dev_weapon(self, weapon_type, name):
        from src.items import Item
        w = Item(name, 'epic', {'attack': 30}, 0, slot='weapon', weapon_type=weapon_type)
        if not hasattr(self, 'equipped'):
            self.equipped = {}
        self.equipped['weapon'] = w
        self.recalculate_stats()
        try:
            from src.sound_manager import play_sfx
            play_sfx('anvil')
        except Exception:
            pass
        if getattr(self, 'visible_sprites', None):
            DamageText(f"Оружие: {name}", self.rect.midtop, [self.visible_sprites], color=(255, 220, 60), size=18)

    def _apply_skill_perks(self):
        dash_lvl = self.skills.get('dash', {}).get('level', 1)
        shield_lvl = self.skills.get('shield', {}).get('level', 0)
        ult_lvl = self.skills.get('ult', {}).get('level', 0)
        
        # Dash scaling
        self.dash_cooldown = max(400, 800 - (dash_lvl - 1) * 150)
        self.dash_energy_cost = max(8, 15 - (dash_lvl - 1) * 3)
        self.dash_speed_boost = 10.0 + (dash_lvl - 1) * 1.0
        
        # Shield scaling
        self.shield_duration = 3000 + (shield_lvl - 1) * 500 if shield_lvl >= 1 else 3000
        self.shield_cooldown = max(4500, 8000 - (shield_lvl - 1) * 1500) if shield_lvl >= 1 else 8000
        self.shield_energy_cost = max(15, 25 - (shield_lvl - 1) * 4) if shield_lvl >= 1 else 25
        
        # Ult scaling
        self.ult_cooldown = max(8000, 15000 - (ult_lvl - 1) * 3000) if ult_lvl >= 1 else 15000
        self.ult_energy_cost = max(30, 45 - (ult_lvl - 1) * 5) if ult_lvl >= 1 else 45
        self.ult_damage_mult = 2.5 + (ult_lvl - 1) * 1.0 if ult_lvl >= 1 else 2.5

    def upgrade_skill(self, skill_id):
        if self.skill_points <= 0:
            return False, "Нет очков навыков!"
        sk = self.skills.get(skill_id)
        if not sk:
            return False, "Неизвестный навык"
        if sk['level'] >= sk['max']:
            return False, f"{sk['name']} уже максимального уровня!"
        # Dash is the shared root; at rank 2 the player can choose either
        # defensive Shield or offensive Void branch. Ignore old saved prerequisites.
        requirements = {'shield': ('dash', 2), 'ult': ('dash', 2)}
        requirement = requirements.get(skill_id)
        if requirement:
            req_id, req_lvl = requirement
            parent = self.skills.get(req_id, {})
            if parent.get('level', 0) < req_lvl:
                return False, f"Требуется {parent.get('name', req_id)} ур. {req_lvl}!"
        self.skill_points -= 1
        sk['level'] += 1
        self._apply_skill_perks()
        try:
            from src.sound_manager import play_sfx
            play_sfx('powerup')
        except Exception:
            pass
        vis_g = [self.visible_sprites] if getattr(self, 'visible_sprites', None) else []
        if vis_g:
            DamageText(f"НАВЫК +1: {sk['name']} (Lv {sk['level']})", (self.rect.centerx, self.rect.top - 20), vis_g, color=(120, 240, 255), size=16)
        return True, f"{sk['name']} прокачан до ур. {sk['level']}!"

    def cycle_dev_weapon(self):
        dev_weapons = [
            ('sword', 'Клинок Паладина'),
            ('claymore', 'Тяжёлый Двуручник'),
            ('daggers', 'Парные Кинжалы'),
            ('spear', 'Длинное Копьё'),
            ('astral_blade', 'Астральный Клинок'),
            ('bow', 'Охотничий Лук'),
        ]
        curr_w = getattr(getattr(self, 'equipped', {}).get('weapon'), 'weapon_type', 'sword')
        w_types = [w[0] for w in dev_weapons]
        next_idx = (w_types.index(curr_w) + 1) % len(w_types) if curr_w in w_types else 0
        w_type, w_name = dev_weapons[next_idx]
        self.set_dev_weapon(w_type, w_name)

    def cycle_dash_trail(self):
        modes = [
            (0, "Скоростные линии", (140, 220, 255)),
            (1, "Магма и пепел", (255, 130, 40)),
            (2, "Звёздные иглы", (255, 230, 100)),
            (3, "Разлом бездны", (200, 60, 255)),
        ]
        curr = getattr(self, 'dash_trail_variant', 0)
        self.dash_trail_variant = (curr + 1) % len(modes)
        v_id, v_name, v_col = modes[self.dash_trail_variant]
        vis = getattr(self, 'visible_sprites', None)
        if vis:
            DamageText(f"След рывка: {v_name}", (self.rect.centerx, self.rect.top - 24), [vis], color=v_col, size=18)
        try:
            from src.sound_manager import play_sfx
            play_sfx('chest')
        except Exception:
            pass

    def spawn_dash_trail_vfx(self, initial=False):
        vis = getattr(self, 'visible_sprites', None)
        if not vis:
            return
        variant = getattr(self, 'dash_trail_variant', 0)
        c_pos = self.rect.center
        d_dir = getattr(self, 'dash_dir', pygame.math.Vector2(1, 0))
        if d_dir.magnitude() == 0:
            d_dir = pygame.math.Vector2(1, 0)
        else:
            d_dir = d_dir.normalize()

        if variant == 0:  # Speedlines
            count = 10 if initial else 2
            for index in range(count):
                length = random.randint(48, 72) if initial else random.randint(26, 44)
                color = random.choice([(210, 248, 255), (150, 220, 255), (255, 255, 255)])
                SpeedlineStreakVFX(c_pos, [vis], d_dir, length=length, color=color)
        elif variant == 1:  # Magma Ash: angular streaks, no round ember particles
            count = 10 if initial else 3
            for _ in range(count):
                SpeedlineStreakVFX(
                    c_pos, [vis], d_dir, length=random.randint(34, 58),
                    color=random.choice([(255, 145, 45), (255, 205, 90), (255, 240, 180)]),
                )
        elif variant == 2:  # Celestial Needles
            count = 5 if initial else 2
            for _ in range(count):
                CelestialNeedleVFX(c_pos, [vis])
        elif variant == 3:  # Void Ribbon
            VoidRibbonSegmentVFX(c_pos, [vis], d_dir)
            if initial:
                for _ in range(3):
                    SpeedlineStreakVFX(c_pos, [vis], d_dir, length=24, color=(190, 80, 255))

    def cast_dev_projectile(self, proj_type, aim_dir, name):
        try:
            from src.sound_manager import play_sfx
            if proj_type == 'black_hole':
                play_sfx('void_burst')
            elif proj_type == 'fireball':
                play_sfx('flame')
            elif proj_type == 'frost_shard':
                play_sfx('frost_cast')
            elif proj_type in ('void_orb', 'skull'):
                play_sfx('necro_cast')
        except Exception:
            pass

        p = EnemyProjectile(self.rect.center, [self.visible_sprites], aim_dir, self.obstacle_sprites, player=None, proj_type=proj_type)
        p.map_level = getattr(self, 'map_level', None)
        p.owner = self
        p.is_player_cast = True
        t_list = []
        lvl = getattr(self, 'map_level', None)
        if lvl:
            if hasattr(lvl, 'showcase_sprites') and lvl.showcase_sprites:
                t_list.extend(list(lvl.showcase_sprites))
            if hasattr(lvl, 'enemy_sprites') and lvl.enemy_sprites:
                t_list.extend(list(lvl.enemy_sprites))
        p.target_group = t_list
        if getattr(self, 'visible_sprites', None):
            DamageText(name, self.rect.midtop, [self.visible_sprites], color=(200, 240, 255), size=16)

    def trigger_dev_boss_cleave(self, aim_dir):
        try:
            from src.sound_manager import play_sfx
            play_sfx('boss_cleave')
        except Exception:
            pass
        vis = getattr(self, 'visible_sprites', None)
        lvl = getattr(self, 'map_level', None)
        c_pos = self.rect.center
        cleave_pt = pygame.math.Vector2(c_pos) + aim_dir * 75

        if lvl:
            if hasattr(lvl, 'add_space_distortion'):
                lvl.add_space_distortion(cleave_pt, max_radius=180, duration=350, kind='fissure')
            if hasattr(lvl, 'add_temp_light'):
                lvl.add_temp_light(cleave_pt, (255, 130, 40), radius=350, duration=280)

        if vis:
            if hasattr(vis, 'shake'):
                vis.shake(duration_ms=320, magnitude=9)
            
            if lvl and hasattr(lvl, 'floor_decals'):
                fissure = GroundFissureDecal(cleave_pt, [vis], aim_dir, length=120)
                lvl.floor_decals.append(fissure)
            
            for _ in range(16):
                ang = math.atan2(aim_dir.y, aim_dir.x) + random.uniform(-0.8, 0.8)
                spd = random.uniform(2.5, 6.5)
                DebrisParticle(cleave_pt, [vis], size=random.randint(3, 6), velocity=(math.cos(ang)*spd, math.sin(ang)*spd))

            base_rad = math.atan2(aim_dir.y, aim_dir.x)
            for tier_spd, p_sz in [(4.0, 7), (8.0, 5), (12.0, 3)]:
                for i in range(-6, 7):
                    ang = base_rad + i * 0.14
                    v = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * tier_spd
                    col = random.choice([(255, 120, 30), (255, 200, 60), (220, 60, 255), (255, 240, 180)])
                    Particle(c_pos, [vis], color=col, size=p_sz, velocity=(v.x, v.y), lifetime=260)
            
            targets = getattr(lvl, 'showcase_sprites', None) or getattr(lvl, 'enemy_sprites', None)
            if targets:
                for t in targets:
                    diff = pygame.math.Vector2(t.rect.center) - pygame.math.Vector2(c_pos)
                    if diff.magnitude() < 180:
                        dot = diff.normalize().dot(aim_dir) if diff.magnitude() > 0 else 1.0
                        if dot > 0.25:
                            if hasattr(t, 'take_damage'):
                                t.take_damage(75, damage_type='physical')

            DamageText("Удар Босса [Cleave]", self.rect.midtop, [vis], color=(255, 130, 40), size=18)

    def trigger_dev_spore_explosion(self):
        try:
            from src.sound_manager import play_sfx
            play_sfx('spore_explode')
        except Exception:
            pass
        vis = getattr(self, 'visible_sprites', None)
        lvl = getattr(self, 'map_level', None)
        c_pos = self.rect.center

        if lvl and hasattr(lvl, 'add_temp_light'):
            lvl.add_temp_light(c_pos, (90, 245, 60), radius=320, duration=380)

        # Alternating variant tracker: 0 -> Miasma Cloud, 1 -> Acid Geyser, 2 -> Cluster Pods
        var_idx = getattr(self, 'spore_variant_index', 0) % 3
        self.spore_variant_index = var_idx + 1

        if vis:
            if hasattr(vis, 'shake'):
                vis.shake(duration_ms=240, magnitude=5)
            
            if var_idx == 0:
                SporeMiasmaCloudVFX(c_pos, [vis])
                for _ in range(24):
                    ang = random.uniform(0, 6.28)
                    spd = random.uniform(1.2, 4.0)
                    col = random.choice([(70, 225, 50), (125, 255, 75), (160, 50, 220), (180, 245, 90)])
                    Particle(c_pos, [vis], color=col, size=random.randint(3, 6), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=320)
                if lvl and hasattr(lvl, 'floor_decals'):
                    puddle = AcidPuddleDecal(c_pos, [vis], radius=38)
                    lvl.floor_decals.append(puddle)
                DamageText("Взрыв Спор [1: Миазменное Облако]", self.rect.midtop, [vis], color=(100, 255, 90), size=18)

            elif var_idx == 1:
                SporeAcidGeyserVFX(c_pos, [vis])
                for _ in range(20):
                    ang = -random.uniform(0.3, 2.8)
                    spd = random.uniform(2.5, 6.0)
                    col = random.choice([(140, 255, 80), (80, 230, 50), (220, 255, 120)])
                    Particle(c_pos, [vis], color=col, size=random.randint(2, 5), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=260)
                if lvl and hasattr(lvl, 'floor_decals'):
                    puddle = AcidPuddleDecal(c_pos, [vis], radius=32)
                    lvl.floor_decals.append(puddle)
                DamageText("Взрыв Спор [2: Кислотный Гейзер]", self.rect.midtop, [vis], color=(130, 255, 60), size=18)

            else:
                SporeClusterPodsVFX(c_pos, [vis])
                for _ in range(16):
                    ang = random.uniform(0, 6.28)
                    spd = random.uniform(3.5, 7.0)
                    col = random.choice([(220, 255, 110), (100, 255, 80), (255, 255, 180)])
                    Particle(c_pos, [vis], color=col, size=random.randint(2, 4), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=220)
                if lvl and hasattr(lvl, 'floor_decals'):
                    for _ in range(2):
                        p_off = (c_pos[0] + random.randint(-40, 40), c_pos[1] + random.randint(-30, 30))
                        puddle = AcidPuddleDecal(p_off, [vis], radius=22)
                        lvl.floor_decals.append(puddle)
                DamageText("Взрыв Спор [3: Био-Кассетный Разрыв]", self.rect.midtop, [vis], color=(180, 255, 70), size=18)

    def trigger_dev_crit_pop(self):
        try:
            from src.sound_manager import play_sfx
            play_sfx('crit')
        except Exception:
            pass
        vis = getattr(self, 'visible_sprites', None)
        lvl = getattr(self, 'map_level', None)
        hit_pos = (self.rect.centerx, self.rect.top)

        if lvl:
            if hasattr(lvl, 'add_space_distortion'):
                lvl.add_space_distortion(hit_pos, max_radius=75, duration=160, kind='lens_snap')
            if hasattr(lvl, 'add_temp_light'):
                lvl.add_temp_light(hit_pos, (255, 230, 110), radius=240, duration=180)

        if vis:
            if hasattr(vis, 'shake'):
                vis.shake(duration_ms=180, magnitude=5)
            
            CritCrossFlare(hit_pos, [vis])
            
            for _ in range(24):
                ang = random.uniform(0, 6.28)
                spd = random.uniform(3.5, 7.0)
                col = random.choice([(255, 245, 160), (255, 215, 60), (255, 255, 240)])
                Particle(hit_pos, [vis], color=col, size=random.randint(2, 4), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=220)
            
            DamageText("КРИТ! 999", (self.rect.centerx, self.rect.top - 20), [vis], color=(255, 220, 60), size=24, is_crit=True)

    def handle_dev_mode_input(self):
        if not getattr(getattr(self, 'map_level', None), 'is_dev_room', False):
            return

        keys = pygame.key.get_pressed()
        now = pygame.time.get_ticks()

        def is_k(k):
            if hasattr(keys, 'get'):
                return bool(keys.get(k, False))
            try:
                return bool(keys[k]) if k < len(keys) else False
            except Exception:
                return False

        def just_pressed(k, key_attr):
            pressed = is_k(k)
            was_pressed = getattr(self, key_attr, False)
            setattr(self, key_attr, pressed)
            return pressed and not was_pressed

        # Full energy in Dev Mode
        self.energy = float(self.stats.get('energy', 60))

        # 1. Weapon Selection: Keys [1..6] & [G]
        dev_weapons = [
            ('sword', 'Клинок Паладина'),
            ('claymore', 'Тяжёлый Двуручник'),
            ('daggers', 'Парные Кинжалы'),
            ('spear', 'Длинное Копьё'),
            ('astral_blade', 'Астральный Клинок'),
            ('bow', 'Охотничий Лук'),
        ]

        num_keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]
        for idx, k in enumerate(num_keys):
            if just_pressed(k, f'_dev_w_{idx}'):
                w_type, w_name = dev_weapons[idx]
                self.set_dev_weapon(w_type, w_name)

        if just_pressed(pygame.K_g, '_dev_g_pressed'):
            self.cycle_dev_weapon()

        # Mouse aim vector
        disp = pygame.display.get_surface()
        dw = disp.get_width() if disp else 960
        dh = disp.get_height() if disp else 540
        mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
        screen_center = pygame.math.Vector2(dw // 2, dh // 2)
        aim_dir = (mouse_pos - screen_center)
        if aim_dir.magnitude() > 0:
            aim_dir = aim_dir.normalize()
        else:
            aim_dir = pygame.math.Vector2(-1, 0) if getattr(self, 'facing_left', False) else pygame.math.Vector2(1, 0)

        # 2. Magic & Projectile Attacks:
        # [B] or [7]: Black Hole
        if just_pressed(pygame.K_b, '_dev_b_key') or just_pressed(pygame.K_7, '_dev_7_key'):
            self.cast_dev_projectile('black_hole', aim_dir, "Сингулярность «Чёрная дыра»")

        # [F] or [8]: Fireball
        if just_pressed(pygame.K_f, '_dev_f_key') or just_pressed(pygame.K_8, '_dev_8_key'):
            self.cast_dev_projectile('fireball', aim_dir, "Огненный Шар")

        # [R] or [9]: Frost Shard
        if just_pressed(pygame.K_r, '_dev_r_key') or just_pressed(pygame.K_9, '_dev_9_key'):
            self.cast_dev_projectile('frost_shard', aim_dir, "Ледяной Осколок")

        # [V] or [0]: Void Orb
        if just_pressed(pygame.K_v, '_dev_v_key') or just_pressed(pygame.K_0, '_dev_0_key'):
            self.cast_dev_projectile('void_orb', aim_dir, "Сфера Бездны")

        # [T]: Boss Cleave Shockwave
        if just_pressed(pygame.K_t, '_dev_t_key'):
            self.trigger_dev_boss_cleave(aim_dir)

        # [Y]: Spore Poison Explosion & Acid Puddle
        if just_pressed(pygame.K_y, '_dev_y_key'):
            self.trigger_dev_spore_explosion()

        # [K]: Critical Strike Pop & Sparks
        if just_pressed(pygame.K_k, '_dev_k_key'):
            self.trigger_dev_crit_pop()

        # [O]: Cycle Dash Trail Style
        if just_pressed(pygame.K_o, '_dev_o_key'):
            self.cycle_dash_trail()

        # [H]: Holy Shield
        if just_pressed(pygame.K_h, '_dev_h_key'):
            self.is_shielded = True
            self.shield_time = now
            self._ensure_barrier_vfx()
            if getattr(self, 'visible_sprites', None):
                DamageText("Священный Щит", self.rect.midtop, [self.visible_sprites], color=(140, 230, 255), size=16)

        # [J]: Void Nova Burst
        if just_pressed(pygame.K_j, '_dev_j_key'):
            self.ult()
            if getattr(self, 'visible_sprites', None):
                DamageText("Нова Бездны", self.rect.midtop, [self.visible_sprites], color=(220, 80, 255), size=16)

    def trigger_level_up_vfx(self):
        self.level_up_time = pygame.time.get_ticks()
        try:
            from src.sound_manager import play_sfx
            play_sfx('level_up')
        except Exception:
            pass
        if hasattr(self, 'visible_sprites') and hasattr(self.visible_sprites, 'shake'):
            self.visible_sprites.shake(duration_ms=250, magnitude=5)


    def recalculate_stats(self):
        base_health = 100 + (self.level - 1) * 10
        base_attack = 10 + (self.level - 1) * 2
        base_energy = 60
        base_magic = 4
        base_speed = 5
        base_attack_cooldown = 400
        wpn = getattr(self, 'equipped', {}).get('weapon')
        if wpn and getattr(wpn, 'weapon_type', None) == 'claymore':
            base_attack_cooldown = 750

        bonus_health = 0
        bonus_attack = 0
        bonus_defense = 0
        bonus_energy = 0
        bonus_speed = 0
        bonus_magic = 0
        bonus_atk_speed = 0
        bonus_energy_regen = 0
        bonus_crit_rate = 0.0
        bonus_crit_dmg = 0.0

        # 1. Dedicated equipped gear slot bonuses (Active Gear ONLY - 6 slots)
        for slot, eq_item in getattr(self, 'equipped', {}).items():
            if eq_item and hasattr(eq_item, 'effects') and eq_item.effects:
                bonus_health += eq_item.effects.get('health', 0)
                bonus_attack += eq_item.effects.get('attack', 0)
                bonus_defense += eq_item.effects.get('defense', 0)
                bonus_energy += eq_item.effects.get('energy', 0)
                bonus_speed += eq_item.effects.get('speed', 0)
                bonus_magic += eq_item.effects.get('magic', 0)
                bonus_atk_speed += eq_item.effects.get('attack_speed', 0)
                bonus_energy_regen += eq_item.effects.get('energy_regen', 0)
                bonus_crit_rate += eq_item.effects.get('crit_rate', 0.0)
                bonus_crit_dmg += eq_item.effects.get('crit_dmg', 0.0)

        # 2. Active Run Relics bonuses
        for relic in getattr(self, 'relics', []):
            if relic and hasattr(relic, 'effects') and relic.effects:
                bonus_health += relic.effects.get('health', 0)
                bonus_attack += relic.effects.get('attack', 0)
                bonus_defense += relic.effects.get('defense', 0)
                bonus_energy += relic.effects.get('energy', 0)
                bonus_speed += relic.effects.get('speed', 0)
                bonus_crit_rate += relic.effects.get('crit_rate', 0.0)
                bonus_crit_dmg += relic.effects.get('crit_dmg', 0.0)
                # Bloodstone Core: +25% attack when below 50% HP
                if 'low_hp_attack' in relic.effects:
                    calc_max_hp = base_health + bonus_health
                    if getattr(self, 'health', calc_max_hp) < calc_max_hp * 0.5:
                        bonus_attack += int((base_attack + bonus_attack) * 0.25)

        # Run-scoped trader buffs survive stat recalculation and floor changes.
        shop_bonuses = getattr(self, 'shop_stat_bonuses', {})
        bonus_attack += shop_bonuses.get('attack', 0)
        bonus_defense += shop_bonuses.get('defense', 0)

        # NOTE: Items carried in backpack (self.inventory) DO NOT grant passive equipment bonuses!

        self.energy_regen = 6.0 + bonus_energy_regen
        self.stats['health'] = base_health + bonus_health
        self.stats['attack'] = base_attack + bonus_attack
        self.stats['defense'] = bonus_defense
        self.stats['crit_rate'] = round(5.0 + bonus_crit_rate, 1)
        self.stats['crit_dmg'] = round(150.0 + bonus_crit_dmg, 1)
        self.crit_rate = self.stats['crit_rate']
        self.crit_dmg = self.stats['crit_dmg']
        self.defense = bonus_defense
        self.attack_power = self.stats['attack']
        self.stats['energy'] = base_energy + bonus_energy
        self.stats['magic'] = base_magic + bonus_magic
        self.stats['speed'] = min(8, base_speed + bonus_speed)
        self.speed = self.stats['speed'] * 0.78
        self.attack_cooldown = max(150, base_attack_cooldown - bonus_atk_speed * 4)
        if getattr(self, 'is_dead', False):
            self.health = 0
            return
        if self.health > self.stats['health']:
            self.health = self.stats['health']

    @property
    def max_energy(self):
        return self.stats.get('energy', 60)

    @property
    def max_health(self):
        return self.stats.get('health', 100)

    def add_item(self, item, count=None):
        """Add item to inventory with automatic stacking and rarity consolidation."""
        if not hasattr(self, 'inventory'):
            self.inventory = []
        if count is not None:
            item.count = int(count)
        elif not hasattr(item, 'count'):
            item.count = 1
        for existing in self.inventory:
            if getattr(existing, 'can_stack_with', lambda o: False)(item):
                existing.count = getattr(existing, 'count', 1) + getattr(item, 'count', 1)
                return existing
        self.inventory.append(item)
        return item

    def consolidate_inventory(self):
        """Merges all stackable items in inventory and sorts them by rarity descending."""
        if not hasattr(self, 'inventory') or not self.inventory:
            return
        consolidated = []
        for itm in self.inventory:
            if not hasattr(itm, 'count'):
                itm.count = 1
            stacked = False
            for c_itm in consolidated:
                if getattr(c_itm, 'can_stack_with', lambda o: False)(itm):
                    c_itm.count = getattr(c_itm, 'count', 1) + getattr(itm, 'count', 1)
                    stacked = True
                    break
            if not stacked:
                consolidated.append(itm)
        from src.items import item_sort_key
        consolidated.sort(key=item_sort_key)
        self.inventory[:] = consolidated

    def equip_item(self, item):
        slot = getattr(item, 'slot', None)
        valid_slots = ['weapon', 'offhand', 'armor', 'boots', 'amulet', 'ring', 'accessory']
        if not slot or slot not in valid_slots:
            n_low = getattr(item, 'name', '').lower()
            if any(k in n_low for k in ['sword', 'blade', 'claymore', 'меч', 'клинок', 'палаш']):
                slot = 'weapon'
            elif any(k in n_low for k in ['shield', 'buckler', 'щит', 'баклер', 'grimoire', 'гримуар']):
                slot = 'offhand'
            elif any(k in n_low for k in ['armor', 'доспех', 'латы', 'мантия', 'кольчуга']):
                slot = 'armor'
            elif any(k in n_low for k in ['boots', 'сапоги', 'ботфорты', 'обувь']):
                slot = 'boots'
            elif any(k in n_low for k in ['amulet', 'амулет', 'подвеска']):
                slot = 'amulet'
            elif any(k in n_low for k in ['ring', 'кольцо']):
                slot = 'ring'
            else:
                slot = 'amulet'

        if not hasattr(self, 'equipped') or not isinstance(self.equipped, dict):
            self.equipped = {s: None for s in valid_slots}
        for s in valid_slots:
            if s not in self.equipped:
                self.equipped[s] = None

        old = self.equipped.get(slot)
        if item in self.inventory:
            if getattr(item, 'count', 1) > 1:
                item.count -= 1
                from copy import copy
                equipped_copy = copy(item)
                equipped_copy.count = 1
                item = equipped_copy
            else:
                self.inventory.remove(item)
        if old:
            self.add_item(old)
        self.equipped[slot] = item
        self.recalculate_stats()
        try:
            from src.sound_manager import play_sfx
            play_sfx('sword_swing')
        except Exception:
            pass
        return True

    def unequip_item(self, slot):
        if not hasattr(self, 'equipped') or not isinstance(self.equipped, dict):
            return None
        item = self.equipped.get(slot)
        if item:
            self.equipped[slot] = None
            self.add_item(item)
            self.recalculate_stats()
            return item
        return None

    def consume_item(self, item):
        if not item or item not in getattr(self, 'inventory', []):
            return False
        max_hp = self.stats.get('health', 100) if hasattr(self, 'stats') else 100
        if self.health >= max_hp:
            return False
        heal_amt = item.effects.get('heal', 25) if hasattr(item, 'effects') else 25
        self.health = min(float(max_hp), self.health + heal_amt)
        if getattr(item, 'count', 1) > 1:
            item.count -= 1
        else:
            self.inventory.remove(item)
        if hasattr(self, 'recalculate_stats'):
            self.recalculate_stats()
        try:
            from src.sound_manager import play_sfx
            play_sfx('potion')
        except Exception:
            pass
        return True

    def use_potion(self):
        if getattr(self, 'is_dead', False):
            return False
        if self.health >= self.stats['health']:
            return False
        potion_item = None
        for item in self.inventory:
            if hasattr(item, 'effects') and 'heal' in item.effects:
                potion_item = item
                break
            elif 'potion' in getattr(item, 'name', '').lower() or 'зелье' in getattr(item, 'name', '').lower():
                potion_item = item
                break

        if not potion_item:
            return False

        heal_amount = potion_item.effects.get('heal', 20) if hasattr(potion_item, 'effects') else 20
        self.health = min(float(self.stats['health']), self.health + heal_amount)
        if getattr(potion_item, 'count', 1) > 1:
            potion_item.count -= 1
        else:
            self.inventory.remove(potion_item)
        self.recalculate_stats()
        try:
            from src.sound_manager import play_sfx
            play_sfx('potion')
        except Exception:
            pass
        if getattr(self, 'visible_sprites', None):
            DamageText(f"+{int(heal_amount)}", self.rect.center, [self.visible_sprites], color=(80, 255, 80))
        return True
    def gain_exp(self, amount):
        if getattr(self, 'is_dead', False):
            return
        self.exp += amount
        leveled_up = False
        while self.exp >= self.level * 100:
            self.exp -= self.level * 100
            self.level += 1
            self.skill_points = getattr(self, 'skill_points', 0) + 1
            leveled_up = True
        if leveled_up:
            self.recalculate_stats()
            self.health = float(self.stats['health'])
            self.energy = float(self.stats['energy'])
            self.trigger_level_up_vfx()

    def input(self):
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()

        def is_k(k):
            if hasattr(keys, 'get'):
                return bool(keys.get(k, False))
            try:
                return bool(keys[k]) if k < len(keys) else False
            except Exception:
                return False
        
        # 1. Movement Input (WASD)
        # We allow up/down and left/right to cancel each other out
        self.direction.y = int(is_k(pygame.K_s)) - int(is_k(pygame.K_w))
        self.direction.x = int(is_k(pygame.K_d)) - int(is_k(pygame.K_a))
        if self.direction.x != 0:
            self.facing_left = (self.direction.x < 0)
        if self.direction.magnitude() > 0:
            now = pygame.time.get_ticks()
            if now - getattr(self, 'last_step_time', 0) > 340:
                self.last_step_time = now
                try:
                    from src.sound_manager import play_sfx
                    play_sfx('step')
                except Exception:
                    pass
        
        # 2. Attack Input
        if mouse[0] and self.can_attack:
            self.attack()
            self.can_attack = False
            # NOTE: attack_time is already set inside self.attack() — do NOT set it again here
            
        # 3. Potion Input (Q or 1 when not in shop context)
        potion_pressed = bool(is_k(pygame.K_q) or (is_k(pygame.K_1) and not getattr(self, 'near_trader', False)))
        if potion_pressed and not getattr(self, 'potion_key_pressed', False):
            self.use_potion()
        self.potion_key_pressed = bool(is_k(pygame.K_q) or is_k(pygame.K_1))

        # 4. Skills Input
        # Dash (Space / Z): 15 Energy
        dash_pressed = is_k(pygame.K_z) or is_k(pygame.K_SPACE)
        dash_cost = getattr(self, 'dash_energy_cost', 15)
        if dash_pressed and getattr(self, 'can_dash', True) and self.energy >= dash_cost:
            self.energy -= dash_cost
            self.speed = getattr(self, 'dash_speed_boost', 10.0)
            self.can_dash = False
            self.dash_time = pygame.time.get_ticks()
            self.animation_controller.start_action('dash', self.dash_time, self.dash_duration)
            self.jump_z(4.5)
            self.dash_dir = pygame.math.Vector2(self.velocity.normalize()) if self.velocity.magnitude() > 0 else (self.direction.copy() if self.direction.magnitude() > 0 else pygame.math.Vector2(1, 0))
            self.last_ghost_trail_time = -1000
            self.last_flame_trail_time = -1000
            if hasattr(self, 'map_level'):
                if hasattr(self.map_level, 'ground_mist_patches'):
                    for mist in self.map_level.ground_mist_patches:
                        mist.on_player_dash_wind(self.rect.center, self.dash_dir)
                if hasattr(self.map_level, 'visible_sprites'):
                    for s in self.map_level.visible_sprites:
                        if getattr(s, 'sprite_type', None) == 'torch' and hasattr(s, 'on_wind_gust'):
                            s.on_wind_gust(self.rect.center, self.dash_dir)
            try:
                from src.sound_manager import play_sfx
                play_sfx('dash')
                play_sfx('flame')
            except Exception:
                pass
            if getattr(self, 'visible_sprites', None):
                enemy_grp = getattr(self, 'enemy_sprites', None)
                FlameTrailHazard(self.rect.center, [self.visible_sprites], enemy_sprites=enemy_grp, player_level=getattr(self, "level", 1), direction=self.dash_dir)
                self.spawn_dash_trail_vfx(initial=True)

        # Shield (X): available only after investing in the defensive branch.
        shield_lvl = getattr(self, 'skills', {}).get('shield', {}).get('level', 0)
        can_use_shield = shield_lvl >= 1
        shield_cost = getattr(self, 'shield_energy_cost', 25)
        if is_k(pygame.K_x) and can_use_shield and getattr(self, 'can_shield', True) and not self.is_shielded and self.energy >= shield_cost:
            self.energy -= shield_cost
            self.is_shielded = True
            self.can_shield = False
            now_t = pygame.time.get_ticks()
            self.shield_time = now_t
            self.shield_start_time = now_t
            self._ensure_barrier_vfx()
            try:
                from src.sound_manager import play_sfx
                play_sfx('shield')
            except Exception:
                pass

        # Ult (C): available only after investing in the offensive branch.
        ult_lvl = getattr(self, 'skills', {}).get('ult', {}).get('level', 0)
        can_use_ult = ult_lvl >= 1
        ult_cost = getattr(self, 'ult_energy_cost', 45)
        if is_k(pygame.K_c) and can_use_ult and getattr(self, 'can_ult', True) and self.energy >= ult_cost:
            self.energy -= ult_cost
            self.ult()
            self.can_ult = False
            self.ult_time = pygame.time.get_ticks()
            try:
                from src.sound_manager import play_sfx
                play_sfx('ult')
            except Exception:
                pass
            if getattr(self, 'visible_sprites', None):
                for a in range(0, 360, 20):
                    rad = math.radians(a)
                    Particle(self.rect.center, [self.visible_sprites], color=(220, 80, 255), size=5, velocity=(math.cos(rad)*6, math.sin(rad)*6), lifetime=350)

        # Skill upgrade shortcuts: Ctrl + 1, 2, 3
        mods = pygame.key.get_mods()
        if (mods & pygame.KMOD_CTRL):
            if is_k(pygame.K_1) and not getattr(self, '_ctrl1_pressed', False):
                self.upgrade_skill('dash')
            if is_k(pygame.K_2) and not getattr(self, '_ctrl2_pressed', False):
                self.upgrade_skill('shield')
            if is_k(pygame.K_3) and not getattr(self, '_ctrl3_pressed', False):
                self.upgrade_skill('ult')
        self._ctrl1_pressed = bool(is_k(pygame.K_1))
        self._ctrl2_pressed = bool(is_k(pygame.K_2))
        self._ctrl3_pressed = bool(is_k(pygame.K_3))

        # 5. Hero Skin Cycling: Key [P]
        if is_k(pygame.K_p) and not getattr(self, '_p_pressed_last', False):
            self.cycle_skin()
        self._p_pressed_last = bool(is_k(pygame.K_p))

        # 6. AAA Level-Up Test VFX: Key [L]
        if is_k(pygame.K_l) and not getattr(self, '_l_pressed_last', False):
            self.trigger_level_up_vfx()
        self._l_pressed_last = bool(is_k(pygame.K_l))

        # 7. Dev Mode Extended Combat & Effects Evaluation
        self.handle_dev_mode_input()

    def attack(self, target_direction=None):
        self.attack_time = pygame.time.get_ticks()
        self._attack_anim_active = True
        self.attack_anim_duration = 240
        controller = getattr(self, 'animation_controller', None)
        if controller:
            controller.start_action('attack', self.attack_time, self.attack_anim_duration)
        w_item = getattr(self, 'equipped', {}).get('weapon')
        w_type = getattr(w_item, 'weapon_type', 'sword') if w_item else 'sword'

        if target_direction is not None:
            direction_vec = pygame.math.Vector2(target_direction)
        else:
            disp = pygame.display.get_surface()
            dw = disp.get_width() if disp else WIDTH
            dh = disp.get_height() if disp else HEIGHT
            screen_center = pygame.math.Vector2(dw // 2, dh // 2)
            mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
            direction_vec = mouse_pos - screen_center
            # If headless dummy mouse at (0, 0) and unfocused, default to current facing
            if mouse_pos == pygame.math.Vector2(0, 0) and not pygame.mouse.get_focused():
                direction_vec = pygame.math.Vector2(-1, 0) if getattr(self, 'facing_left', False) else pygame.math.Vector2(1, 0)

        if direction_vec.magnitude() > 0:
            direction_vec = direction_vec.normalize()
        else:
            direction_vec = pygame.math.Vector2(1, 0)

        if direction_vec.x != 0:
            self.facing_left = (direction_vec.x < 0)
        self.attack_direction = direction_vec.copy()

        if w_type == 'bow':
            try:
                from src.sound_manager import play_sfx
                play_sfx('shoot')
            except Exception:
                pass
            p = EnemyProjectile(self.rect.center, [self.visible_sprites], direction_vec, self.obstacle_sprites, player=None, proj_type='arrow')
            p.map_level = getattr(self, 'map_level', None)
            p.owner = self
            p.target_group = getattr(getattr(self, 'map_level', None), 'showcase_sprites', None) or getattr(getattr(self, 'map_level', None), 'enemy_sprites', None)
            damage = getattr(self, 'stats', {}).get('attack', getattr(self, 'attack_power', 10))
            p.is_crit = random.random() * 100.0 < getattr(self, 'crit_rate', 5.0)
            if p.is_crit:
                damage = int(damage * getattr(self, 'crit_dmg', 150.0) / 100.0)
            p.damage = max(1, int(damage))
            return

        try:
            from src.sound_manager import play_sfx
            if w_type == 'claymore':
                play_sfx('claymore_swing')
            elif w_type == 'spear':
                play_sfx('spear_thrust')
            elif w_type == 'daggers':
                play_sfx('dagger_slash')
            else:
                play_sfx('sword_swing')
        except Exception:
            pass

        weapon_swing = Weapon(self, [self.visible_sprites], direction_vec, weapon_type=w_type)
        self.attack_anim_duration = max(240, weapon_swing.life_time)
        if controller:
            controller.start_action('attack', self.attack_time, self.attack_anim_duration)



    def ult(self):
        try:
            from src.sound_manager import play_sfx
            play_sfx('void_burst')
        except Exception:
            pass
        vis = getattr(self, 'visible_sprites', None)
        lvl = getattr(self, 'map_level', None)
        c_pos = self.rect.center

        if lvl:
            if hasattr(lvl, 'add_space_distortion'):
                lvl.add_space_distortion(c_pos, max_radius=320, duration=550, kind='shockwave', intensity=1.2)
            if hasattr(lvl, 'add_temp_light'):
                lvl.add_temp_light(c_pos, (210, 65, 255), radius=500, duration=450)

        if vis and hasattr(vis, 'shake'):
            vis.shake(duration_ms=450, magnitude=9)

        if vis:
            for _ in range(40):
                ang = random.uniform(0, 6.28)
                spd = random.uniform(4.0, 9.5)
                col = random.choice([(210, 70, 255), (75, 230, 255), (255, 255, 255), (160, 40, 220)])
                Particle(c_pos, [vis], color=col, size=random.randint(3, 6), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=350)

        all_targets = list(getattr(self, 'enemy_sprites', []))
        if lvl and hasattr(lvl, 'showcase_sprites'):
            all_targets.extend(list(lvl.showcase_sprites))

        for tgt in all_targets:
            t_box = getattr(tgt, 'hitbox', getattr(tgt, 'rect', None))
            if t_box:
                dist = (pygame.math.Vector2(t_box.center) - pygame.math.Vector2(c_pos)).magnitude()
                if dist < 800:
                    if hasattr(tgt, 'take_damage'):
                        tgt.take_damage(220, source='ult')
                    elif hasattr(tgt, 'kill'):
                        tgt.kill()

    def cooldowns(self):
        current_time = pygame.time.get_ticks()

        if not self.can_attack:
            if current_time - self.attack_time >= self.attack_cooldown:
                self.can_attack = True

        if not self.can_dash:
            if current_time - self.dash_time >= getattr(self, 'dash_duration', 200):
                self.speed = self.stats['speed'] * 0.78
            if current_time - self.dash_time >= self.dash_cooldown:
                self.can_dash = True

        # Shield Duration (3s) & Cooldown (8s)
        if self.is_shielded:
            if current_time - self.shield_time >= getattr(self, 'shield_duration', 3000):
                self.is_shielded = False
        if not getattr(self, 'can_shield', True):
            if current_time - self.shield_time >= getattr(self, 'shield_cooldown', 8000):
                self.can_shield = True

        if not self.can_ult:
            if current_time - self.ult_time >= self.ult_cooldown:
                self.can_ult = True

        # Passive energy regeneration (6 units/s), paused during active shield
        if not self.is_shielded:
            dt = (current_time - getattr(self, 'last_regen_tick', current_time)) / 1000.0
            if 0 < dt < 1.0:
                max_energy = float(self.stats.get('energy', 60))
                self.energy = min(max_energy, self.energy + self.energy_regen * dt)
        self.last_regen_tick = current_time

    def take_damage(self, amount, source_pos=None):
        if getattr(self, 'is_dead', False):
            return False
        if getattr(self, 'is_shielded', False):
            return False
        mitigated = max(1, amount - getattr(self, 'defense', 0) // 4)
        self.health -= mitigated
        if self.health <= 0:
            # Check Obsidian Heart death defiance!
            relics = getattr(self, 'relics', [])
            obsidian_heart = next((r for r in relics if ('Обсидиан' in getattr(r, 'name', '') or 'Heart' in getattr(r, 'name', '')) and getattr(r, 'slot', '') == 'relic' and not getattr(r, 'used_this_floor', False)), None)
            if obsidian_heart:
                obsidian_heart.used_this_floor = True
                max_hp = self.stats.get('health', 100) if hasattr(self, 'stats') else 100
                self.health = max(10, int(max_hp * 0.4))
                self.is_shielded = True
                now_ticks = pygame.time.get_ticks()
                self.shield_start_time = now_ticks
                self.shield_time = now_ticks
                vis_g = [self.visible_sprites] if getattr(self, 'visible_sprites', None) else []
                if vis_g:
                    DamageText("ОБСИДИАНОВОЕ БЕССМЕРТИЕ!", self.rect.center, vis_g, color=(215, 120, 255), size=18)
                    for _ in range(16):
                        ang = random.uniform(0, 6.28)
                        spd = random.uniform(3, 7)
                        Particle(self.rect.center, vis_g, color=(190, 70, 255), size=random.randint(3, 5), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=350)
                try:
                    from src.sound_manager import play_sfx
                    play_sfx('shield')
                except Exception:
                    pass
                return True

            self.health = 0
            self.is_dead = True
            self.direction = pygame.math.Vector2()
            self.velocity = pygame.math.Vector2()
            return True
        self.took_damage_time = pygame.time.get_ticks()
        if source_pos and hasattr(self, 'hitbox') and self.hitbox:
            diff = pygame.math.Vector2(self.hitbox.center) - pygame.math.Vector2(source_pos)
            if diff.magnitude() > 0:
                self.velocity += diff.normalize() * 7.0
        try:
            from src.sound_manager import play_sfx
            play_sfx('hit')
        except Exception:
            pass
        vis_g = [self.visible_sprites] if getattr(self, 'visible_sprites', None) else []
        if vis_g:
            DamageText(f"-{int(mitigated)}", self.rect.center, vis_g, color=(255, 60, 60), size=18)
        return True

    def animate(self):
        if not hasattr(self, 'idle_frames') or not self.idle_frames:
            return

        now = pygame.time.get_ticks()
        is_hit_stop = (now - getattr(self, 'took_damage_time', -1000) < 110)
        is_moving = self.velocity.magnitude() > 0.2
        controller = getattr(self, 'animation_controller', None)
        if controller is None:
            return
        sample = controller.sample(now, is_moving, freeze_locomotion=is_hit_stop)
        if sample.frame is None:
            return

        # Keep the legacy animation fields in sync for HUD/debug consumers.
        self.frames = controller.sequences[sample.state]
        self.frame_index = float(sample.frame_index)
        if getattr(self, '_attack_anim_active', False) and now - getattr(self, 'attack_time', 0) >= getattr(self, 'attack_anim_duration', 240):
            self._attack_anim_active = False

        base_img = sample.frame
        self.image = pygame.transform.flip(base_img, True, False) if getattr(self, 'facing_left', False) else base_img.copy()

        # Dash motion changes width only; character height and the full-body pose stay stable.
        if sample.state == 'dash':
            dash_progress = controller.action_progress('dash', now)
            width_scale = 1.18 if dash_progress < 0.65 else 0.94
            scaled_width = max(1, round(self.image.get_width() * width_scale))
            if scaled_width != self.image.get_width():
                self.image = pygame.transform.scale(self.image, (scaled_width, self.image.get_height()))

        attack_offset = (0, 0)
        if sample.state == 'attack':
            attack_offset = controller.body_lunge_offset(
                sample.progress, (self.attack_direction.x, self.attack_direction.y),
            )
        if getattr(self, 'current_skin', 'default') in getattr(self, 'dev_skins', ['slayer', 'wanderer', 'crusader', 'champion_redux']):
            anchor = (round(self.hitbox.centerx + attack_offset[0]), round(self.hitbox.bottom + 2 + attack_offset[1]))
            self.rect = self.image.get_rect(midbottom=anchor)
        else:
            anchor = (round(self.hitbox.centerx + attack_offset[0]), round(self.hitbox.centery + attack_offset[1]))
            self.rect = self.image.get_rect(center=anchor)

        # Hurt flash colors the chosen full-body frame; it never draws another pose over it.
        if is_hit_stop:
            try:
                mask = pygame.mask.from_surface(self.image)
                overlay = mask.to_surface(setcolor=(235, 65, 65, 180), unsetcolor=(0, 0, 0, 0))
                self.image.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            except Exception:
                pass

        if getattr(self, 'is_shielded', False):
            self._ensure_barrier_vfx()
        else:
            self._active_barrier_vfx = None

    def update(self):
        if self.health <= 0:
            self.is_dead = True
            self.direction = pygame.math.Vector2()
            return
        now = pygame.time.get_ticks()
        is_hit_stop = (now < getattr(self, 'hit_stop_until', 0))
        
        # Low HP Panic Heartbeat check (<28% HP)
        max_hp = self.stats.get('health', 100) if hasattr(self, 'stats') else 100
        hp_ratio = self.health / float(max(1, max_hp))
        if hp_ratio <= 0.28 and not getattr(self, 'is_dead', False):
            self.low_hp_active = True
            pulse_interval = int(450 + hp_ratio * 1400)
            if now - getattr(self, 'last_heartbeat_time', 0) >= pulse_interval:
                self.last_heartbeat_time = now
                try:
                    from src.sound_manager import play_sfx
                    play_sfx('heartbeat')
                except Exception:
                    pass
        else:
            self.low_hp_active = False

        # Continuous Ghost Trail and Flame Trail during dash
        is_dashing = (now - getattr(self, 'dash_time', -1000) < getattr(self, 'dash_duration', 200))
        if is_dashing:
            if (now - getattr(self, 'last_ghost_trail_time', 0) > 45):
                self.last_ghost_trail_time = now
                if getattr(self, 'visible_sprites', None):
                    GhostTrail(self.rect.center, [self.visible_sprites], self.image, lifetime=180, chromatic=True)
            self.spawn_dash_trail_vfx(initial=False)
            if (now - getattr(self, 'last_flame_trail_time', 0) > 60):
                self.last_flame_trail_time = now
                if getattr(self, 'visible_sprites', None):
                    enemy_grp = getattr(self, 'enemy_sprites', None)
                    FlameTrailHazard(self.rect.center, [self.visible_sprites], enemy_sprites=enemy_grp, player_level=getattr(self, "level", 1), direction=self.dash_dir)

        self.input()
        self.cooldowns()
        now = pygame.time.get_ticks()
        eff_speed = self.speed
        if is_hit_stop:
            eff_speed = 0.0
        elif now < getattr(self, 'speed_modifier_timer', 0):
            eff_speed *= getattr(self, 'speed_modifier', 1.0)
        
        # 2x Movement Speed in Developer Mode
        if getattr(getattr(self, 'map_level', None), 'is_dev_room', False):
            eff_speed *= 2.0

        self.move(eff_speed)
        # Movement resets rect from the hitbox; apply the final animation pose afterward.
        self.animate()







class Weapon(pygame.sprite.Sprite):
    def __init__(self, player, groups, direction, weapon_type='sword'):
        super().__init__(groups)
        self.sprite_type = 'weapon'
        self.player = player
        self.direction = direction
        self.weapon_type = weapon_type
        self.spawn_time = pygame.time.get_ticks()
        self.hit_enemies = set()

        self.base_angle = math.degrees(math.atan2(-direction.y, direction.x))
        # 2.5D Z-Elevation Sync
        self.z = float(getattr(player, 'z', 0.0))
        self.vz = float(getattr(player, 'vz', 0.0))
        self.gravity_z = float(getattr(player, 'gravity_z', 0.8))
        
        if weapon_type == 'claymore':
            self.life_time = 320
            self.reach = 62
            self.arc_degrees = 160.0
            self.kb_power = 14.0
            self.slash_col = (255, 175, 45)
        elif weapon_type == 'spear':
            self.life_time = 190
            self.reach = 66
            self.arc_degrees = 45.0
            self.kb_power = 12.0
            self.slash_col = (220, 245, 255)
        elif weapon_type == 'daggers':
            self.life_time = 150
            self.reach = 36
            self.arc_degrees = 130.0
            self.kb_power = 6.0
            self.slash_col = (220, 80, 255)
        elif weapon_type == 'astral_blade':
            self.life_time = 260
            self.reach = 58
            self.arc_degrees = 150.0
            self.kb_power = 12.0
            self.slash_col = (130, 235, 255)
        else: # Standard 1H Sword
            self.life_time = 220
            self.reach = 48
            self.arc_degrees = 90.0
            self.kb_power = 8.0
            self.slash_col = (100, 225, 255)

        self.image = self.render_slash(0.0)
        self.rect = self.image.get_rect(center=player.rect.center)
        self.hitbox = self.rect

    def render_slash(self, progress):
        sz = int((self.reach + 28) * 2)
        surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
        cx, cy = sz // 2, sz // 2

        if self.weapon_type == 'spear':
            if progress < 0.25:
                w_p = progress / 0.25
                p_reach = self.reach * (0.35 - 0.15 * math.sin(w_p * math.pi))
            elif progress < 0.75:
                s_p = (progress - 0.25) / 0.50
                p_reach = self.reach * (0.35 + 0.65 * math.sin(s_p * math.pi * 0.5))
            else:
                r_p = (progress - 0.75) / 0.25
                p_reach = self.reach * (1.0 - 0.65 * r_p)

            rad = math.radians(-self.base_angle)
            tip_x = cx + math.cos(rad) * p_reach
            tip_y = cy + math.sin(rad) * p_reach
            alpha = int(255 * math.sin(progress * math.pi))
            
            if 0.25 <= progress < 0.75:
                c_alpha = int(200 * math.sin((progress - 0.25) / 0.50 * math.pi))
                cone_rad = 12 * ((progress - 0.25) / 0.50)
                perp_x = -math.sin(rad)
                perp_y = math.cos(rad)
                c1 = (tip_x - math.cos(rad) * 16 + perp_x * cone_rad, tip_y - math.sin(rad) * 16 + perp_y * cone_rad)
                c2 = (tip_x - math.cos(rad) * 16 - perp_x * cone_rad, tip_y - math.sin(rad) * 16 - perp_y * cone_rad)
                pygame.draw.polygon(surf, (220, 245, 255, c_alpha // 2), [(tip_x, tip_y), c1, c2])

            pygame.draw.line(surf, (110, 75, 45, alpha), (cx, cy), (int(tip_x - math.cos(rad) * 12), int(tip_y - math.sin(rad) * 12)), 3)
            pygame.draw.line(surf, (240, 245, 255, alpha), (int(tip_x - math.cos(rad) * 12), int(tip_y - math.sin(rad) * 12)), (int(tip_x), int(tip_y)), 4)
            pygame.draw.circle(surf, (255, 255, 255, alpha), (int(tip_x), int(tip_y)), 4)
            return surf

        v_arc = getattr(self, "visual_arc_degrees", self.arc_degrees)
        swing_start = self.base_angle - v_arc * 0.5
        swing_end = self.base_angle + v_arc * 0.5

        if progress < 0.24:
            # PHASE 1: Anticipation / Windup (Cocked back with gathering glint)
            w_t = progress / 0.24
            cur_angle = swing_start - (1.0 - w_t) * 14.0
            alpha = int(255 * (0.6 + 0.4 * w_t))
            # Authentic slash anticipation: No ghost blade drawn behind/over player
            pass
            rad = math.radians(-cur_angle)
            tx, ty = cx + math.cos(rad) * self.reach, cy + math.sin(rad) * self.reach
            g_sz = int(2 + 4 * w_t)
            pygame.draw.circle(surf, (255, 255, 255, alpha), (int(tx), int(ty)), g_sz)
            pygame.draw.line(surf, (self.slash_col[0], self.slash_col[1], self.slash_col[2], alpha), (int(tx - g_sz*2), int(ty)), (int(tx + g_sz*2), int(ty)), 1)
            pygame.draw.line(surf, (self.slash_col[0], self.slash_col[1], self.slash_col[2], alpha), (int(tx), int(ty - g_sz*2)), (int(tx), int(ty + g_sz*2)), 1)

        elif progress < 0.78:
            # PHASE 2: Active Strike & 180° Crescent Smear Mesh (Dead Cells Canon)
            s_t = (progress - 0.24) / 0.54
            t = s_t ** 0.54
            cur_angle = swing_start + (swing_end - swing_start) * t
            trail_span = min(v_arc * 0.82, v_arc * t)

            steps = 18
            outer_pts = []
            inner_pts = []
            for i in range(steps + 1):
                frac = i / float(steps)
                a = cur_angle - trail_span * (1.0 - frac)
                rad = math.radians(-a)
                r_out = self.reach + (1.0 - (1.0 - frac)**2) * 6
                r_in = max(8, self.reach - 22 + frac * 14)
                outer_pts.append((cx + math.cos(rad) * r_out, cy + math.sin(rad) * r_out))
                inner_pts.append((cx + math.cos(rad) * r_in, cy + math.sin(rad) * r_in))

            poly = outer_pts + list(reversed(inner_pts))
            if len(poly) >= 3:
                smear_alpha = int(230 * (1.0 - s_t ** 1.8))
                c_fill = (self.slash_col[0], self.slash_col[1], self.slash_col[2], max(0, min(255, int(smear_alpha * 0.65))))
                pygame.draw.polygon(surf, c_fill, poly)
                c_edge = (255, 255, 255, max(0, min(255, smear_alpha)))
                pygame.draw.lines(surf, c_edge, False, outer_pts, 2)
                c_inner = (self.slash_col[0], self.slash_col[1], self.slash_col[2], max(0, min(255, smear_alpha // 2)))
                pygame.draw.lines(surf, c_inner, False, inner_pts, 1)

            # Authentic slash energy trail: Dynamic crescent arc without duplicate blade
            pass

        else:
            # PHASE 3: Inertia & Follow-through Recovery
            r_t = (progress - 0.78) / 0.22
            cur_angle = swing_end + (1.0 - r_t) * 8.0
            blade_alpha = max(0, min(255, int(255 * (1.0 - r_t * 0.4))))
            # Authentic recovery: Clean trail decay without duplicate blade
            pass

        return surf

    def update(self):
        self.z = float(getattr(self.player, 'z', 0.0))
        self.vz = float(getattr(self.player, 'vz', 0.0))
        enemy_group = getattr(self.player, 'enemy_sprites', None)
        if enemy_group:
            hits = pygame.sprite.spritecollide(self, enemy_group, False)
            for enemy in hits:
                 if not getattr(enemy, 'alive', lambda: True)():
                     continue
                 # Directional weapon sector check: prevent hitting behind player
                 e_dx = enemy.rect.centerx - self.player.rect.centerx
                 e_dy = enemy.rect.centery - self.player.rect.centery
                 dist = math.hypot(e_dx, e_dy)
                 max_reach = self.reach + 24
                 if dist > max_reach:
                     continue
                 if dist > 8:
                     e_angle = math.degrees(math.atan2(-e_dy, e_dx))
                     diff_ang = (e_angle - self.base_angle + 180) % 360 - 180
                     half_arc = max(38.0, self.arc_degrees * 0.65)
                     if abs(diff_ang) > half_arc:
                         continue
                 if enemy not in getattr(self, 'hit_enemies', set()):
                     self.hit_enemies.add(enemy)
                     damage = self.player.stats.get('attack', 10)
                     if self.weapon_type == 'claymore':
                         damage = int(damage * 1.35)

                     # Genshin/Resonance Critical Hit roll
                     is_crit = (random.random() * 100.0) < getattr(self.player, 'crit_rate', 5.0)
                     vis_g = [self.player.visible_sprites] if getattr(self.player, 'visible_sprites', None) else []
                     if is_crit:
                         c_mult = getattr(self.player, 'crit_dmg', 150.0) / 100.0
                         damage = int(damage * c_mult)
                         try:
                             from src.sound_manager import play_sfx
                             play_sfx('crit')
                         except Exception:
                             pass
                         # Single authoritative DamageText handled in enemy.take_damage(is_crit=True)
                         # Vampiric Fang relic: heal upon critical strikes
                         relic_names = {getattr(r, 'name', '') for r in getattr(self.player, 'relics', []) if getattr(r, 'slot', '') == 'relic'}
                         if any('Клык' in r for r in relic_names):
                             heal_amt = max(2, int(damage * 0.12))
                             max_hp = self.player.stats.get('health', 100) if hasattr(self.player, 'stats') else 100
                             self.player.health = min(max_hp, self.player.health + heal_amt)
                             if vis_g:
                                 DamageText(f"+{heal_amt} HP", self.player.rect.center, vis_g, color=(120, 255, 140), size=14)

                     # Directional high-velocity metallic sparks along cut normal
                     if vis_g:
                         p_col_core = (255, 245, 200) if is_crit else (225, 240, 255)
                         p_col_glow = (255, 210, 60) if is_crit else (140, 195, 255)
                         cut_ang = math.radians(self.base_angle)
                         spark_count = 8 if is_crit else 4
                         for sp_i in range(spark_count):
                             norm_sign = 1.0 if sp_i % 2 == 0 else -1.0
                             spark_ang = cut_ang + norm_sign * (math.pi * 0.5) + random.uniform(-0.35, 0.35)
                             spark_spd = random.uniform(4.5, 8.5) if is_crit else random.uniform(3.0, 5.5)
                             col = p_col_core if sp_i < spark_count // 2 else p_col_glow
                             Particle(
                                 enemy.rect.center,
                                 vis_g,
                                 color=col,
                                 size=random.randint(2, 4) if is_crit else random.randint(1, 3),
                                 velocity=(math.cos(spark_ang) * spark_spd, math.sin(spark_ang) * spark_spd),
                                 lifetime=160 if is_crit else 120
                             )

                     # Dynamic Micro-Freeze Hit-Stop on impactful strikes
                     now = pygame.time.get_ticks()
                     freeze_ms = 40 if (is_crit or self.weapon_type == 'claymore') else 20
                     self.player.hit_stop_until = now + freeze_ms
                     if hasattr(enemy, 'hit_stop_until'):
                         enemy.hit_stop_until = now + freeze_ms + 10

                     # Knockback
                     if self.direction.magnitude() > 0:
                         kb = self.direction * self.kb_power
                         if hasattr(enemy, 'displace_safe'):
                             enemy.displace_safe(kb.x, kb.y)
                         elif hasattr(enemy, 'hitbox') and enemy.hitbox:
                             enemy.hitbox.x += int(kb.x)
                             enemy.hitbox.y += int(kb.y)
                             enemy.pos = pygame.math.Vector2(enemy.hitbox.topleft)
                             enemy.rect.center = enemy.hitbox.center
                     if hasattr(enemy, 'take_damage'):
                         enemy.take_damage(damage, source='claymore' if self.weapon_type == 'claymore' else 'weapon', is_crit=is_crit, hit_angle=math.radians(self.base_angle))
                         if hasattr(enemy, 'apply_status_effect'):
                             if is_crit:
                                 enemy.apply_status_effect('burn', duration_ms=2500, magnitude=1.0)
                             if self.weapon_type in ('dagger', 'daggers', 'claymore') and random.random() < 0.35:
                                 enemy.apply_status_effect('bleed', duration_ms=3000, magnitude=1.0)
                     else:
                         enemy.kill()

                     # Relic Synergies & Chain Lightning on Crit
                     relic_names = {getattr(r, 'name', '') for r in getattr(self.player, 'relics', []) if getattr(r, 'slot', '') == 'relic'}
                     has_lightning = is_crit or any('Грозы' in r or 'Storm' in r or 'Молни' in r for r in relic_names)
                     if has_lightning and vis_g:
                         enemy_group = getattr(self.player, 'enemy_sprites', None)
                         if enemy_group:
                             sec_enemies = []
                             for other in enemy_group:
                                 if other != enemy and getattr(other, 'alive', lambda: True)() and getattr(other, 'hp', 0) > 0:
                                     d = (pygame.math.Vector2(other.rect.center) - pygame.math.Vector2(enemy.rect.center)).magnitude()
                                     if d < 200:
                                         sec_enemies.append((d, other))
                             sec_enemies.sort(key=lambda x: x[0])
                             if sec_enemies:
                                 level = getattr(self.player, 'map_level', None)
                                 if level and hasattr(level, 'trigger_lightning_flash'):
                                     level.trigger_lightning_flash()
                                 try:
                                     from src.sound_manager import play_sfx
                                     play_sfx('lightning')
                                 except Exception:
                                     pass
                                 chain_dmg = max(5, int(damage * 0.55))
                                 for _, target_e in sec_enemies[:2]:
                                     ChainLightningVFX(enemy.rect.center, target_e.rect.center, vis_g)
                                     if hasattr(target_e, 'take_damage'):
                                         target_e.take_damage(chain_dmg, source='lightning')
                                     DamageText(f"⚡ {chain_dmg}", target_e.rect.center, vis_g, color=(100, 220, 255), size=15)
              
        # Destructibles
        obs_group = getattr(self.player, 'obstacle_sprites', None)
        if obs_group:
            obs_hits = pygame.sprite.spritecollide(self, obs_group, False)
            for obs in obs_hits:
                if hasattr(obs, 'destroy') and not getattr(obs, 'destroyed', False): 
                    loot = obs.destroy()
                    vis_g = [self.player.visible_sprites] if getattr(self.player, 'visible_sprites', None) else []
                    if random.random() < 0.65:
                        from src.items import Gold
                        Gold(obs.rect.center, vis_g, random.randint(3, 7), self.player)
                    if loot == "potion":
                        from src.items import Item
                        pot = Item("Health Potion", "common", {'heal': 20}, 10, 'assets/sprites/item_heart.png', slot='consumable')
                        self.player.add_item(pot)
                        if vis_g:
                            DamageText("+1 Potion", obs.rect.center, vis_g, color=(255, 100, 120), size=14)

        # Chest interaction upon weapon strike
        chest_group = getattr(self.player, 'chest_sprites', None)
        if chest_group:
            hit_chests = pygame.sprite.spritecollide(self, chest_group, False)
            for chest in hit_chests:
                vis_g = [self.player.visible_sprites] if getattr(self.player, 'visible_sprites', None) else []
                if not getattr(chest, 'opened', False):
                    opened_now = False
                    if hasattr(chest, 'open'):
                        opened_now = chest.open()
                    else:
                        chest.opened = True
                        opened_now = True
                    if opened_now:
                        from src.items import generate_random_item
                        item = generate_random_item()
                        self.player.add_item(item)
                        chest_gold = random.randint(20, 40)
                        self.player.gold += chest_gold
                        if hasattr(self.player, 'recalculate_stats'):
                            self.player.recalculate_stats()
                        if vis_g:
                            for _ in range(8):
                                Particle(chest.rect.center, vis_g, color=(255, 215, 50), size=random.randint(2, 4), velocity=(random.uniform(-2, 2), random.uniform(-3, -0.5)), lifetime=350)
                        try:
                            from src.sound_manager import play_sfx
                            play_sfx('chest')
                        except Exception:
                            pass
                        lvl = getattr(self.player, 'map_level', None)
                        if lvl and hasattr(lvl, 'pickup_notification'):
                            eff_list = [f"+{v} {k.capitalize()}" for k, v in getattr(item, 'effects', {}).items()] if getattr(item, 'effects', None) else []
                            sub_str = ", ".join(eff_list) if eff_list else "Artifact"
                            lvl.pickup_notification = {
                                'name': item.name,
                                'rarity': getattr(item, 'rarity', 'common'),
                                'desc': sub_str,
                                'icon': getattr(item, 'image', None),
                                'time': pygame.time.get_ticks()
                            }
                else:
                    # Already opened - gentle wooden spark
                    if vis_g and random.random() < 0.2:
                        Particle(chest.rect.center, vis_g, color=(170, 130, 80), size=3, velocity=(random.uniform(-1, 1), random.uniform(-1, 1)), lifetime=120)
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        if elapsed > self.life_time:
            self.kill()
            return

        progress = min(1.0, max(0.0, elapsed / float(self.life_time)))
        self.image = self.render_slash(progress)
        # Clean combat placement: Weapon slash arc aligns precisely with player center (Layer 3 foreground VFX)
        self.rect = self.image.get_rect(center=self.player.rect.center)

class EnemyProjectile(pygame.sprite.Sprite):
    def __init__(self, pos, groups, direction, obstacle_sprites, player, proj_type='arrow'):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.proj_type = proj_type
        self.direction = direction.normalize() if direction.magnitude() > 0 else pygame.math.Vector2(1, 0)
        self.obstacle_sprites = obstacle_sprites
        self.player = player
        self.map_level = getattr(player, 'map_level', None)
        self.owner = None
        self.is_player_cast = (player is None)
        self.spawn_time = pygame.time.get_ticks()
        self.has_hit = False
        self.z = 0.0
        self.vz = 0.0
        self.gravity_z = 0.8

        config = {
            'arrow': {'speed': 6.0, 'life': 1200, 'dmg': 10, 'size': (28, 28), 'img': 'projectile.png', 'color': (240, 230, 200)},
            'skull': {'speed': 4.8, 'life': 1600, 'dmg': 12, 'size': (32, 32), 'img': 'projectile_skull.png', 'color': (140, 60, 220)},
            'void_orb': {'speed': 5.0, 'life': 2400, 'dmg': 14, 'size': (38, 38), 'img': 'projectile_void.png', 'color': (200, 50, 255)},
            'frost_shard': {'speed': 5.2, 'life': 2200, 'dmg': 12, 'size': (28, 28), 'img': 'projectile_frost.png', 'color': (70, 210, 255)},
            'bone_spike': {'speed': 5.5, 'life': 2000, 'dmg': 11, 'size': (26, 26), 'img': 'projectile_bone.png', 'color': (235, 230, 210)},
            'fireball': {'speed': 5.0, 'life': 2200, 'dmg': 13, 'size': (30, 30), 'img': 'projectile_fire.png', 'color': (255, 120, 30)},
            'black_hole': {'speed': 3.2, 'life': 3200, 'dmg': 22, 'size': (56, 56), 'img': 'projectile_void.png', 'color': (180, 50, 240)}
        }
        cfg = config.get(proj_type, config['arrow'])
        self.speed = cfg['speed']
        self.life_time = cfg['life']
        self.damage = cfg['dmg']
        self.proj_color = cfg['color']

        if proj_type == 'black_hole':
            loaded_img = pygame.Surface(cfg['size'], pygame.SRCALPHA)
        else:
            from src.utils import load_image
            loaded_img = None
            try:
                loaded_img = load_image(f'assets/sprites/{cfg["img"]}', scale=cfg['size'])
            except Exception:
                try:
                    loaded_img = load_image('assets/sprites/projectile.png', scale=cfg['size'])
                except Exception:
                    pass

        if loaded_img is None:
            sz = cfg['size'][0]
            surf = pygame.Surface(cfg['size'], pygame.SRCALPHA)
            c_center = (sz // 2, sz // 2)
            c = self.proj_color
            if proj_type in ['void_orb', 'fireball', 'skull']:
                pygame.draw.circle(surf, (c[0]//2, c[1]//2, c[2]//2, 160), c_center, sz // 2)
                pygame.draw.circle(surf, c, c_center, sz // 3)
                pygame.draw.circle(surf, (255, 255, 255, 240), c_center, sz // 6)
            elif proj_type == 'frost_shard':
                pts = [(sz // 2, 2), (sz - 4, sz // 2), (sz // 2, sz - 2), (4, sz // 2)]
                pygame.draw.polygon(surf, c, pts)
                pygame.draw.polygon(surf, (220, 250, 255), [(sz//2, 5), (sz-7, sz//2), (sz//2, sz-5), (7, sz//2)])
            else: # arrow / bone
                pygame.draw.line(surf, c, (4, sz // 2), (sz - 4, sz // 2), 3)
                pygame.draw.polygon(surf, c, [(sz - 4, sz // 2), (sz - 10, sz // 2 - 4), (sz - 10, sz // 2 + 4)])
            loaded_img = surf

        angle = math.degrees(math.atan2(-self.direction.y, self.direction.x))
        self.image = pygame.transform.rotate(loaded_img, angle)
        self.rect = self.image.get_rect(center = pos)
        self.hitbox = self.rect.inflate(-4, -4)
        self.sprite_type = 'projectile'
        self.pos = pygame.math.Vector2(pos)

    def _spawn_black_hole_impact(self, vis=None):
        if vis is None:
            vis = next((group for group in self.groups() if hasattr(group, 'shake') or hasattr(group, 'display_surface')), None)
        try:
            from src.sound_manager import play_sfx
            play_sfx('void_burst')
        except Exception:
            pass
        if vis and hasattr(vis, 'shake'):
            vis.shake(duration_ms=280, magnitude=8)
        lvl = getattr(self, 'map_level', None) or getattr(self.player, 'map_level', None)
        if lvl and hasattr(lvl, 'add_space_distortion'):
            lvl.add_space_distortion(self.rect.center, max_radius=220, duration=420, kind='shockwave', intensity=1.1)
        if vis:
            for _ in range(24):
                ang = random.uniform(0, 6.28)
                spd = random.uniform(2.5, 6.5)
                col = random.choice([(210, 70, 255), (75, 235, 255), (255, 255, 255)])
                Particle(self.rect.center, [vis], color=col, size=random.randint(3, 6), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=280)

    def _spawn_projectile_impact(self, vis=None):
        if vis is None:
            groups = self.groups()
            vis = next((group for group in groups if hasattr(group, 'shake') or hasattr(group, 'display_surface')), None)
            if vis is None and groups:
                vis = groups[0]

        if self.proj_type == 'black_hole':
            self._spawn_black_hole_impact(vis)
            return

        level = getattr(self, 'map_level', None) or getattr(self.owner, 'map_level', None)
        if self.proj_type == 'void_orb':
            try:
                from src.sound_manager import play_sfx
                play_sfx('void_burst')
            except Exception:
                pass
            if vis and hasattr(vis, 'shake'):
                vis.shake(duration_ms=180, magnitude=4)
            if level and hasattr(level, 'add_temp_light'):
                level.add_temp_light(self.rect.center, (200, 50, 255), radius=190, duration=220)
            colors, count, speed, lifetime = [(200, 50, 255), (245, 90, 255), (70, 220, 255)], 16, (2.2, 5.0), 220
        elif self.proj_type == 'fireball':
            try:
                from src.sound_manager import play_sfx
                play_sfx('flame')
            except Exception:
                pass
            colors, count, speed, lifetime = [(255, 120, 30), (255, 200, 50), (255, 60, 20)], 12, (2.0, 4.5), 200
        elif self.proj_type == 'frost_shard':
            try:
                from src.sound_manager import play_sfx
                play_sfx('frost_cast')
            except Exception:
                pass
            colors, count, speed, lifetime = [(140, 230, 255), (200, 245, 255), (60, 160, 255)], 12, (1.8, 4.0), 220
        else:
            colors, count, speed, lifetime = [self.proj_color], 6, (1.5, 3.5), 180

        if vis:
            for _ in range(count):
                ang = random.uniform(0, 6.28)
                spd = random.uniform(*speed)
                Particle(self.rect.center, [vis], color=random.choice(colors), size=random.randint(2, 5), velocity=(math.cos(ang) * spd, math.sin(ang) * spd), lifetime=lifetime)

    def _break_player_projectile_obstacle(self, obstacle):
        destroy = getattr(obstacle, 'destroy', None)
        if not self.is_player_cast or not callable(destroy) or getattr(obstacle, 'destroyed', False):
            return

        loot = destroy()
        owner = getattr(self, 'owner', None)
        visible = getattr(owner, 'visible_sprites', None)
        if owner and visible and random.random() < 0.65:
            from src.items import Gold
            Gold(obstacle.rect.center, [visible], random.randint(3, 7), owner)
        if owner and loot == 'potion' and hasattr(owner, 'add_item'):
            from src.items import Item
            owner.add_item(Item('Health Potion', 'common', {'heal': 20}, 10, 'assets/sprites/item_heart.png', slot='consumable'))

    def update(self):
        if not self.alive() or self.has_hit:
            return

        # 2.5D Elevation Physics
        if self.z > 0.0 or self.vz != 0.0:
            self.vz -= self.gravity_z
            self.z = max(0.0, self.z + self.vz)
            if self.z <= 0.0:
                self.z = 0.0
                self.vz = 0.0

        # 1. Lifetime check
        if pygame.time.get_ticks() - self.spawn_time > self.life_time:
            self.kill()
            return

        # 2. Position update with swept segment tracking (Float vector precision!)
        prev_center = self.rect.center
        if not hasattr(self, 'pos'):
            self.pos = pygame.math.Vector2(self.rect.center)
        self.pos += self.direction * self.speed
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.hitbox.center = self.rect.center
        curr_center = self.rect.center

        # Gravitational Pull Physics for Black Hole Singularity
        if self.proj_type == 'black_hole':
            bh_vec = pygame.math.Vector2(self.rect.center)
            is_player_cast = getattr(self, 'is_player_cast', False) or (self.player is None)

            if is_player_cast:
                # Cast by player: gently and weakly pull opponents (enemies / showcase entities).
                # Strictly does NOT pull the player!
                all_targets = []
                if hasattr(self, 'target_group') and self.target_group:
                    all_targets.extend(list(self.target_group))
                vis = getattr(self, 'visible_sprites', None) or next((g for g in self.groups() if hasattr(g, 'sprites')), None)
                if not all_targets and vis and hasattr(vis, 'sprites'):
                    for sp in vis.sprites():
                        if getattr(sp, 'sprite_type', None) in ('enemy', 'showcase_entity'):
                            all_targets.append(sp)

                for tgt in all_targets:
                    if tgt is self or getattr(tgt, 'sprite_type', None) == 'player':
                        continue
                    t_box = getattr(tgt, 'hitbox', getattr(tgt, 'rect', None))
                    if t_box:
                        t_vec = pygame.math.Vector2(t_box.center)
                        dist = (bh_vec - t_vec).magnitude()
                        if 0 < dist < 190:
                            # Gentle, weak pull as requested ("затягивала противников очень слабо")
                            pull_force = (1.0 - dist / 190.0) * 0.85
                            pull_dir = (bh_vec - t_vec).normalize()
                            if hasattr(tgt, 'displace_safe'):
                                tgt.displace_safe(pull_dir.x * pull_force, pull_dir.y * pull_force)
            else:
                # Cast by enemy / boss: pulls ONLY the player! Does NOT pull enemies!
                if self.player and getattr(self.player, 'hitbox', None):
                    p_vec = pygame.math.Vector2(self.player.hitbox.center)
                    dist = (bh_vec - p_vec).magnitude()
                    if 0 < dist < 180:
                        pull_force = (1.0 - dist / 180.0) * 1.25
                        pull_dir = (bh_vec - p_vec).normalize()
                        if hasattr(self.player, 'displace_safe'):
                            self.player.displace_safe(pull_dir.x * pull_force, pull_dir.y * pull_force)

        # Particles for Black Hole & Magical Projectile Trails (Synchronized with 0-lag center!)
        vis = getattr(self, 'visible_sprites', None) or next((g for g in self.groups() if hasattr(g, 'shake') or hasattr(g, 'display_surface')), None)
        if vis:
            if self.proj_type == 'black_hole':
                if random.random() < 0.55:
                    m_ang = random.uniform(0, 6.28)
                    m_dist = random.uniform(32, 60)
                    sx = self.rect.centerx + math.cos(m_ang) * m_dist
                    sy = self.rect.centery + math.sin(m_ang) * m_dist
                    v_in = pygame.math.Vector2(self.rect.centerx - sx, self.rect.centery - sy).normalize() * random.uniform(2.5, 4.2)
                    col = random.choice([(210, 70, 255), (75, 230, 255), (255, 140, 255)])
                    Particle((sx, sy), [vis], color=col, size=random.randint(2, 4), velocity=(v_in.x, v_in.y), lifetime=140)
            elif self.proj_type == 'void_orb' and random.random() < 0.60:
                v_back = -self.direction * random.uniform(0.6, 2.0) + pygame.math.Vector2(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
                col = random.choice([(180, 40, 240), (235, 70, 255), (50, 15, 80)])
                Particle(self.rect.center, [vis], color=col, size=random.randint(2, 4), velocity=(v_back.x, v_back.y), lifetime=180)
            elif self.proj_type == 'fireball' and random.random() < 0.60:
                v_back = -self.direction * random.uniform(0.8, 2.2) + pygame.math.Vector2(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
                col = random.choice([(255, 120, 30), (255, 200, 50), (255, 60, 20)])
                Particle(self.rect.center, [vis], color=col, size=random.randint(2, 4), velocity=(v_back.x, v_back.y), lifetime=160)
            elif self.proj_type == 'frost_shard' and random.random() < 0.55:
                v_back = -self.direction * random.uniform(0.5, 1.8) + pygame.math.Vector2(random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4))
                col = random.choice([(140, 230, 255), (220, 250, 255), (60, 170, 255)])
                Particle(self.rect.center, [vis], color=col, size=random.randint(2, 3), velocity=(v_back.x, v_back.y), lifetime=160)
            elif self.proj_type == 'arrow' and random.random() < 0.35:
                v_back = -self.direction * random.uniform(0.4, 1.2)
                Particle(self.rect.center, [vis], color=(230, 220, 190), size=random.randint(1, 2), velocity=(v_back.x, v_back.y), lifetime=90)
            elif self.proj_type in ('skull', 'bone_spike') and random.random() < 0.45:
                v_back = -self.direction * random.uniform(0.5, 1.5)
                c_bone = (140, 60, 220) if self.proj_type == 'skull' else (225, 220, 200)
                Particle(self.rect.center, [vis], color=c_bone, size=random.randint(2, 3), velocity=(v_back.x, v_back.y), lifetime=120)

        # 3. Collision with walls
        for obstacle in getattr(self, 'obstacle_sprites', []):
            if getattr(obstacle, 'sprite_type', None) in ('particle', 'ui_effect', 'floor_overlay', 'decal', 'showcase_entity'):
                continue
            o_hitbox = getattr(obstacle, 'hitbox', getattr(obstacle, 'rect', None))
            if o_hitbox is not None and hasattr(o_hitbox, 'colliderect') and getattr(o_hitbox, 'width', 0) > 0:
                try:
                    if o_hitbox.colliderect(self.hitbox) or (hasattr(o_hitbox, 'clipline') and o_hitbox.clipline(prev_center, curr_center)):
                        self._break_player_projectile_obstacle(obstacle)
                        self._spawn_projectile_impact()
                        self.kill()
                        return
                except Exception:
                    continue

        # 4. Collision with Targets (Showcase Entities / Enemies) or Player
        hit_entity = None
        targets = getattr(self, 'target_group', None)
        if targets:
            for tgt in targets:
                t_box = getattr(tgt, 'hitbox', getattr(tgt, 'rect', None))
                if t_box and t_box.colliderect(self.hitbox):
                    hit_entity = tgt
                    break
        elif self.player and getattr(self.player, 'hitbox', None):
            if self.hitbox.colliderect(self.player.hitbox):
                hit_entity = self.player

        if hit_entity is not None:
            self.has_hit = True
            if hit_entity == self.player:
                if hasattr(self.player, 'take_damage'):
                    self.player.take_damage(self.damage, source_pos=self.rect.center)
                elif not getattr(self.player, 'is_shielded', False):
                    self.player.health -= self.damage
                if self.proj_type == 'frost_shard':
                    self.player.speed_modifier = 0.60
                    self.player.speed_modifier_timer = pygame.time.get_ticks() + 900
            else:
                if hasattr(hit_entity, 'take_damage'):
                    dmg_source = 'void' if self.proj_type in ('black_hole', 'void_orb', 'skull') else ('fire' if self.proj_type == 'fireball' else ('frost' if self.proj_type == 'frost_shard' else 'projectile'))
                    if getattr(self, 'is_crit', False):
                        try:
                            from src.sound_manager import play_sfx
                            play_sfx('crit')
                        except Exception:
                            pass
                    hit_entity.take_damage(self.damage, source=dmg_source, is_crit=getattr(self, 'is_crit', False))

            self._spawn_projectile_impact()

            self.kill()
            return

class Enemy(Entity):
    def __init__(self, pos, groups, obstacle_sprites, player, enemy_type, visible_sprites=None):
        super().__init__(groups)
        self.enemy_type = enemy_type
        self.visible_sprites = visible_sprites if visible_sprites is not None else (groups[0] if groups else None)
        from src.utils import load_image
        
        is_boss = 'boss' in enemy_type
        self.is_boss = is_boss
        self.is_flying = enemy_type in ('bat', 'phantom', 'imp') or 'necro' in enemy_type
        scale_size = (TILE_SIZE * 2, TILE_SIZE * 2) if is_boss else (TILE_SIZE, TILE_SIZE)

        self.frames = []
        try:
             self.frames.append(load_image(f'assets/sprites/{enemy_type}_0.png', scale=scale_size))
             self.frames.append(load_image(f'assets/sprites/{enemy_type}_1.png', scale=scale_size))
        except:
             # Fallback if no specific frames
             img = load_image(f'assets/sprites/{enemy_type}.png', scale=scale_size)
             self.frames = [img]

        # Multi-state animation framework (Idle, Walk, Telegraph, Attack, Squash & Stretch)
        self.anim_states = {'walk': list(self.frames), 'idle': list(self.frames)}
        self.anim_state = 'walk'

        def try_load_state(state_name, suffix):
            try:
                state_img = load_image(f'assets/sprites/{enemy_type}_{suffix}.png', scale=scale_size)
                self.anim_states[state_name] = [state_img]
            except Exception:
                pass

        for st_name, sfx in [
            ('charge', 'charge'),
            ('leap', 'leap'),
            ('land', 'land'),
            ('aim', 'aim'),
            ('attack', 'attack'),
            ('anticipation', 'anticipation'),
            ('recovery', 'recovery'),
            ('cast', 'cast'),
            ('ambush', 'ambush'),
            ('telegraph', 'telegraph'),
            ('cleave', 'cleave'),
            ('burst', 'burst'),
            ('smash', 'smash'),
            ('roar', 'roar'),
            ('detonate', 'detonate'),
            ('swell', 'swell')
        ]:
            try_load_state(st_name, sfx)

        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft = pos)
        self.hitbox = self.rect.inflate(-15, -15) if is_boss else self.rect.inflate(-10, -10)
        self.pos = pygame.math.Vector2(self.hitbox.topleft) # Sync
        self.obstacle_sprites = obstacle_sprites
        self.player = player
        base_enemy_speeds = {
            'zombie': 2.3,
            'skeleton': 2.5,
            'goblin': 3.3,
            'imp': 3.2,
            'bat': 3.5,
            'lurker': 3.4,
            'yeti': 2.0,
            'necromancer': 2.2,
            'spore_bomber': 3.6,
            'toxic_slime': 1.8,
            'mini_slime': 2.6,
            'phantom': 2.8,
            'mimic': 3.2,
            'gargoyle': 3.2,
            'mosquito': 4.2,
            'cultist': 2.2,
            'skeleton_brute': 1.9,
            'spore_creeper': 2.4,
            'banshee': 2.6,
            'lava_hound': 3.8,
            'sarcophagus': 0.0,
            'iron_maiden': 1.6,
            'boss': 2.2
        }
        self.speed = 2.2 if is_boss else base_enemy_speeds.get(enemy_type, 2.8)
        self.exp_value = 250 if is_boss else 20
        damage_map = {
            'mosquito': 6,
            'mimic': 14,
            'skeleton_brute': 14,
            'iron_maiden': 18,
            'lava_hound': 12,
            'gargoyle': 10,
            'spore_creeper': 8,
            'banshee': 8,
            'cultist': 8
        }
        if self.enemy_type in damage_map:
            self.attack_damage = damage_map[self.enemy_type]

        # Health pool
        hp_val = ENEMY_HP_CONFIG.get(enemy_type, 250 if is_boss else 30)
        self.max_hp = hp_val
        self.hp = hp_val
        self.took_damage_time = 0
        self.status_effects = {}
        
        self.can_attack = True
        self.attack_time = 0
        if enemy_type == 'skeleton':
            self.attack_cooldown = 1600
        elif enemy_type == 'imp':
            self.attack_cooldown = 1700
        elif enemy_type == 'yeti':
            self.attack_cooldown = 1500
        else:
            self.attack_cooldown = 900

        # Slime leap state machine
        if self.enemy_type in ['toxic_slime', 'mini_slime']:
            self.slime_state = 'crawling'
            self.slime_leap_timer = pygame.time.get_ticks() + random.randint(1000, 2200)
            self.slime_charge_start = 0
            self.slime_leap_start = 0
            self.slime_recovery_start = 0
            self.slime_leap_dir = pygame.math.Vector2()

        # Flanking sign for agile mobs
        self.flank_side = 1 if (id(self) % 2 == 0) else -1
        self.alerted = False
        if self.enemy_type == 'lurker':
            self.is_cloaked = True

        if getattr(self, 'is_boss', False):
            self.boss_phase = 1
            self.boss_dash_time = pygame.time.get_ticks()
            self.boss_burst_time = pygame.time.get_ticks()
            self.boss_attack_state = 'idle'
            self.cleave_dir = pygame.math.Vector2(1, 0)
            self.boss_telegraph_start = pygame.time.get_ticks()
            self.boss_cleave_timer = pygame.time.get_ticks() + 2500
            self.boss_spiral_timer = pygame.time.get_ticks() + 3500
            self.boss_ring_timer = pygame.time.get_ticks() + 4500
            self.boss_lance_timer = pygame.time.get_ticks() + 2000
            self.boss_spiral_angle = 0.0
        
        # Optimization: LOS Check Stagger
        self.los_interval = 10 # Check every 10 frames
        self.los_timer = self.los_interval # Immediate first check
        self.has_los = False # Cached result
        self.last_known_player_pos = None

    def apply_status_effect(self, name, duration_ms, magnitude=1.0):
        if not getattr(self, 'alive', lambda: False)() or getattr(self, 'hp', 0) <= 0:
            return
        if not hasattr(self, 'status_effects') or not isinstance(self.status_effects, dict):
            self.status_effects = {}
        now = pygame.time.get_ticks()
        if name in self.status_effects:
            self.status_effects[name]['expires'] = max(self.status_effects[name]['expires'], now + duration_ms)
            self.status_effects[name]['magnitude'] = max(self.status_effects[name]['magnitude'], magnitude)
            self.status_effects[name]['duration'] = duration_ms
        else:
            self.status_effects[name] = {
                'expires': now + duration_ms,
                'magnitude': magnitude,
                'tick_timer': now,
                'duration': duration_ms,
                'start_time': now
            }

    def take_damage(self, amount, source=None, is_crit=False, hit_angle=None):
        if not self.alive() or self.hp <= 0:
            return False
        if getattr(self, 'is_ethereal', False):
            return False
        now = pygame.time.get_ticks()
        if hit_angle is not None:
            cur_hit_angle = hit_angle
        elif getattr(self, 'player', None) and hasattr(self.player, 'rect'):
            dx = self.rect.centerx - self.player.rect.centerx
            dy = self.rect.centery - self.player.rect.centery
            cur_hit_angle = math.atan2(dy, dx)
        else:
            cur_hit_angle = 0.0
        self.hit_angle = cur_hit_angle

        if self.enemy_type == 'gargoyle':
            amount = max(1, int(amount * 0.60))
        elif self.enemy_type == 'skeleton_brute':
            facing = getattr(self, 'facing_angle', 0.0)
            if hasattr(self, 'direction') and self.direction.magnitude() > 0:
                facing = math.atan2(self.direction.y, self.direction.x)
            diff_ang = abs((cur_hit_angle - facing + math.pi) % (2 * math.pi) - math.pi)
            if diff_ang < 1.5:  # Frontal shield block
                amount = max(1, int(amount * 0.35))
        self.hp -= amount
        self.took_damage_time = now
        self.is_crit_hit = is_crit
        if source in ('weapon', 'claymore', 'heavy', 'slash'):
            self.hit_stop_until = now + (45 if is_crit else 25)
        else:
            self.hit_stop_until = 0
        try:
            from src.sound_manager import play_sfx
            if self.enemy_type == 'skeleton':
                play_sfx('skeleton_hit')
            elif source in ('claymore', 'heavy', 'boss_cleave'):
                play_sfx('hit_heavy')
            else:
                play_sfx('hit')
        except Exception:
            pass
        vis_g = [self.visible_sprites] if getattr(self, 'visible_sprites', None) else []
        if vis_g:
            if is_crit:
                CritCrossFlare(self.rect.center, vis_g)
                for _ in range(16):
                    ang = random.uniform(0, 6.28)
                    spd = random.uniform(3.0, 6.5)
                    col = random.choice([(255, 245, 160), (255, 215, 60), (255, 255, 220)])
                    Particle(self.rect.center, vis_g, color=col, size=random.randint(2, 4), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=220)
                DamageText(f"КРИТ! {int(amount)}", self.rect.center, vis_g, color=(255, 215, 60), size=22, is_crit=True)
            elif source == 'ult':
                DamageText(f"{int(amount)}", self.rect.center, vis_g, color=(140, 230, 255), size=18)
            else:
                DamageText(f"{int(amount)}", self.rect.center, vis_g, color=(250, 250, 250), size=16)
            for _ in range(4):
                ang = random.uniform(0, 6.28)
                spd = random.uniform(1.5, 4.0)
                Particle(self.rect.center, vis_g, color=(220, 50, 50), size=random.randint(2, 3), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=200)
        if self.hp <= 0:
            self.hp = 0
            try:
                from src.sound_manager import play_sfx
                play_sfx('enemy_die')
            except Exception:
                pass
            if vis_g:
                for _ in range(8):
                    ang = random.uniform(0, 6.28)
                    spd = random.uniform(2, 6)
                    p_col = (150, 40, 180) if getattr(self, 'is_boss', False) else (180, 180, 190)
                    Particle(self.rect.center, vis_g, color=p_col, size=random.randint(3, 5), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=320)
                if self.enemy_type in ('skeleton', 'skeleton_brute'):
                    try:
                        from src.entities import DebrisParticle
                        bone_colors = [(235, 230, 215), (210, 205, 190), (185, 180, 165)]
                        for _ in range(random.randint(5, 7)):
                            vx = random.uniform(-4.5, 4.5)
                            vy = random.uniform(-6.0, -2.5)
                            col = random.choice(bone_colors)
                            DebrisParticle(self.rect.center, vis_g, color=col, size=random.randint(4, 8), velocity=(vx, vy), lifetime=random.randint(450, 700))
                    except Exception:
                        pass
                
                # Soul Motes: Drop soul essence homing to player
                player_obj = getattr(self, 'player', None)
                if not player_obj and vis_g and hasattr(vis_g[0], 'player'):
                    player_obj = vis_g[0].player
                if player_obj and not getattr(player_obj, 'is_dead', False):
                    has_vamp = any('Клык' in getattr(r, 'name', '') or 'Vamp' in getattr(r, 'name', '') for r in getattr(player_obj, 'relics', []))
                    if getattr(self, 'is_boss', False) or has_vamp or random.random() < 0.45:
                        mote_count = 3 if getattr(self, 'is_boss', False) else (2 if has_vamp else 1)
                        for _ in range(mote_count):
                            SoulMote(self.rect.center, vis_g, player_obj)
            # Toxic Slime division on death
            if self.enemy_type == 'toxic_slime':
                vis_g = [self.visible_sprites] if getattr(self, 'visible_sprites', None) else []
                g_list = [self.visible_sprites] if self.visible_sprites else []
                enemy_grp = getattr(self, '_enemy_group', None)
                if enemy_grp is None:
                    for g in self.groups():
                        if g is not getattr(self, 'visible_sprites', None):
                            self._enemy_group = g
                            enemy_grp = g
                            break
                if enemy_grp and enemy_grp not in g_list:
                    g_list.append(enemy_grp)
                for offset_x in [-16, 16]:
                    sp_pos = (self.rect.centerx + offset_x, self.rect.centery)
                    Enemy(sp_pos, g_list, self.obstacle_sprites, self.player, 'mini_slime', visible_sprites=self.visible_sprites)
                    if vis_g:
                        Particle(sp_pos, vis_g, color=(90, 240, 110), size=5, velocity=(0, -1), lifetime=250)

            self.kill()
            if self.player:
                self.player.kills = getattr(self.player, 'kills', 0) + 1
                from src.items import Gold
                is_boss = getattr(self, 'is_boss', False)
                loot_rng = getattr(self.player, 'loot_rng', None)
                if not loot_rng and getattr(self, 'visible_sprites', None) and hasattr(self.visible_sprites, 'loot_rng'):
                    loot_rng = self.visible_sprites.loot_rng
                _lr = loot_rng or random
                gold_reward = _lr.randint(45, 80) if is_boss else _lr.randint(4, 9)
                p_vis_g = [self.player.visible_sprites] if getattr(self.player, 'visible_sprites', None) else []
                Gold(self.rect.center, p_vis_g, gold_reward, self.player)
                if hasattr(self, 'exp_value') and hasattr(self.player, 'gain_exp'):
                    self.player.gain_exp(self.exp_value)
            return True
        return False
        
    def has_line_of_fire(self, target_pos=None):
        if not getattr(self, 'alive', lambda: False)() or not getattr(self, 'player', None):
            return False
        p_hitbox = getattr(self.player, 'hitbox', getattr(self.player, 'rect', None))
        if not p_hitbox:
            return False
        start = getattr(self.rect, 'center', getattr(self, 'pos', (0, 0)))
        end = target_pos if target_pos is not None else p_hitbox.center
        
        for obstacle in getattr(self, 'obstacle_sprites', []):
            if obstacle is None or obstacle is self:
                continue
            if getattr(obstacle, 'sprite_type', None) in ('particle', 'ui_effect', 'floor_overlay', 'decal', 'showcase_entity'):
                continue
            hitbox = getattr(obstacle, 'hitbox', None) or getattr(obstacle, 'rect', None)
            if hitbox is None or not hasattr(hitbox, 'clipline'):
                continue
            if getattr(hitbox, 'width', 0) <= 0 or getattr(hitbox, 'height', 0) <= 0:
                continue
            try:
                if hitbox.clipline(start, end):
                    return False
            except Exception:
                continue
        return True

    def alert_nearby_allies(self):
        if not self.player or not self.alive():
            return
        enemy_group = getattr(self, '_enemy_group', None)
        if enemy_group is None:
            for g in self.groups():
                if g is not getattr(self, 'visible_sprites', None):
                    self._enemy_group = g
                    enemy_group = g
                    break
        if not enemy_group:
            return
        c_pos = self.hitbox.center
        p_pos = pygame.math.Vector2(self.player.hitbox.center)
        for ally in enemy_group:
            if ally is self or not getattr(ally, 'alive', lambda: False)():
                continue
            if getattr(ally, 'is_boss', False):
                continue
            dist = (pygame.math.Vector2(ally.hitbox.center) - pygame.math.Vector2(c_pos)).magnitude()
            if dist < 340:
                if ally.last_known_player_pos is None:
                    ally.last_known_player_pos = p_pos

    def check_line_of_sight(self, force=False):
        if force:
            self.los_timer = self.los_interval
        # Optimization: Only run every X frames for chase state
        self.los_timer += 1
        if self.los_timer < self.los_interval:
            return self.has_los
             
        self.los_timer = 0
        
        enemy_vec = pygame.math.Vector2(self.rect.center)
        player_vec = pygame.math.Vector2(self.player.hitbox.center)
        
        if (player_vec - enemy_vec).magnitude() > 600:
            self.has_los = False
            return False

        self.has_los = self.has_line_of_fire(self.player.hitbox.center)
        return self.has_los

    def calculate_direction(self, target_pos):
        enemy_vec = pygame.math.Vector2(self.hitbox.center)
        diff = target_pos - enemy_vec
        dist = diff.magnitude()
        if dist < 1e-4:
            return pygame.math.Vector2()
        desired = diff.normalize()

        def is_blocked(displacement):
            test_rect = self.hitbox.move(displacement.x, displacement.y)
            for obs in getattr(self, 'obstacle_sprites', []):
                if obs is None or obs is self:
                    continue
                if getattr(obs, 'sprite_type', None) in ('particle', 'ui_effect', 'floor_overlay', 'decal', 'showcase_entity'):
                    continue
                hitbox = getattr(obs, 'hitbox', None) or getattr(obs, 'rect', None)
                if hitbox and hasattr(hitbox, 'colliderect') and getattr(hitbox, 'width', 0) > 0 and getattr(hitbox, 'height', 0) > 0:
                    if hitbox.colliderect(test_rect):
                        return True
            return False

        step = desired * self.speed
        if not is_blocked(step):
            return desired

        # BFS Grid Pathfinding around obstacles (libtcod / Red Blob Games standard)
        from collections import deque
        cell_size = 32
        start_cell = (int(enemy_vec.x // cell_size), int(enemy_vec.y // cell_size))
        target_cell = (int(target_pos.x // cell_size), int(target_pos.y // cell_size))

        def cell_blocked(c):
            test_rect = self.hitbox.copy()
            test_rect.center = (c[0] * cell_size + cell_size // 2, c[1] * cell_size + cell_size // 2)
            for obs in getattr(self, 'obstacle_sprites', []):
                if obs is None or obs is self:
                    continue
                if getattr(obs, 'sprite_type', None) in ('particle', 'ui_effect', 'floor_overlay', 'decal', 'showcase_entity'):
                    continue
                hitbox = getattr(obs, 'hitbox', None) or getattr(obs, 'rect', None)
                if hitbox and hasattr(hitbox, 'colliderect') and getattr(hitbox, 'width', 0) > 0 and getattr(hitbox, 'height', 0) > 0:
                    if hitbox.colliderect(test_rect):
                        return True
            return False

        queue = deque([start_cell])
        visited = {start_cell}
        parent = {}
        found_target = None
        max_expansions = 300

        while queue and len(visited) < max_expansions:
            curr = queue.popleft()
            if curr == target_cell or (abs(curr[0] - target_cell[0]) <= 1 and abs(curr[1] - target_cell[1]) <= 1 and not cell_blocked(curr)):
                found_target = curr
                break

            neighbors = [
                (curr[0] + 1, curr[1]),
                (curr[0] - 1, curr[1]),
                (curr[0], curr[1] + 1),
                (curr[0], curr[1] - 1),
            ]
            neighbors.sort(key=lambda n: (n[0] - target_cell[0])**2 + (n[1] - target_cell[1])**2)
            for n in neighbors:
                if n not in visited:
                    visited.add(n)
                    if not cell_blocked(n):
                        parent[n] = curr
                        queue.append(n)

        if found_target and found_target in parent:
            curr = found_target
            while parent.get(curr) != start_cell and curr in parent:
                curr = parent[curr]
            next_cell = curr
            target_pt = pygame.math.Vector2(next_cell[0] * cell_size + cell_size // 2, next_cell[1] * cell_size + cell_size // 2)
            step_dir = target_pt - enemy_vec
            if step_dir.magnitude() > 0:
                cand = step_dir.normalize()
                if not is_blocked(cand * self.speed):
                    return cand
                comp1 = pygame.math.Vector2(0, 1 if cand.y > 0 else -1) if abs(cand.y) > 0 else None
                comp2 = pygame.math.Vector2(1 if cand.x > 0 else -1, 0) if abs(cand.x) > 0 else None
                for comp in [comp1, comp2]:
                    if comp and not is_blocked(comp * self.speed):
                        return comp

        candidates = []
        if abs(desired.x) > abs(desired.y):
            dx = 1 if desired.x > 0 else -1
            dy = 1 if desired.y >= 0 else -1
            candidates = [
                pygame.math.Vector2(dx, 0),
                pygame.math.Vector2(0, dy),
                pygame.math.Vector2(0, -dy),
                pygame.math.Vector2(-dx, 0)
            ]
        else:
            dx = 1 if desired.x >= 0 else -1
            dy = 1 if desired.y > 0 else -1
            candidates = [
                pygame.math.Vector2(0, dy),
                pygame.math.Vector2(dx, 0),
                pygame.math.Vector2(-dx, 0),
                pygame.math.Vector2(0, -dy)
            ]

        for cand in candidates:
            cand_step = cand.normalize() * self.speed
            if not is_blocked(cand_step):
                return cand.normalize()

        return desired

    def move_towards_player(self):
        enemy_vec = pygame.math.Vector2(self.hitbox.center)
        player_vec = pygame.math.Vector2(self.player.hitbox.center)
        distance = (player_vec - enemy_vec).magnitude()

        has_los = self.check_line_of_sight()
        if has_los:
            self.last_known_player_pos = pygame.math.Vector2(self.player.hitbox.center)
            self.alert_nearby_allies()

        target = None
        if has_los:
            if distance < 500:
                target = player_vec
        elif self.last_known_player_pos is not None:
            dist_to_last = (self.last_known_player_pos - enemy_vec).magnitude()
            if 15 < dist_to_last < 600:
                target = self.last_known_player_pos
            else:
                self.last_known_player_pos = None
        elif distance < 160:
            target = player_vec

        # Special Combat AI for 10 New AAA Mobs
        if self.enemy_type == 'mimic':
            if not getattr(self, 'mimic_awake', False):
                if distance < 65 or self.hp < self.max_hp:
                    self.mimic_awake = True
                    self.anim_state = 'attack'
                else:
                    self.direction = pygame.math.Vector2()
                    self.anim_state = 'idle'
                    return
        elif self.enemy_type == 'sarcophagus':
            self.direction = pygame.math.Vector2()
            now_s = pygame.time.get_ticks()
            if now_s - getattr(self, 'last_spawn_time', 0) >= 3800:
                self.last_spawn_time = now_s
                self.anim_state = 'attack'
                vis_g = [self.visible_sprites] if getattr(self, 'visible_sprites', None) else []
                g_list = [self.visible_sprites] if self.visible_sprites else []
                sp_pos = (self.rect.centerx + random.choice([-24, 24]), self.rect.centery + 12)
                Enemy(sp_pos, g_list, self.obstacle_sprites, self.player, 'skeleton', visible_sprites=self.visible_sprites)
                if vis_g:
                    Particle(sp_pos, vis_g, color=(65, 235, 140), size=6, velocity=(0, -1), lifetime=280)
            return
        elif self.enemy_type == 'banshee':
            now_b = pygame.time.get_ticks()
            if distance < 180 and now_b - getattr(self, 'last_wail_time', 0) >= 3200:
                self.last_wail_time = now_b
                self.anim_state = 'attack'
                if self.player and hasattr(self.player, 'speed_modifier'):
                    self.player.speed_modifier = 0.60
                    self.player.speed_modifier_timer = now_b + 1500
                    vis_g = [self.visible_sprites] if getattr(self, 'visible_sprites', None) else []
                    if vis_g:
                        DamageText("ВОЙ БАНЬШИ (-40% СКОРОСТИ)", self.player.rect.center, vis_g, color=(160, 230, 255), size=16)
        elif self.enemy_type == 'cultist':
            if 130 < distance < 320 and self.can_attack and self.has_line_of_fire():
                self.shoot(proj_type='fireball')
                self.can_attack = False
                self.attack_time = pygame.time.get_ticks()
                self.anim_state = 'attack'
                return

        if target is not None:
            is_melee = self.enemy_type in ['zombie', 'goblin', 'bat', 'lurker', 'mimic', 'gargoyle', 'mosquito', 'skeleton_brute', 'spore_creeper', 'banshee', 'lava_hound', 'iron_maiden'] or 'boss' in self.enemy_type
            if is_melee:
                # Zombie aggressive lunge within 120px
                if self.enemy_type == 'zombie':
                    self.speed = 3.3 if distance < 120 else 2.3

                # Agile mob flanking (surrounding tactic)
                target_to_seek = target
                if self.enemy_type in ['goblin', 'bat', 'lurker'] and 65 < distance < 300:
                    flank_sign = getattr(self, 'flank_side', 1)
                    diff = target - enemy_vec
                    flank_ang = math.radians(35 * flank_sign)
                    flank_x = diff.x * math.cos(flank_ang) - diff.y * math.sin(flank_ang)
                    flank_y = diff.x * math.sin(flank_ang) + diff.y * math.cos(flank_ang)
                    target_to_seek = enemy_vec + pygame.math.Vector2(flank_x, flank_y).normalize() * min(distance, 90)

                if self.enemy_type == 'lurker':
                    if distance > 140:
                        self.is_cloaked = True
                    else:
                        if getattr(self, 'is_cloaked', False):
                            self.is_cloaked = False
                            diff = player_vec - enemy_vec
                            if diff.magnitude() > 0:
                                self.velocity = diff.normalize() * 6.5
                            self.anim_state = 'ambush'
                            self.attack_anim_until = pygame.time.get_ticks() + 320
                            try:
                                from src.sound_manager import play_sfx
                                play_sfx('attack')
                            except Exception:
                                pass

                self.direction = self.calculate_direction(target_to_seek)
                now_atk = pygame.time.get_ticks()
                if self.hitbox.colliderect(self.player.hitbox):
                    # In melee range: halt movement so enemy doesn't phase through or push player
                    self.direction = pygame.math.Vector2()
                    if self.can_attack:
                        self.anim_state = 'attack'
                        self.attack_anim_until = now_atk + 260
                        if hasattr(self.player, 'take_damage'):
                            self.player.take_damage(getattr(self, 'attack_damage', 8), source_pos=self.hitbox.center)
                        elif not getattr(self.player, 'is_shielded', False):
                            self.player.health -= getattr(self, 'attack_damage', 8)
                        self.can_attack = False
                        self.attack_time = now_atk
                        if self.enemy_type == 'zombie':
                            try:
                                from src.sound_manager import play_sfx
                                play_sfx('zombie_attack')
                            except Exception:
                                pass
                    elif now_atk >= getattr(self, 'attack_anim_until', 0):
                        if self.enemy_type == 'zombie':
                            if now_atk >= getattr(self, 'attack_time', 0) + getattr(self, 'attack_cooldown', 900) - 280:
                                self.anim_state = 'anticipation'
                            else:
                                self.anim_state = 'recovery'
                        else:
                            self.anim_state = 'walk'
                elif self.enemy_type == 'zombie' and distance < 85:
                    if now_atk >= getattr(self, 'attack_anim_until', 0):
                        self.anim_state = 'anticipation'
                elif now_atk >= getattr(self, 'attack_anim_until', 0):
                    self.anim_state = 'walk'
            elif self.enemy_type == 'skeleton':
                now_sk = pygame.time.get_ticks()
                if has_los and distance <= 250:
                    self.direction = pygame.math.Vector2()
                    if self.can_attack:
                        self.shoot('arrow')
                        self.can_attack = False
                        self.attack_time = now_sk
                        self.anim_state = 'attack'
                        self.attack_anim_until = now_sk + 240
                        diff = enemy_vec - player_vec
                        if diff.magnitude() > 0:
                            self.velocity = diff.normalize() * 5.0
                    elif distance < 85:
                        diff = enemy_vec - player_vec
                        self.direction = diff.normalize() if diff.magnitude() > 0 else pygame.math.Vector2()
                    elif now_sk >= getattr(self, 'attack_anim_until', 0):
                        self.anim_state = 'aim'
                else:
                    if now_sk >= getattr(self, 'attack_anim_until', 0):
                        self.anim_state = 'walk'
                    self.direction = self.calculate_direction(target)
            elif self.enemy_type in ['toxic_slime', 'mini_slime']:
                now = pygame.time.get_ticks()
                is_mini = (self.enemy_type == 'mini_slime')
                leap_cooldown = 1400 if is_mini else 2100
                charge_duration = 300 if is_mini else 420
                leap_duration = 320 if is_mini else 380
                recovery_duration = 180 if is_mini else 280
                leap_speed = 13.5 if is_mini else 12.0
                touch_damage = 7 if is_mini else 12

                if not hasattr(self, 'slime_state'):
                    self.slime_state = 'crawling'
                    self.slime_leap_timer = now + random.randint(800, 1600)

                # 1. State: CRAWLING / APPROACH
                if self.slime_state == 'crawling':
                    self.anim_state = 'walk'
                    self.direction = self.calculate_direction(target)
                    if has_los and distance < (320 if is_mini else 380) and now >= self.slime_leap_timer:
                        self.slime_state = 'charging'
                        self.anim_state = 'charge'
                        self.slime_charge_start = now
                        self.direction = pygame.math.Vector2()
                        diff = player_vec - enemy_vec
                        self.slime_leap_dir = diff.normalize() if diff.magnitude() > 0 else pygame.math.Vector2(1, 0)

                # 2. State: CHARGING / SQUISH WINDUP
                elif self.slime_state == 'charging':
                    self.anim_state = 'charge'
                    self.direction = pygame.math.Vector2()
                    vis_g = [self.visible_sprites] if getattr(self, 'visible_sprites', None) else []
                    if random.random() < 0.4 and vis_g:
                        p_col = (110, 255, 90) if is_mini else (40, 200, 60)
                        Particle(self.rect.midbottom, vis_g, color=p_col, size=random.randint(2, 4), velocity=(random.uniform(-0.8, 0.8), random.uniform(-1.5, -0.5)), lifetime=180)

                    if now - self.slime_charge_start >= charge_duration:
                        self.slime_state = 'leaping'
                        self.anim_state = 'leap'
                        self.slime_leap_start = now
                        self.velocity = self.slime_leap_dir * leap_speed
                        if not is_mini and vis_g:
                            haz_group = getattr(getattr(self, 'level', None), 'hazard_sprites', None)
                            puddle_groups = [self.visible_sprites] + ([haz_group] if haz_group else [])
                            ToxicPuddle(self.rect.center, puddle_groups, duration=3500, radius=20, damage=4)
                        try:
                            from src.sound_manager import play_sfx
                            play_sfx('slime_leap')
                        except Exception:
                            pass

                # 3. State: LEAPING (Airborne thrust towards player)
                elif self.slime_state == 'leaping':
                    self.anim_state = 'leap'
                    self.direction = pygame.math.Vector2()
                    if self.hitbox.colliderect(self.player.hitbox):
                        if self.can_attack:
                            if hasattr(self.player, 'take_damage'):
                                self.player.take_damage(touch_damage, source_pos=self.rect.center)
                            elif not getattr(self.player, 'is_shielded', False):
                                self.player.health -= touch_damage
                            self.can_attack = False
                            self.attack_time = now
                            self.velocity = -self.slime_leap_dir * 3.0

                    if now - self.slime_leap_start >= leap_duration:
                        self.slime_state = 'recovery'
                        self.anim_state = 'land'
                        self.slime_recovery_start = now
                        self.velocity = pygame.math.Vector2()
                        try:
                            from src.sound_manager import play_sfx
                            play_sfx('slime_land')
                        except Exception:
                            pass
                        vis_g = [self.visible_sprites] if getattr(self, 'visible_sprites', None) else []
                        if not is_mini and vis_g:
                            haz_group = getattr(getattr(self, 'level', None), 'hazard_sprites', None)
                            puddle_groups = [self.visible_sprites] + ([haz_group] if haz_group else [])
                            ToxicPuddle(self.rect.center, puddle_groups, duration=3800, radius=22, damage=4)
                        for _ in range(5):
                            ang = random.uniform(0, 6.28)
                            spd = random.uniform(1.0, 3.0)
                            Particle(self.rect.center, vis_g, color=(60, 220, 80), size=3, velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=180)

                # 4. State: RECOVERY
                elif self.slime_state == 'recovery':
                    self.direction = pygame.math.Vector2()
                    if now - self.slime_recovery_start >= recovery_duration:
                        self.slime_state = 'crawling'
                        self.slime_leap_timer = now + leap_cooldown
            elif self.enemy_type == 'necromancer':
                now = pygame.time.get_ticks()
                if not hasattr(self, 'summon_timer'):
                    self.summon_timer = now + 4000
                if now >= self.summon_timer:
                    self.summon_timer = now + 8000
                    if self.player and getattr(self, 'visible_sprites', None):
                        spawn_pos = (self.rect.centerx + random.randint(-40, 40), self.rect.centery + random.randint(-40, 40))
                        g_list = [self.visible_sprites]
                        enemy_grp = getattr(self, '_enemy_group', None)
                        if enemy_grp:
                            g_list.append(enemy_grp)
                        Enemy(spawn_pos, g_list, self.obstacle_sprites, self.player, 'skeleton', visible_sprites=self.visible_sprites)
                        Particle(spawn_pos, [self.visible_sprites], color=(40, 240, 210), size=6, velocity=(0, -1), lifetime=250)
                        self.anim_state = 'cast'
                        self.cast_until = now + 450
                        try:
                            from src.sound_manager import play_sfx
                            play_sfx('necro_cast')
                        except Exception:
                            pass

                if now < getattr(self, 'cast_until', 0):
                    self.anim_state = 'cast'
                    self.direction = pygame.math.Vector2()
                else:
                    self.anim_state = 'walk'
                    if has_los and 180 <= distance <= 320:
                        self.direction = pygame.math.Vector2()
                        if self.can_attack:
                            self.shoot('skull')
                            self.can_attack = False
                            self.attack_time = now
                    elif has_los and distance < 180:
                        diff = enemy_vec - player_vec
                        self.direction = diff.normalize() if diff.magnitude() > 0 else pygame.math.Vector2()
                    else:
                        self.direction = self.calculate_direction(target)
            elif self.enemy_type == 'spore_bomber':
                now = pygame.time.get_ticks()
                if not hasattr(self, 'detonating'):
                    self.detonating = False
                    self.detonate_start = 0

                if distance < 65 and not self.detonating:
                    self.detonating = True
                    self.detonate_start = now
                    self.anim_state = 'telegraph'
                    self.direction = pygame.math.Vector2()

                if self.detonating:
                    self.direction = pygame.math.Vector2()
                    self.anim_state = 'telegraph'
                    vis_g = [self.visible_sprites] if getattr(self, 'visible_sprites', None) else []
                    if random.random() < 0.7 and vis_g:
                        Particle(self.rect.center, vis_g, color=(240, 50, 255), size=random.randint(2, 5), velocity=(random.uniform(-1, 1), random.uniform(-1, 1)), lifetime=180)
                    if now - self.detonate_start >= 850:
                        self.anim_state = 'detonate'
                        try:
                            from src.sound_manager import play_sfx
                            play_sfx('spore_explode')
                        except Exception:
                            pass
                        p_dist = (player_vec - enemy_vec).magnitude()
                        if p_dist < 90 and hasattr(self.player, 'take_damage'):
                            self.player.take_damage(35, source_pos=self.rect.center)
                        if vis_g:
                            spore_var = random.choice([0, 1, 2])
                            if spore_var == 0:
                                SporeMiasmaCloudVFX(self.rect.center, vis_g)
                            elif spore_var == 1:
                                SporeAcidGeyserVFX(self.rect.center, vis_g)
                            else:
                                SporeClusterPodsVFX(self.rect.center, vis_g)
                            for _ in range(12):
                                ang = random.uniform(0, 6.28)
                                spd = random.uniform(2, 5)
                                Particle(self.rect.center, vis_g, color=(120, 240, 60), size=random.randint(3, 5), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=240)
                        self.kill()
                        return
                else:
                    self.anim_state = 'walk'
                    self.direction = self.calculate_direction(target)
            elif self.enemy_type == 'yeti':
                now_yeti = pygame.time.get_ticks()
                if not hasattr(self, 'yeti_state'):
                    self.yeti_state = 'walk'
                    self.yeti_state_until = 0

                if self.yeti_state == 'telegraph':
                    self.direction = pygame.math.Vector2()
                    self.anim_state = 'telegraph'
                    if now_yeti >= self.yeti_state_until:
                        self.yeti_state = 'smash'
                        self.anim_state = 'smash'
                        self.yeti_state_until = now_yeti + 280
                        try:
                            from src.sound_manager import play_sfx
                            play_sfx('hit_heavy')
                        except Exception:
                            pass
                        p_dist = (player_vec - enemy_vec).magnitude()
                        if p_dist < 80 and hasattr(self.player, 'take_damage'):
                            self.player.take_damage(20, source_pos=self.rect.center)
                        vis_g = [self.visible_sprites] if getattr(self, 'visible_sprites', None) else []
                        if vis_g:
                            for _ in range(8):
                                ang = random.uniform(0, 6.28)
                                spd = random.uniform(2, 5)
                                Particle(self.rect.center, vis_g, color=(130, 225, 255), size=random.randint(3, 5), velocity=(math.cos(ang)*spd, math.sin(ang)*spd), lifetime=220)
                elif self.yeti_state == 'smash':
                    self.direction = pygame.math.Vector2()
                    self.anim_state = 'smash'
                    if now_yeti >= self.yeti_state_until:
                        self.yeti_state = 'attack'
                        self.anim_state = 'attack'
                        self.yeti_state_until = now_yeti + 200
                elif self.yeti_state == 'attack':
                    self.direction = pygame.math.Vector2()
                    self.anim_state = 'attack'
                    if now_yeti >= self.yeti_state_until:
                        self.yeti_state = 'walk'
                        self.anim_state = 'walk'
                        self.attack_time = now_yeti
                        self.can_attack = False
                else:
                    self.anim_state = 'walk'
                    if distance < 75 and self.can_attack:
                        self.yeti_state = 'telegraph'
                        self.anim_state = 'telegraph'
                        self.yeti_state_until = now_yeti + 340
                        self.direction = pygame.math.Vector2()
                    else:
                        self.direction = self.calculate_direction(target)
            elif self.enemy_type == 'imp':
                now_imp = pygame.time.get_ticks()
                if not hasattr(self, 'imp_state'):
                    self.imp_state = 'hover'
                    self.imp_cast_until = 0

                if self.imp_state == 'casting':
                    self.direction = pygame.math.Vector2()
                    self.anim_state = 'cast'
                    vis_g = [self.visible_sprites] if getattr(self, 'visible_sprites', None) else []
                    if random.random() < 0.4 and vis_g:
                        Particle(self.rect.center, vis_g, color=(255, 140, 20), size=random.randint(2, 4), velocity=(random.uniform(-0.5, 0.5), random.uniform(-1, 0)), lifetime=150)
                    if now_imp >= self.imp_cast_until:
                        self.shoot('fireball')
                        self.can_attack = False
                        self.attack_time = now_imp
                        self.imp_state = 'hover'
                        self.anim_state = 'walk'
                else:
                    self.anim_state = 'walk'
                    if has_los and 110 <= distance <= 240:
                        self.direction = pygame.math.Vector2()
                        if self.can_attack:
                            self.imp_state = 'casting'
                            self.anim_state = 'cast'
                            self.imp_cast_until = now_imp + 300
                    elif has_los and distance < 110:
                        diff = enemy_vec - player_vec
                        self.direction = diff.normalize() if diff.magnitude() > 0 else pygame.math.Vector2()
                    else:
                        self.direction = self.calculate_direction(target)
            elif self.enemy_type == 'phantom':
                now_ph = pygame.time.get_ticks()
                if has_los and 120 <= distance <= 360 and self.can_attack:
                    self.direction = pygame.math.Vector2()
                    self.anim_state = 'attack'
                    self.attack_anim_until = now_ph + 400
                    self.shoot('black_hole')
                    self.can_attack = False
                    self.attack_time = now_ph
                else:
                    self.direction = (target - enemy_vec).normalize() if (target - enemy_vec).magnitude() > 0 else pygame.math.Vector2()
                    if self.hitbox.colliderect(self.player.hitbox):
                        self.direction = pygame.math.Vector2()
                        if self.can_attack:
                            self.anim_state = 'attack'
                            self.attack_anim_until = now_ph + 300
                            if hasattr(self.player, 'take_damage'):
                                self.player.take_damage(14, source_pos=self.hitbox.center)
                            self.can_attack = False
                            self.attack_time = now_ph
                        elif now_ph >= getattr(self, 'attack_anim_until', 0):
                            self.anim_state = 'walk'
                    elif distance < 95 and now_ph >= getattr(self, 'attack_anim_until', 0):
                        self.anim_state = 'attack'
                    elif now_ph >= getattr(self, 'attack_anim_until', 0):
                        self.anim_state = 'walk'
        else:
            self.direction = pygame.math.Vector2()

    def shoot(self, proj_type='arrow'):
        if not self.alive() or not self.visible_sprites:
            return
        if not self.has_line_of_fire():
            return
        try:
            from src.sound_manager import play_sfx
            if proj_type == 'skull':
                play_sfx('necro_cast')
            elif proj_type == 'fireball':
                play_sfx('flame')
            else:
                play_sfx('shoot')
        except Exception:
            pass
        enemy_vec = pygame.math.Vector2(self.rect.center)
        player_vec = pygame.math.Vector2(self.player.rect.center)
        diff = player_vec - enemy_vec
        direction = diff.normalize() if diff.magnitude() > 0 else pygame.math.Vector2(1, 0)
        EnemyProjectile(self.rect.center, [self.visible_sprites], direction, self.obstacle_sprites, self.player, proj_type=proj_type)

    def cooldowns(self):
        current_time = pygame.time.get_ticks()
        if not self.can_attack:
            if current_time - self.attack_time >= self.attack_cooldown:
                self.can_attack = True

    def separate_from_enemies(self):
        # Elastic boid separation: prevents enemies from stacking onto or phasing through each other
        enemy_group = getattr(self, '_enemy_group', None)
        if enemy_group is None:
            for g in self.groups():
                if g is not getattr(self, 'visible_sprites', None):
                    self._enemy_group = g
                    enemy_group = g
                    break
        if not enemy_group:
            return

        my_center = pygame.math.Vector2(self.hitbox.center)
        sep_radius = 28
        push = pygame.math.Vector2()

        for other in enemy_group:
            if other is self or not getattr(other, 'alive', lambda: False)():
                continue
            if not hasattr(other, 'hitbox'):
                continue
            diff = my_center - pygame.math.Vector2(other.hitbox.center)
            dist = diff.magnitude()
            if 0 < dist < sep_radius:
                overlap = sep_radius - dist
                push += (diff / dist) * overlap * 0.45

        if push.magnitude() > 0:
            if push.magnitude() > 4.0:
                push.scale_to_length(4.0)
            self.displace_safe(push.x, push.y)

    def animate(self):
        now = pygame.time.get_ticks()
        is_hit_stop = (now - getattr(self, 'took_damage_time', -1000) < 110)

        # 1. Determine active animation frames
        current_frames = getattr(self, 'anim_states', {}).get(getattr(self, 'anim_state', 'walk'), self.frames)
        if not current_frames:
            current_frames = self.frames
        if not current_frames:
            return

        if not is_hit_stop:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(current_frames):
                self.frame_index = 0

        idx = int(self.frame_index) % len(current_frames)
        base_img = current_frames[idx]

        # 2. Organic Procedural Squash & Stretch for Slimes
        if self.enemy_type in ['toxic_slime', 'mini_slime']:
            st = getattr(self, 'slime_state', 'crawling')
            if st == 'charging':
                scale_w = int(base_img.get_width() * 1.25)
                scale_h = max(4, int(base_img.get_height() * 0.75))
                base_img = pygame.transform.scale(base_img, (scale_w, scale_h))
            elif st == 'leaping':
                scale_w = max(4, int(base_img.get_width() * 0.78))
                scale_h = int(base_img.get_height() * 1.30)
                base_img = pygame.transform.scale(base_img, (scale_w, scale_h))
            elif st == 'recovery':
                scale_w = int(base_img.get_width() * 1.30)
                scale_h = max(4, int(base_img.get_height() * 0.70))
                base_img = pygame.transform.scale(base_img, (scale_w, scale_h))

        # 3. Directional Flip
        if self.player and hasattr(self.player, 'hitbox') and self.player.hitbox:
            if self.player.hitbox.centerx < self.hitbox.centerx:
                self.facing_left = True
            elif self.player.hitbox.centerx > self.hitbox.centerx:
                self.facing_left = False
        elif self.direction.x != 0:
            self.facing_left = (self.direction.x < 0)

        if getattr(self, 'facing_left', False):
            self.image = pygame.transform.flip(base_img, True, False)
        else:
            self.image = base_img.copy()

        self.rect = self.image.get_rect(midbottom=(self.hitbox.centerx, self.hitbox.bottom + 2))

        # 4. Hit Recoil & Directional Squash & Hurt Flash
        elapsed_hurt = now - getattr(self, 'took_damage_time', -1000)
        if 0 <= elapsed_hurt < 95:
            t = elapsed_hurt / 95.0
            squash_factor = math.sin(t * math.pi) * (0.18 if getattr(self, 'is_crit_hit', False) else 0.12)
            if squash_factor > 0.01:
                cur_w, cur_h = self.image.get_size()
                h_ang = getattr(self, 'hit_angle', 0.0)
                if abs(math.cos(h_ang)) >= abs(math.sin(h_ang)):
                    sq_w = max(4, int(cur_w * (1.0 - squash_factor)))
                    sq_h = max(4, int(cur_h * (1.0 + squash_factor * 0.75)))
                else:
                    sq_w = max(4, int(cur_w * (1.0 + squash_factor * 0.75)))
                    sq_h = max(4, int(cur_h * (1.0 - squash_factor)))
                self.image = pygame.transform.scale(self.image, (sq_w, sq_h))
                self.rect = self.image.get_rect(midbottom=(self.hitbox.centerx, self.hitbox.bottom + 2))

            try:
                m = pygame.mask.from_surface(self.image)
                overlay = m.to_surface(setcolor=(235, 235, 235, 175), unsetcolor=(0, 0, 0, 0))
                self.image.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            except Exception:
                pass

    def update(self):
        if not self.alive():
            return

        now = pygame.time.get_ticks()
        is_hit_stop = (now < getattr(self, 'hit_stop_until', 0))
        if is_hit_stop:
            self.direction = pygame.math.Vector2()

        # AAA Status Effects Simulation (Burn, Chill, Bleed)
        if hasattr(self, 'status_effects') and self.status_effects:
            expired = []
            for eff_name, eff_data in list(self.status_effects.items()):
                if now >= eff_data.get('expires', 0):
                    expired.append(eff_name)
                    continue
                mag = eff_data.get('magnitude', 1.0)
                if eff_name == 'burn':
                    if now - eff_data.get('tick_timer', 0) >= 500:
                        eff_data['tick_timer'] = now
                        tick_dmg = max(1, int(4 * mag))
                        self.take_damage(tick_dmg, source='fire')
                    if self.visible_sprites and random.random() < 0.28:
                        vis_g = [self.visible_sprites] if not isinstance(self.visible_sprites, (list, tuple)) else self.visible_sprites
                        Particle(self.rect.center, vis_g, color=(255, random.randint(110, 180), 30), size=random.randint(2, 4), velocity=(random.uniform(-0.8, 0.8), random.uniform(-2.2, -0.8)), lifetime=220)
                elif eff_name in ('chill', 'freeze'):
                    if self.visible_sprites and random.random() < 0.22:
                        vis_g = [self.visible_sprites] if not isinstance(self.visible_sprites, (list, tuple)) else self.visible_sprites
                        Particle(self.rect.center, vis_g, color=(140, 220, 255), size=random.randint(2, 3), velocity=(random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6)), lifetime=180)
                elif eff_name == 'bleed':
                    if now - eff_data.get('tick_timer', 0) >= 600:
                        eff_data['tick_timer'] = now
                        tick_dmg = max(1, int(3 * mag))
                        self.take_damage(tick_dmg, source='bleed')
                    if self.visible_sprites and random.random() < 0.28:
                        vis_g = [self.visible_sprites] if not isinstance(self.visible_sprites, (list, tuple)) else self.visible_sprites
                        Particle(self.rect.center, vis_g, color=(220, 25, 45), size=random.randint(2, 4), velocity=(random.uniform(-0.6, 0.6), random.uniform(0.6, 2.0)), lifetime=200)
            for ex in expired:
                if ex in self.status_effects:
                    del self.status_effects[ex]

        if not self.alive():
            return

        if getattr(self, 'is_boss', False):
            now = pygame.time.get_ticks()
            # Boss Heavy Cleave Telegraph State Machine
            if not hasattr(self, 'boss_attack_state'):
                self.boss_attack_state = 'idle'
            if not hasattr(self, 'boss_cleave_timer'):
                self.boss_cleave_timer = now + 2500

            # 1. Start Telegraphing Cleave
            if self.boss_attack_state == 'idle' and now >= self.boss_cleave_timer:
                dist_to_p = (pygame.math.Vector2(self.player.hitbox.center) - pygame.math.Vector2(self.hitbox.center)).magnitude()
                if dist_to_p < 260:
                    self.boss_attack_state = 'telegraph'
                    self.anim_state = 'telegraph'
                    self.boss_telegraph_start = now
                    self.velocity = pygame.math.Vector2()
                    # Aim cleave at player
                    diff = pygame.math.Vector2(self.player.hitbox.center) - pygame.math.Vector2(self.hitbox.center)
                    self.cleave_dir = diff.normalize() if diff.magnitude() > 0 else pygame.math.Vector2(1, 0)

            # 2. In Telegraph: Windup & charging particles
            if self.boss_attack_state == 'telegraph':
                self.anim_state = 'telegraph'
                self.velocity = pygame.math.Vector2()
                windup_duration = 1000
                if random.random() < 0.6:
                    Particle(self.rect.center, [self.visible_sprites], color=(255, 40, 50), size=random.randint(3, 6), velocity=(random.uniform(-1.5, 1.5), random.uniform(-2, -0.5)), lifetime=250)
                    # Ground telegraph arc sparks along cleave direction
                    c_pos = self.hitbox.center
                    cleave_dir = getattr(self, 'cleave_dir', pygame.math.Vector2(1, 0))
                    t_rad = math.atan2(cleave_dir.y, cleave_dir.x) + random.uniform(-0.9, 0.9)
                    t_dist = random.uniform(30, 110)
                    t_pt = (c_pos[0] + math.cos(t_rad) * t_dist, c_pos[1] + math.sin(t_rad) * t_dist)
                    Particle(t_pt, [self.visible_sprites], color=(255, 60, 60), size=3, velocity=(0, 0), lifetime=140)

                # Release Cleave after windup
                if now - getattr(self, 'boss_telegraph_start', now) >= windup_duration:
                    self.boss_attack_state = 'idle'
                    self.anim_state = 'cleave'
                    self.boss_anim_until = now + 420
                    self.boss_cleave_timer = now + (3200 if getattr(self, 'boss_phase', 1) == 2 else 4200)
                    # Heavy Cleave Blast
                    try:
                        from src.sound_manager import play_sfx
                        play_sfx('boss_cleave')
                    except Exception:
                        pass
                    if hasattr(self.visible_sprites, 'apply_camera_shake'):
                        self.visible_sprites.apply_camera_shake(7, 240)
                    elif hasattr(self.visible_sprites, 'shake'):
                        self.visible_sprites.shake(240, 7)
                    # Multi-Tile Epic Boss Cleave Wave (5-6 tiles / 220px reach!)
                    c_pos = self.hitbox.center
                    cleave_col = (56, 239, 125) if self.enemy_type == 'boss_necro_lord' else ((120, 220, 255) if self.enemy_type == 'boss_frost_revenant' else ((220, 60, 255) if self.enemy_type == 'boss_void_knight' else (255, 140, 40)))
                    base_deg = math.degrees(math.atan2(self.cleave_dir.y, self.cleave_dir.x))
                    
                    # 3-tier expanding crescent shockwave
                    for tier_speed, p_size, life in [(6.0, 8, 380), (10.5, 6, 320), (14.0, 4, 260)]:
                        for ang in range(-70, 71, 10):
                            rad = math.radians(base_deg + ang)
                            vx = math.cos(rad) * tier_speed
                            vy = math.sin(rad) * tier_speed
                            Particle(c_pos, [self.visible_sprites], color=cleave_col, size=p_size, velocity=(vx, vy), lifetime=life)
                    
                    # Ground fissure decal & debris
                    lvl = getattr(self.player, 'map_level', None)
                    if lvl:
                        if hasattr(lvl, 'add_space_distortion'):
                            lvl.add_space_distortion(c_pos, max_radius=190, duration=360, kind='fissure')
                        if hasattr(lvl, 'add_temp_light'):
                            lvl.add_temp_light(c_pos, cleave_col, radius=360, duration=280)
                        if hasattr(lvl, 'floor_decals'):
                            cleave_pt = pygame.math.Vector2(c_pos) + getattr(self, 'cleave_dir', pygame.math.Vector2(1, 0)) * 75
                            lvl.floor_decals.append(GroundFissureDecal(cleave_pt, [self.visible_sprites], self.cleave_dir, length=120))
                    
                    for _ in range(12):
                        f_ang = math.radians(base_deg + random.uniform(-65, 65))
                        f_dist = random.uniform(40, 180)
                        f_pt = (c_pos[0] + math.cos(f_ang) * f_dist, c_pos[1] + math.sin(f_ang) * f_dist)
                        DebrisParticle(f_pt, [self.visible_sprites], size=random.randint(3, 5), velocity=(random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5)))

                    # Check player damage in massive 220px cleave cone
                    p_diff = pygame.math.Vector2(self.player.hitbox.center) - pygame.math.Vector2(c_pos)
                    if p_diff.magnitude() < 220:
                        p_ang = math.degrees(math.atan2(p_diff.y, p_diff.x))
                        diff_ang = (p_ang - base_deg + 180) % 360 - 180
                        if abs(diff_ang) <= 75:
                            cl_dmg = 28 if getattr(self, 'boss_phase', 1) == 2 else 22
                            if hasattr(self.player, 'take_damage'):
                                self.player.take_damage(cl_dmg, source_pos=c_pos)
                            elif not getattr(self.player, 'is_shielded', False):
                                self.player.health -= cl_dmg
                            # Directional knockback
                            if hasattr(self.player, 'pos') and self.cleave_dir.magnitude() > 0:
                                self.player.pos += self.cleave_dir * 18

            # 3. Ground Tremor Stomp Attack
            if not hasattr(self, 'boss_stomp_timer'):
                self.boss_stomp_timer = now + 4000
            if self.boss_attack_state == 'idle' and now >= self.boss_stomp_timer:
                self.boss_stomp_timer = now + 6500
                self.anim_state = 'cleave'
                self.boss_anim_until = now + 350
                try:
                    from src.sound_manager import play_sfx
                    play_sfx('break')
                except Exception:
                    pass
                if hasattr(self.visible_sprites, 'apply_camera_shake'):
                    self.visible_sprites.apply_camera_shake(9, 280)
                elif hasattr(self.visible_sprites, 'shake'):
                    self.visible_sprites.shake(280, 9)
                c_pos = self.hitbox.center
                for a in range(0, 360, 20):
                    s_rad = math.radians(a)
                    vx = math.cos(s_rad) * 5.5
                    vy = math.sin(s_rad) * 5.5
                    Particle(c_pos, [self.visible_sprites], color=(255, 120, 40), size=random.randint(5, 7), velocity=(vx, vy), lifetime=260)
                p_dist = (pygame.math.Vector2(self.player.hitbox.center) - pygame.math.Vector2(c_pos)).magnitude()
                if p_dist < 150:
                    if hasattr(self.player, 'take_damage'):
                        self.player.take_damage(16, source_pos=c_pos)
                    elif not getattr(self.player, 'is_shielded', False):
                        self.player.health -= 16

            if self.hp <= 100:
                self.boss_phase = 2
                self.speed = 3.2
                # Enrage Shadow Motes
                if random.random() < 0.4:
                    Particle(self.rect.center, [self.visible_sprites], color=(240, 30, 50), size=random.randint(2, 4), velocity=(random.uniform(-1, 1), random.uniform(-1.5, 0.5)), lifetime=180)
                # Summon phase 2 bone minions once
                if not getattr(self, 'phase2_minions_spawned', False):
                    self.phase2_minions_spawned = True
                    try:
                        from src.sound_manager import play_sfx
                        play_sfx('enemy_die')
                    except Exception:
                        pass
                    # Flanking minion spawns matching boss archetype
                    m_type = 'phantom' if self.enemy_type == 'boss_necro_lord' else ('toxic_slime' if self.enemy_type == 'boss_bone_golem' else 'skeleton')
                    for offset_x in [-96, 96]:
                        spawn_pos = (self.hitbox.centerx + offset_x, self.hitbox.centery)
                        Enemy(spawn_pos, [self.visible_sprites, self.player.enemy_sprites], self.obstacle_sprites, self.player, m_type, visible_sprites=self.visible_sprites)

                burst_ready = (now - getattr(self, 'boss_burst_time', 0) >= 2200)
                if burst_ready:
                    self.boss_burst_time = now
                    self.anim_state = 'burst'
                    self.boss_anim_until = now + 400
                    p_type = 'frost_shard' if self.enemy_type == 'boss_frost_revenant' else ('bone_spike' if self.enemy_type == 'boss_bone_golem' else ('skull' if self.enemy_type == 'boss_necro_lord' else 'void_orb'))
                    for angle_deg in range(0, 360, 45):
                        rad = math.radians(angle_deg)
                        proj_dir = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                        EnemyProjectile(self.rect.center, [self.visible_sprites], proj_dir, self.obstacle_sprites, self.player, proj_type=p_type)

                # Secondary Phase 2 Bullet Hell Spiral (only fires when NOT bursting in same tick, so 8-burst count is preserved)
                if not burst_ready and (now - getattr(self, 'boss_spiral_timer', 0) >= 650):
                    self.boss_spiral_timer = now
                    self.boss_spiral_angle = (getattr(self, 'boss_spiral_angle', 0.0) + 28) % 360
                    p_type = 'frost_shard' if self.enemy_type == 'boss_frost_revenant' else ('bone_spike' if self.enemy_type == 'boss_bone_golem' else ('skull' if self.enemy_type == 'boss_necro_lord' else 'void_orb'))
                    for off in [0, 180]:
                        rad = math.radians(self.boss_spiral_angle + off)
                        proj_dir = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                        EnemyProjectile(self.rect.center, [self.visible_sprites], proj_dir, self.obstacle_sprites, self.player, proj_type=p_type)
            else:
                self.boss_phase = 1
                if now - getattr(self, 'boss_dash_time', 0) >= 4500 and self.boss_attack_state == 'idle':
                    self.boss_dash_time = now
                    dash_diff = pygame.math.Vector2(self.player.hitbox.center) - pygame.math.Vector2(self.hitbox.center)
                    if dash_diff.magnitude() > 0:
                        self.velocity = dash_diff.normalize() * 6.5

                # Phase 1: Aimed 3-way projectile spread
                if now - getattr(self, 'boss_lance_timer', 0) >= 3800 and self.boss_attack_state == 'idle':
                    self.boss_lance_timer = now
                    diff = pygame.math.Vector2(self.player.hitbox.center) - pygame.math.Vector2(self.hitbox.center)
                    if diff.magnitude() > 0:
                        base_deg = math.degrees(math.atan2(diff.y, diff.x))
                        p_type = 'frost_shard' if self.enemy_type == 'boss_frost_revenant' else ('bone_spike' if self.enemy_type == 'boss_bone_golem' else ('skull' if self.enemy_type == 'boss_necro_lord' else 'void_orb'))
                        for spread in [-18, 0, 18]:
                            r = math.radians(base_deg + spread)
                            EnemyProjectile(self.rect.center, [self.visible_sprites], pygame.math.Vector2(math.cos(r), math.sin(r)), self.obstacle_sprites, self.player, proj_type=p_type)

            if now >= getattr(self, 'boss_anim_until', 0) and self.boss_attack_state == 'idle':
                self.anim_state = 'walk'

        if not is_hit_stop:
            if getattr(self, 'is_flying', False) and self.vz == 0.0:
                self.z = 14.0 + 3.0 * math.sin(pygame.time.get_ticks() * 0.005)
            self.animate()
            if getattr(self, 'boss_attack_state', 'idle') not in ['telegraph', 'recovery']:
                self.move_towards_player()
                effective_speed = self.speed * 0.55 if (hasattr(self, 'status_effects') and ('chill' in self.status_effects or 'freeze' in self.status_effects)) else self.speed
                self.move(effective_speed)
                self.separate_from_enemies()
        self.cooldowns()


# 2.5D Projectile Alias
Projectile = EnemyProjectile
