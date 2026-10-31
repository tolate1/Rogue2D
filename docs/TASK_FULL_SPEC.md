<USER_REQUEST>
# Rogue2 — подробное задание на стабилизацию, развитие и визуальную переработку

## 1. Роль, цель и законченный результат

Работай с существующим Rogue2 как разработчик Python/Pygame, геймдизайнер и арт-директор. Требуется реализовать изменения в проекте и проверить их в игре.

Основной цикл:

**Подготовка в убежище → выбор постоянной экипировки → забег → временные реликвии и боевые комбинации → босс или смерть → сохранённые постоянные достижения → следующая попытка.**

Бой остаётся ручным: игрок направляет атаки, двигается, использует рывок и способности. Главный приоритет развития — постоянная экипировка и осмысленные сборки. Внутри забега разнообразие создают реликвии, встречи и решения игрока.

Законченный объём этой итерации:

- Исправленные подтверждённые технические проблемы.
- Постоянный профиль и надёжное продолжение забега.
- Убежище с экипировкой, торговцем и кузнецом.
- Шесть слотов и двенадцать базовых вариантов постоянного снаряжения.
- Два действительно разных вида оружия.
- Одна полностью работающая операция перековки.
- Четыре временные реликвии и две проверенные комбинации.
- Первая глава «Верхние катакомбы»: два этажа, шесть ролей обычных врагов, один босс.
- Обновлённые интерфейс, спрайты, анимации и освещение.
- Подтверждённая проверками сборка либо точный список ограничений окружения.

Этот документ заменяет противоречащие ему пункты прежних планов. Прежний запрет на новые механики больше не относится к перечисленным здесь системам.

Комплекты из пяти вещей, дерево талантов, сокеты, онлайн, кооператив, дополнительные игровые валюты и новые движки не входят в текущую итерацию. Следующие биомы получают краткий план, но не должны задерживать завершение первой главы.

Не останавливайся на одном плане. Реализуй этапы последовательно, сохраняя работоспособность проекта. Не спрашивай «Переходим дальше?» после каждого изменения.

## 2. Правила работы с существующим проектом

Сначала прочитай AGENTS.md, docs/PROJECT_MAP.md, docs/CURRENT_STATE.md, ART_DIRECTION.md при наличии, а также относящиеся к задаче Legacy, juicy-ui-menu и game-lighting-vfx.

Документацию проверяй по исходникам. В последнем проверенном архиве PROJECT_MAP.md описывал старый Random Walk и устаревшее расписание боссов. Старые отчёты не являются доказательством текущего поведения.

Установи:

- Действительный корень запускаемой игры.
- Используемый Python и виртуальное окружение.
- Точку входа и штатный способ сборки.
- Фактический путь загрузки изображений и шрифтов.
- Местоположение сохранений.

Сделай контрольную точку и отдельную резервную копию существующего сохранения. Не работай в старой копии из Trash.

Сохрани Python 3.11, Pygame 2.6.1 и Pillow 10.4.0. Не добавляй зависимости и платные ресурсы без отдельного согласования. Используй существующий src/ui.py и загрузку изображений через src/utils.py.

Item, Player.equipped, equip_item(), unequip_item(), EquipmentModal, ShopModal и BlacksmithModal уже существуют. Расширяй общую систему. Не создавай второй независимый инвентарь.

Небольшие вспомогательные модули допустимы при понятной ответственности. Полное переписывание файлов, переход на ECS и создание универсального игрового фреймворка не требуются.

**Техническое уточнение:** в проверенном архиве переход этажа находится внутри Level.update(), отдельного next_floor() нет. Работай с реальными символами текущей версии.

## 3. Технический аудит: что проверить и исправить

Находки ниже относятся к архиву Rogue2(3).zip. Для каждой установи статус в рабочей версии: подтверждается, уже исправлена либо требует воспроизведения. Затем исправляй подтверждённое.

### 3.1. Нестабильная генерация при одинаковом seed

В Level.create_map() используются set(rooms[1:]) и min по одному расстоянию. При равных расстояниях порядок объектов влияет на выбор следующей комнаты.

Воспроизведено:

- Этаж 1, seed 57: 393 либо 376 клеток пола.
- Этаж 1, seed 157: 310 либо 292 клетки.
- После настоящего Continue сохранённая клетка коридора (15,15) стала стеной.
- Игрока переместила защитная проверка загрузки, а сохранённый враг остался внутри стены.

Исправление:

- Постоянные индексы комнат.
- Стабильный порядок обхода.
- Явное разрешение равных расстояний.
- Стабильный порядок элементов перед случайным выбором.
- Отдельные источники случайности карты, добычи, перековки и декоративных эффектов.

Дополнительные частицы, открытие меню и частота кадров не должны менять геометрию или уже определённую награду.

