import pygame
import os
import sys

BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_image_cache = {}
_placeholder_keys = set()

def clear_image_cache():
    """Clears cached surfaces and resets placeholder tracking."""
    global _image_cache, _placeholder_keys
    _image_cache.clear()
    _placeholder_keys.clear()

def get_asset_path(path):
    if os.path.isabs(path):
        return path
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        cand = os.path.join(exe_dir, path)
        if os.path.exists(cand):
            return cand
    if os.path.exists(path):
        return path
    candidate = os.path.join(BASE_DIR, path)
    if os.path.exists(candidate):
        return candidate
    if hasattr(sys, '_MEIPASS'):
        cand_mei = os.path.join(sys._MEIPASS, path)
        if os.path.exists(cand_mei):
            return cand_mei
    return path

def load_image(path, scale=None):
    global _image_cache, _placeholder_keys
    resolved_path = get_asset_path(path)

    # Re-check disk existence if previously registered as placeholder (non-poisoning cache)
    if resolved_path in _placeholder_keys and os.path.exists(resolved_path):
        _placeholder_keys.discard(resolved_path)
        _image_cache.pop(resolved_path, None)

    if resolved_path not in _image_cache:
        try:
            # Use convert_alpha for transparency
            image = pygame.image.load(resolved_path).convert_alpha()
            _image_cache[resolved_path] = image
        except (FileNotFoundError, pygame.error) as e:
            # Create a placeholder and record it so it won't permanently poison the cache
            surf = pygame.Surface((32, 32))
            surf.fill((255, 0, 255)) # Magenta for missing
            _image_cache[resolved_path] = surf
            _placeholder_keys.add(resolved_path)
            
    image = _image_cache[resolved_path]
    if scale:
         # Note: We are not caching scaled versions here for simplicity, 
         # but avoiding disk read is the big win.
         image = pygame.transform.scale(image, scale)
    return image

def import_folder(path):
    resolved_path = get_asset_path(path)
    surface_list = []
    for _, __, img_files in os.walk(resolved_path):
        for image in img_files:
            full_path = os.path.join(resolved_path, image)
            image_surf = load_image(full_path)
            surface_list.append(image_surf)
    return surface_list
