"""Share cards for a bot: 1200x630 link card and 1080x1920 story. Deterministic, local, no network.

Uses the typefaces of the user's own Hermes installation when present (never shipped with this plugin),
otherwise Pillow's built-in font."""
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

BG, INK, MUTED, LIME, LINE = '#0c2420', '#eef3e6', '#9fb5ab', '#c6f36a', '#24423a'


def _font_dirs():
    dirs = []
    # Inside Hermes the CLI package is already loaded; read its location without importing private modules.
    loaded = sys.modules.get('hermes_cli')
    if loaded is not None and getattr(loaded, '__file__', None):
        base = Path(loaded.__file__).resolve().parent / 'web_dist'
        dirs += [base / 'fonts', base / 'fonts-terminal']
    base = Path.home() / '.hermes' / 'hermes-agent' / 'hermes_cli' / 'web_dist'
    return dirs + [base / 'fonts', base / 'fonts-terminal']


_CACHE = {}


def font(role, size):
    """role: wordmark | title | body | mono"""
    names = {'wordmark': ['RulesExpanded-Bold.woff2'], 'title': ['Collapse-Bold.woff2'],
             'body': ['Collapse-Regular.woff2'], 'mono': ['JetBrainsMono-Bold.woff2']}[role]
    key = (role, size)
    if key not in _CACHE:
        found = None
        for directory in _font_dirs():
            for name in names:
                path = directory / name
                if path.is_file():
                    try:
                        found = ImageFont.truetype(str(path), size); break
                    except OSError:
                        pass
            if found:
                break
        _CACHE[key] = found or ImageFont.load_default(size=size)
    return _CACHE[key]


def _wrap(draw, text, fnt, width, limit):
    words, lines, line = str(text).split(), [], ''
    for word in words:
        trial = (line + ' ' + word).strip()
        if draw.textlength(trial, font=fnt) <= width:
            line = trial; continue
        if line: lines.append(line)
        line = word
        while draw.textlength(line, font=fnt) > width and len(line) > 1:  # one very long word
            cut = len(line)
            while cut > 1 and draw.textlength(line[:cut], font=fnt) > width: cut -= 1
            lines.append(line[:cut]); line = line[cut:]
    if line: lines.append(line)
    if len(lines) > limit:
        lines = lines[:limit]
        last = lines[-1]
        while last and draw.textlength(last + '…', font=fnt) > width: last = last[:-1]
        lines[-1] = last.rstrip() + '…'
    return lines


def _facts(info):
    skills = len(info.get('skills', []))
    keys = [e['name'] for e in info.get('env_requires', []) if e.get('required')]
    facts = ([f"{skills} skill" + ('' if skills == 1 else 's')] if skills else []) + \
            ['needs ' + keys[0].replace('_API_KEY', '').replace('_', ' ').lower() + ' key' if keys else 'bring your own model']
    author = str(info.get('author') or '').strip()
    if author and author != 'Not specified':
        facts.insert(0, 'shared by ' + author)
    return facts


def _title(info):
    return str(info.get('name') or 'my-bot').replace('-', ' ').replace('_', ' ').title()


def _brand(draw, x, y, size):
    mark = font('wordmark', size)
    draw.text((x, y), 'BOT DROPS', fill=INK, font=mark)
    w = draw.textlength('BOT DROPS', font=mark)
    draw.text((x + w + size * .7, y), 'FOR HERMES', fill=LIME, font=mark)


def _pill(draw, right, y, text, size):
    fnt = font('mono', size)
    w = draw.textlength(text, font=fnt)
    pad = size * .8
    draw.rounded_rectangle((right - w - 2 * pad, y, right, y + size * 2), radius=size, fill=LIME)
    draw.text((right - w - pad, y + size * .45), text, fill=BG, font=fnt)


AVATAR = Path(__file__).resolve().parent / 'assets' / 'brainarts.png'


