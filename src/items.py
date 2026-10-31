import pygame
import random
from src.settings import *

VALID_EQUIP_SLOTS = ['weapon', 'offhand', 'armor', 'boots', 'amulet', 'ring']

import pygame
import random
from src.settings import *

VALID_EQUIP_SLOTS = ['weapon', 'offhand', 'armor', 'boots', 'amulet', 'ring']

SUBSTAT_DEFINITIONS = {
    'attack': {'label': 'Сила атаки', 'base': 3, 'growth': 2, 'is_percent': False},
    'crit_rate': {'label': 'Крит. шанс', 'base': 3.5, 'growth': 1.5, 'is_percent': True},
    'crit_dmg': {'label': 'Крит. урон', 'base': 8.0, 'growth': 3.5, 'is_percent': True},
    'defense': {'label': 'Защита', 'base': 3, 'growth': 2, 'is_percent': False},
    'health': {'label': 'Здоровье', 'base': 15, 'growth': 10, 'is_percent': False},
    'attack_speed': {'label': 'Скор. атаки', 'base': 6.0, 'growth': 2.5, 'is_percent': True},
    'speed': {'label': 'Скорость', 'base': 0.2, 'growth': 0.1, 'is_percent': False},
}

RARITY_WEIGHTS = {
    'legendary': 0,
    'epic': 1,
    'rare': 2,
    'common': 3
}

def item_sort_key(item):
    """Sort items by rarity (Legendary -> Epic -> Rare -> Common), then upgrade level desc, then name."""
    r_w = RARITY_WEIGHTS.get(getattr(item, 'rarity', 'common').lower(), 4)
    upg = getattr(item, 'upgrade_level', 0)
    name = getattr(item, 'name', '')
    return (r_w, -upg, name)

def sort_items_by_rarity(items):
    """Return a list of items sorted by rarity."""
    return sorted(items, key=item_sort_key)

def generate_default_substats(slot, rarity='common', exclude_stat=None):
    """Generates exactly 4 distinct Genshin/Resonance style substats for an equipment piece."""
    if slot == 'weapon':
        chosen = ['crit_rate', 'crit_dmg', 'attack_speed', 'speed']
    elif slot == 'armor':
        chosen = ['health' if exclude_stat != 'health' else 'defense',
                  'defense' if exclude_stat != 'defense' else 'crit_rate',
                  'crit_rate' if exclude_stat != 'crit_rate' else 'crit_dmg',
                  'speed']
    elif slot == 'offhand':
        chosen = ['defense' if exclude_stat != 'defense' else 'health',
                  'health' if exclude_stat != 'health' else 'attack_speed',
                  'crit_rate',
                  'crit_dmg']
    elif slot == 'boots':
        chosen = ['defense', 'health', 'crit_rate', 'crit_dmg']
    elif slot == 'amulet':
        chosen = ['crit_dmg' if exclude_stat != 'crit_dmg' else 'attack_speed',
                  'crit_rate',
                  'defense',
                  'health']
    elif slot == 'ring':
        chosen = ['crit_rate' if exclude_stat != 'crit_rate' else 'attack_speed',
                  'crit_dmg',
                  'defense',
                  'health']
    else:
        chosen = [k for k in SUBSTAT_DEFINITIONS.keys() if k != exclude_stat][:4]

    # Guarantee uniqueness and exclude_stat exclusion
    unique_chosen = []
    for k in chosen:
        if k != exclude_stat and k not in unique_chosen:
            unique_chosen.append(k)
    for k in SUBSTAT_DEFINITIONS.keys():
        if len(unique_chosen) >= 4:
            break
        if k != exclude_stat and k not in unique_chosen:
            unique_chosen.append(k)

    substats = []
    for k in unique_chosen[:4]:
        info = SUBSTAT_DEFINITIONS.get(k, {'label': k.capitalize(), 'base': 3, 'growth': 1.5, 'is_percent': False})
        growth = info['growth']
        if rarity in ['rare', 'epic']:
            growth = round(growth * 1.2, 1)
        substats.append({
            'id': k,
            'label': info['label'],
            'value': 0.0,
            'growth': growth,
            'rolls': 0,
            'is_percent': info['is_percent']
        })
    return substats

