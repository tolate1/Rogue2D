"""Single-source pose selection for the player sprite."""
from dataclasses import dataclass


@dataclass(frozen=True)
class AnimationSample:
    state: str
    frame_index: int
    frame: object
    progress: float
    is_action: bool


class PlayerAnimationController:
    """Select exactly one full-body frame for each animation update."""

    ACTION_PRIORITY = {"dash": 1, "attack": 2}
    LOOP_INTERVAL_MS = {"idle": 200, "walk": 92}

    def __init__(self, idle, walk, attack, dash, now_ms=0):
        self.sequences = {}
        self._actions = {}
        self._loop_state = None
        self._loop_started_at = int(now_ms)
        self._last_sample_time = int(now_ms)
        self.last_sample = None
        self.set_sequences(idle, walk, attack, dash, now_ms=now_ms)

    def set_sequences(self, idle, walk, attack, dash, now_ms=0):
        supplied = {
            "idle": tuple(idle or ()),
            "walk": tuple(walk or ()),
            "attack": tuple(attack or ()),
            "dash": tuple(dash or ()),
        }
        fallback = next((frames for frames in supplied.values() if frames), ())
        self.sequences = {
            state: frames or fallback for state, frames in supplied.items()
        }
        self._actions.clear()
        self._loop_state = None
        self._loop_started_at = int(now_ms)
        self._last_sample_time = int(now_ms)
        self.last_sample = None

    def start_action(self, state, now_ms, duration_ms):
        if state not in self.ACTION_PRIORITY:
            raise ValueError(f"Unsupported player action: {state}")
        duration_ms = max(1, int(duration_ms))
        self._actions[state] = (int(now_ms), duration_ms)

    def frame_count(self, state):
        return len(self.sequences.get(state, ()))

    def action_progress(self, state, now_ms):
        action = self._actions.get(state)
        if action is None:
            return None
        started_at, duration_ms = action
        elapsed = int(now_ms) - started_at
        if elapsed < 0 or elapsed >= duration_ms:
            return None
        return elapsed / float(duration_ms)

    @staticmethod
    def body_lunge_offset(progress, direction):
        """Return a crisp pixel offset: windup back, strike forward, then recover."""
        progress = max(0.0, min(1.0, float(progress)))
        if progress < 0.18:
            distance = -2.0 * (1.0 - progress / 0.18)
        elif progress < 0.62:
            phase = (progress - 0.18) / 0.44
            eased = phase * phase * (3.0 - 2.0 * phase)
            distance = 3.0 * eased
        else:
            phase = (progress - 0.62) / 0.38
            distance = 3.0 * (1.0 - phase) ** 2
        return round(direction[0] * distance), round(direction[1] * distance)

    def sample(self, now_ms, moving, freeze_locomotion=False):
        now_ms = int(now_ms)
        active = []
        for state, (started_at, duration_ms) in tuple(self._actions.items()):
            elapsed = now_ms - started_at
            if elapsed < 0:
                continue
            if elapsed >= duration_ms:
                del self._actions[state]
                continue
            active.append((self.ACTION_PRIORITY[state], started_at, state, elapsed, duration_ms))

        if active:
            _, _, state, elapsed, duration_ms = max(active)
            frames = self.sequences[state]
            frame_index = min(len(frames) - 1, (elapsed * len(frames)) // duration_ms) if frames else 0
            frame = frames[frame_index] if frames else None
            sample = AnimationSample(state, frame_index, frame, elapsed / duration_ms, True)
        else:
            state = "walk" if moving else "idle"
            frames = self.sequences[state]
            if state != self._loop_state:
                self._loop_state = state
                self._loop_started_at = now_ms
            if freeze_locomotion:
                self._loop_started_at += max(0, now_ms - self._last_sample_time)
            interval = self.LOOP_INTERVAL_MS[state]
            elapsed = max(0, now_ms - self._loop_started_at)
            frame_index = (elapsed // interval) % len(frames) if frames else 0
            frame = frames[frame_index] if frames else None
            sample = AnimationSample(state, frame_index, frame, (elapsed % interval) / interval, False)

        self._last_sample_time = now_ms
        self.last_sample = sample
        return sample
