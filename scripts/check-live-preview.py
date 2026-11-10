"""Preview a published bot for real: clone it from GitHub, read it, draw its card. Nothing is installed.

Usage: python scripts/check-live-preview.py https://<owner>.github.io/<bot>/
Runs against a throwaway folder, never against your Hermes home.
"""
from pathlib import Path
import re
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from drops_v2.card import render_card  # noqa: E402
from drops_v2.core import Drops  # noqa: E402

link = sys.argv[1]
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
    drops = Drops(Path(temp) / 'home', hermes='hermes')  # the Hermes program is only needed to adopt
    info = drops.preview(link)
    assert re.fullmatch(r'[0-9a-f]{40}', info['commit']), info['commit']
    assert info['status'] == 'review' and info['skills'], info
    card = Path(temp) / 'card.png'
    render_card(info, card)
    assert card.stat().st_size > 10_000
    print('ok', info['name'], info['version'], info['commit'][:7], len(info['skills']), 'skills,', info['file_count'], 'files')
