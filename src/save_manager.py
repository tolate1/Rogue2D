import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURRENT_SCHEMA_VERSION = 2

def _get_storage_path(filename):
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), filename)
    return os.path.join(PROJECT_ROOT, filename)

SAVE_FILE = _get_storage_path('savegame.json')
PROFILE_FILE = _get_storage_path('profile.json')
SETTINGS_FILE = _get_storage_path('settings.json')

DEFAULT_SETTINGS = {
    'master_volume': 0.8,
    'sfx_volume': 0.8,
    'music_volume': 0.6,
    'zoom': 1.0,
    'hud_scale': 1.0,
    'fullscreen': False
}

def _safe_write_json(path, data):
    import time
    tmp_path = path + '.tmp'
    bak_path = path + '.bak'
    for attempt in range(4):
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if os.path.exists(path):
                try:
                    os.replace(tmp_path, path)
                except Exception:
                    # Keep backup of old file before removal to protect against disk write failure
                    try:
                        if os.path.exists(bak_path):
                            os.remove(bak_path)
                        os.replace(path, bak_path)
                    except Exception:
                        pass
                    try:
                        os.rename(tmp_path, path)
                        if os.path.exists(bak_path):
                            try:
                                os.remove(bak_path)
                            except Exception:
                                pass
                    except Exception as rename_err:
                        # Restore from backup if rename failed
                        if os.path.exists(bak_path) and not os.path.exists(path):
                            try:
                                os.rename(bak_path, path)
                            except Exception:
                                pass
                        raise rename_err
            else:
                os.rename(tmp_path, path)
            return True
        except Exception as e:
            if attempt < 3:
                time.sleep(0.02)
            else:
                print(f"Safe write failed for {path}: {e}")
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                return False

# =========================================================================
# 1. SETTINGS PERSISTENCE
# =========================================================================

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        settings = dict(DEFAULT_SETTINGS)
        settings.update(data)
        return settings
    except Exception:
        return dict(DEFAULT_SETTINGS)

def save_settings(settings):
    return _safe_write_json(SETTINGS_FILE, settings)

# =========================================================================
# 2. PERSISTENT PROFILE (METAGAME / HUB / ARMORY)
# =========================================================================