Проверяй одинаковые номер этажа, seed и версию генератора в повторных вызовах и отдельных процессах. Сравнивай пол, стены и исходные размещения значимых объектов.

### 3.2. Сохранение несовместимой геометрии

Проверяй позиции восстановленных игрока, врагов и других сохраняемых сущностей с их настоящими хитбоксами.

Исправление алгоритма может изменить карту старого сохранения. Нужны версия генератора и явная обработка несовместимости. Если исходную геометрию невозможно восстановить из одного seed, не обещай точное продолжение. Сохрани исходный файл.

Перенос сущности из стены допустим как защитное восстановление повреждённых данных, но не заменяет детерминированную генерацию.

### 3.3. Выход не выбирается по расстоянию

В проверенном коде берётся rooms[-1], хотя комментарий обещает дальнюю комнату. На seed 1 расстояние до выбранной комнаты составляло 13 шагов, до наиболее дальней — 49.

Выбирай выход с учётом пути по проходимому графу и структуры главы. До выхода и обязательных наград должен существовать путь с реальным хитбоксом игрока. Особые правила босса задавай явно.

### 3.4. Открытие магазина покупает лечение

В Level.update() перед open_modal('shop') вызывается interact_trader(1).

Проверенный пример: **100 G и 25 HP → одно нажатие E → 50 G и 75 HP.**

Клавиша E должна только открывать окно. Открытие, закрытие, наведение и выбор карточки не изменяют деньги, здоровье или предметы. Покупка выполняется отдельным действием один раз.

Старые горячие клавиши покупки не должны обходить это правило или конфликтовать с инвентарём.

### 3.5. Неверный расчёт и потеря экипировки

recalculate_stats() учитывает надетое снаряжение и вещи в рюкзаке. Снятый предмет продолжает давать бонусы.

Сохранение и переход этажа переносят inventory без полноценного сохранения equipped.

Исправь единственный учёт экипировки, сохранение экземпляров и пересчёт после загрузки. Надевание, снятие, сортировка и смена этажа не создают копий и не теряют вещи.

### 3.6. Ошибки UI и времени

Устрани:

- Двойную отрисовку модалки из Level.draw() и основного рендера.
- Двойное затемнение и обновление её анимаций.
- Срабатывание клика по устаревшему hover.
- Расхождение расчёта строк инвентаря при рисовании и обработке клика примерно на 21 px.

Используй координаты самого события и общие прямоугольники элементов.

Отдельно воспроизведи риск таймеров после длительного открытия модалки. Боевые эффекты не должны истекать или догонять пропущенные секунды, если игра считается поставленной на паузу. Это проверяемый риск, а не уже доказанный результат.

### 3.7. Генераторы ресурсов и кэш

Повторный запуск scripts/generate_sprites.py в отдельной копии изменил текущие skeleton_0/1, floor, chest и chest_open. Он не воспроизводит актуальный комплект изображений.

Часть генераторов использует старые абсолютные пути, часть записывает PNG при импорте.

Требуется:

- Явный project_root/output_dir.
- Отсутствие записи при импорте.
- Каталог кандидатов для новых вариантов.
- Замена только перечисленных проверенных ресурсов.
- Защита одобренных сундука и логотипа.

В src/utils.py неудачная загрузка кэшируется как magenta-заглушка. Созданный позже файл не подхватывается до очистки кэша или нового процесса. Исправь обработку неудачной загрузки и инвалидацию. Проверка обязательных ресурсов должна выявлять отсутствие настоящего изображения.

### 3.8. Бой и физика

Проверь инерцию при отпущенных кнопках, разворот у стены, диагональное скольжение, углы, рывок, расталкивание мобов, обход препятствий, стрельбу через стены, быстрые снаряды, повторный урон одного взмаха и действия убитого ультой врага.

Не приписывай текущей версии все ошибки из истории. Добавляй исправление вместе с воспроизведением конкретного поведения.

## 4. Правила профиля, забега и переходов

Постоянный профиль и активный забег — разные логические состояния. Их можно хранить в одном версионированном JSON.

**Профиль содержит:**

- Реестр экземпляров постоянного снаряжения.
- Выбранные слоты экипировки.
- Постоянные материалы.
- Открытые рецепты, варианты вещей и главы.
- Незавершённую операцию кузницы, если она существует.
- Результат последнего завершённого забега.

**Активный забег содержит:**

- run_id, chapter_id, этаж, seed и версию генератора.
- Выбранное снаряжение или его согласованный снимок.
- HP, энергию, опыт, уровень и счётчики.
- Временные реликвии, эффекты и их состояния.
- Монеты забега.
- Состояние комнат, врагов, предметов и значимых опасностей.
- Отметки уже выданных наград.

