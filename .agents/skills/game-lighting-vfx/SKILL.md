---
name: game-lighting-vfx
description: Архитектура атмосферного освещения, масок тьмы (BLEND_RGBA_SUB/ADD), мерцания факелов, объемного тумана и эффектов взрывных волн в Pygame.
---

# Скилл "game-lighting-vfx" — Атмосферный свет и визуальные эффекты в Pygame

Этот скилл содержит проверенные математические паттерны и техники отрисовки, позволяющие добиться глубокой мрачной атмосферы (Dark Fantasy) без падения FPS и без «плоских желтых кругов».

---

## 1. Архитектура «Слой Тьмы» (Lighting via Subtractive & Additive Blending)

Никогда не рисуйте свет поверх игрового мира непрозрачными цветными фигурами! Правильный конвейер света:

### Шаг 1: Подготовка кэшированных радиальных масок
Перед игровым циклом один раз генерируются гладкие текстуры градиента света (мягкое затухание от центра к краю):

```python
def create_radial_light_mask(radius, color=(255, 180, 70), max_alpha=200):
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        factor = (r / radius) ** 1.5  # Нелинейное сглаживание к краям
        alpha = int(max_alpha * (1.0 - factor))
        pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
    return surf
```

### Шаг 2: Композитинг слоя освещения в кадре
В методе отрисовки карты (`draw`):
```python
# 1. Создаем поверхность тьмы под размер экрана
darkness = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
# Заливаем цветом ночи/склепа (глубокий индиго вместо 100% черного)
darkness.fill((10, 8, 16))

# 2. Вырезаем тьму вокруг источников света (Фонарь игрока, факелы)
# Используем BLEND_RGBA_SUB или рисование альфа-маски
darkness.blit(light_mask, (light_screen_x - radius, light_screen_y - radius), special_flags=pygame.BLEND_RGBA_SUB)

# 3. Накладываем тьму поверх отрендеренной карты и персонажей
display.blit(darkness, (0, 0), special_flags=pygame.BLEND_MULT)

# 4. Легкое теплое свечение накладываем аддитивно (золотые блики на факелах)
display.blit(torch_bloom, (torch_screen_x - bloom_r, torch_screen_y - bloom_r), special_flags=pygame.BLEND_RGBA_ADD)
```

---

## 2. Живое мерцание факелов (Torch Flame Jitter)

Чтобы факелы не выглядели статично, их радиус и интенсивность должны непрерывно «дышать»:

```python
# Двойная гармоника синусоид для нерегулярного органичного мерцания
flicker = math.sin(time_ms * 0.008) * 3.5 + math.sin(time_ms * 0.021) * 2.0
current_radius = base_radius + int(flicker)
```

---

## 3. Объемный воздух: Пылинки в лучах (Dust Motes & Ash)

В освещенных комнатах подземелья воздух не должен быть пустым.
- Спавнить 20–30 микрочастиц размером 1–2 пикселя цвета слоновой кости/пепла `(190, 180, 160)`.
- Они медленно поднимаются и дрейфуют горизонтально:
  ```python
  self.x += math.sin(self.time + self.seed) * 0.3
  self.y -= self.rise_speed  # 0.2 - 0.5 px/frame
  ```
- **Правило видимости**: Пылинка рисуется только тогда, когда находится в радиусе света от факела или фонаря.

---

## 4. Эффект Ударной Волны (Shockwave / Screen Distortion)

При повышении уровня, критах или взрыве бочки:

1. **Кольцо искажения**:
   - Растущее кольцо с шириной обода 3–6 px.
   - Радиус увеличивается со временем: `radius += speed * dt`.
   - Прозрачность падает от 220 до 0.
2. **Camera Shake (Тряска экрана)**:
   - Не дергать экран резко! Применять затухающую синусоиду:
     ```python
     shake_x = math.sin(shake_timer * 0.5) * current_intensity
     shake_y = math.cos(shake_timer * 0.7) * current_intensity
     current_intensity *= 0.88  # Быстрое затухание
     ```
3. **Хитстоп (Freeze Frame)**:
   - При мощном сокрушительном ударе игра замирает на 2–3 кадра (30–50 мс). Это дает максимальное физическое ощущение силы попадания.