def get_default_profile():
    return {
        'schema_version': 2,
        'permanent_gold': 50,
        'purple_shards': 15,
        'dark_iron': 3,
        'total_ascensions': 0,
        'unlocked_chapters': ['catacombs_1'],
        'equipped': {
            'weapon': {
                'name': 'Рыцарский Меч',
                'rarity': 'common',
                'effects': {'attack': 4, 'attack_speed': 10},
                'value': 30,
                'image_path': 'assets/sprites/item_sword.png',
                'slot': 'weapon',
                'weapon_type': 'sword',
                'upgrade_level': 0
            },
            'offhand': {
                'name': 'Железный Баклер',
                'rarity': 'common',
                'effects': {'health': 15},
                'value': 25,
                'image_path': 'assets/sprites/item_shield.png',
                'slot': 'offhand',
                'upgrade_level': 0
            },
            'armor': {
                'name': 'Кожаный Колет',
                'rarity': 'common',
                'effects': {'health': 20, 'speed': 0.3},
                'value': 35,
                'image_path': 'assets/sprites/item_armor.png',
                'slot': 'armor',
                'upgrade_level': 0
            },
            'boots': {
                'name': 'Сапоги Странника',
                'rarity': 'common',
                'effects': {'speed': 0.8},
                'value': 25,
                'image_path': 'assets/sprites/item_boots.png',
                'slot': 'boots',
                'upgrade_level': 0
            },
            'amulet': {
                'name': 'Амулет Ярости',
                'rarity': 'common',
                'effects': {'attack': 2},
                'value': 40,
                'image_path': 'assets/sprites/item_amulet.png',
                'slot': 'amulet',
                'upgrade_level': 0
            },
            'ring': {
                'name': 'Кольцо Упорства',
                'rarity': 'common',
                'effects': {'energy': 15},
                'value': 30,
                'image_path': 'assets/sprites/item_gear.png',
                'slot': 'ring',
                'upgrade_level': 0
            }
        },
        'armory': [
            {
                'name': 'Тяжёлый Клеймор',
                'rarity': 'common',
                'effects': {'attack': 9, 'speed': -0.4},
                'value': 45,
                'image_path': 'assets/sprites/item_wide_blade.png',
                'slot': 'weapon',
                'weapon_type': 'claymore',
                'upgrade_level': 0
            },
            {
                'name': 'Гримуар Пустоты',
                'rarity': 'common',
                'effects': {'magic': 2, 'energy_regen': 1},
                'value': 40,
                'image_path': 'assets/sprites/item_scroll.png',
                'slot': 'offhand',
                'upgrade_level': 0
            },
            {
                'name': 'Латный Доспех',
                'rarity': 'common',
                'effects': {'health': 50, 'speed': -0.3},
                'value': 55,
                'image_path': 'assets/sprites/item_armor.png',
                'slot': 'armor',
                'upgrade_level': 0
            },
            {
                'name': 'Тяжёлые Ботфорты',
                'rarity': 'common',
                'effects': {'health': 25},
                'value': 35,
                'image_path': 'assets/sprites/item_boots.png',
                'slot': 'boots',
                'upgrade_level': 0
            },
            {
                'name': 'Оберег Жизни',
                'rarity': 'common',
                'effects': {'health': 35},
                'value': 45,
                'image_path': 'assets/sprites/item_heart.png',
                'slot': 'amulet',
                'upgrade_level': 0
            },
            {
                'name': 'Кольцо Искры',
                'rarity': 'common',
                'effects': {'magic': 2},
                'value': 35,
                'image_path': 'assets/sprites/item_star.png',
                'slot': 'ring',
                'upgrade_level': 0
            }
        ],
        'runs_completed': 0,
        'total_kills': 0,
        'last_run_summary': None,
        'stats': {
            'total_runs': 0,
            'total_kills': 0,
            'total_gold_collected': 0
        },
        'achievements': {}
    }

def load_profile():
    if not os.path.exists(PROFILE_FILE):
        profile = get_default_profile()
        save_profile(profile)
        return profile
    try:
        with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        profile = get_default_profile()
        profile.update(data)
        return profile
    except Exception as e:
        print(f"Failed to load profile: {e}")
        return get_default_profile()

def save_profile(profile):
    return _safe_write_json(PROFILE_FILE, profile)

# =========================================================================
# 3. ACTIVE RUN STATE PERSISTENCE (DURING DUNGEON RUN)
# =========================================================================

def has_save():
    return os.path.exists(SAVE_FILE)

def has_active_run():
    return has_save()

def delete_save():
    """Removes ONLY the active run save, leaving the profile intact."""
    if os.path.exists(SAVE_FILE):
        try:
            os.remove(SAVE_FILE)
        except Exception:
            pass

def clear_run_state():
    delete_save()

def _serialize_item(item):
    if not item:
        return None
    if hasattr(item, 'to_dict'):
        return item.to_dict()
    return {
        'name': getattr(item, 'name', 'Item'),
        'rarity': getattr(item, 'rarity', 'common'),
        'effects': dict(getattr(item, 'effects', {})),
        'value': int(getattr(item, 'value', 10)),
        'image_path': getattr(item, 'image_path', 'assets/sprites/item_heart.png'),
        'slot': getattr(item, 'slot', 'accessory'),
        'weapon_type': getattr(item, 'weapon_type', None),
        'upgrade_level': getattr(item, 'upgrade_level', 0)
    }