def _credit(image, draw, x, y, size):
    """Small sender line: round BrainArts avatar + BY BRAINARTS."""
    fnt = font('mono', size)
    side = int(size * 1.9)
    try:
        with Image.open(AVATAR) as avatar:
            mark = avatar.convert('RGBA').resize((side, side), Image.LANCZOS)
        image.paste(mark, (x, y), mark)
        x += side + int(size * .6)
    except OSError:
        pass
    draw.text((x, y + (side - size) / 2 - 1), 'BY BRAINARTS', fill=MUTED, font=fnt)


def render_card(info, target, credit=True):
    """Link preview card, 1200x630 (X, LinkedIn, Reddit, Bluesky, chat apps)."""
    image = Image.new('RGB', (1200, 630), BG)
    draw = ImageDraw.Draw(image)
    _brand(draw, 64, 58, 22)
    if credit: _credit(image, draw, 64, 94, 14)
    _pill(draw, 1136, 50, 'BOT DROP', 17)
    size = 96
    while size > 52 and len(_wrap(draw, _title(info), font('title', size), 1072, 9)) > 2:
        size -= 4
    y = 150
    title = _wrap(draw, _title(info), font('title', size), 1072, 2)
    for line in title:
        draw.text((64, y), line, fill=INK, font=font('title', size)); y += int(size * 1.02)
    # A short name leaves room: let the one line that says what the bot does be read at thumbnail size.
    roomy = len(title) == 1
    body = font('body', 40 if roomy else 32)
    for line in _wrap(draw, info.get('description') or 'A Hermes bot, ready to make your own.', body, 1040, 3):
        draw.text((64, y + 18), line, fill=MUTED, font=body); y += 52 if roomy else 42
    draw.line((64, 520, 1136, 520), fill=LINE, width=2)
    mono = font('mono', 20)
    cta = 'ADOPT IN YOUR HERMES →'
    room = 1072 - draw.textlength(cta, font=mono) - 48
    facts = _facts(info)
    line = lambda: '   ·   '.join(facts).upper()
    while len(facts) > 1 and draw.textlength(line(), font=mono) > room:
        facts.pop()  # the sharer's name matters most; later facts are also on the page
    text = line()
    while len(text) > 1 and draw.textlength(text, font=mono) > room:
        text = text[:-2].rstrip() + '…'
    draw.text((64, 552), text, fill=MUTED, font=mono)
    draw.text((1136 - draw.textlength(cta, font=mono), 552), cta, fill=LIME, font=mono)
    image.save(target, format='PNG', optimize=True)


def render_story(info, target, credit=True):
    """Instagram/WhatsApp story, 1080x1920. Space at the bottom is left for a link sticker."""
    image = Image.new('RGB', (1080, 1920), BG)
    draw = ImageDraw.Draw(image)
    _brand(draw, 88, 150, 30)
    if credit: _credit(image, draw, 88, 204, 20)
    _pill(draw, 992, 140, 'BOT DROP', 22)
    size = 140
    while size > 72 and len(_wrap(draw, _title(info), font('title', size), 904, 9)) > 3:
        size -= 6
    y = 520
    for line in _wrap(draw, _title(info), font('title', size), 904, 3):
        draw.text((88, y), line, fill=INK, font=font('title', size)); y += int(size * 1.02)
    body = font('body', 46)
    for line in _wrap(draw, info.get('description') or 'A Hermes bot, ready to make your own.', body, 904, 4):
        draw.text((88, y + 30), line, fill=MUTED, font=body); y += 60
    draw.line((88, 1420, 992, 1420), fill=LINE, width=3)
    mono = font('mono', 30)
    for i, fact in enumerate(_facts(info)):
        draw.text((88, 1460 + i * 52), fact.upper(), fill=MUTED, font=mono)
    draw.text((88, 1720), 'TAP THE LINK TO ADOPT IT', fill=LIME, font=mono)
    image.save(target, format='PNG', optimize=True)
