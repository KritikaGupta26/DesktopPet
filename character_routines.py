"""Finite character performances, with readable setup, action and recovery.

These timelines reference actual artwork poses. They never log water or change
reminder schedules. The application owns interruption and the night schedule.
"""

STORIES = {
    "kungfu_story": ("Kung fu practice", (
        ("greeting", 1.1), ("kung_fu", 5.0), ("balance_on_log", 2.0),
        ("bashful", 1.1), ("victory", 1.5), ("bow", 1.3))),
    "snack_story": ("Secret snack", (
        ("sneak", 1.8), ("dumpling_balance", 2.0), ("dumpling_catch", 1.2),
        ("belly_rub", 2.1), ("happy_idle", 1.5))),
    "noodles": ("Noodle break", (
        ("sit_down", 1.2), ("noodles", 5.0), ("belly_rub", 2.0), ("happy_idle", 1.2))),
    "staff_practice": ("Bamboo staff practice", (
        ("greeting", 1.0), ("staff_ready", 1.2), ("staff_turn", 1.2),
        ("staff_ready", 1.0), ("staff_turn", 1.0), ("bow", 1.3))),
    "balance_story": ("Wobbly balance", (
        ("sit_on_log", 1.6), ("balance_on_log", 3.0),
        ("startled", .8), ("bashful", 1.2), ("victory", 1.4))),
    "butterfly": ("Butterfly curiosity", (
        ("cursor_follow", 1.0), ("butterfly", 4.5), ("wave", 1.5), ("happy_idle", 1.0))),
    "shadow_game": ("Inspect a shadow", (
        ("cursor_follow", 1.2), ("shadow_look", 3.0), ("jump", 2.0),
        ("bashful", 1.1), ("happy_idle", 1.0))),
    "doodle": ("Doodle on a scroll", (
        ("sit_down", 1.2), ("doodle", 6.0), ("victory", 1.5))),
    "side_roll": ("Sideways tumble", (
        ("sit_down", 1.2), ("side_roll", 2.5), ("wake_up", 1.5), ("happy_idle", 1.0))),
    "hero_landing": ("Wobbly heroic landing", (
        ("jump", 2.0), ("hero_landing", 2.0), ("bashful", 1.5), ("bow", 1.2))),
}


def story_duration(key):
    return sum(seconds for _, seconds in STORIES[key][1])


def story_pose(key, elapsed):
    timeline = STORIES[key][1]
    remaining = max(0, elapsed)
    for pose, seconds in timeline:
        if remaining < seconds:
            return pose, remaining
        remaining -= seconds
    return timeline[-1][0], timeline[-1][1]


def routine_pool(enabled, available, hungry=False):
    """Respect saved choices; eating is user initiated when hunger is pending."""
    return tuple(key for key in available if key in enabled
                 and not (hungry and key in ("snack_story", "noodles")))
