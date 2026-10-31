import os
import sys
import pygame
from src.utils import get_asset_path

class SoundManager:
    _instance = None

    def __init__(self):
        self.enabled = False
        self.sounds = {}
        self._last_played = {}
        self.music_loaded = False
        self.sfx_volume = 0.7
        self.music_volume = 0.45
        
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.enabled = True
        except Exception:
            self.enabled = False

        if self.enabled:
            sound_dir = get_asset_path(os.path.join('assets', 'sounds'))
            sound_files = {
                'hit': 'hit.wav',
                'hit_heavy': 'hit_heavy.wav',
                'crit': 'crit.wav',
                'sword_swing': 'sword_swing.wav',
                'attack': 'attack.wav',
                'claymore_swing': 'claymore_swing.wav',
                'skeleton_hit': 'skeleton_hit.wav',
                'shoot': 'shoot.wav',
                'dash': 'dash.wav',
                'shield': 'shield.wav',
                'ult': 'ult.wav',
                'coin': 'coin.wav',
                'chest': 'chest.wav',
                'break': 'break.wav',
                'potion': 'potion.wav',
                'stairs': 'stairs.wav',
                'level_up': 'level_up.wav',
                'game_over': 'game_over.wav',
                'step': 'step.wav',
                'step_0': 'step_0.wav',
                'step_1': 'step_1.wav',
                'step_2': 'step_2.wav',
                'step_3': 'step_3.wav',
                'enemy_die': 'enemy_die.wav',
                'slime_leap': 'slime_leap.wav',
                'slime_land': 'slime_land.wav',
                'zombie_attack': 'zombie_attack.wav',
                'boss_cleave': 'boss_cleave.wav',
                'frost_cast': 'frost_cast.wav',
                'void_burst': 'void_burst.wav',
                'spear_thrust': 'spear_thrust.wav',
                'dagger_slash': 'dagger_slash.wav',
                'spore_explode': 'spore_explode.wav',
                'necro_cast': 'necro_cast.wav',
                'anvil': 'anvil.wav',
                'heartbeat': 'heartbeat.wav',
                'altar': 'altar.wav',
                'lightning': 'lightning.wav',
                'flame': 'flame.wav',
                'soul_absorb': 'soul_absorb.wav',
                'water_drip': 'water_drip.wav',
                'debris_crunch': 'debris_crunch.wav'
            }
            sound_names = list(sound_files.keys())
            for name in sound_names:
                ogg_path = os.path.join(sound_dir, f"{name}.ogg")
                wav_path = os.path.join(sound_dir, f"{name}.wav")
                target_path = None
                if os.path.exists(wav_path) and os.path.exists(ogg_path):
                    target_path = wav_path if os.path.getmtime(wav_path) >= os.path.getmtime(ogg_path) else ogg_path
                elif os.path.exists(wav_path):
                    target_path = wav_path
                elif os.path.exists(ogg_path):
                    target_path = ogg_path

                if target_path:
                    try:
                        snd = pygame.mixer.Sound(target_path)
                        snd.set_volume(self.sfx_volume)
                        self.sounds[name] = snd
                    except Exception:
                        pass
            
            # Background Music Setup
            bgm_path = os.path.join(sound_dir, 'bgm.wav')
            if os.path.exists(bgm_path):
                try:
                    pygame.mixer.music.load(bgm_path)
                    pygame.mixer.music.set_volume(self.music_volume)
                    self.music_loaded = True
                except Exception:
                    self.music_loaded = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SoundManager()
        return cls._instance

    def play(self, name):
        if not self.enabled:
            return
        now = pygame.time.get_ticks()
        if now - self._last_played.get(name, 0) < 55:  # Sound throttle (§7.5): prevents audio clipping
            return
        self._last_played[name] = now
        if name == 'step':
            step_idx = getattr(self, '_step_idx', 0)
            step_name = f'step_{step_idx % 4}'
            self._step_idx = step_idx + 1
            sound = self.sounds.get(step_name) or self.sounds.get('step')
        else:
            sound = self.sounds.get(name)
        if sound:
            try:
                sound.play()
            except Exception:
                pass

    def play_music(self, loop=True):
        if not self.enabled or not self.music_loaded:
            return
        try:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1 if loop else 0)
        except Exception:
            pass

    def stop_music(self):
        if not self.enabled or not self.music_loaded:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def set_master_volume(self, vol):
        self.master_volume = max(0.0, min(1.0, vol))
        self.set_sfx_volume(self.sfx_volume)
        self.set_music_volume(self.music_volume)

    def get_master_volume(self):
        return getattr(self, 'master_volume', 0.8)

    def set_sfx_volume(self, vol):
        self.sfx_volume = max(0.0, min(1.0, vol))
        master = getattr(self, 'master_volume', 0.8)
        eff_vol = self.sfx_volume * master
        for snd in self.sounds.values():
            try:
                snd.set_volume(eff_vol)
            except Exception:
                pass

    def get_sfx_volume(self):
        return getattr(self, 'sfx_volume', 0.7)

    def set_music_volume(self, vol):
        self.music_volume = max(0.0, min(1.0, vol))
        master = getattr(self, 'master_volume', 0.8)
        eff_vol = self.music_volume * master
        if self.enabled and self.music_loaded:
            try:
                pygame.mixer.music.set_volume(eff_vol)
            except Exception:
                pass

    def get_music_volume(self):
        return getattr(self, 'music_volume', 0.5)

def play_sfx(name):
    SoundManager.get_instance().play(name)

def start_bgm():
    SoundManager.get_instance().play_music(loop=True)

def stop_bgm():
    SoundManager.get_instance().stop_music()

def set_sfx_volume(vol):
    SoundManager.get_instance().set_sfx_volume(vol)

def get_sfx_volume():
    return SoundManager.get_instance().get_sfx_volume()

def set_music_volume(vol):
    SoundManager.get_instance().set_music_volume(vol)

def get_music_volume():
    return SoundManager.get_instance().get_music_volume()

def set_master_volume(vol):
    SoundManager.get_instance().set_master_volume(vol)

def get_master_volume():
    return SoundManager.get_instance().get_master_volume()
