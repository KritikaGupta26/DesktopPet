"""Horizontal escape selection and phase-matched travel for short panda legs."""


def escape_target(pet_x, pointer_x, left, right, width=180, distance=240):
    maximum = max(left, right - width)
    center = pet_x + width / 2
    delta = center - pointer_x
    if abs(delta) < 12:
        direction = 1 if maximum - pet_x >= pet_x - left else -1
    else:
        direction = 1 if delta > 0 else -1
    room = maximum - pet_x if direction > 0 else pet_x - left
    other_room = pet_x - left if direction > 0 else maximum - pet_x
    if room < min(80, distance) and other_room > room:
        direction *= -1
    return max(left, min(maximum, pet_x + direction * distance))


def run_step(cycle_seconds, stride=92, tick_seconds=.04):
    return (stride * 180 / 512) / (cycle_seconds * .5) * tick_seconds
