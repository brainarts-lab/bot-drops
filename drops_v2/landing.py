"""The public page of a shared bot (GitHub Pages). Self-contained: no external assets, fonts or trackers.

Rendered twice: once in the local package (links unknown, the page derives them from its Pages address),
and again right before upload with the final repository and page links, so link previews on X, LinkedIn,
Reddit and chat apps can show the card (they need absolute image URLs)."""
import base64
from html import escape
import json
from pathlib import Path
import re

DASHBOARD = 'http://127.0.0.1:9119/drops/import'
# Credit line on shared pages and cards (the sharer can turn it off).
CREDIT_NAME = 'BrainArts'
CREDIT_URL = 'https://x.com/chrisbrainarts'
CREDIT_AVATAR = Path(__file__).resolve().parent / 'assets' / 'brainarts-48.png'


def _avatar_uri():
    try: return 'data:image/png;base64,' + base64.b64encode(CREDIT_AVATAR.read_bytes()).decode()
    except OSError: return ''
# Where people get the Bot Drops plugin. Must be a public repository before real sharing starts.
PLUGIN_REPO = 'https://github.com/brainarts-lab/bot-drops'


def title_of(info):
    return str(info.get('name') or 'my-bot').replace('-', ' ').replace('_', ' ').title()


def post_text(info, link):
    description = ' '.join(str(info.get('description') or '').split())
    if len(description) > 140:
        description = description[:139].rsplit(' ', 1)[0] + '…'
    head = 'I made a Hermes bot: ' + title_of(info) + '.'
    return (head + (' ' + description if description else '') + '\nAdopt it in your own Hermes: ' + link).strip()


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ · Bot Drops for Hermes</title>
<meta name="description" content="__DESCRIPTION__">
<meta property="og:type" content="website"><meta property="og:site_name" content="Bot Drops for Hermes">
<meta property="og:title" content="__TITLE__ · a Hermes bot"><meta property="og:description" content="__DESCRIPTION__">
<meta property="og:image" content="__IMAGE__"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
__OGURL__<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="__IMAGE__">
<style>
:root{--bg:#0c2420;--panel:#11302a;--ink:#eef3e6;--muted:#9fb5ab;--line:#24423a;--lime:#c6f36a}
*{box-sizing:border-box}html{background:var(--bg)}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:720px;margin:0 auto;padding:28px 16px 56px}
.brand{display:flex;justify-content:space-between;align-items:center;font:600 13px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.14em}
.brand b{color:var(--lime);font-weight:600}.pill{background:var(--lime);color:var(--bg);border-radius:20px;padding:6px 12px}
h1{font:600 clamp(38px,9vw,64px)/1.02 ui-serif,Georgia,"Times New Roman",serif;margin:40px 0 12px;letter-spacing:-.01em}
.lead{color:var(--muted);font-size:19px;margin:0 0 18px}
.facts{font:600 12px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.1em;color:var(--muted);text-transform:uppercase}
img{display:block;width:100%;height:auto;border-radius:14px;border:1px solid var(--line);margin:26px 0}
.btn{font:inherit;font-weight:600;min-height:52px;padding:0 22px;border-radius:12px;border:1px solid var(--lime);background:var(--lime);color:var(--bg);cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:8px;text-decoration:none}
.btn.ghost{background:transparent;color:var(--ink);border-color:var(--line)}.btn:focus-visible{outline:3px solid var(--ink);outline-offset:2px}
.row{display:flex;gap:10px;flex-wrap:wrap}.primary .btn{flex:1 1 220px}
ul.steps{list-style:none;padding:0;margin:16px 0 0;color:var(--muted);font-size:15px}ul.steps li{padding:4px 0 4px 22px;position:relative}ul.steps li:before{content:"";position:absolute;left:4px;top:13px;width:6px;height:6px;border-radius:3px;background:var(--lime)}
section{border-top:1px solid var(--line);margin-top:32px;padding-top:24px}h2{font-size:15px;margin:0 0 12px;letter-spacing:.02em}
details{border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin:10px 0;background:var(--panel)}#chat{margin-top:18px}summary{cursor:pointer;font-weight:600}
details p{color:var(--muted);font-size:14px;margin:10px 0 8px}code{display:block;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:10px 12px;font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;overflow-wrap:anywhere;color:var(--ink)}
.copy{margin-top:8px;font:inherit;font-size:13px;background:none;border:0;color:var(--lime);cursor:pointer;padding:4px 0}
.share a{flex:1 1 120px}.note{color:var(--muted);font-size:13px;margin-top:14px}[hidden]{display:none!important}
footer{margin-top:40px;color:var(--muted);font-size:12px}footer a{color:var(--ink);text-underline-offset:3px}footer .credit img{display:inline-block;width:20px;height:20px;border-radius:50%;border:0;margin:0 6px 0 2px;vertical-align:-5px}
</style></head><body><main data-repo="__REPO__" data-page="__PAGE__">
<div class="brand"><span>BOT DROPS <b>FOR HERMES</b></span><span class="pill">BOT DROP</span></div>
<h1>__TITLE__</h1>
<p class="lead">__DESCRIPTION__</p>
<div class="facts">__FACTS__</div>
<img src="drop-card.png" alt="Card for the Hermes bot __TITLE__" width="1200" height="630">