class Item:
    def __init__(self, name, rarity, effects, value, image_path='assets/sprites/item_heart.png',
                 slot=None, weapon_type=None, upgrade_level=0, description="",
                 main_stat=None, substats=None, max_level=10, count=1):
        self.name = name
        self.rarity = rarity 
        self.base_effects = dict(effects) if effects else {}
        self.effects = dict(self.base_effects)
        self.value = int(value)
        self.image_path = image_path
        self.upgrade_level = int(upgrade_level)
        self.max_level = int(max_level)
        self.description = description
        self.count = max(1, int(count))

        # Auto-infer slot and weapon_type if not explicitly passed
        if slot is None:
            n_low = name.lower()
            if any(k in n_low for k in ['spear', 'копь', 'пика']):
                slot = 'weapon'
                weapon_type = weapon_type or 'spear'
            elif any(k in n_low for k in ['dagger', 'кинжал', 'клинки']):
                slot = 'weapon'
                weapon_type = weapon_type or 'daggers'
            elif any(k in n_low for k in ['claymore', 'клеймор', 'палаш', 'wide']):
                slot = 'weapon'
                weapon_type = weapon_type or 'claymore'
            elif any(k in n_low for k in ['sword', 'blade', 'клинок', 'меч']):
                slot = 'weapon'
                weapon_type = weapon_type or 'sword'
            elif any(k in n_low for k in ['shield', 'buckler', 'щит', 'баклер', 'grimoire', 'гримуар']):
                slot = 'offhand'
            elif any(k in n_low for k in ['armor', 'броня', 'колет', 'доспех', 'кольчуга']):
                slot = 'armor'
            elif any(k in n_low for k in ['boots', 'сапоги', 'ботфорты', 'обувь']):
                slot = 'boots'
            elif any(k in n_low for k in ['potion', 'зелье']):
                slot = 'consumable'
            elif any(k in n_low for k in ['relic', 'реликвия', 'fang', 'core', 'feather', 'shard', 'crown', 'венец', 'корона', 'сердце']):
                slot = 'relic'
            elif any(k in n_low for k in ['amulet', 'амулет', 'оберег']):
                slot = 'amulet'
            elif any(k in n_low for k in ['ring', 'кольцо']):
                slot = 'ring'
            else:
                slot = 'accessory'

        if slot == 'weapon' and weapon_type is None:
            n_low = name.lower()
            if any(k in n_low for k in ['spear', 'копь', 'пика']):
                weapon_type = 'spear'
            elif any(k in n_low for k in ['dagger', 'кинжал', 'клинки']):
                weapon_type = 'daggers'
            elif any(k in n_low for k in ['claymore', 'клеймор']):
                weapon_type = 'claymore'
            else:
                weapon_type = 'sword'

        self.slot = slot
        self.weapon_type = weapon_type

        # Genshin / Resonance Stats Initialization
        if main_stat is not None:
            self.main_stat = dict(main_stat)
        else:
            if self.slot == 'weapon':
                base_atk = self.base_effects.get('attack', 8)
                if self.weapon_type == 'claymore':
                    growth = 5
                elif self.weapon_type == 'spear':
                    growth = 4
                elif self.weapon_type == 'daggers':
                    growth = 2.5
                else:
                    growth = 3
                self.main_stat = {'id': 'attack', 'label': 'Базовая Атака', 'value': base_atk, 'growth': growth}
            elif self.slot == 'armor':
                if 'defense' in self.base_effects:
                    base_def = self.base_effects['defense']
                    self.main_stat = {'id': 'defense', 'label': 'Защита', 'value': base_def, 'growth': 3}
                else:
                    base_hp = self.base_effects.get('health', 40)
                    self.main_stat = {'id': 'health', 'label': 'Макс. HP', 'value': base_hp, 'growth': 15}
            elif self.slot == 'offhand':
                if 'attack_speed' in self.base_effects:
                    base_as = self.base_effects['attack_speed']
                    self.main_stat = {'id': 'attack_speed', 'label': 'Скор. Атаки', 'value': base_as, 'growth': 3.0}
                else:
                    base_def = self.base_effects.get('defense', 5)
                    self.main_stat = {'id': 'defense', 'label': 'Защита', 'value': base_def, 'growth': 2}
            elif self.slot == 'boots':
                base_spd = self.base_effects.get('speed', 0.6)
                self.main_stat = {'id': 'speed', 'label': 'Скорость', 'value': base_spd, 'growth': 0.15}
            elif self.slot == 'amulet':
                if 'health' in self.base_effects:
                    base_hp = self.base_effects['health']
                    self.main_stat = {'id': 'health', 'label': 'Макс. HP', 'value': base_hp, 'growth': 12}
                else:
                    base_cdmg = self.base_effects.get('crit_dmg', 15.0)
                    self.main_stat = {'id': 'crit_dmg', 'label': 'Крит. Урон', 'value': base_cdmg, 'growth': 4.0}
            elif self.slot == 'ring':
                if 'attack' in self.base_effects:
                    base_atk = self.base_effects['attack']
                    self.main_stat = {'id': 'attack', 'label': 'Атака', 'value': base_atk, 'growth': 2}
                else:
                    base_crate = self.base_effects.get('crit_rate', 6.0)
                    self.main_stat = {'id': 'crit_rate', 'label': 'Крит. Шанс', 'value': base_crate, 'growth': 1.8}
            else:
                first_k = next(iter(self.base_effects.keys()), 'attack')
                val = self.base_effects.get(first_k, 2)
                lbl = SUBSTAT_DEFINITIONS.get(first_k, {}).get('label', first_k.capitalize())
                self.main_stat = {'id': first_k, 'label': lbl, 'value': val, 'growth': 1}

        if substats is not None and len(substats) == 4:
            self.substats = [dict(s) for s in substats]
        else:
            self.substats = generate_default_substats(self.slot, self.rarity, exclude_stat=self.main_stat.get('id'))

        self._sync_effects()

        from src.utils import load_image
        self.image = load_image(image_path, scale=(32, 32))

    def can_stack_with(self, other):
        """Determines if this item can stack with another item."""
        if not isinstance(other, Item):
            return False
        if self.name != other.name or self.rarity != other.rarity:
            return False
        if getattr(self, 'slot', None) != getattr(other, 'slot', None):
            return False
        if getattr(self, 'upgrade_level', 0) != getattr(other, 'upgrade_level', 0):
            return False
        if getattr(self, 'effects', {}) != getattr(other, 'effects', {}):
            return False
        if getattr(self, 'substats', None) or getattr(other, 'substats', None):
            s1 = [(s['id'], s['value']) for s in getattr(self, 'substats', [])]
            s2 = [(s['id'], s['value']) for s in getattr(other, 'substats', [])]
            if s1 != s2:
                return False
        return True

    def _sync_effects(self):
        """Synchronizes flat and percent bonuses into self.effects for combat calculation."""
        if not hasattr(self, 'main_stat') or not self.main_stat:
            return
        m_id = self.main_stat['id']
        m_val = self.main_stat['value']
        new_eff = {m_id: m_val}
        for sub in getattr(self, 'substats', []):
            s_id = sub['id']
            s_val = sub.get('value', 0.0)
            if s_val > 0:
                new_eff[s_id] = round(new_eff.get(s_id, 0.0) + s_val, 1)
        for k, v in self.base_effects.items():
            if k not in new_eff:
                new_eff[k] = v
        self.effects = new_eff

    def upgrade(self):
        """Genshin/Resonance style upgrade: increases main stat and rolls 1 of 4 substats."""
        if self.upgrade_level >= self.max_level:
            return False, "Максимальный уровень предмета достигнут!"
        self.upgrade_level += 1
        growth = self.main_stat.get('growth', 2)
        self.main_stat['value'] = round(self.main_stat['value'] + growth, 1)

        sub = random.choice(self.substats)
        sub_growth = sub.get('growth', 1.5)
        sub['value'] = round(sub.get('value', 0.0) + sub_growth, 1)
        sub['rolls'] = sub.get('rolls', 0) + 1

        self._sync_effects()

        base_name = self.name.split(' +')[0]
        self.name = f"{base_name} +{self.upgrade_level}"
        sub_val_str = f"+{sub_growth}%" if sub.get('is_percent') else f"+{sub_growth}"
        return True, f"Уровень +{self.upgrade_level}! {self.main_stat['label']} +{growth}, {sub['label']} {sub_val_str} (+ Ролл #{sub['rolls']})"

    def to_dict(self):
        return {
            'name': self.name,
            'rarity': self.rarity,
            'effects': dict(self.effects),
            'value': self.value,
            'image_path': self.image_path,
            'slot': self.slot,
            'weapon_type': self.weapon_type,
            'upgrade_level': self.upgrade_level,
            'max_level': self.max_level,
            'description': self.description,
            'count': getattr(self, 'count', 1),
            'main_stat': dict(self.main_stat) if getattr(self, 'main_stat', None) else None,
            'substats': [dict(s) for s in getattr(self, 'substats', [])]
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        return cls(
            name=data.get('name', 'Неизвестный предмет'),
            rarity=data.get('rarity', 'common'),
            effects=data.get('effects', {}),
            value=data.get('value', 10),
            image_path=data.get('image_path', 'assets/sprites/item_sword.png'),
            slot=data.get('slot', None),
            weapon_type=data.get('weapon_type', None),
            upgrade_level=data.get('upgrade_level', 0),
            max_level=data.get('max_level', 10),
            description=data.get('description', ''),
            main_stat=data.get('main_stat', None),
            substats=data.get('substats', None),
            count=data.get('count', 1)
        )

    def clone(self):
        return Item.from_dict(self.to_dict())

# =========================================================================
# 12 BASELINE PERMANENT GEAR OPTIONS (2 PER SLOT)
# =========================================================================

PERMANENT_GEAR_CATALOGUE = {
    # 1. Weapon
    'sword_knight': {
        'name': 'Рыцарский Меч',
        'rarity': 'common',
        'effects': {'attack': 4, 'attack_speed': 10},
        'value': 30,
        'image_path': 'assets/sprites/item_sword.png',
        'slot': 'weapon',
        'weapon_type': 'sword',
        'description': 'Быстрый одноручный клинок (дуга 90 град, быстрый взмах).'
    },
    'claymore_heavy': {
        'name': 'Тяжёлый Клеймор',
        'rarity': 'common',
        'effects': {'attack': 9, 'speed': -0.4},
        'value': 45,
        'image_path': 'assets/sprites/item_wide_blade.png',
        'slot': 'weapon',
        'weapon_type': 'claymore',
        'description': 'Сокрушительный двуручник (дуга 160 град, мощное отбрасывание).'
    },
    'spear_abyss': {
        'name': 'Копьё Бездны',
        'rarity': 'rare',
        'effects': {'attack': 8, 'reach': 110, 'crit_rate': 4.0},
        'value': 60,
        'image_path': 'assets/sprites/item_spear.png',
        'slot': 'weapon',
        'weapon_type': 'spear',
        'description': 'Длинное копьё с колющим выпадом на 110 px, пробивающим строй врагов.'
    },
    'daggers_shadow': {
        'name': 'Клинки Теней',
        'rarity': 'rare',
        'effects': {'attack': 5, 'crit_rate': 12.0, 'attack_speed': 25},
        'value': 60,
        'image_path': 'assets/sprites/item_daggers.png',
        'slot': 'weapon',
        'weapon_type': 'daggers',
        'description': 'Парные кинжалы с высокой скоростью атаки и повышенным шансом крита.'
    },
    # 2. Offhand
    'buckler_iron': {
        'name': 'Железный Баклер',
        'rarity': 'common',
        'effects': {'health': 15, 'shield_power': 10},
        'value': 25,
        'image_path': 'assets/sprites/item_shield.png',
        'slot': 'offhand',
        'description': 'Кованый щит, повышающий живучесть и силу блокирования.'
    },
    'grimoire_void': {
        'name': 'Гримуар Пустоты',
        'rarity': 'common',
        'effects': {'magic': 2, 'energy_regen': 1},
        'value': 40,
        'image_path': 'assets/sprites/item_scroll.png',
        'slot': 'offhand',
        'description': 'Тёмный том заклятий, ускоряющий восстановление энергии.'
    },
    # 3. Armor
    'vest_leather': {
        'name': 'Кожаный Колет',
        'rarity': 'common',
        'effects': {'health': 20, 'speed': 0.3},
        'value': 35,
        'image_path': 'assets/sprites/item_armor.png',
        'slot': 'armor',
        'description': 'Лёгкий доспех разведчика, не сковывающий шаг.'
    },
    'plate_armor': {
        'name': 'Латный Доспех',
        'rarity': 'common',
        'effects': {'health': 50, 'speed': -0.3},
        'value': 55,
        'image_path': 'assets/sprites/item_armor.png',
        'slot': 'armor',
        'description': 'Тяжёлые стальные латы, дающие максимальную защиту.'
    },
    # 4. Boots
    'boots_traveler': {
        'name': 'Сапоги Странника',
        'rarity': 'common',
        'effects': {'speed': 0.8},
        'value': 25,
        'image_path': 'assets/sprites/item_boots.png',
        'slot': 'boots',
        'description': 'Удобная обувь для быстрого перемещения по склепу.'
    },
    'boots_sabatons': {
        'name': 'Тяжёлые Ботфорты',
        'rarity': 'common',
        'effects': {'health': 25, 'knockback_resist': 0.3},
        'value': 35,
        'image_path': 'assets/sprites/item_boots.png',
        'slot': 'boots',
        'description': 'Окованные сталью сапоги, уменьшающие отбрасывание.'
    },
    # 5. Amulet
    'amulet_fury': {
        'name': 'Амулет Ярости',
        'rarity': 'common',
        'effects': {'attack': 2, 'crit_chance': 0.10},
        'value': 40,
        'image_path': 'assets/sprites/item_amulet.png',
        'slot': 'amulet',
        'description': 'Кулон из алого кристалла, обостряющий удары героя.'
    },
    'amulet_vitality': {
        'name': 'Оберег Жизни',
        'rarity': 'common',
        'effects': {'health': 35, 'life_regen': 0.5},
        'value': 45,
        'image_path': 'assets/sprites/item_heart.png',
        'slot': 'amulet',
        'description': 'Реликвия целителей, укрепляющая запас здоровья.'
    },
    # 6. Ring
    'ring_spark': {
        'name': 'Кольцо Искры',
        'rarity': 'common',
        'effects': {'magic': 2, 'dash_spark': 1},
        'value': 35,
        'image_path': 'assets/sprites/item_star.png',
        'slot': 'ring',
        'description': 'Серебряное кольцо, порождающее огненный след при рывке.'
    },
    'ring_tenacity': {
        'name': 'Кольцо Упорства',
        'rarity': 'common',
        'effects': {'energy': 15, 'dash_cost_reduction': 0.2},
        'value': 30,
        'image_path': 'assets/sprites/item_gear.png',
        'slot': 'ring',
        'description': 'Гномье кольцо, повышающее запас выносливости.'
    }
}

def create_catalogue_item(item_id):
    raw = PERMANENT_GEAR_CATALOGUE.get(item_id)
    if not raw:
        return None
    return Item.from_dict(raw)

# =========================================================================
# ASTRAL WEAPONS (BOUGHT / CRAFTED WITH PURPLE SHARDS)
# =========================================================================

ASTRAL_WEAPONS_CATALOGUE = {
    'astral_blade': {
        'name': 'Астральный Клинок Пустоты',
        'rarity': 'epic',
        'effects': {'attack': 14, 'crit_rate': 7.5, 'crit_dmg': 22.0},
        'value': 120,
        'cost_shards': 10,
        'image_path': 'assets/sprites/item_sword.png',
        'slot': 'weapon',
        'weapon_type': 'sword',
        'description': 'Оружие из фиолетовых осколков (высокий крит. урон и скорость).',
        'main_stat': {'id': 'attack', 'label': 'Базовая Атака', 'value': 14, 'growth': 4},
        'substats': [
            {'id': 'crit_rate', 'label': 'Крит. шанс', 'value': 7.5, 'growth': 2.0, 'rolls': 1, 'is_percent': True},
            {'id': 'crit_dmg', 'label': 'Крит. урон', 'value': 22.0, 'growth': 6.0, 'rolls': 1, 'is_percent': True},
            {'id': 'speed', 'label': 'Скорость', 'value': 0.4, 'growth': 0.15, 'rolls': 1, 'is_percent': False},
            {'id': 'attack_speed', 'label': 'Скор. атаки', 'value': 12, 'growth': 4, 'rolls': 1, 'is_percent': True}
        ]
    },
    'rift_claymore': {
        'name': 'Клеймор Разлома',
        'rarity': 'epic',
        'effects': {'attack': 22, 'crit_dmg': 30.0, 'health': 35},
        'value': 140,
        'cost_shards': 10,
        'image_path': 'assets/sprites/item_wide_blade.png',
        'slot': 'weapon',
        'weapon_type': 'claymore',
        'description': 'Тяжёлый двуручник из астрального кристалла (дуга 160 град, сокрушительный удар).',
        'main_stat': {'id': 'attack', 'label': 'Базовая Атака', 'value': 22, 'growth': 6},
        'substats': [
            {'id': 'crit_dmg', 'label': 'Крит. урон', 'value': 30.0, 'growth': 8.0, 'rolls': 1, 'is_percent': True},
            {'id': 'crit_rate', 'label': 'Крит. шанс', 'value': 5.0, 'growth': 1.8, 'rolls': 1, 'is_percent': True},
            {'id': 'defense', 'label': 'Защита', 'value': 6, 'growth': 2, 'rolls': 1, 'is_percent': False},
            {'id': 'health', 'label': 'Здоровье', 'value': 35, 'growth': 15, 'rolls': 1, 'is_percent': False}
        ]
    },
    'shadow_scythe': {
        'name': 'Теневой Жнец',
        'rarity': 'epic',
        'effects': {'attack': 16, 'crit_rate': 8.0, 'crit_dmg': 18.0},
        'value': 130,
        'cost_shards': 10,
        'image_path': 'assets/sprites/item_sword.png',
        'slot': 'weapon',
        'weapon_type': 'sword',
        'description': 'Клинок вечной ночи, поглощающий души поверженных врагов.',
        'main_stat': {'id': 'attack', 'label': 'Базовая Атака', 'value': 16, 'growth': 4},
        'substats': [
            {'id': 'crit_rate', 'label': 'Крит. шанс', 'value': 8.0, 'growth': 2.2, 'rolls': 1, 'is_percent': True},
            {'id': 'crit_dmg', 'label': 'Крит. урон', 'value': 18.0, 'growth': 5.0, 'rolls': 1, 'is_percent': True},
            {'id': 'speed', 'label': 'Скорость бега', 'value': 0.6, 'growth': 0.2, 'rolls': 1, 'is_percent': False},
            {'id': 'health', 'label': 'Здоровье', 'value': 25, 'growth': 12, 'rolls': 1, 'is_percent': False}
        ]
    },
    'warhammer_crusher': {
        'name': 'Боевой Молот Громовержца',
        'rarity': 'epic',
        'effects': {'attack': 24, 'crit_dmg': 35.0, 'defense': 8},
        'value': 145,
        'cost_shards': 10,
        'image_path': 'assets/sprites/item_warhammer.png',
        'slot': 'weapon',
        'weapon_type': 'claymore',
        'description': 'Тяжёлый двуручный молот из метеоритной стали, сокрушающий доспехи врагов.',
        'main_stat': {'id': 'attack', 'label': 'Базовая Атака', 'value': 24, 'growth': 6},
        'substats': [
            {'id': 'crit_dmg', 'label': 'Крит. урон', 'value': 35.0, 'growth': 8.0, 'rolls': 1, 'is_percent': True},
            {'id': 'defense', 'label': 'Защита', 'value': 8, 'growth': 3, 'rolls': 1, 'is_percent': False},
            {'id': 'crit_rate', 'label': 'Крит. шанс', 'value': 6.0, 'growth': 2.0, 'rolls': 1, 'is_percent': True},
            {'id': 'health', 'label': 'Здоровье', 'value': 40, 'growth': 15, 'rolls': 1, 'is_percent': False}
        ]
    },
    'reaper_scythe': {
        'name': 'Жатвенная Коса Забвения',
        'rarity': 'epic',
        'effects': {'attack': 18, 'crit_rate': 9.0, 'crit_dmg': 25.0},
        'value': 140,
        'cost_shards': 10,
        'image_path': 'assets/sprites/item_scythe.png',
        'slot': 'weapon',
        'weapon_type': 'sword',
        'description': 'Коса вечной ночи, пожинающая души и восстанавливающая здоровье.',
        'main_stat': {'id': 'attack', 'label': 'Базовая Атака', 'value': 18, 'growth': 5},
        'substats': [
            {'id': 'crit_rate', 'label': 'Крит. шанс', 'value': 9.0, 'growth': 2.5, 'rolls': 1, 'is_percent': True},
            {'id': 'crit_dmg', 'label': 'Крит. урон', 'value': 25.0, 'growth': 6.0, 'rolls': 1, 'is_percent': True},
            {'id': 'speed', 'label': 'Скорость', 'value': 0.5, 'growth': 0.15, 'rolls': 1, 'is_percent': False},
            {'id': 'health', 'label': 'Здоровье', 'value': 30, 'growth': 12, 'rolls': 1, 'is_percent': False}
        ]
    },
    'dueling_rapier': {
        'name': 'Дуэльная Рапира Чести',
        'rarity': 'rare',
        'effects': {'attack': 15, 'crit_rate': 12.0, 'speed': 0.5},
        'value': 85,
        'cost_shards': 8,
        'image_path': 'assets/sprites/item_rapier.png',
        'slot': 'weapon',
        'weapon_type': 'spear',
        'description': 'Изящная колющая рапира с филигранной гардой и повышенным шансом крита.',
        'main_stat': {'id': 'attack', 'label': 'Базовая Атака', 'value': 15, 'growth': 4},
        'substats': [
            {'id': 'crit_rate', 'label': 'Крит. шанс', 'value': 12.0, 'growth': 3.0, 'rolls': 1, 'is_percent': True},
            {'id': 'speed', 'label': 'Скорость', 'value': 0.5, 'growth': 0.2, 'rolls': 1, 'is_percent': False},
            {'id': 'attack_speed', 'label': 'Скор. атаки', 'value': 15, 'growth': 5, 'rolls': 1, 'is_percent': True},
            {'id': 'crit_dmg', 'label': 'Крит. урон', 'value': 15.0, 'growth': 4.5, 'rolls': 1, 'is_percent': True}
        ]
    }
}

def create_astral_weapon(weapon_id):
    raw = ASTRAL_WEAPONS_CATALOGUE.get(weapon_id)
    if not raw:
        return None
    return Item.from_dict(raw)

# =========================================================================
# 4 RUN-ONLY TEMPORARY RELICS & SYNERGIES
# =========================================================================

RUN_RELICS = {
    'vampiric_fang': {
        'name': 'Клык Вампира',
        'rarity': 'rare',
        'effects': {'vampirism': 2, 'crit_vamp': 0.12},
        'value': 65,
        'image_path': 'assets/sprites/item_vampire_fang.png',
        'slot': 'relic',
        'description': 'Восстанавливает +2 HP за каждые 3 убийства и 12% урона при критах.'
    },
    'bloodstone_core': {
        'name': 'Кровавый Камень',
        'rarity': 'epic',
        'effects': {'low_hp_attack': 25},
        'value': 75,
        'image_path': 'assets/sprites/item_amulet.png',
        'slot': 'relic',
        'description': 'Увеличивает урон на +25%, когда здоровье ниже 50%.'
    },
    'zephyr_feather': {
        'name': 'Перо Зефира',
        'rarity': 'rare',
        'effects': {'dash_distance_boost': 0.35, 'dash_invul': 1},
        'value': 70,
        'image_path': 'assets/sprites/item_zephyr_feather.png',
        'slot': 'relic',
        'description': '+35% дальности рывка и неуязвимость к снарядам во время дэша.'
    },
    'midas_crown': {
        'name': 'Венец Мидаса',
        'rarity': 'rare',
        'effects': {'gold_multiplier': 0.60, 'midas_sparks': 1},
        'value': 75,
        'image_path': 'assets/sprites/item_midas_crown.png',
        'slot': 'relic',
        'description': '+60% к получаемому золоту, враги осыпаются золотыми искрами.'
    },
    'obsidian_heart': {
        'name': 'Обсидиановое Сердце',
        'rarity': 'epic',
        'effects': {'death_defiance': 1},
        'value': 90,
        'image_path': 'assets/sprites/item_obsidian_heart.png',
        'slot': 'relic',
        'description': 'Поглощает первый смертельный удар за этаж, даруя 3 сек неуязвимости.'
    },
    'gale_feather': {
        'name': 'Перо Бури',
        'rarity': 'rare',
        'effects': {'dash_damage': 30, 'dash_speed_boost': 2.0},
        'value': 65,
        'image_path': 'assets/sprites/item_boots.png',
        'slot': 'relic',
        'description': 'Рывок наносит 30 урона встречным врагам и ускоряет бег на 2 сек.'
    },
    'mimic_fang': {
        'name': 'Клык Мимика',
        'rarity': 'rare',
        'effects': {'gold_multiplier': 0.40, 'crit_rate': 4.0},
        'value': 80,
        'image_path': 'assets/sprites/item_mimic_fang.png',
        'slot': 'relic',
        'description': 'Острый зуб коварного сундука-мимика: +40% золота и притяжение скрытых сокровищ.'
    },
    'storm_shard': {
        'name': 'Осколок Грозы',
        'rarity': 'epic',
        'effects': {'chain_lightning': 20},
        'value': 80,
        'image_path': 'assets/sprites/item_star.png',
        'slot': 'relic',
        'description': 'Критический удар выпускает цепные молнии в 2 соседних врагов.'
    }
}

def generate_relic(chosen_id=None):
    if chosen_id and chosen_id in RUN_RELICS:
        return Item.from_dict(RUN_RELICS[chosen_id])
    r_id = random.choice(list(RUN_RELICS.keys()))
    return Item.from_dict(RUN_RELICS[r_id])

def check_synergies(relic_list):
    names = {getattr(r, 'name', '') for r in relic_list}
    active = []
    # Synergy 1: Berserker (Vampiric Fang + Bloodstone Core)
    if any('Клык' in n for n in names) and any('Кровавый' in n for n in names):
        active.append({
            'name': 'Синергия: Берсерк',
            'desc': 'При HP < 50% вампиризм удваивается (+4 HP), а скорость атаки растет на 20%.'
        })
    # Synergy 2: Stormcaller (Gale Feather + Storm Shard)
    if any('Бури' in n for n in names) and any('Грозы' in n for n in names):
        active.append({
            'name': 'Синергия: Буревестник',
            'desc': 'Каждый рывок автоматически выпускает цепные молнии по врагам.'
        })
    # Synergy 3: Golden Defiance (Midas Crown + Obsidian Heart)
    if any('Венец' in n or 'Мидас' in n for n in names) and any('Сердце' in n or 'Обсидиан' in n for n in names):
        active.append({
            'name': 'Синергия: Золотое Бессмертие',
            'desc': 'Поглощение смертельного удара вызывает золотой взрыв на 80 урона по всем врагам.'
        })
    return active

# =========================================================================
# PROCEDURAL LOOT GENERATOR (FOR CHESTS & MONSTERS)
# =========================================================================

def generate_random_item():
    rarity = random.choices(['common', 'rare', 'epic', 'legendary'], weights=[55, 25, 14, 6])[0]
    value_mult = {'common': 1, 'rare': 2, 'epic': 3, 'legendary': 5}
    
    # Can also drop a relic with 12% chance in dungeon
    if random.random() < 0.12:
        return generate_relic()

    item_type = random.choice([
        'sword', 'armor', 'potion', 'amulet', 'boots', 'gloves',
        'claymore', 'spear', 'daggers', 'magnet', 'scroll', 'star', 'gear',
        'warhammer', 'scythe', 'rapier', 'void_elixir'
    ])
    
    if item_type == 'sword':
        effects = {'attack': 2 * value_mult[rarity]}
        image = 'assets/sprites/item_sword.png'
        slot = 'weapon'
    elif item_type == 'claymore':
        effects = {'attack': 4 * value_mult[rarity]}
        image = 'assets/sprites/item_wide_blade.png'
        slot = 'weapon'
    elif item_type == 'spear':
        effects = {'attack': 3 * value_mult[rarity], 'reach': 110}
        image = 'assets/sprites/item_spear.png'
        slot = 'weapon'
    elif item_type == 'daggers':
        effects = {'attack': 2 * value_mult[rarity], 'crit_rate': 4.0 * value_mult[rarity]}
        image = 'assets/sprites/item_daggers.png'
        slot = 'weapon'
    elif item_type == 'armor':
        effects = {'health': 10 * value_mult[rarity]}
        image = 'assets/sprites/item_armor.png'
        slot = 'armor'
    elif item_type == 'potion':
        effects = {'heal': 20 * value_mult[rarity]}
        image = 'assets/sprites/item_heart.png'
        slot = 'consumable'
    elif item_type == 'amulet':
        effects = {'magic': 1 * value_mult[rarity]}
        image = 'assets/sprites/item_amulet.png'
        slot = 'amulet'
    elif item_type == 'boots':
        effects = {'speed': 1 * value_mult[rarity]}
        image = 'assets/sprites/item_boots.png'
        slot = 'boots'
    elif item_type == 'gloves':
        effects = {'attack_speed': 10 * value_mult[rarity]}
        image = 'assets/sprites/item_gloves.png'
        slot = 'accessory'
    elif item_type == 'magnet':
        effects = {'magnet': 1 * value_mult[rarity]}
        image = 'assets/sprites/item_magnet.png'
        slot = 'accessory'
    elif item_type == 'scroll':
        effects = {'magic': 2 * value_mult[rarity], 'energy_regen': 1 * value_mult[rarity]}
        image = 'assets/sprites/item_scroll.png'
        slot = 'offhand'
    elif item_type == 'star':
        effects = {'speed': 1 * value_mult[rarity], 'magic': 1 * value_mult[rarity]}
        image = 'assets/sprites/item_star.png'
        slot = 'ring'
    elif item_type == 'gear':
        effects = {'attack_speed': 15 * value_mult[rarity]}
        image = 'assets/sprites/item_gear.png'
        slot = 'ring'
    elif item_type == 'warhammer':
        effects = {'attack': 5 * value_mult[rarity], 'crit_dmg': 15.0 * value_mult[rarity]}
        image = 'assets/sprites/item_warhammer.png'
        slot = 'weapon'
    elif item_type == 'scythe':
        effects = {'attack': 3 * value_mult[rarity], 'crit_rate': 4.0 * value_mult[rarity]}
        image = 'assets/sprites/item_scythe.png'
        slot = 'weapon'
    elif item_type == 'rapier':
        effects = {'attack': 3 * value_mult[rarity], 'crit_rate': 5.0 * value_mult[rarity]}
        image = 'assets/sprites/item_rapier.png'
        slot = 'weapon'
    elif item_type == 'void_elixir':
        effects = {'buff_atk': 4 * value_mult[rarity], 'heal': 25 * value_mult[rarity]}
        image = 'assets/sprites/item_void_elixir.png'
        slot = 'consumable'
    else:
        effects = {'heal': 20 * value_mult[rarity]}
        image = 'assets/sprites/item_heart.png'
        slot = 'consumable'
        
    return Item(f"{rarity.title()} {item_type.title()}", rarity, effects, 10 * value_mult[rarity], image, slot=slot)

# =========================================================================
# CHEST, BREAKABLE, GOLD SPRITES
# =========================================================================

class Chest(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        from src.utils import load_image
        self.sprite_type = 'chest'
        self.frames = []
        for name in ['chest.png', 'chest_opening.png', 'chest_open.png']:
            try:
                self.frames.append(load_image(f'assets/sprites/{name}', scale=(TILE_SIZE, TILE_SIZE)))
            except Exception:
                pass
        if not self.frames:
            self.frames = [load_image('assets/sprites/chest.png', scale=(TILE_SIZE, TILE_SIZE))]
        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft = pos)
        self.hitbox = self.rect.inflate(-10, -10)
        self.opened = False
        self.open_time = 0
        self.frame_index = 0

    def open(self):
        if not self.opened:
            self.opened = True
            self.open_time = pygame.time.get_ticks()
            try:
                from src.sound_manager import play_sfx
                play_sfx('chest')
            except Exception:
                pass
            return True
        return False

    def update(self):
        if self.opened and len(self.frames) >= 3:
            now = pygame.time.get_ticks()
            elapsed = now - self.open_time
            if elapsed < 120:
                self.image = self.frames[0]
            elif elapsed < 280:
                self.image = self.frames[1]
            else:
                self.image = self.frames[2]

class Breakable(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'obstacle'
        self.destroyed = False
        from src.utils import load_image
        sprite_name = random.choice(['crate.png', 'barrel.png'])
        self.image = load_image(f'assets/sprites/{sprite_name}', scale=(TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect(topleft = pos)
        self.hitbox = self.rect.inflate(-10, -10)
        self.visible_groups = [g for g in clean_groups if hasattr(g, 'custom_draw') or hasattr(g, 'offset')]
        if not self.visible_groups and clean_groups:
            self.visible_groups = [clean_groups[0]]
        
    def destroy(self):
        if getattr(self, 'destroyed', False):
            return None
        self.destroyed = True
        c_pos = self.rect.center
        v_groups = [g for g in self.visible_groups if g is not None]
        self.kill()
        if hasattr(self, 'level') and hasattr(self.level, 'destroyed_obstacle_positions'):
            self.level.destroyed_obstacle_positions.append([int(self.rect.x), int(self.rect.y)])
        try:
            from src.sound_manager import play_sfx
            play_sfx('break')
        except Exception:
            pass
        try:
            from src.entities import DebrisParticle, Particle
            for _ in range(random.randint(12, 18)):
                vx = random.uniform(-5.5, 5.5)
                vy = random.uniform(-6.5, -2.0)
                col = random.choice([(150, 95, 50), (125, 75, 40), (180, 125, 65), (85, 55, 30)])
                DebrisParticle(c_pos, v_groups, color=col, size=random.randint(4, 9), velocity=(vx, vy), lifetime=random.randint(400, 650))
            for _ in range(8):
                Particle(c_pos, v_groups, color=(140, 125, 110), size=random.randint(3, 5), velocity=(random.uniform(-2, 2), random.uniform(-2, 2)), lifetime=300)
        except Exception:
            pass
        if random.random() < 0.4:
             return "potion"
        return None

class Gold(pygame.sprite.Sprite):
    def __init__(self, pos, groups, amount, player):
        clean_groups = [g for g in groups if g is not None] if groups else []
        super().__init__(clean_groups)
        self.sprite_type = 'item'
        from src.utils import load_image
        self.image = load_image('assets/sprites/item_gold.png', scale=(24, 24))
        self.rect = self.image.get_rect(center = pos)
        self.hitbox = self.rect.inflate(-5, -5)
        self.amount = max(1, int(amount))
        self.player = player
        
    def update(self):
        if not self.player or not hasattr(self.player, 'rect') or not self.player.rect:
            return
        dx = self.rect.centerx - self.player.rect.centerx
        dy = self.rect.centery - self.player.rect.centery
        magnet_bonus = 0
        all_items = list(getattr(self.player, 'inventory', [])) + list(getattr(self.player, 'equipped', {}).values())
        for item in all_items:
            if item:
                eff = getattr(item, 'effects', None)
                if isinstance(eff, dict):
                    magnet_bonus += eff.get('magnet', 0) or 0
        pickup_radius = 50 + magnet_bonus * 35

        if abs(dx) < pickup_radius and abs(dy) < pickup_radius:
            if magnet_bonus > 0:
                pull = pygame.math.Vector2(-dx, -dy)
                if pull.magnitude() > 0:
                    pull = pull.normalize() * (4 + magnet_bonus * 2)
                    self.rect.x += int(pull.x)
                    self.rect.y += int(pull.y)
                    self.hitbox.center = self.rect.center
            p_hitbox = getattr(self.player, 'hitbox', self.player.rect)
            if p_hitbox and self.hitbox.colliderect(p_hitbox):
                self.player.gold = getattr(self.player, 'gold', 0) + self.amount
                try:
                    from src.sound_manager import play_sfx
                    play_sfx('coin')
                except Exception:
                    pass
                self.kill()
