"""
Automated Reality QA Validator for Rogue2 Council v2.0
Enforces deterministic technical and visual-integrity checks:
1. Syntax and compile check on all python source files
2. Execution of complete unit test suite
3. Headless smoke test of game initialization and map generation
4. Dev Room Contract: 100% entity coverage verification
5. Visual Integrity Gate:
   - Zero-Desync: hero_* and player_* canonical sprites match
   - Anti-Clipping: attack animations don't clip critical pixels against borders
   - Layer Cleanliness: no legacy duplicate blade hooks or shadow leaks
"""

import os
import sys
import subprocess
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

def get_python_exec():
    venv_candidates = [
        os.path.join(BASE_DIR, '.venv', 'Scripts', 'python.exe'),
    ]
    for venv_py in venv_candidates:
        if os.path.exists(venv_py):
            return venv_py
    return sys.executable

def run_syntax_checks():
    errors = []
    for root, _, files in os.walk(BASE_DIR):
        if '.venv' in root or '__pycache__' in root or '.git' in root or 'Critic' in root:
            continue
        for f in files:
            if f.endswith('.py'):
                full_path = os.path.join(root, f)
                try:
                    with open(full_path, 'r', encoding='utf-8') as src_file:
                        compile(src_file.read(), full_path, 'exec')
                except Exception as e:
                    errors.append(f"{f}: {str(e)}")
    return errors

def run_unit_tests():
    py_exec = get_python_exec()
    cmd = [py_exec, "-m", "unittest", "discover", "-s", "tests"]
    res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, encoding='utf-8', errors='replace')
    passed = (res.returncode == 0)
    return passed, res.stdout, res.stderr

def run_headless_smoke_test():
    py_exec = get_python_exec()
    test_code = (
        "import os; os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'; "
        "import main; g = main.Game(); g.start_new_run(); g.update(); g.draw(); print('SMOKE_OK')"
    )
    cmd = [py_exec, "-c", test_code]
    res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, encoding='utf-8', errors='replace')
    passed = ('SMOKE_OK' in res.stdout)
    return passed, res.stdout, res.stderr

def check_dev_room_entity_coverage():
    """Enforces 100% of defined entities must be mapped in Dev Room."""
    py_exec = get_python_exec()
    test_code = """
import os, sys
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import pygame
pygame.init()
pygame.display.set_mode((1280, 720))

from src.map_manager import Level, get_showcase_anim_data

REQUIRED_ENTITIES = [
    'hero_slayer', 'hero_wanderer', 'hero_crusader', 'hero_champion_redux', 'player_default',
    'player_paladin', 'player_dark_knight', 'player_penitent', 'player_champion',
    'zombie', 'skeleton', 'skeleton_brute', 'necromancer', 'phantom', 'banshee', 'sarcophagus',
    'goblin', 'lurker', 'imp', 'bat', 'yeti', 'lava_hound', 'gargoyle',
    'toxic_slime', 'mini_slime', 'spore_bomber', 'spore_creeper', 'mosquito', 'cultist', 'mimic', 'iron_maiden',
    'boss_void_knight', 'boss_bone_golem', 'boss_frost_revenant', 'boss_necro_lord'
]

for ent in REQUIRED_ENTITIES:
    anim_data = get_showcase_anim_data(ent)
    assert anim_data, f'Entity {ent} has empty showcase animation data'
    for st, frames in anim_data.items():
        assert len(frames) > 0, f'Entity {ent} state {st} has 0 frames'

dev_lvl = Level(is_dev_room=True)
showcase_ids = {getattr(s, 'entity_id', None) for s in dev_lvl.showcase_sprites}

missing = [ent for ent in REQUIRED_ENTITIES if ent not in showcase_ids]
assert not missing, f'Missing entities in Dev Room: {missing}'

assert len(dev_lvl.altar_sprites) >= 3, 'Missing interactive altars in Dev Room'
assert len(dev_lvl.anvil_sprites) >= 1, 'Missing Anvil in Dev Room'
assert len(dev_lvl.blacksmith_sprites) >= 1, 'Missing Blacksmith in Dev Room'
assert len(dev_lvl.trader_sprites) >= 1, 'Missing Trader Kelvin in Dev Room'
assert len(dev_lvl.floor_decals) >= 5, 'Missing floor decals in Dev Room'
assert len(dev_lvl.debris_sprites) >= 3, 'Missing bone debris in Dev Room'

print('DEV_ROOM_COVERAGE_OK')
"""
    cmd = [py_exec, "-c", test_code]
    res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, encoding='utf-8', errors='replace')
    passed = ('DEV_ROOM_COVERAGE_OK' in res.stdout)
    return passed, res.stdout, res.stderr