<div class="primary row"><a class="btn" id="open" href="#">Adopt in my Hermes</a><button class="btn ghost" id="copy" type="button">Copy link</button></div>
<ul class="steps">
  <li>Opens Bot Drops in Hermes on this computer</li>
  <li>You see what the bot contains first. Nothing installs on its own</li>
  <li>Your keys, chats and memory stay yours. The bot brings none of the creator's</li>
</ul>
<details id="chat"><summary>On your phone? Send it to your Hermes chat</summary>
<p>Paste this into the chat where you talk to your Hermes, for example Telegram. Hermes shows a preview and asks before it adopts anything. Needs Bot Drops on that Hermes.</p><code id="chatcmd">/drop preview __REPO_TEXT__</code><button class="copy" data-copy="chatcmd" type="button">Copy message</button></details>

<section><h2>New to Bot Drops?</h2>
<details><summary>I have Hermes, but not Bot Drops</summary>
<p>Install the free plugin once, then press Adopt again.</p><code id="plugin">hermes plugins install __PLUGIN__ --enable</code><button class="copy" data-copy="plugin" type="button">Copy command</button></details>
<details><summary>I use Hermes without plugins</summary>
<p>Hermes can install this bot as a new profile by itself. You review its manifest in the terminal.</p><code id="cli">hermes profile install __REPO_TEXT__</code><button class="copy" data-copy="cli" type="button">Copy command</button></details>
<details><summary>What is Hermes?</summary><p>Hermes Agent is an open-source AI agent by Nous Research that runs on your own computer with the model you choose.</p></details>
</section>

