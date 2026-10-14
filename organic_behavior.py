"""Clock-based rest and a fair, varied queue for ambient activities."""
import random


def clock_in_window(now, start, end):
    """Half-open local-time window, including schedules crossing midnight."""
    minute = now.hour * 60 + now.minute
    def minutes(value):
        hour, minute = map(int, value.split(":"))
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError("Use a 24-hour time such as 22:00.")
        return hour * 60 + minute
    first, last = minutes(start), minutes(end)
    if first == last:
        return False
    return first <= minute < last if first < last else minute >= first or minute < last


def activity_delay(minutes, personality, rng=random):
    pace = {"Calm": 1.3, "Balanced": 1.0, "Playful": .8}.get(personality, 1.0)
    return max(30.0, minutes * 60 * pace * rng.uniform(.72, 1.28))


class OrganicQueue:
    """Visit every enabled activity, deferring cooldowns without losing fairness."""
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.pending = []
        self.members = ()
        self.previous = None

    def choose(self, pool, blocked=()):
        members = tuple(dict.fromkeys(pool))
        if members != self.members:
            self.pending = [key for key in self.pending if key in members]
            self.pending.extend(key for key in members if key not in self.members)
            self.members = members
            self.rng.shuffle(self.pending)
        if not self.pending:
            self.pending = list(members)
            self.rng.shuffle(self.pending)
        eligible = [key for key in self.pending if key not in blocked]
        if not eligible:
            return None
        candidates = [key for key in eligible if key != self.previous] or eligible
        key = candidates[0]
        self.pending.remove(key)
        self.previous = key
        return key
