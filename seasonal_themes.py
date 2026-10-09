"""Offline, deterministic desktop-panda theme calendar.

Lunar festival dates are curated for New Delhi, India in 2026/2027.
They are not astronomical calculations. Local/custom dates override the table.
"""
from datetime import date, timedelta
from calendar import isleap

# label, cloud tint, accent, thematic activity, two original dialogue lines
THEMES = {
    'classic': ('Classic panda', '#FFF9EF', '#B7A1CC', None, ('A little bamboo, a little peace.', 'Happy to keep you company.')),
    'autumn': ('Autumn', '#FFF2DF', '#CE894D', 'groom', ('Pumpkin season. Cozy paws, cozy day.', 'A little leaf watching between tasks?')),
    'spooky': ('Spooky season', '#F3EAFE', '#9670C3', 'peekaboo', ('Boo! Only friendly panda surprises.', 'Pumpkins and tiny adventures today.')),
    'diwali': ('Diwali', '#FFF2D9', '#D39A3D', 'victory', ('Happy Diwali! A little light for your day.', 'Warm wishes, bright lights, happy paws.')),
    'holi': ('Holi', '#FFF0F5', '#D686B8', 'dance', ('Happy Holi! Let us add some colour.', 'Colourful wishes from your little panda.')),
    'navratri': ('Navratri', '#FFF0E9', '#D88C63', 'dance', ('Happy Navratri! A little dance break?', 'Nine nights of colour and joy.')),
    'thanksgiving': ('Thanksgiving', '#FFF2E3', '#C59160', 'bow', ('Thankful for bamboo and your company.', 'A small pause for something good today.')),
    'christmas': ('Christmas', '#FFF1EF', '#CC7B7B', 'victory', ('Merry Christmas! A gift-sized smile.', 'Cozy wishes and a little panda cheer.')),
    'new_year': ('New Year', '#FFF6DB', '#C49F4D', 'victory', ('Happy New Year! One gentle step at a time.', 'A fresh start, with bamboo on the side.')),
    'valentine': ("Valentine's Day", '#FFF0F4', '#D58EAA', 'blow_kiss', ('A little love for your day.', 'You deserve a kind moment today.')),
    'birthday': ('Birthday', '#FFF0F6', '#C58DC3', 'victory', ('Happy birthday! A big panda hug.', 'Cake for you, bamboo for me!')),
    'ganesh': ('Ganesh Chaturthi', '#FFF3E1', '#D1A254', 'bow', ('Warm wishes for Ganesh Chaturthi.', 'A hopeful beginning and a peaceful day.')),
    'krishna': ('Krishna Janmashtami', '#ECF8F4', '#6FA99C', 'dance', ('Happy Janmashtami! Joyful wishes.', 'A little melody and a gentle smile.')),
    'shiva': ('Maha Shivaratri', '#EFF1FD', '#8C93BF', 'meditate', ('Peaceful wishes for Maha Shivaratri.', 'A quiet breath and a calm moment.')),
    'spring': ('Spring', '#FFF1F5', '#BD96AD', 'wave', ('New blossoms, fresh little steps.', 'A small fresh start today.')),
    'summer': ('Summer', '#FFF8DD', '#CAB459', 'wave', ('Sunny days, gentle breaks.', 'A little shade and some bamboo.')),
    'winter': ('Winter', '#F0F7FD', '#8BAFC6', 'wind_down', ('Cozy paws for a cool day.', 'Time for a warm, quiet moment.')),
}
PROP_KEYS = tuple(key for key in THEMES if key != 'classic')
LUNAR_KEYS = ('diwali', 'holi', 'navratri', 'ganesh', 'krishna', 'shiva')
CALENDAR_SOURCES = {
    year: f'https://www.drikpanchang.com/calendars/hindu/hinducalendar.html?geoname-id=1261481&year={year}'
    for year in (2026, 2027)
}
FESTIVAL_RANGES = {
    2026: {'diwali': [('11-06','11-11')], 'holi': [('03-03','03-04')],
           'navratri': [('03-19','03-27'),('10-11','10-19')],
           'ganesh': [('09-14','09-25')], 'krishna': [('09-04','09-04')], 'shiva': [('02-15','02-15')]},
    2027: {'diwali': [('10-27','10-31')], 'holi': [('03-21','03-22')],
           'navratri': [('04-07','04-15'),('09-30','10-08')],
           'ganesh': [('09-04','09-14')], 'krishna': [('08-25','08-25')], 'shiva': [('03-06','03-06')]},
}