def save_game_state(floor, player, level=None):
    if level and hasattr(level, 'floor_seed'):
        floor_seed = level.floor_seed
    elif player and hasattr(player, 'floor_seed'):
        floor_seed = player.floor_seed
    else:
        floor_seed = int(floor * 9876543)

    player_pos = [int(player.rect.x), int(player.rect.y)] if player else [100, 100]
    opened_chests = []
    if level and hasattr(level, 'chest_sprites'):
        for c in level.chest_sprites:
            if getattr(c, 'opened', False):
                opened_chests.append([int(c.rect.x), int(c.rect.y)])

    used_altars = []
    if level and hasattr(level, 'altar_sprites'):
        for a in level.altar_sprites:
            if getattr(a, 'used', False):
                used_altars.append([int(a.rect.x), int(a.rect.y)])

    destroyed_obstacles = [list(pos) for pos in getattr(level, 'destroyed_obstacle_positions', [])] if level else []
    living_enemies = []
    if level and hasattr(level, 'enemy_sprites'):
        for e in level.enemy_sprites:
            if getattr(e, 'alive', lambda: False)():
                living_enemies.append({
                    'type': getattr(e, 'enemy_type', 'zombie'),
                    'pos': [int(e.rect.x), int(e.rect.y)],
                    'hp': float(getattr(e, 'hp', 10))
                })

    dropped_gold = []
    if level and hasattr(level, 'visible_sprites'):
        for s in level.visible_sprites:
            if s.__class__.__name__ == 'Gold' and getattr(s, 'alive', lambda: False)():
                dropped_gold.append({
                    'pos': [int(s.rect.centerx), int(s.rect.centery)],
                    'amount': int(getattr(s, 'amount', 5))
                })

    # Serialize equipped gear (6 slots)
    equipped_data = {}
    if player and hasattr(player, 'equipped') and isinstance(player.equipped, dict):
        for slot, itm in player.equipped.items():
            equipped_data[slot] = _serialize_item(itm)

    # Serialize active run relics
    relics_data = []
    if player and hasattr(player, 'relics') and isinstance(player.relics, list):
        for r in player.relics:
            relics_data.append(_serialize_item(r))

    data = {
        'schema_version': 2,
        'generator_version': 2,
        'floor': int(floor),
        'floor_seed': int(floor_seed),
        'player_pos': player_pos,
        'opened_chests': opened_chests,
        'used_altars': used_altars,
        'destroyed_obstacles': destroyed_obstacles,
        'living_enemies': living_enemies,
        'dropped_gold': dropped_gold,
        'health': float(player.health) if player else 100.0,
        'max_health': float(player.stats.get('health', 100)) if player else 100.0,
        'energy': float(player.energy) if player else 60.0,
        'max_energy': float(player.stats.get('energy', 60)) if player else 60.0,
        'exp': int(player.exp) if player else 0,
        'level': int(player.level) if player else 1,
        'gold': int(player.gold) if player else 0,
        'bombs': int(getattr(player, 'bombs', 0)) if player else 0,
        'current_skin': getattr(player, 'current_skin', 'champion') if player else 'champion',
        'shop_stat_bonuses': dict(getattr(player, 'shop_stat_bonuses', {})) if player else {},
        'skill_points': int(getattr(player, 'skill_points', 0)) if player else 0,
        'skills': dict(getattr(player, 'skills', {})) if player else {},
        'kills': int(getattr(player, 'kills', 0)) if player else 0,
        'equipped': equipped_data,
        'relics': relics_data,
        'inventory': [
            _serialize_item(item)
            for item in getattr(player, 'inventory', [])
            if item
        ]
    }
    return _safe_write_json(SAVE_FILE, data)

def load_game_state():
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        if data.get('schema_version', 1) > CURRENT_SCHEMA_VERSION:
            print(f"Rejecting unsupported future save schema_version {data.get('schema_version')} > {CURRENT_SCHEMA_VERSION}")
            return None
        return data
    except Exception as e:
        print(f'Failed to load game state: {e}')
        return None
