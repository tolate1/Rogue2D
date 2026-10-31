import pygame
import sys
import os
import random
import math

class SafeLogStream:
    def __init__(self, filepath=None):
        self.file = None
        if filepath:
            try:
                self.file = open(filepath, 'w', encoding='utf-8', errors='replace')
            except Exception:
                self.file = None
    def write(self, s):
        try:
            if self.file:
                self.file.write(s)
                self.file.flush()
        except Exception:
            pass
    def flush(self):
        try:
            if self.file:
                self.file.flush()
        except Exception:
            pass

# PyInstaller frozen runtime initialization
if getattr(sys, 'frozen', False):
    exe_dir = os.path.dirname(sys.executable)
    try:
        os.chdir(exe_dir)
    except Exception:
        pass
    log_stream = SafeLogStream(os.path.join(exe_dir, 'game.log'))
    sys.stdout = log_stream
    sys.stderr = log_stream
from src.settings import *
from src.map_manager import Level
from src.ui import UI, Button, get_pixel_font, draw_workbench, service_label
from src.sound_manager import (
    start_bgm, stop_bgm, play_sfx,
    set_sfx_volume, get_sfx_volume,
    set_music_volume, get_music_volume,
    set_master_volume, get_master_volume
)
from src.save_manager import (
    has_save, load_game_state, save_game_state,
    delete_save, load_settings, save_settings,
    load_profile, save_profile, clear_run_state
)
from src.items import Item
from src.utils import load_image

class MenuEmber:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.reset(random_y=True)

    def reset(self, random_y=False):
        # Spawns directly above architecture pillar torch bowls (x = 176 and x = w - 176)
        torch_x = 176 if random.random() < 0.5 else (self.w - 176)
        self.x = torch_x + random.uniform(-6, 6)
        self.y = random.uniform(80, 230) if random_y else random.uniform(215, 232)
        self.vx = random.uniform(-0.6, 0.6)
        self.vy = random.uniform(-1.8, -0.7)
        self.size = random.uniform(2.0, 4.0)
        self.max_life = random.randint(70, 140)
        self.life = random.randint(1, self.max_life) if random_y else self.max_life
        self.base_color = random.choice([(255, 120, 25), (255, 185, 45), (255, 70, 20), (255, 215, 70)])

    def update(self):
        self.life -= 1
        self.x += self.vx + math.sin(self.life * 0.08) * 0.5
        self.y += self.vy
        if self.life <= 0 or self.y < 30:
            self.reset(random_y=False)

    def draw(self, surface):
        progress = self.life / self.max_life
        alpha = int(240 * progress)
        s = max(1, int(self.size * progress))
        col = (self.base_color[0], self.base_color[1], self.base_color[2], alpha)
        ember_surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        pygame.draw.circle(ember_surf, col, (s, s), s)
        surface.blit(ember_surf, (int(self.x - s), int(self.y - s)))

class MenuMist:
    def __init__(self, w, h, idx):
        self.w = w
        self.h = h
        self.x = (idx * (w / 3.0)) - 60
        self.y = h - random.randint(80, 150)
        self.vx = random.uniform(0.35, 0.65)
        try:
            self.surf = load_image('assets/sprites/menu_fog.png')
        except Exception:
            self.surf = None

    def update(self):
        self.x += self.vx
        if self.x > self.w + 100:
            self.x = -220
            self.y = self.h - random.randint(80, 150)

    def draw(self, surface):
        if self.surf:
            surface.blit(self.surf, (int(self.x), int(self.y)))