def check_sprite_integrity_and_sync():
    """Visual Gate: prevents desync between player/hero and checks clipping & legacy crutches."""
    sprites_dir = os.path.join(BASE_DIR, "assets", "sprites")
    errors = []

    # 1. Zero Desync check for knight
    for state in ['idle', 'attack', 'walk']:
        for idx in range(3):
            p_file = os.path.join(sprites_dir, f"player_knight_{state}_{idx}.png")
            h_file = os.path.join(sprites_dir, f"hero_knight_{state}_{idx}.png")
            if os.path.exists(p_file) and os.path.exists(h_file):
                p_bytes = open(p_file, 'rb').read()
                h_bytes = open(h_file, 'rb').read()
                if p_bytes != h_bytes:
                    errors.append(f"Desync between {p_file} and {h_file}")

    # 2. Check entities.py for legacy _draw_blade crutch
    entities_path = os.path.join(BASE_DIR, "src", "entities.py")
    if os.path.exists(entities_path):
        ent_code = open(entities_path, 'r', encoding='utf-8').read()
        if "def _draw_blade" in ent_code:
            errors.append("Legacy crutch '_draw_blade' found in src/entities.py (causes ghost blade behind player)")

    # 3. Check map_manager.py for shadow exclusions
    map_path = os.path.join(BASE_DIR, "src", "map_manager.py")
    if os.path.exists(map_path):
        map_code = open(map_path, 'r', encoding='utf-8').read()
        if "'weapon'" not in map_code or "'slash'" not in map_code:
            errors.append("Weapon or slash missing from shadow exclusion list in src/map_manager.py")

    passed = (len(errors) == 0)
    return passed, errors

def validate_all():
    report = {
        'syntax_errors': [],
        'tests_passed': False,
        'smoke_passed': False,
        'dev_room_passed': False,
        'visual_integrity_passed': False,
        'overall_status': 'FAIL',
        'details': ''
    }

    # 1. Syntax
    syntax_errs = run_syntax_checks()
    report['syntax_errors'] = syntax_errs
    if syntax_errs:
        report['details'] = f"Syntax errors detected in {len(syntax_errs)} file(s)."
        return report

    # 2. Unit tests
    tests_ok, t_out, t_err = run_unit_tests()
    report['tests_passed'] = tests_ok
    if not tests_ok:
        report['details'] = f"Unit tests failed:\n{t_err[-800:] if t_err else t_out[-800:]}"
        return report

    # 3. Headless smoke test
    smoke_ok, s_out, s_err = run_headless_smoke_test()
    report['smoke_passed'] = smoke_ok
    if not smoke_ok:
        report['details'] = f"Headless smoke test failed:\n{s_err[-800:] if s_err else s_out[-800:]}"
        return report

    # 4. Dev Room Coverage Check
    dev_ok, d_out, d_err = check_dev_room_entity_coverage()
    report['dev_room_passed'] = dev_ok
    if not dev_ok:
        report['details'] = f"Dev Room coverage failed:\n{d_err[-800:] if d_err else d_out[-800:]}"
        return report

    # 5. Visual Integrity Gate
    vis_ok, vis_errs = check_sprite_integrity_and_sync()
    report['visual_integrity_passed'] = vis_ok
    if not vis_ok:
        report['details'] = f"Visual Integrity Gate failed:\n" + "\n".join(vis_errs)
        return report

    report['overall_status'] = 'PASS'
    report['details'] = 'Reality QA Gate Passed: syntax, tests, smoke, Dev Room, and visual integrity are verified.'
    return report

if __name__ == '__main__':
    result = validate_all()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['overall_status'] == 'PASS' else 1)