def valid_birthday(value):
    if not value:
        return ''
    try:
        value = str(value).strip()
        date.fromisoformat('2000-' + value)
        if len(value) != 5:
            raise ValueError
        return value
    except (ValueError, TypeError):
        raise ValueError('Use MM-DD for the birthday, or leave it blank.')

def normalize_custom_dates(raw):
    result = {}
    if isinstance(raw, dict):
        for key, ranges in raw.items():
            if key not in LUNAR_KEYS or not isinstance(ranges, list):
                continue
            good = []
            for pair in ranges:
                if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                    continue
                try:
                    start, end = (date.fromisoformat(str(value)) for value in pair)
                    if 0 <= (end-start).days <= 31:
                        good.append([start.isoformat(), end.isoformat()])
                except (ValueError, TypeError):
                    pass
            if good:
                result[key] = good
    return result

def festival_ranges(key, year, custom=None):
    overrides = normalize_custom_dates(custom).get(key, [])
    overrides = [(date.fromisoformat(a), date.fromisoformat(b)) for a, b in overrides
                 if date.fromisoformat(a).year == year or date.fromisoformat(b).year == year]
    if overrides:
        return overrides
    return [(date.fromisoformat(f'{year}-{a}'), date.fromisoformat(f'{year}-{b}'))
            for a, b in FESTIVAL_RANGES.get(year, {}).get(key, [])]

def resolve_theme(day, mode='Auto', birthday='', enabled=None, custom=None, hemisphere='Northern', thanksgiving='US'):
    if mode in THEMES:
        return mode
    enabled = set(THEMES) if enabled is None else set(enabled)
    # Personal celebrations win over calendar events, which win over seasons.
    try:
        birth = valid_birthday(birthday)
    except ValueError:
        birth = ''
    if birth and 'birthday' in enabled:
        month, number = map(int, birth.split('-'))
        observed = 28 if month == 2 and number == 29 and not isleap(day.year) else number
        if day.month == month and day.day == observed:
            return 'birthday'
    for key in LUNAR_KEYS:
        if key in enabled and any(start <= day <= end for start, end in festival_ranges(key, day.year, custom)):
            return key
    if 'new_year' in enabled and ((day.month == 12 and day.day == 31) or (day.month == 1 and day.day <= 3)):
        return 'new_year'
    if 'christmas' in enabled and day.month == 12 and 15 <= day.day <= 30:
        return 'christmas'
    if 'valentine' in enabled and day.month == 2 and 12 <= day.day <= 14:
        return 'valentine'
    if 'thanksgiving' in enabled:
        month, occurrence = (10, 2) if thanksgiving == 'Canada' else (11, 4)
        weekday = 0 if thanksgiving == 'Canada' else 3
        first = date(day.year, month, 1)
        holiday = first + timedelta(days=(weekday-first.weekday()) % 7 + 7*(occurrence-1))
        if holiday <= day <= holiday + timedelta(days=2):
            return 'thanksgiving'
    if 'spooky' in enabled and day.month == 10 and day.day >= 24:
        return 'spooky'
    season = ('winter' if day.month in (12,1,2) else 'spring' if day.month in (3,4,5)
              else 'summer' if day.month in (6,7,8) else 'autumn')
    if hemisphere == 'Southern':
        season = {'winter':'summer','summer':'winter','spring':'autumn','autumn':'spring'}[season]
    return season if season in enabled else 'classic'
