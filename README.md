# Rogue2D — Dungeon Descent

Пиксельная игра на Python и Pygame: процедурные подземелья, бои, предметы, торговец, кузница и развитие навыков.

## Скачать игру для Windows

Готовый `Rogue2.exe` находится в [Releases](https://github.com/tolate1/Rogue2D/releases/latest). Скачайте его в отдельную папку и запустите. Python для EXE не требуется. Игра создаёт настройки и сохранения рядом с EXE.

## Запуск из исходников

Требуется Python 3.11. Команды для PowerShell из корня репозитория:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Можно также использовать `run.bat`. NumPy используется для визуальных эффектов. Настройки и сохранения создаются при запуске и исключены из Git.

## Разработка и проверки

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:SDL_VIDEODRIVER = "dummy"
$env:SDL_AUDIODRIVER = "dummy"
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe tools\council\orchestrator.py verify
```

Pillow нужен тестам и инструментам подготовки графики; PyInstaller — сборке EXE.

## Сборка для Windows

```powershell
.\.venv\Scripts\python.exe scripts\build_exe.py
```

Сборщик обновляет `Rogue2.exe` в корне проекта. Для обычного запуска игры используйте новый терминал, если ранее включали фиктивные драйверы SDL для тестов.

## Структура

- `main.py` — запуск и состояния игры.
- `src/` — игровой код.
- `assets/` — спрайты, звуки, шрифты и исходные листы для проверок графики.
- `tests/` — автоматические проверки.
- `tools/` — проверка проекта и инструменты графики.
- `docs/` — техническая и игровая документация.
- `.agents/` — правила и инструкции для разработки.

## Ресурсы

Уведомления о лицензиях сторонних ресурсов сохранены вместе с ними. Пакет UI Kenney содержит [лицензию CC0](assets/sprites/ui_kenney/LICENSE.txt). Общая лицензия на весь проект пока не назначена.