**Правила переходов:**

- Начало попытки создаёт новый run_id, уровень 1, свежие временные состояния и стартовые HP/энергию по экипировке.
- Смена этажа сохраняет снаряжение, реликвии, монеты и состояние героя.
- Выход через меню сохраняет незавершённую попытку.
- Continue восстанавливает именно её, включая временные реликвии.
- Смерть завершает попытку и очищает временное состояние.
- Победа завершает главу, фиксирует открытия и возвращает в убежище.
- Постоянные вещи и уже зачисленные материалы остаются после смерти и победы.
- Полный сброс профиля существует только как отдельное явно названное действие.

Сейчас start_new_run() и game_over вызывают delete_save(). Переработай это место: удаление текущего забега не должно удалять профиль.

Постоянную экипировку в этой версии меняют в убежище. Во время забега она отображается, но не перековывается и не переставляется. Continue использует неизменяемый выбор снаряжения этой попытки. Услуги убежища недоступны до завершения или явного отказа от активного забега. Расходники и временные реликвии работают внутри попытки.

## 5. Надёжные сохранения и однократные операции

Введи версию схемы данных, версию генератора и идентификаторы операций, которым нужна защита от повторного выполнения.

Сохраняй простые данные: строки, числа, списки и словари. Не сериализуй Pygame Surface, Sprite, ссылки на объекты и абсолютные значения времени текущего процесса.

Для таймеров сохраняй оставшуюся длительность и состояние действия. Время, пока приложение закрыто, не расходует игровые кулдауны /plan 
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-10-29T18:06:13+03:00.

The user has mentioned some items in the form @[ITEM]. Here is extra information about the items that were mentioned by the user, in the order that they appear:

/plan is a [Slash Command]:
<PLAN>The user is requesting that you think and plan carefully before executing the upcoming task.
Carefully research the task, make sure that you and the user are aligned on the goals and requirements,
create a detailed implementation plan artifact, and get user approval on the plan before making any code changes (besides artifacts)
or running any modifying commands.

# Guidelines
- Establish a shared understanding of the task with the user. If there are any ambiguities, underspecified requirements,
or implicit assumptions, clarify them with the user before proceeding.
- Thoroughly research the codebase to establish a solid understanding of the relevant components, systems, dependencies, and architecture.
As you research, provide verbal updates of your research steps and thought process with the user, so they can follow along.
- Create an implementation plan artifact that outlines your proposed execution strategy.
Set request_feedback = true and user_facing = true in the ArtifactMetadata. The user will automatically
see any new and modified plans you create, so DO NOT re-summarize the plan.
- Only after the user explicitly approves the plan should you proceed to execution.
- Verify that your changes have the desired effects e.g. run unit tests, make sure code builds, etc. before claiming that the task is complete.
- After you've completed your task and verified that your solution works, create a walkthrough artifact to summarize your work.

# Planning Mode Artifacts
When in planning mode, you should create two special artifacts.

# Implementation Plan
Path: <Artifact Directory>/<plan_name>.md

**Purpose**: A technical design document to present your implementation plan to the user for feedback and approval.
After reading the document, the user should understand the key technical details of your plan, and be able to make an informed decision on whether to approve it.
This document should be very detailed, including code snippets, diffs, mermaid diagrams, verification strategies, and background information.

**Format**: Use the following format, omitting any irrelevant sections:

## [Goal Description]
Provide a brief description of the problem, any background context, and what the change accomplishes.

## User Review Required
Document anything that requires user review or feedback, for example, breaking changes or significant design decisions. Use GitHub alerts (IMPORTANT/WARNING/CAUTION) to highlight critical items.

## Open Questions
Any clarifying or design questions for the user that will impact the implementation plan. Use GitHub alerts (IMPORTANT/WARNING/CAUTION) to highlight critical items.

## Proposed Changes
Group files by component (e.g., package, feature area, dependency layer) and order logically (dependencies first). Separate components with horizontal rules for visual clarity.

### [Component Name]
Summary of what will change in this component with explicit code snippets and diffs. For specific files, Use [NEW] and [DELETE] to demarcate new and deleted files, for example:
#### [MODIFY] file basename
#### [NEW] file basename
#### [DELETE] file basename

## Verification Plan
Summary of how you will verify that your changes have the desired effects.

### Automated Tests
Exact commands to run automated tests

### Manual Verification
Instructions for what the user should manually verify.

# Walkthrough
Path: <Artifact Directory>/walkthrough.md

**Purpose**: After completing work, summarize what you accomplished. Update an existing walkthrough for related follow-up work rather than creating a new one.

**Document**:
- Changes made
- What was tested
- Validation results

Embed screenshots and recordings to visually demonstrate UI changes and user flows.</PLAN>
</ADDITIONAL_METADATA>