<section><h2>Share this bot</h2>
<div class="share row" id="share"></div></section>
<footer>__CREDIT__Only adopt bots from people you trust.</footer>
</main>
<script>
(function(){
  var root=document.querySelector('main'),DASHBOARD=__DASHBOARD__,TEXT=__TEXT__;
  function fromPages(){var m=location.hostname.match(/^([^.]+)\\.github\\.io$/),r=location.pathname.split('/').filter(Boolean)[0];return m&&r?{repo:'https://github.com/'+m[1]+'/'+r,page:location.origin+'/'+r+'/'}:null;}
  var guess=fromPages(),repo=root.dataset.repo||(guess&&guess.repo)||'',page=root.dataset.page||(guess&&guess.page)||repo;
  var link=page||location.href;
  var open=document.getElementById('open');
  if(repo){open.href=DASHBOARD+'?url='+encodeURIComponent(repo);document.getElementById('cli').textContent='hermes profile install '+repo;document.getElementById('chatcmd').textContent='/drop preview '+repo;}
  else{open.removeAttribute('href');open.setAttribute('aria-disabled','true');open.style.opacity=.45;}
  if(window.matchMedia&&matchMedia('(pointer:coarse)').matches){var chat=document.getElementById('chat');chat.open=true;root.insertBefore(chat,document.querySelector('.primary'));}
  function copy(text,button){var done=function(){var t=button.textContent;button.textContent='Copied';setTimeout(function(){button.textContent=t},1600)};
    if(navigator.clipboard)navigator.clipboard.writeText(text).then(done,function(){prompt('Copy',text)});else prompt('Copy',text);}
  document.getElementById('copy').onclick=function(){copy(link,this)};
  Array.prototype.forEach.call(document.querySelectorAll('[data-copy]'),function(b){b.onclick=function(){copy(document.getElementById(b.dataset.copy).textContent,b)}});
  var post=TEXT+link,e=encodeURIComponent,targets=[
    ['X','https://x.com/intent/post?text='+e(TEXT)+'&url='+e(link)],
    ['LinkedIn','https://www.linkedin.com/sharing/share-offsite/?url='+e(link)],
    ['Reddit','https://www.reddit.com/submit?url='+e(link)+'&title='+e(document.querySelector('h1').textContent+' · a Hermes bot')],
    ['Bluesky','https://bsky.app/intent/compose?text='+e(post)]];
  var share=document.getElementById('share');
  targets.forEach(function(t){var a=document.createElement('a');a.className='btn ghost';a.textContent=t[0];a.href=t[1];a.target='_blank';a.rel='noopener noreferrer';share.appendChild(a);});
  if(navigator.share){var b=document.createElement('button');b.className='btn ghost';b.type='button';b.textContent='More…';b.onclick=function(){navigator.share({title:document.title,text:TEXT,url:link}).catch(function(){})};share.appendChild(b);}
})();
</script></body></html>
"""


def facts(info):
    skills = len(info.get('skills') or [])
    keys = [e['name'] for e in info.get('env_requires') or [] if e.get('required', True)]
    out = []
    author = str(info.get('author') or '').strip()
    if author and author != 'Not specified':
        out.append('shared by ' + author)
    if skills:
        out.append(f"{skills} skill" + ('' if skills == 1 else 's'))
    out.append('needs ' + ', '.join(keys) if keys else 'bring your own model')
    return '  ·  '.join(out)


def render_landing(info, *, repo='', page='', dashboard=DASHBOARD, plugin=PLUGIN_REPO, credit=True):
    image = (page + 'drop-card.png') if page else 'drop-card.png'
    text = post_text(info, '').rsplit('\n', 1)[0] + '\nAdopt it in your own Hermes: '
    values = {
        '__TITLE__': escape(title_of(info)),
        '__DESCRIPTION__': escape(' '.join(str(info.get('description') or 'A Hermes bot, ready to make your own.').split())),
        '__FACTS__': escape(facts(info)),
        '__IMAGE__': escape(image), '__OGURL__': ('<meta property="og:url" content="' + escape(page) + '">\n') if page else '',
        '__REPO__': escape(repo), '__PAGE__': escape(page), '__REPO_TEXT__': escape(repo or '<this repository link>'),
        '__PLUGIN__': escape(plugin),
        '__CREDIT__': ('Made with Bot Drops · by <a class="credit" href="' + escape(CREDIT_URL) + '" target="_blank" rel="noopener noreferrer">' + (('<img src="' + _avatar_uri() + '" alt="" width="20" height="20">') if _avatar_uri() else '') + escape(CREDIT_NAME) + '</a>. ') if credit else '',
        '__DASHBOARD__': json.dumps(dashboard).replace('<', '\\u003c'), '__TEXT__': json.dumps(text).replace('<', '\\u003c'),
    }
    # One pass over the template only: author text is never scanned for placeholders.
    return re.sub(r'__[A-Z_]+__', lambda m: values.get(m.group(0), m.group(0)), PAGE)