class Game:
    def __init__(self):
        pygame.init()
        self.settings = load_settings()
        self.settings_tab = 'video'

        # Display Setup
        # Display Setup: Resizable window by default, Fullscreen toggle supported
        self.fullscreen = self.settings.get('fullscreen', False)
        self.window_size = list(self.settings.get('window_size', [WIDTH, HEIGHT]))
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
        if self.fullscreen:
            try:
                self.screen = pygame.display.set_mode((0, 0), flags)
            except Exception:
                self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        else:
            self.screen = pygame.display.set_mode((self.window_size[0], self.window_size[1]), flags)
        pygame.display.set_caption("Rogue 2D: Dungeon Descent")
        try:
            icon = load_image('assets/icon.png')
            if icon:
                pygame.display.set_icon(icon)
        except Exception:
            pass
        self.clock = pygame.time.Clock()
        self.running = True

        # Audio Setup
        set_master_volume(self.settings.get('master_volume', 0.8))
        set_sfx_volume(self.settings.get('sfx_volume', 0.8))
        set_music_volume(self.settings.get('music_volume', 0.6))

        self.ui = UI()
        self.ui.ui_scale = self.settings.get('hud_scale', 1.0)

        self.level = Level(current_floor=1)
        self.level.visible_sprites.zoom_level = self.settings.get('zoom', 1.0)

        # Main Menu Atmospheric Assets
        sw, sh = self.screen.get_size()
        try:
            self.menu_bg = load_image('assets/sprites/menu_bg.png')
            self.menu_bg_scaled = pygame.transform.scale(self.menu_bg, (sw, sh)) if self.menu_bg else None
        except Exception:
            self.menu_bg = None
            self.menu_bg_scaled = None

        try:
            self.title_logo = load_image('assets/sprites/title_logo.png')
        except Exception:
            self.title_logo = None

        try:
            self.game_over_banner = load_image('assets/sprites/game_over_banner.png')
        except Exception:
            self.game_over_banner = None

        self.torch_frames = []
        try:
            for f in range(4):
                self.torch_frames.append(load_image(f'assets/sprites/torch_{f}.png', scale=(36, 36)))
        except Exception:
            pass
        sw, sh = self.screen.get_size()
        self.menu_embers = [MenuEmber(sw, sh) for _ in range(35)]
        self.menu_mists = [MenuMist(sw, sh, i) for i in range(4)]

        self.menu_show_gear = False
        self.menu_hero_rect = pygame.Rect(sw - 330, 150, 270, 380)
        self.menu_hero_hover = False
        self.menu_player_frames = []
        try:
            for f in range(4):
                self.menu_player_frames.append(load_image(f'assets/sprites/player_idle_{f}.png', scale=(80, 80)))
        except Exception:
            try:
                self.menu_player_frames.append(load_image('assets/sprites/player.png', scale=(80, 80)))
            except Exception:
                pass

        self.ui_buttons = []
        self.last_run_stats = {}
        self.skill_tree_open = False
        self.skill_tree_opened_at = None
        self.state = 'menu'
        self.set_state('menu')

    def open_skill_tree(self):
        if self.skill_tree_open:
            return
        self.skill_tree_open = True
        self.skill_tree_opened_at = pygame.time.get_ticks()

    def close_skill_tree(self):
        if not self.skill_tree_open:
            return
        duration = max(0, pygame.time.get_ticks() - (self.skill_tree_opened_at or pygame.time.get_ticks()))
        self.skill_tree_open = False
        self.skill_tree_opened_at = None
        self.on_resume(duration)

    def toggle_menu_gear(self):
        self.menu_show_gear = not self.menu_show_gear
        try:
            from src.sound_manager import play_sfx
            play_sfx('chest')
        except Exception:
            pass

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.settings['fullscreen'] = self.fullscreen
        save_settings(self.settings)
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
        if self.fullscreen:
            try:
                self.screen = pygame.display.set_mode((0, 0), flags)
            except Exception:
                self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        else:
            w, h = self.window_size if hasattr(self, 'window_size') else [WIDTH, HEIGHT]
            self.screen = pygame.display.set_mode((w, h), flags)
        self.on_display_resize()

    def on_display_resize(self):
        sw, sh = self.screen.get_size()
        if not self.fullscreen:
            self.window_size = [sw, sh]
            self.settings['window_size'] = self.window_size
            save_settings(self.settings)
        if getattr(self, 'menu_bg', None):
            self.menu_bg_scaled = pygame.transform.scale(self.menu_bg, (sw, sh))
        self.menu_hero_rect = pygame.Rect(sw - 330, 150, 270, 380)
        self.menu_embers = [MenuEmber(sw, sh) for _ in range(35)]
        self.menu_mists = [MenuMist(sw, sh, i) for i in range(4)]
        if hasattr(self, 'ui') and self.ui:
            self.ui.display_surface = self.screen
        if hasattr(self, 'level') and hasattr(self.level, 'visible_sprites') and self.level.visible_sprites:
            self.level.visible_sprites.display_surface = self.screen
            self.level.visible_sprites.half_width = sw // 2
            self.level.visible_sprites.half_height = sh // 2
            self.level.visible_sprites.light_surf = pygame.Surface((sw, sh))
            self.level.visible_sprites.light_mask = pygame.Surface((sw, sh))
        self.set_state(self.state)

    def start_dev_room(self):
        zoom_level = getattr(self.level.visible_sprites, 'zoom_level', 1.0) if hasattr(self, 'level') else 1.0
        self.level = Level(is_dev_room=True)
        self.level.visible_sprites.zoom_level = zoom_level
        self.set_state('dev_room')

    def start_hub(self):
        zoom_level = getattr(self.level.visible_sprites, 'zoom_level', 1.0) if hasattr(self, 'level') else 1.0
        self.level = Level(is_hub=True)
        self.level.visible_sprites.zoom_level = zoom_level
        self.set_state('hub')

    def start_dungeon_run(self, chapter='catacombs_1'):
        delete_save()
        zoom_level = getattr(self.level.visible_sprites, 'zoom_level', 1.0) if hasattr(self, 'level') else 1.0

        # Carry over equipped items from hub player or load from profile
        equipped_to_carry = {}
        is_from_hub = hasattr(self, 'level') and getattr(self.level, 'is_hub', False) and hasattr(self.level, 'player') and getattr(self.level.player, 'equipped', None)
        skin_to_carry = getattr(self.level.player, 'current_skin', 'champion') if is_from_hub else 'champion'
        shop_bonuses_to_carry = dict(getattr(self.level.player, 'shop_stat_bonuses', {})) if is_from_hub else {'attack': 0, 'defense': 0}
        if is_from_hub:
            for slot, itm in self.level.player.equipped.items():
                equipped_to_carry[slot] = itm.clone() if itm else None
        else:
            prof = load_profile()
            for slot, itm_data in prof.get('equipped', {}).items():
                equipped_to_carry[slot] = Item.from_dict(itm_data) if itm_data else None

        start_floor = 6 if chapter == 'catacombs_2' else 1
        self.level = Level(current_floor=start_floor)
        self.level.chapter_name = chapter
        self.level.visible_sprites.zoom_level = zoom_level
        all_slots = ['weapon', 'offhand', 'armor', 'boots', 'amulet', 'ring', 'accessory']
        for s in all_slots:
            if s not in equipped_to_carry:
                equipped_to_carry[s] = None
        self.level.player.set_skin(skin_to_carry)
        self.level.player.shop_stat_bonuses = shop_bonuses_to_carry
        self.level.player.equipped = equipped_to_carry
        self.level.player.recalculate_stats()

        try:
            self.level.player.add_item(Item("Health Potion", "common", {'heal': 25}, 10, 'assets/sprites/item_heart.png'))
            self.level.player.recalculate_stats()
        except Exception:
            pass

        try:
            start_bgm()
        except Exception:
            pass
        self.set_state('game')

    def start_new_run(self, chapter='catacombs_1'):
        delete_save()
        self.start_dungeon_run(chapter=chapter)

    def continue_saved_run(self):
        save_data = load_game_state()
        if not save_data:
            self.start_hub()
            return

        if save_data.get('is_hub', False) or save_data.get('floor', 1) == 0:
            self.start_hub()
            return

        saved_floor = save_data.get('floor', 1)
        saved_seed = save_data.get('floor_seed')
        zoom_level = getattr(self.level.visible_sprites, 'zoom_level', 1.0) if hasattr(self, 'level') else 1.0
        self.level = Level(current_floor=saved_floor, floor_seed=saved_seed)
        self.level.visible_sprites.zoom_level = zoom_level

        p = self.level.player
        p.set_skin(save_data.get('current_skin', 'champion'))
        p.shop_stat_bonuses = dict(save_data.get('shop_stat_bonuses', {}))
        p.health = save_data.get('health', 100)
        p.energy = save_data.get('energy', 60)
        p.exp = save_data.get('exp', 0)
        p.level = save_data.get('level', 1)
        p.gold = save_data.get('gold', 0)
        p.kills = save_data.get('kills', 0)

        saved_pos = save_data.get('player_pos')
        if saved_pos:
            p.rect.topleft = (saved_pos[0], saved_pos[1])
            p.hitbox.center = p.rect.center
            p.pos = pygame.math.Vector2(p.hitbox.topleft)

            # Defensive validation: ensure loaded player position is not trapped inside walls
            tile_pos = (saved_pos[0] // 64, saved_pos[1] // 64)
            is_in_wall = any(p.hitbox.colliderect(w.hitbox) for w in getattr(self.level, 'obstacle_sprites', []) if hasattr(w, 'hitbox'))
            floor_positions = getattr(self.level, 'floor_positions', set())
            if is_in_wall or (floor_positions and tile_pos not in floor_positions):
                if floor_positions:
                    best_tile = min(floor_positions, key=lambda t: (t[0]*64 - saved_pos[0])**2 + (t[1]*64 - saved_pos[1])**2)
                    p.rect.topleft = (best_tile[0] * 64 + 8, best_tile[1] * 64 + 8)
                    p.hitbox.center = p.rect.center
                    p.pos = pygame.math.Vector2(p.hitbox.topleft)

        # Restore already opened chests
        for cx, cy in save_data.get('opened_chests', []):
            for c in getattr(self.level, 'chest_sprites', []):
                if c.rect.x == cx and c.rect.y == cy:
                    c.opened = True
                    if hasattr(c, 'open'): c.open()

        # Restore destroyed breakables / obstacles
        for ox, oy in save_data.get('destroyed_obstacles', []):
            for obs in list(getattr(self.level, 'obstacle_sprites', [])):
                if obs.rect.x == ox and obs.rect.y == oy:
                    obs.kill()
            if hasattr(self.level, 'destroyed_obstacle_positions'):
                self.level.destroyed_obstacle_positions.append([ox, oy])

        # Restore exact living enemies state (kills, positions, hp)
        saved_enemies = save_data.get('living_enemies')
        if saved_enemies is not None:
            for e in list(getattr(self.level, 'enemy_sprites', [])):
                e.kill()
            from src.entities import Enemy
            for edata in saved_enemies:
                e = Enemy(
                    (edata['pos'][0], edata['pos'][1]),
                    [self.level.visible_sprites, self.level.enemy_sprites],
                    self.level.obstacle_sprites,
                    self.level.player,
                    edata['type'],
                    visible_sprites=self.level.visible_sprites
                )
                e.hp = edata['hp']

        # Restore dropped gold coins on the floor
        saved_gold_drops = save_data.get('dropped_gold', [])
        if saved_gold_drops:
            from src.items import Gold
            for gdata in saved_gold_drops:
                Gold((gdata['pos'][0], gdata['pos'][1]), [self.level.visible_sprites], gdata['amount'], self.level.player)

        # Restore equipped permanent items (6 slots)
        saved_equipped = save_data.get('equipped', {})
        if isinstance(saved_equipped, dict):
            for slot_name in ['weapon', 'offhand', 'armor', 'boots', 'amulet', 'ring', 'accessory']:
                slot_item_data = saved_equipped.get(slot_name)
                if slot_item_data:
                    p.equipped[slot_name] = Item.from_dict(slot_item_data)
                else:
                    p.equipped[slot_name] = None

        # Restore temporary run relics
        p.relics = []
        for rdata in save_data.get('relics', []):
            p.relics.append(Item.from_dict(rdata))

        # Restore inventory items
        p.inventory = []
        for it in save_data.get('inventory', []):
            p.inventory.append(Item.from_dict(it))

        p.skill_points = save_data.get('skill_points', 0)
        saved_skills = save_data.get('skills')
        if saved_skills and isinstance(saved_skills, dict):
            p.skills.update(saved_skills)
            if hasattr(p, '_apply_skill_perks'):
                p._apply_skill_perks()
        p.bombs = save_data.get('bombs', 0)

        # Restore used altars state
        used_altars = save_data.get('used_altars', [])
        if used_altars and hasattr(self.level, 'altar_sprites'):
            for a in self.level.altar_sprites:
                if [int(a.rect.x), int(a.rect.y)] in used_altars:
                    a.used = True

        p.recalculate_stats()

        try:
            start_bgm()
        except Exception:
            pass
        self.set_state('game')

    def on_resume(self, pause_duration):
        if not hasattr(self, 'level') or not self.level:
            return
        p = getattr(self.level, 'player', None)
        if p:
            if hasattr(p, 'attack_time'): p.attack_time += pause_duration
            if hasattr(p, 'dash_time'): p.dash_time += pause_duration
            if hasattr(p, 'shield_time'): p.shield_time += pause_duration
            if hasattr(p, 'ult_time'): p.ult_time += pause_duration
            if hasattr(p, 'last_regen_tick'): p.last_regen_tick += pause_duration
            if hasattr(p, 'took_damage_time'): p.took_damage_time += pause_duration

        for enemy in getattr(self.level, 'enemy_sprites', []):
            if hasattr(enemy, 'attack_time'):
                enemy.attack_time += pause_duration
            if hasattr(enemy, 'boss_burst_time'):
                enemy.boss_burst_time += pause_duration
            if hasattr(enemy, 'boss_telegraph_start'):
                enemy.boss_telegraph_start += pause_duration
            if hasattr(enemy, 'boss_cleave_timer'):
                enemy.boss_cleave_timer += pause_duration
            if hasattr(enemy, 'boss_dash_time'):
                enemy.boss_dash_time += pause_duration

        for sprite in getattr(self.level, 'visible_sprites', []):
            if hasattr(sprite, 'spawn_time'):
                sprite.spawn_time += pause_duration
        if hasattr(self.level, '_lightning_flash_updated_at'):
            self.level._lightning_flash_updated_at += pause_duration

    def set_state(self, new_state):
        old_state = getattr(self, 'state', None)
        self.state = new_state
        self.ui_buttons = []

        if old_state in ['pause', 'settings_ingame'] and new_state in ['game', 'hub']:
            if hasattr(self, 'pause_start_time') and self.pause_start_time is not None:
                pause_duration = pygame.time.get_ticks() - self.pause_start_time
                self.on_resume(pause_duration)
                self.pause_start_time = None

        if new_state == 'pause':
            if old_state != 'settings_ingame':
                self.pause_start_time = pygame.time.get_ticks()

        btn_w = 290
        btn_h = 46
        sw, sh = self.screen.get_size() if hasattr(self, 'screen') and self.screen else (WIDTH, HEIGHT)
        center_x = sw // 2 - btn_w // 2

        if self.state == 'menu':
            self.menu_show_gear = False
            save_data = load_game_state()
            btn_w = 280
            btn_h = 44
            bx = 160
            y_start = 200 if save_data else 230
            gap = 48

            if save_data:
                saved_fl = save_data.get('floor', 1)
                self.ui_buttons.append(Button(f"Продолжить (Этаж {saved_fl})", (bx, y_start), btn_w, btn_h, self.continue_saved_run))
                y_start += gap

            prof = load_profile()
            unlocked = prof.get('unlocked_chapters', ['catacombs_1'])
            if 'catacombs_2' in unlocked:
                self.ui_buttons.append(Button("Новая Игра: Катакомбы I", (bx, y_start), btn_w, btn_h, lambda: self.start_new_run(chapter='catacombs_1')))
                y_start += gap
                self.ui_buttons.append(Button("Новая Игра: Бездны II", (bx, y_start), btn_w, btn_h, lambda: self.start_new_run(chapter='catacombs_2')))
            else:
                btn_txt = "Новая Игра" if save_data else "Начать Игру"
                self.ui_buttons.append(Button(btn_txt, (bx, y_start), btn_w, btn_h, lambda: self.start_new_run(chapter='catacombs_1')))

            y_start += gap
            self.ui_buttons.append(Button("Снаряжение", (bx, y_start), btn_w, btn_h, self.toggle_menu_gear))
            y_start += gap
            self.ui_buttons.append(Button("Режим разработчика", (bx, y_start), btn_w, btn_h, self.start_dev_room))
            y_start += gap
            self.ui_buttons.append(Button("Настройки", (bx, y_start), btn_w, btn_h, lambda: self.set_state('settings')))
            y_start += gap
            self.ui_buttons.append(Button("Выход", (bx, y_start), btn_w, btn_h, lambda: setattr(self, 'running', False)))

        elif self.state == 'pause':
            def resume_game():
                self.set_state('hub' if getattr(self.level, 'is_hub', False) else 'game')
            def open_settings_ingame(): self.set_state('settings_ingame')
            def save_and_quit():
                save_ok = True
                if hasattr(self, 'level') and hasattr(self.level, 'player'):
                    if not getattr(self.level, 'is_hub', False):
                        save_ok = save_game_state(self.level.current_floor, self.level.player, level=self.level)
                if save_ok:
                    self.set_state('menu')
                else:
                    if hasattr(self, 'ui') and self.ui:
                        self.ui.message = "Ошибка сохранения!" 

            y_start = 240
            gap = 56
            self.ui_buttons.append(Button("Resume", (center_x, y_start), btn_w, btn_h, resume_game))
            self.ui_buttons.append(Button("Settings", (center_x, y_start + gap), btn_w, btn_h, open_settings_ingame))
            self.ui_buttons.append(Button("Save & Main Menu", (center_x, y_start + gap * 2), btn_w, btn_h, save_and_quit))

        elif self.state in ['settings', 'settings_ingame']:
            if not hasattr(self, 'settings_tab') or not self.settings_tab:
                self.settings_tab = 'video'

            def back():
                save_settings(self.settings)
                if self.state == 'settings': self.set_state('menu')
                else: self.set_state('pause')

            def change_master(delta):
                v = round(max(0.0, min(1.0, get_master_volume() + delta)), 1)
                set_master_volume(v)
                self.settings['master_volume'] = v
                save_settings(self.settings)

            def change_sfx(delta):
                v = round(max(0.0, min(1.0, get_sfx_volume() + delta)), 1)
                set_sfx_volume(v)
                self.settings['sfx_volume'] = v
                save_settings(self.settings)

            def change_music(delta):
                v = round(max(0.0, min(1.0, get_music_volume() + delta)), 1)
                set_music_volume(v)
                self.settings['music_volume'] = v
                save_settings(self.settings)

            def change_zoom(delta):
                z = round(max(0.7, min(1.5, self.level.visible_sprites.zoom_level + delta)), 1)
                self.level.visible_sprites.zoom_level = z
                self.settings['zoom'] = z
                save_settings(self.settings)

            def change_hud(delta):
                s = round(max(0.7, min(1.4, self.ui.ui_scale + delta)), 1)
                self.ui.ui_scale = s
                self.settings['hud_scale'] = s
                save_settings(self.settings)

            def toggle_fullscreen():
                self.toggle_fullscreen()
            def reset_save():
                delete_save()
                play_sfx('break')
                self.set_state(self.state)

            card_w = min(960, sw - 40)
            card_h = min(600, sh - 40)
            cx = sw // 2 - card_w // 2
            cy = sh // 2 - card_h // 2
            btn_minus_x = cx + 680
            btn_plus_x = cx + 810
            b_w = 36
            b_h = 32

            # 3 Tab Navigation Header Buttons
            tab_defs = [
                ('video', '1. ВИДЕО И ЭКРАН'),
                ('audio', '2. ЗВУК И МУЗЫКА'),
                ('game', '3. УПРАВЛЕНИЕ')
            ]
            for t_idx, (t_id, t_lbl) in enumerate(tab_defs):
                tx = cx + 285 + t_idx * 205
                ty = cy + 54
                def switch_tab(tab_name):
                    def _cb():
                        self.settings_tab = tab_name
                        self.set_state(self.state)
                    return _cb
                tab_btn = Button(t_lbl, (tx, ty), 195, 34, switch_tab(t_id))
                tab_btn.ui_selected = (self.settings_tab == t_id)
                self.ui_buttons.append(tab_btn)

            # Tab-Specific Controls
            if self.settings_tab == 'video':
                rows_y = [cy + 135, cy + 205, cy + 275]
                # Display Mode Toggle Button
                fs_text = "Полноэкранный" if self.fullscreen else "Оконный (Растягиваемый)"
                self.ui_buttons.append(Button(fs_text, (btn_minus_x, rows_y[0]), 180, b_h, toggle_fullscreen))
                # Zoom
                self.ui_buttons.append(Button("-", (btn_minus_x, rows_y[1]), b_w, b_h, lambda: change_zoom(-0.1)))
                self.ui_buttons.append(Button("+", (btn_plus_x, rows_y[1]), b_w, b_h, lambda: change_zoom(0.1)))
                # HUD Scale
                self.ui_buttons.append(Button("-", (btn_minus_x, rows_y[2]), b_w, b_h, lambda: change_hud(-0.1)))
                self.ui_buttons.append(Button("+", (btn_plus_x, rows_y[2]), b_w, b_h, lambda: change_hud(0.1)))

            elif self.settings_tab == 'audio':
                rows_y = [cy + 135, cy + 205, cy + 275]
                # Master Volume
                self.ui_buttons.append(Button("-", (btn_minus_x, rows_y[0]), b_w, b_h, lambda: change_master(-0.1)))
                self.ui_buttons.append(Button("+", (btn_plus_x, rows_y[0]), b_w, b_h, lambda: change_master(0.1)))
                # SFX Volume
                self.ui_buttons.append(Button("-", (btn_minus_x, rows_y[1]), b_w, b_h, lambda: change_sfx(-0.1)))
                self.ui_buttons.append(Button("+", (btn_plus_x, rows_y[1]), b_w, b_h, lambda: change_sfx(0.1)))
                # Music Volume
                self.ui_buttons.append(Button("-", (btn_minus_x, rows_y[2]), b_w, b_h, lambda: change_music(-0.1)))
                self.ui_buttons.append(Button("+", (btn_plus_x, rows_y[2]), b_w, b_h, lambda: change_music(0.1)))

            elif self.settings_tab == 'game':
                if has_save():
                    self.ui_buttons.append(Button("Удалить сохранение", (cx + 295, cy + 395), 220, b_h, reset_save))

            # Bottom Back Button
            back_btn_w = 240
            back_btn_h = 36
            self.ui_buttons.append(Button("НАЗАД", (cx + card_w - back_btn_w - 30, cy + card_h - 62), back_btn_w, back_btn_h, back))
            for button in self.ui_buttons:
                button.ui_style = 'secondary'

        elif self.state == 'game_over':
            if old_state != 'game_over':
                delete_save()
                try:
                    stop_bgm()
                    play_sfx('game_over')
                except Exception:
                    pass
                p = getattr(self.level, 'player', None) if hasattr(self, 'level') else None
                earned_gold = getattr(p, 'gold', 0) if p else 0
                kills = getattr(p, 'kills', 0) if p else 0
                fl = getattr(self.level, 'current_floor', 1) if hasattr(self, 'level') else 1
                lvl = getattr(p, 'level', 1) if p else 1

                shards_earned = fl * 3 + kills // 4
                prof = load_profile()
                prof['purple_shards'] = prof.get('purple_shards', 0) + shards_earned
                save_profile(prof)

                self.last_run_stats = {
                    'floor': fl,
                    'level': lvl,
                    'gold': earned_gold,
                    'shards_earned': shards_earned,
                    'kills': kills
                }

            btn_w = 280
            btn_h = 44
            center_x = sw // 2 - btn_w // 2
            card_h = 480
            cy = max(20, sh // 2 - card_h // 2)
            self.ui_buttons.append(Button("НАЧАТЬ ЗАНОВО (R)", (center_x, cy + 345), btn_w, btn_h, self.start_new_run))
            self.ui_buttons.append(Button("В ГЛАВНОЕ МЕНЮ (M)", (center_x, cy + 402), btn_w, btn_h, lambda: self.set_state('menu')))

        elif self.state == 'victory':
            if old_state != 'victory':
                clear_run_state()
                try:
                    stop_bgm()
                    play_sfx('chest_open')
                except Exception:
                    pass
                p = getattr(self.level, 'player', None) if hasattr(self, 'level') else None
                earned_gold = getattr(p, 'gold', 0) if p else 0
                kills = getattr(p, 'kills', 0) if p else 0
                lvl = getattr(p, 'level', 1) if p else 1

                shards_reward = 25  # Grand reward for Ascension!
                prof = load_profile()
                prof['permanent_gold'] = prof.get('permanent_gold', 0) + earned_gold
                prof['purple_shards'] = prof.get('purple_shards', 0) + shards_reward
                prof['total_ascensions'] = prof.get('total_ascensions', 0) + 1
                prof['dark_iron'] = prof.get('dark_iron', 0) + 3
                chaps = list(prof.get('unlocked_chapters', ['catacombs_1']))
                if 'catacombs_2' not in chaps:
                    chaps.append('catacombs_2')
                prof['unlocked_chapters'] = chaps
                if p and getattr(p, 'equipped', None):
                    for slot, itm in p.equipped.items():
                        if itm and hasattr(itm, 'to_dict'):
                            prof.setdefault('equipped', {})[slot] = itm.to_dict()
                if p and getattr(p, 'inventory', None):
                    armory = list(prof.get('armory', []))
                    for itm in p.inventory:
                        if itm and getattr(itm, 'slot', '') not in ('consumable', 'potion', 'relic'):
                            if len(armory) < 16:
                                armory.append(itm.to_dict())
                    prof['armory'] = armory
                save_profile(prof)

                self.last_run_stats = {
                'floor': getattr(self.level, 'current_floor', 2),
                'level': lvl,
                'gold': earned_gold,
                'purple_shards_reward': shards_reward,
                'dark_iron_reward': 3,
                'kills': kills,
                'ascension': True
            }

            btn_w = 280
            btn_h = 36
            center_x = sw // 2 - btn_w // 2
            card_h = 490
            cy = max(20, sh // 2 - card_h // 2)
            self.ui_buttons.append(Button("В УБЕЖИЩЕ (H)", (center_x, cy + 325), btn_w, btn_h, self.start_hub))
            self.ui_buttons.append(Button("В ГЛАВНОЕ МЕНЮ (M)", (center_x, cy + 369), btn_w, btn_h, lambda: self.set_state('menu')))
            self.ui_buttons.append(Button("НОВЫЙ ЗАБЕГ (R)", (center_x, cy + 413), btn_w, btn_h, self.start_new_run))

    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                if not getattr(self, 'fullscreen', False):
                    new_w = max(640, event.w)
                    new_h = max(480, event.h)
                    self.window_size = [new_w, new_h]
                    self.settings['window_size'] = self.window_size
                    save_settings(self.settings)
                    self.screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
                    self.on_display_resize()
            elif event.type == pygame.KEYDOWN and (event.key == pygame.K_F11 or (event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT))):
                self.toggle_fullscreen()
                continue

            # The skill tree is a true pause overlay; keep its inputs isolated from gameplay.
            if self.skill_tree_open:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_n):
                    self.close_skill_tree()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.ui.handle_skill_tree_click(event.pos, self.level.player):
                        continue
                    close_rect = self.ui.skill_tree_close_rect
                    panel_rect = self.ui.skill_tree_panel_rect
                    if (close_rect and close_rect.collidepoint(event.pos)) or (panel_rect and not panel_rect.collidepoint(event.pos)):
                        self.close_skill_tree()
                continue

            if self.state in ('game', 'hub') and event.type == pygame.KEYDOWN and event.key == pygame.K_n:
                if not getattr(self.level, 'active_modal', None):
                    self.open_skill_tree()
                    continue

            if self.state in ('game', 'hub') and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                opener = getattr(self.ui, 'skill_tree_open_rect', None)
                if opener and opener.collidepoint(event.pos) and not getattr(self.level, 'active_modal', None):
                    self.open_skill_tree()
                    continue

            # Dev Room Interactive Action Button clicks
            if self.state == 'dev_room':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked_dev_btn = False
                    if hasattr(self, 'dev_button_rects') and self.dev_button_rects:
                        p = self.level.player
                        dw = self.screen.get_width()
                        dh = self.screen.get_height()
                        screen_center = pygame.math.Vector2(dw // 2, dh // 2)
                        aim = (pygame.math.Vector2(event.pos) - screen_center)
                        aim = aim.normalize() if aim.magnitude() > 0 else (pygame.math.Vector2(-1, 0) if getattr(p, 'facing_left', False) else pygame.math.Vector2(1, 0))

                        for r, act_id in self.dev_button_rects:
                            if r.collidepoint(event.pos):
                                clicked_dev_btn = True
                                if act_id == 'w_next': p.cycle_dev_weapon()
                                elif act_id == 'dash_style': p.cycle_dash_trail()
                                elif act_id == 'black_hole': p.cast_dev_projectile('black_hole', aim, "Сингулярность «Чёрная дыра»")
                                elif act_id == 'fireball': p.cast_dev_projectile('fireball', aim, "Огненный Шар")
                                elif act_id == 'frost_shard': p.cast_dev_projectile('frost_shard', aim, "Ледяной Осколок")
                                elif act_id == 'void_orb': p.cast_dev_projectile('void_orb', aim, "Сфера Бездны")
                                elif act_id == 'boss_cleave': p.trigger_dev_boss_cleave(aim)
                                elif act_id == 'spore': p.trigger_dev_spore_explosion()
                                elif act_id == 'level_up': p.trigger_level_up_vfx()
                                elif act_id == 'crit': p.trigger_dev_crit_pop()
                                elif act_id == 'ult': p.ult()
                                elif act_id == 'skin': p.cycle_skin()
                                break
                    if clicked_dev_btn:
                        continue

            # Skill upgrade [+] clicks on HUD
            if self.state in ['game', 'hub']:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if hasattr(self, 'ui') and hasattr(self.ui, 'handle_skill_click') and hasattr(self, 'level') and hasattr(self.level, 'player'):
                        if self.ui.handle_skill_click(event.pos, self.level.player):
                            continue

            # Left Click on Potions in Top Inventory Bar (U05: blocked when modal is active)
            if self.state in ['game', 'hub']:
                if not getattr(self.level, 'active_modal', None):
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if hasattr(self.ui, 'inv_slot_rects'):
                            for slot_rect, item in self.ui.inv_slot_rects:
                                if slot_rect.collidepoint(event.pos):
                                    if hasattr(item, 'effects') and 'heal' in item.effects or 'potion' in getattr(item, 'name', '').lower():
                                        self.level.player.use_potion()
                                        break

            # Active RPG Modal mouse click handling
            if self.state in ['game', 'hub']:
                if hasattr(self, 'level') and getattr(self.level, 'active_modal', None) and self.level.modal_instance:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.level.modal_instance.handle_event(event)

            # Menu gear inspection click handling
            if self.state == 'menu':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.menu_show_gear:
                        sw, sh = self.screen.get_size()
                        gw, gh = 860, 560
                        gx, gy = (sw - gw) // 2, (sh - gh) // 2
                        modal_rect = pygame.Rect(gx, gy, gw, gh)
                        r_close = pygame.Rect(sw // 2 - 70, gy + gh - 42, 140, 32)
                        if r_close.collidepoint(event.pos) or not modal_rect.collidepoint(event.pos):
                            self.menu_show_gear = False
                            continue
                    else:
                        if self.menu_hero_rect.collidepoint(event.pos):
                            self.toggle_menu_gear()
                            continue

            # Button click handling
            if self.state in ['menu', 'settings', 'settings_ingame', 'pause', 'game_over', 'victory']:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn in self.ui_buttons:
                        if btn.hovered:
                            try:
                                play_sfx('sword_swing')
                            except Exception:
                                pass
                            if btn.callback:
                                btn.callback()
                            break

            if event.type == pygame.KEYDOWN:
                if self.state == 'menu':
                    if self.menu_show_gear:
                        if event.key in [pygame.K_ESCAPE, pygame.K_i, pygame.K_RETURN]:
                            self.menu_show_gear = False
                    else:
                        if event.key == pygame.K_RETURN:
                            if has_save(): self.continue_saved_run()
                            else: self.start_new_run()
                        elif event.key == pygame.K_i:
                            self.toggle_menu_gear()
                        elif event.key == pygame.K_s:
                            self.set_state('settings')
                        elif event.key == pygame.K_ESCAPE:
                            self.running = False
                elif self.state in ['settings', 'settings_ingame']:
                    if event.key in [pygame.K_ESCAPE, pygame.K_b]:
                        save_settings(self.settings)
                        if self.state == 'settings': self.set_state('menu')
                        else: self.set_state('pause')
                elif self.state in ['game', 'hub', 'dev_room']:
                    if hasattr(self, 'level') and getattr(self.level, 'active_modal', None) and self.level.modal_instance:
                        if self.level.modal_instance.handle_event(event):
                            continue
                    if event.key in [pygame.K_i, pygame.K_TAB]:
                        if hasattr(self, 'level'):
                            new_m = 'equipment' if self.level.active_modal != 'equipment' else None
                            self.level.open_modal(new_m)
                    elif event.key == pygame.K_ESCAPE:
                        if hasattr(self, 'level') and getattr(self.level, 'active_modal', None):
                            if hasattr(self.level, 'close_modal'):
                                self.level.close_modal()
                            else:
                                self.level.active_modal = None
                        elif self.state == 'dev_room':
                            self.set_state('menu')
                        else:
                            self.set_state('pause')
                    elif event.key == pygame.K_F3:
                        self.ui.show_debug = not self.ui.show_debug
                elif self.state == 'pause':
                    if event.key == pygame.K_ESCAPE:
                        self.set_state('hub' if getattr(self.level, 'is_hub', False) else 'game')
                elif self.state == 'game_over':
                    if event.key in [pygame.K_RETURN, pygame.K_r]:
                        self.start_new_run()
                    elif event.key in [pygame.K_ESCAPE, pygame.K_m]:
                        self.set_state('menu')
                elif self.state == 'victory':
                    if event.key in [pygame.K_RETURN, pygame.K_r]:
                        self.start_new_run()
                    elif event.key in [pygame.K_ESCAPE, pygame.K_m]:
                        self.set_state('menu')
                    elif event.key in [pygame.K_h]:
                        self.start_hub()

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.skill_tree_open:
            return
        if self.state == 'menu':
            for ember in self.menu_embers:
                ember.update()
            for mist in self.menu_mists:
                mist.update()
            self.menu_hero_hover = self.menu_hero_rect.collidepoint(mouse_pos)
            for btn in self.ui_buttons:
                btn.check_hover(mouse_pos)

        elif self.state in ['settings', 'settings_ingame', 'pause', 'game_over', 'victory']:
            for btn in self.ui_buttons:
                btn.check_hover(mouse_pos)

        elif self.state in ['game', 'hub', 'dev_room']:
            self.level.update()
            if self.state == 'dev_room':
                if getattr(self.level, 'dev_exit_portal', None):
                    p_rect = self.level.player.rect
                    if self.level.dev_exit_portal.rect.colliderect(p_rect):
                        self.set_state('menu')
            else:
                if getattr(self.level, 'start_catacombs_run', False):
                    self.start_dungeon_run()
                elif getattr(self.level, 'chapter_victory', False):
                    self.set_state('victory')
                elif getattr(self.level, 'game_over', False):
                    self.set_state('game_over')

    def draw(self):
        sw, sh = self.screen.get_size()
        now = pygame.time.get_ticks()

        if self.state == 'menu':
            # 1. Base dark fantasy background image (scaled to current resolution)
            if getattr(self, 'menu_bg_scaled', None):
                self.screen.blit(self.menu_bg_scaled, (0, 0))
            elif getattr(self, 'menu_bg', None):
                self.screen.blit(self.menu_bg, (0, 0))
            else:
                self.screen.fill((16, 14, 22))

            # 2. Atmospheric multi-layer particles (embers and fog)

            # 2.5 Architecture pillars have torch sconces built-in; no flat yellow circles!

            # 3. Rolling Floor Mists
            for mist in self.menu_mists:
                mist.draw(self.screen)

            # 4. Rising Torch Embers
            for ember in self.menu_embers:
                ember.draw(self.screen)

            # 5. Pre-rendered High-Res Dark Fantasy Title Logo
            if getattr(self, 'title_logo', None):
                t_y = 75 + int(3 * math.sin(now * 0.003))
                tx = sw // 2 - self.title_logo.get_width() // 2
                self.screen.blit(self.title_logo, (tx, t_y))
            else:
                title_font = get_pixel_font(28, bold=True)
                t_text = "ROGUE 2D"
                t_y = 90
                tx = sw // 2 - title_font.size(t_text)[0] // 2
                self.screen.blit(title_font.render(t_text, True, (255, 215, 60)), (tx, t_y))

            # 6. Draw Buttons
            for btn in self.ui_buttons:
                btn.draw(self.screen)

            # 7. Right-side Interactive Hero Pedestal
            hr = self.menu_hero_rect
            ped_bg = pygame.Surface((hr.width, hr.height), pygame.SRCALPHA)
            ped_bg.fill((20, 16, 28, 225))
            self.screen.blit(ped_bg, (hr.x, hr.y))

            border_col = (255, 215, 60) if self.menu_hero_hover else (130, 105, 70)
            pygame.draw.rect(self.screen, border_col, hr, 2)
            pygame.draw.rect(self.screen, (50, 40, 60), (hr.x + 3, hr.y + 3, hr.width - 6, hr.height - 6), 1)

            # Rivets
            for cx, cy in [(hr.left, hr.top), (hr.right - 8, hr.top), (hr.left, hr.bottom - 8), (hr.right - 8, hr.bottom - 8)]:
                pygame.draw.rect(self.screen, (255, 215, 60), (cx, cy, 8, 8))

            # Header
            h_font = get_pixel_font(16, bold=True)
            h_title = h_font.render("ВАШ ГЕРОЙ", True, (255, 215, 80))
            self.screen.blit(h_title, (hr.centerx - h_title.get_width() // 2, hr.y + 14))
            pygame.draw.line(self.screen, (100, 80, 50), (hr.x + 20, hr.y + 40), (hr.right - 20, hr.y + 40), 1)

            # Multi-tier carved gothic stone dais/pedestal
            # Lower tier base
            pygame.draw.rect(self.screen, (24, 20, 32), (hr.centerx - 65, hr.y + 172, 130, 16), border_radius=3)
            pygame.draw.rect(self.screen, (60, 50, 75), (hr.centerx - 65, hr.y + 172, 130, 16), 1, border_radius=3)
            # Upper tier step
            pygame.draw.rect(self.screen, (34, 28, 44), (hr.centerx - 52, hr.y + 162, 104, 12), border_radius=2)
            pygame.draw.rect(self.screen, (170, 140, 65), (hr.centerx - 52, hr.y + 162, 104, 12), 1, border_radius=2)
            # Runic highlight line
            pygame.draw.line(self.screen, (255, 215, 70), (hr.centerx - 48, hr.y + 162), (hr.centerx + 48, hr.y + 162), 1)
            # Soft shadow ellipse on top step
            pygame.draw.ellipse(self.screen, (14, 10, 20), (hr.centerx - 38, hr.y + 160, 76, 10))

            # Floating ambient motes around hero
            for i in range(5):
                angle = (now * 0.002 + i * 1.25) % (math.pi * 2)
                rad_x = 42 + (i % 2) * 12
                rad_y = 30 + (i % 3) * 8
                mx = int(hr.centerx + math.cos(angle) * rad_x)
                my = int(hr.y + 125 + math.sin(angle) * rad_y)
                mote_col = (215, 140, 255) if i % 2 == 0 else (255, 215, 80)
                pygame.draw.circle(self.screen, mote_col, (mx, my), 2 if i % 2 == 0 else 1)

            # Player sprite with idle bobbing
            bob = int(2.5 * math.sin(now * 0.003))
            p_surf = None
            if self.menu_player_frames:
                frame_idx = (now // 200) % len(self.menu_player_frames)
                p_surf = self.menu_player_frames[frame_idx]
            else:
                try:
                    p_surf = load_image('assets/sprites/player.png', scale=(80, 80))
                except Exception:
                    pass

            if p_surf:
                self.screen.blit(p_surf, (hr.centerx - p_surf.get_width() // 2, hr.y + 85 + bob))

            # Profile Info
            prof = load_profile()
            sub_font = get_pixel_font(12, bold=True)
            tiny_font = get_pixel_font(11, bold=False)

            wpn_info = prof.get('equipped', {}).get('weapon')
            wpn_name = wpn_info.get('name', 'Рыцарский Меч') if wpn_info else 'Кулаки'
            w_surf = sub_font.render(f"Оружие: {wpn_name[:18]}", True, (240, 235, 250))
            self.screen.blit(w_surf, (hr.centerx - w_surf.get_width() // 2, hr.y + 200))

            # Gold chip
            gold_str = f"Золото: {prof.get('permanent_gold', 0)} G"
            g_surf = sub_font.render(gold_str, True, (255, 225, 90))
            self.screen.blit(g_surf, (hr.centerx - g_surf.get_width() // 2, hr.y + 230))

            # Purple Shards chip (Фиолетовые осколки)
            shards_str = f"Осколки: {prof.get('purple_shards', 0)}"
            sh_surf = sub_font.render(shards_str, True, (220, 130, 255))
            self.screen.blit(sh_surf, (hr.centerx - sh_surf.get_width() // 2, hr.y + 260))

            # Total Ascensions (Вознесения)
            asc_count = prof.get('total_ascensions', 0)
            if asc_count > 0:
                asc_str = f"Вознесений: {asc_count}"
                a_surf = tiny_font.render(asc_str, True, (130, 225, 255))
                self.screen.blit(a_surf, (hr.centerx - a_surf.get_width() // 2, hr.y + 290))

            # Prompt / Hover
            prompt_col = (255, 230, 100) if self.menu_hero_hover else (170, 160, 185)
            pr_surf = tiny_font.render("[ Кликните для осмотра ]", True, prompt_col)
            self.screen.blit(pr_surf, (hr.centerx - pr_surf.get_width() // 2, hr.bottom - 32))

            # 8. Equipment Inspection Overlay in Menu
            if self.menu_show_gear:
                overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
                overlay.fill((8, 6, 12, 235))
                self.screen.blit(overlay, (0, 0))

                gw, gh = 860, 560
                gx, gy = (sw - gw) // 2, (sh - gh) // 2
                pygame.draw.rect(self.screen, (20, 18, 28), (gx, gy, gw, gh))
                pygame.draw.rect(self.screen, (34, 30, 46), (gx + 3, gy + 3, gw - 6, gh - 6))
                pygame.draw.rect(self.screen, (190, 145, 65), (gx, gy, gw, gh), 2)

                # Corner gold brackets
                for cx_c, cy_c in [(gx, gy), (gx + gw - 8, gy), (gx, gy + gh - 8), (gx + gw - 8, gy + gh - 8)]:
                    pygame.draw.rect(self.screen, (255, 215, 60), (cx_c, cy_c, 8, 8))

                m_title = get_pixel_font(20, bold=True).render("ВАШЕ СНАРЯЖЕНИЕ (6 СЛОТОВ)", True, (255, 215, 60))
                self.screen.blit(m_title, (sw // 2 - m_title.get_width() // 2, gy + 14))

                slot_keys = [
                    ('weapon', 'Оружие'),
                    ('offhand', 'Вторая рука'),
                    ('armor', 'Броня'),
                    ('boots', 'Сапоги'),
                    ('amulet', 'Амулет'),
                    ('ring', 'Кольцо')
                ]
                cw, ch = 264, 180
                total_stats = {'atk': 10, 'defense': 5, 'hp': 100, 'crit_rate': 5, 'crit_dmg': 50}
                for s_i, (sk, s_label) in enumerate(slot_keys):
                    col = s_i % 3
                    row = s_i // 3
                    cx_slot = gx + 24 + col * (cw + 16)
                    cy_slot = gy + 46 + row * (ch + 10)

                    raw_item = prof.get('equipped', {}).get(sk)
                    if raw_item:
                        from src.items import Item
                        itm = Item.from_dict(raw_item)
                        lvl = getattr(itm, 'upgrade_level', 0)

                        if lvl >= 5:
                            border_col = (255, 215, 60)
                            box_bg = (32, 26, 42)
                        elif lvl >= 3:
                            border_col = (60, 200, 255)
                            box_bg = (26, 24, 38)
                        elif lvl >= 1:
                            border_col = (80, 220, 120)
                            box_bg = (24, 22, 34)
                        else:
                            border_col = (100, 90, 120)
                            box_bg = (22, 20, 30)

                        pygame.draw.rect(self.screen, box_bg, (cx_slot, cy_slot, cw, ch))
                        pygame.draw.rect(self.screen, border_col, (cx_slot, cy_slot, cw, ch), 1)

                        # Socket frame for item icon
                        sock_r = pygame.Rect(cx_slot + 8, cy_slot + 8, 42, 42)
                        pygame.draw.rect(self.screen, (16, 14, 22), sock_r)
                        pygame.draw.rect(self.screen, border_col, sock_r, 1)

                        try:
                            ic = load_image(itm.image_path, scale=(36, 36))
                            self.screen.blit(ic, (sock_r.x + 3, sock_r.y + 3))
                        except Exception:
                            pass

                        n_surf = get_pixel_font(12, bold=True).render(f"{itm.name[:16]}", True, border_col)
                        self.screen.blit(n_surf, (cx_slot + 56, cy_slot + 10))

                        lvl_surf = get_pixel_font(10, bold=False).render(f"LVL +{lvl} ({s_label})", True, (180, 210, 240))
                        self.screen.blit(lvl_surf, (cx_slot + 56, cy_slot + 28))

                        # Divider
                        pygame.draw.line(self.screen, (50, 45, 65), (cx_slot + 8, cy_slot + 54), (cx_slot + cw - 8, cy_slot + 54), 1)

                        # Main stat
                        m_stat = getattr(itm, 'main_stat', None) or {'label': 'Атака', 'value': 8}
                        m_lbl = m_stat.get('label', 'Атака')
                        m_val = m_stat.get('value', 0)
                        m_txt = f"{m_lbl}: +{m_val}"
                        m_surf = get_pixel_font(11, bold=True).render(m_txt, True, (120, 245, 160))
                        self.screen.blit(m_surf, (cx_slot + 10, cy_slot + 60))

                        # Aggregate into total stats for summary
                        stat_lbl = str(m_lbl).lower()
                        if 'атак' in stat_lbl or 'урон' in stat_lbl: total_stats['atk'] += m_val
                        elif 'защит' in stat_lbl or 'брон' in stat_lbl: total_stats['defense'] += m_val
                        elif 'здоров' in stat_lbl or 'хп' in stat_lbl: total_stats['hp'] += m_val

                        # 4 Sub-stats with Gold Stars
                        substats_list = getattr(itm, 'substats', []) or []
                        for sub_idx, sub in enumerate(substats_list[:4]):
                            if not isinstance(sub, dict):
                                continue
                            sy = cy_slot + 82 + sub_idx * 22
                            s_val = sub.get('value', 0)
                            s_val_str = f"+{s_val}%" if sub.get('is_percent') else f"+{s_val}"
                            s_rolls = sub.get('rolls', 0)
                            star_badge = f" [+ x{s_rolls}]" if s_rolls > 0 else ""
                            sub_txt = f"- {sub.get('label', '')}: {s_val_str}{star_badge}"
                            sub_col = (255, 220, 90) if s_rolls > 0 else (195, 190, 210)
                            sub_s = get_pixel_font(10, bold=(s_rolls > 0)).render(sub_txt, True, sub_col)
                            self.screen.blit(sub_s, (cx_slot + 10, sy))

                            # Aggregate substat
                            s_lbl = str(sub.get('label', '')).lower()
                            if 'крит. шанс' in s_lbl: total_stats['crit_rate'] += s_val
                            elif 'крит. урон' in s_lbl: total_stats['crit_dmg'] += s_val
                            elif 'атак' in s_lbl: total_stats['atk'] += s_val
                            elif 'защит' in s_lbl: total_stats['defense'] += s_val
                            elif 'здоров' in s_lbl: total_stats['hp'] += s_val
                    else:
                        pygame.draw.rect(self.screen, (22, 18, 28), (cx_slot, cy_slot, cw, ch))
                        pygame.draw.rect(self.screen, (55, 45, 68), (cx_slot, cy_slot, cw, ch), 1)
                        empty_surf = get_pixel_font(12, bold=True).render(f"[ {s_label}: Пусто ]", True, (130, 120, 140))
                        self.screen.blit(empty_surf, (cx_slot + cw // 2 - empty_surf.get_width() // 2, cy_slot + ch // 2 - 10))

                # Aggregate Character Stats Bar at bottom
                sb_y = gy + gh - 82
                sb_w = gw - 48
                pygame.draw.rect(self.screen, (16, 14, 24), (gx + 24, sb_y, sb_w, 32))
                pygame.draw.rect(self.screen, (160, 130, 60), (gx + 24, sb_y, sb_w, 32), 1)

                shards_cnt = prof.get('purple_shards', 0)
                asc_cnt = prof.get('total_ascensions', 0)
                stat_bar_str = (f"УРОН: {total_stats['atk']}   БРОНЯ: {total_stats['defense']}   "
                                f"HP: {total_stats['hp']}   КРИТ: {total_stats['crit_rate']}%   "
                                f"ОСКОЛКИ: {shards_cnt}   ВОЗНЕСЕНИЙ: {asc_cnt}")
                sb_txt = get_pixel_font(11, bold=True).render(stat_bar_str, True, (240, 230, 255))
                self.screen.blit(sb_txt, (sw // 2 - sb_txt.get_width() // 2, sb_y + 8))

                # Close Button
                r_close = pygame.Rect(sw // 2 - 70, gy + gh - 42, 140, 32)
                pygame.draw.rect(self.screen, (45, 38, 55), r_close)
                pygame.draw.rect(self.screen, (200, 160, 70), r_close, 1)
                cl_txt = get_pixel_font(12, bold=True).render("ЗАКРЫТЬ (ESC)", True, (255, 230, 100))
                self.screen.blit(cl_txt, (r_close.centerx - cl_txt.get_width() // 2, r_close.centery - cl_txt.get_height() // 2))

            # Footer credits
            footer_font = get_pixel_font(10, bold=False)
            footer_txt = footer_font.render("Rogue 2D v8.4 | Permadeath - Procedural Dungeons - Action RPG", True, (125, 120, 140))
            self.screen.blit(footer_txt, (sw // 2 - footer_txt.get_width() // 2, sh - 24))

        elif self.state in ['settings', 'settings_ingame']:
            if getattr(self, 'menu_bg_scaled', None):
                self.screen.blit(self.menu_bg_scaled, (0, 0))
            elif getattr(self, 'menu_bg', None):
                self.screen.blit(self.menu_bg, (0, 0))
            else:
                self.screen.fill((16, 14, 22))

            card_w = min(960, sw - 40)
            card_h = min(600, sh - 40)
            cx = sw // 2 - card_w // 2
            cy = sh // 2 - card_h // 2

            cur_tab = getattr(self, 'settings_tab', 'video')
            tab_titles = {
                'video': ('НАСТРОЙКИ', 'Видео и экран'),
                'audio': ('НАСТРОЙКИ', 'Звук и музыка'),
                'game': ('НАСТРОЙКИ', 'Игра и управление')
            }
            main_title, sub_title = tab_titles.get(cur_tab, ('НАСТРОЙКИ', 'Параметры'))
            draw_workbench(self.screen, pygame.Rect(cx, cy, card_w, card_h),
                           main_title, sub_title, (162, 125, 80))
            pygame.draw.rect(self.screen, (25, 23, 28), (cx + 9, cy + 84, 250, card_h - 93))
            pygame.draw.line(self.screen, (83, 67, 57), (cx + 259, cy + 100), (cx + 259, cy + 565))

            # Left Sidebar Info
            service_label(self.screen, "ГОТИЧЕСКИЙ РОГАЛИК", (cx + 32, cy + 121), (197, 153, 99), 14)
            if cur_tab == 'video':
                service_label(self.screen, "Видеорежим и масштаб", (cx + 32, cy + 158), (219, 207, 191), 16)
                service_label(self.screen, "Полноэкранный F11 и зум.", (cx + 32, cy + 181), (164, 151, 141), 14, False)
                emblem_name = 'assets/sprites/item_shield.png'
            elif cur_tab == 'audio':
                service_label(self.screen, "Акустика и эмбиент", (cx + 32, cy + 158), (219, 207, 191), 16)
                service_label(self.screen, "Настройка SFX и музыки.", (cx + 32, cy + 181), (164, 151, 141), 14, False)
                emblem_name = 'assets/sprites/item_warhammer.png'
            else:
                service_label(self.screen, "Управление рыцарем", (cx + 32, cy + 158), (219, 207, 191), 16)
                service_label(self.screen, "Клавиатура и мышь.", (cx + 32, cy + 181), (164, 151, 141), 14, False)
                emblem_name = 'assets/sprites/item_sword.png'

            try:
                emblem = load_image(emblem_name, scale=(112, 112))
                self.screen.blit(emblem, (cx + 72, cy + 250))
            except Exception:
                pass

            service_label(self.screen, "ESC  /  НАЗАД", (cx + 32, cy + 552), (149, 137, 127), 12)
            row_font = get_pixel_font(15, bold=True)

            if cur_tab == 'video':
                service_label(self.screen, "ПАРАМЕТРЫ ЭКРАНА И КАМЕРЫ", (cx + 295, cy + 106), (190, 148, 99), 13)
                service_label(self.screen, "[F11] — Быстрое переключение полный экран / окно", (cx + 295, cy + 370), (170, 160, 150), 12)
                v_labels = [
                    ("Режим экрана", ""),
                    ("Масштаб камеры", f"{self.level.visible_sprites.zoom_level:.1f}x"),
                    ("Масштаб интерфейса", f"{self.ui.ui_scale:.1f}x")
                ]
                rows_y = [cy + 135, cy + 205, cy + 275]
                for idx, (label, val_str) in enumerate(v_labels):
                    ry = rows_y[idx]
                    pygame.draw.line(self.screen, (60, 53, 51), (cx + 295, ry + 43), (cx + 895, ry + 43))
                    lbl_surf = row_font.render(label, True, (235, 226, 218))
                    self.screen.blit(lbl_surf, (cx + 295, ry + 6))
                    if idx > 0:
                        v_surf = row_font.render(val_str, True, (255, 215, 60))
                        vx = cx + 745 - v_surf.get_width() // 2
                        self.screen.blit(v_surf, (vx, ry + 6))
                        val_pct = (self.level.visible_sprites.zoom_level - .7) / .8 if idx == 1 else (self.ui.ui_scale - .7) / .7
                        fraction = max(0.0, min(1.0, val_pct))
                        pygame.draw.rect(self.screen, (67, 57, 51), (cx + 726, ry + 29, 38, 2))
                        pygame.draw.rect(self.screen, (211, 164, 94), (cx + 726, ry + 29, int(38 * fraction), 2))

            elif cur_tab == 'audio':
                service_label(self.screen, "РЕГУЛИРОВКА ГРОМКОСТИ", (cx + 295, cy + 106), (190, 148, 99), 13)
                a_labels = [
                    ("Общая громкость", f"{int(get_master_volume() * 100)}%"),
                    ("Звуковые эффекты", f"{int(get_sfx_volume() * 100)}%"),
                    ("Музыкальное сопровождение", f"{int(get_music_volume() * 100)}%")
                ]
                rows_y = [cy + 135, cy + 205, cy + 275]
                a_vals = [get_master_volume(), get_sfx_volume(), get_music_volume()]
                for idx, (label, val_str) in enumerate(a_labels):
                    ry = rows_y[idx]
                    pygame.draw.line(self.screen, (60, 53, 51), (cx + 295, ry + 43), (cx + 895, ry + 43))
                    lbl_surf = row_font.render(label, True, (235, 226, 218))
                    self.screen.blit(lbl_surf, (cx + 295, ry + 6))
                    v_surf = row_font.render(val_str, True, (255, 215, 60))
                    vx = cx + 745 - v_surf.get_width() // 2
                    self.screen.blit(v_surf, (vx, ry + 6))
                    fraction = max(0.0, min(1.0, a_vals[idx]))
                    pygame.draw.rect(self.screen, (67, 57, 51), (cx + 726, ry + 29, 38, 2))
                    pygame.draw.rect(self.screen, (211, 164, 94), (cx + 726, ry + 29, int(38 * fraction), 2))

            elif cur_tab == 'game':
                service_label(self.screen, "НАЗНАЧЕНИЕ КЛАВИШ И УПРАВЛЕНИЕ", (cx + 295, cy + 106), (190, 148, 99), 13)
                guide_items = [
                    ("[W, A, S, D] / Стрелки", "Перемещение персонажа"),
                    ("[ЛКМ] / Клавиша [J]", "Атака оружием / комбо-удары"),
                    ("[ПРОБЕЛ] / Клавиша [K]", "Рывок (Dash) с неуязвимостью"),
                    ("[E]", "Взаимодействие (Наковальня, Сундуки, Порталы)"),
                    ("[I] / [TAB] / [C]", "Кукла снаряжения и инвентарь"),
                    ("[P]", "Смена облика / скина героя"),
                    ("[F11]", "Полный экран / Окно")
                ]
                for idx, (k_bind, k_desc) in enumerate(guide_items):
                    gy = cy + 132 + idx * 34
                    pygame.draw.line(self.screen, (45, 40, 50), (cx + 295, gy + 28), (cx + 895, gy + 28))
                    k_surf = row_font.render(k_bind, True, (255, 215, 60))
                    d_surf = self.ui.font_sm.render(k_desc, True, (215, 210, 225)) if hasattr(self.ui, 'font_sm') else row_font.render(k_desc, True, (215, 210, 225))
                    self.screen.blit(k_surf, (cx + 295, gy + 4))
                    self.screen.blit(d_surf, (cx + 560, gy + 6))

            for btn in self.ui_buttons:
                btn.draw(self.screen)

        elif self.state in ['game', 'hub', 'dev_room']:
            self.level.draw()
            self.ui.draw(self.level.player, self.level)
            if getattr(self.level, 'active_modal', None) and getattr(self.level, 'modal_instance', None):
                self.level.modal_instance.draw(self.screen)
            if self.skill_tree_open and self.state in ('game', 'hub'):
                self.ui.draw_skill_tree(self.screen, self.level.player)
            if self.state == 'dev_room':
                banner_w, banner_h = min(960, sw - 20), 58
                bx = (sw - banner_w) // 2
                by = 8
                b_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
                b_surf.fill((14, 10, 22, 240))
                pygame.draw.rect(b_surf, (255, 215, 60), [0, 0, banner_w, banner_h], 1, border_radius=6)
                self.screen.blit(b_surf, (bx, by))

                guide_font = get_pixel_font(12, bold=True)
                btn_font = get_pixel_font(10, bold=True)

                w_item = getattr(self.level.player, 'equipped', {}).get('weapon')
                w_name = getattr(w_item, 'name', 'Клинок Паладина')
                r1_txt = f"[WASD] Движение [2x СКОРОСТЬ] | Оружие [1-6/G]: {w_name} | [ЛКМ] Атака | [ПРОБЕЛ] Рывок | [ESC] Меню"
                r1_s = guide_font.render(r1_txt, True, (255, 235, 120))
                self.screen.blit(r1_s, (bx + (banner_w - r1_s.get_width()) // 2, by + 5))

                dev_actions = [
                    ('w_next', '[1-6/G] Оружие', (255, 220, 80)),
                    ('dash_style', '[O] След рывка', (180, 220, 255)),
                    ('black_hole', '[B] Чёрная дыра', (195, 70, 255)),
                    ('fireball', '[F] Огонь', (255, 120, 40)),
                    ('frost_shard', '[R] Лёд', (100, 220, 255)),
                    ('void_orb', '[V] Сфера Босса', (190, 70, 255)),
                    ('boss_cleave', '[T] Удар Босса', (255, 100, 60)),
                    ('spore', '[Y] Взрыв Спор (1-3)', (90, 230, 90)),
                    ('crit', '[K] Крит', (255, 215, 60)),
                    ('ult', '[J] Нова Бездны', (220, 80, 255)),
                    ('level_up', '[L] Level-Up', (255, 245, 180)),
                    ('skin', '[P] Скин', (225, 205, 255)),
                ]

                mouse_pos = pygame.mouse.get_pos()
                self.dev_button_rects = []
                num_btns = len(dev_actions)
                gap = 5
                btn_w = max(60, (banner_w - 20 - gap * (num_btns - 1)) // num_btns)
                btn_h = 22
                start_x = bx + (banner_w - (num_btns * btn_w + (num_btns - 1) * gap)) // 2
                btn_y = by + 28

                for idx, (act_id, label, col) in enumerate(dev_actions):
                    cur_x = start_x + idx * (btn_w + gap)
                    r = pygame.Rect(cur_x, btn_y, btn_w, btn_h)
                    self.dev_button_rects.append((r, act_id))
                    is_h = r.collidepoint(mouse_pos)
                    b_box = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
                    b_box.fill((45, 30, 65, 240) if is_h else (22, 16, 32, 220))
                    border_c = (255, 255, 255) if is_h else col
                    pygame.draw.rect(b_box, border_c, [0, 0, btn_w, btn_h], 1, border_radius=4)
                    t_s = btn_font.render(label, True, (255, 255, 255) if is_h else col)
                    b_box.blit(t_s, ((btn_w - t_s.get_width()) // 2, (btn_h - t_s.get_height()) // 2))
                    self.screen.blit(b_box, (cur_x, btn_y))

        elif self.state == 'pause':
            self.level.draw()
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((8, 6, 12, 190))
            self.screen.blit(overlay, (0, 0))

            p_font = get_pixel_font(24, bold=True)
            pause_txt = p_font.render("GAME PAUSED", True, (255, 215, 60))
            self.screen.blit(pause_txt, (sw // 2 - pause_txt.get_width() // 2, max(40, sh // 2 - 160)))

            for btn in self.ui_buttons:
                btn.draw(self.screen)
            self.ui.draw(self.level.player, self.level)

        elif self.state == 'game_over':
            self.level.draw()
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((16, 6, 10, 220))
            self.screen.blit(overlay, (0, 0))

            card_w, card_h = 520, 480
            cx, cy = sw // 2 - card_w // 2, max(20, sh // 2 - card_h // 2)
            card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            card.fill((14, 10, 18, 248))
            self.screen.blit(card, (cx, cy))
            pygame.draw.rect(self.screen, (180, 40, 50), (cx, cy, card_w, card_h), 2)
            pygame.draw.rect(self.screen, (220, 180, 70), (cx + 4, cy + 4, card_w - 8, card_h - 8), 1)

            # 4 Gothic corner brackets
            for kx, ky in [(cx, cy), (cx + card_w - 10, cy), (cx, cy + card_h - 10), (cx + card_w - 10, cy + card_h - 10)]:
                pygame.draw.rect(self.screen, (235, 195, 55), (kx, ky, 10, 10))
                pygame.draw.rect(self.screen, (30, 20, 15), (kx + 2, ky + 2, 6, 6))

            # Title banner: Pre-rendered high-res gothic banner (No raw fonts / slop text!)
            if getattr(self, 'game_over_banner', None):
                banner_x = sw // 2 - self.game_over_banner.get_width() // 2
                self.screen.blit(self.game_over_banner, (banner_x, cy + 18))
            else:
                font_title = get_pixel_font(26, bold=True)
                title_text = "ПАВШИЙ В БЕЗДНЕ"
                tx = sw // 2 - font_title.size(title_text)[0] // 2
                self.screen.blit(font_title.render(title_text, True, (230, 40, 50)), (tx, cy + 22))

            font_stats = get_pixel_font(13, bold=True)
            stats = self.last_run_stats
            rows = [
                ("Достигнутый этаж", f"ЭТАЖ {stats.get('floor', 1)}", (255, 255, 255)),
                ("Уровень героя", f"LVL {stats.get('level', 1)}", (160, 210, 255)),
                ("Награбленное золото", f"{stats.get('gold', 0)} G", (255, 215, 60)),
                ("Фиолетовые осколки", f"+{stats.get('shards_earned', 0)} Оск.", (220, 130, 255)),
                ("Сражено чудовищ", f"{stats.get('kills', 0)}", (245, 120, 120))
            ]

            start_sy = cy + 105
            for idx, (label, val, val_col) in enumerate(rows):
                ry = start_sy + idx * 36
                # Subtle pill row background
                row_surf = pygame.Surface((card_w - 60, 30), pygame.SRCALPHA)
                row_surf.fill((22, 18, 30, 160))
                self.screen.blit(row_surf, (cx + 30, ry - 4))
                pygame.draw.rect(self.screen, (55, 45, 65), (cx + 30, ry - 4, card_w - 60, 30), 1)

                lbl_surf = font_stats.render(label, True, (200, 205, 225))
                self.screen.blit(lbl_surf, (cx + 45, ry + 2))
                val_surf = font_stats.render(val, True, val_col)
                self.screen.blit(val_surf, (cx + card_w - 45 - val_surf.get_width(), ry + 2))

            for btn in self.ui_buttons:
                btn.draw(self.screen)

        elif self.state == 'victory':
            self.level.draw()
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((10, 16, 24, 220))
            self.screen.blit(overlay, (0, 0))

            card_w, card_h = 580, 490
            cx, cy = sw // 2 - card_w // 2, max(20, sh // 2 - card_h // 2)
            card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            card.fill((12, 16, 24, 248))
            self.screen.blit(card, (cx, cy))
            pygame.draw.rect(self.screen, (220, 185, 60), (cx, cy, card_w, card_h), 2)
            pygame.draw.rect(self.screen, (70, 130, 180), (cx + 4, cy + 4, card_w - 8, card_h - 8), 1)

            # 4 Gothic corner brackets
            for kx, ky in [(cx, cy), (cx + card_w - 10, cy), (cx, cy + card_h - 10), (cx + card_w - 10, cy + card_h - 10)]:
                pygame.draw.rect(self.screen, (245, 215, 80), (kx, ky, 10, 10))
                pygame.draw.rect(self.screen, (20, 30, 45), (kx + 2, ky + 2, 6, 6))

            font_title = get_pixel_font(24, bold=True)
            title_text = "ВЕЛИКОЕ ВОЗНЕСЕНИЕ"
            subtitle_text = "ХОРОШАЯ КОНЦОВКА: ПОБЕДА НАД ТЬМОЙ"
            tx = sw // 2 - font_title.size(title_text)[0] // 2
            self.screen.blit(font_title.render(title_text, True, (255, 220, 80)), (tx, cy + 18))

            font_sub = get_pixel_font(14, bold=True)
            sx = sw // 2 - font_sub.size(subtitle_text)[0] // 2
            self.screen.blit(font_sub.render(subtitle_text, True, (130, 225, 255)), (sx, cy + 50))

            pygame.draw.line(self.screen, (90, 80, 50), (cx + 40, cy + 78), (cx + card_w - 40, cy + 78), 1)

            font_stats = get_pixel_font(13, bold=True)
            stats = self.last_run_stats
            rows = [
                ("Пройдено этажей", "ЭТАЖИ 1 - 2 (ВОЗНЕСЕНИЕ)", (120, 240, 150)),
                ("Побеждённый владыка", "КОСТЯНОЙ ГОЛЕМ", (255, 140, 140)),
                ("Награда: Фиолетовые осколки", f"+{stats.get('purple_shards_reward', 25)} Оск.", (220, 130, 255)),
                ("Награда золотом в профиль", f"+{stats.get('gold', 100)} G", (255, 215, 60)),
                ("Сражено порождений тьмы", f"{stats.get('kills', 0)}", (220, 220, 220))
            ]

            start_sy = cy + 96
            for idx, (label, val, val_col) in enumerate(rows):
                ry = start_sy + idx * 36
                row_surf = pygame.Surface((card_w - 60, 30), pygame.SRCALPHA)
                row_surf.fill((20, 28, 42, 160))
                self.screen.blit(row_surf, (cx + 30, ry - 4))
                pygame.draw.rect(self.screen, (50, 70, 95), (cx + 30, ry - 4, card_w - 60, 30), 1)

                lbl_surf = font_stats.render(label, True, (200, 215, 230))
                self.screen.blit(lbl_surf, (cx + 45, ry + 2))
                val_surf = font_stats.render(val, True, val_col)
                self.screen.blit(val_surf, (cx + card_w - 45 - val_surf.get_width(), ry + 2))

            for btn in self.ui_buttons:
                btn.draw(self.screen)

        pygame.display.flip()

if __name__ == '__main__':
    try:
        game = Game()
        game.run()
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        try:
            with open("crash.log", "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"Rogue 2D encountered an error:\n\n{err_msg}", "Rogue2 Error", 0x10)
        except Exception:
            pass
        sys.exit(1)
    finally:
        try:
            pygame.quit()
        except Exception:
            pass
        sys.exit(0)
