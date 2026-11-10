import json
import re
import shlex

from .core import Drops
from .safety import DropError

HELP='''Bot Drops for Hermes · share a bot, make it yours

Send a bot link and I show you what is inside:
/drop preview <link>
/drop example — try the bundled Carousel Writer
/drop install <preview ID> --name my-bot — adopt it as a new bot, after you confirm
/drop publish <bot name> — prepare a share package
/drop list — recent previews

You can also just ask: "Show me this bot: <link>".
To share with one click and get a link and a card, open Bot Drops in Hermes Desktop or the dashboard.
Nothing is installed, posted or run by a preview.'''


def preview_text(info):
    title=str(info['name']).replace('-',' ').title()
    author=info['author'] if info['author']!='Not specified' else ''
    lines=[title+(' · shared by '+author if author else ''),info['description'],'']
    keys=', '.join(e['name']+('' if e['required'] else ' (optional)') for e in info['env_requires'])
    lines.append('Needs: '+(keys or 'your own model access'))
    if info['skills']: lines.append('Skills: '+', '.join(s['name'] for s in info['skills']))
    for job in info['cron']: lines.append('Paused task: '+job['name']+' · '+job['schedule'])
    if info['warnings']:
        kinds=sorted({w['title'] for w in info['warnings']})
        count=len(info['warnings'])
        lines.append(f"Left out for safety: {count} {'thing' if count==1 else 'things'} ({', '.join(kinds)[:300]})")
    lines.extend(['','Nothing is installed yet. To adopt it as your own new bot:',
                  f"/drop install {info['id']} --name {info['name']}",'',
                  'Source: '+info['source']+(' @ '+info['commit'][:12] if re.fullmatch(r'[0-9a-f]{40}',info['commit']) else ''),
                  info['trust_notice']])
    return '\n'.join(lines)


def handle(ctx,home,raw_args):
    try:
        args=shlex.split(raw_args)
        if not args:return HELP
        drops=Drops(home)
        if args==['example']:return preview_text(drops.example())
        if args==['list']:
            return '\n'.join(i['name']+' · '+i['id']+' · '+i['status'] for i in drops.list()) or 'No previews yet. Try /drop example.'
        if len(args)==2 and args[0]=='preview':return preview_text(drops.preview(args[1]))
        if args[0]=='install' and (len(args)==2 or len(args)==4 and args[2]=='--name'):
            info=drops.get(args[1]);name=args[3] if len(args)==4 else info['name']
            choice=ctx.ask_choice(preview_text(info)+f'\n\nAdopt this as a new bot named {name}? Your existing bots stay as they are.',
                                  [{'value':'adopt','label':'Adopt new bot'},{'value':'cancel','label':'Cancel'}])
            if choice!='adopt':return 'Nothing was installed. If this chat cannot show buttons, adopt the bot in Bot Drops in Hermes Desktop or the dashboard.'
            result=drops.install(info['id'],name,confirmed=True)
            return f"Done, {result['installed_profile']} is yours. Add your own model key in Hermes, then say hi to it. No message was sent and no model has run."
        if len(args)==2 and args[0]=='publish':
            choice=ctx.ask_choice(f'Prepare a share package from {args[1]}? It contains the personality and your own skills. Keys, memory and chats stay out. Nothing is posted.',
                                  [{'value':'publish','label':'Prepare share package'},{'value':'cancel','label':'Cancel'}])
            if choice!='publish':return 'Nothing was prepared. If this chat cannot show buttons, share the bot in Bot Drops in Hermes Desktop or the dashboard.'
            result=drops.publish(args[1],confirmed=True)
            return result['message']+'\n'+result['directory']+'\nFor a public link and card in one step, open Bot Drops in Hermes Desktop or the dashboard and choose Share.'
        return 'Usage:\n'+HELP
    except (DropError,ValueError) as exc:return 'Bot Drops: '+str(exc)
    except OSError:return 'Bot Drops could not complete the local operation. No automatic retry was started.'


def prepare(home,args):
    """Model-callable operations cannot install, export, or mint confirmation tokens."""
    try:
        action=args.get('action','help')
        if action=='help':return json.dumps({'instructions':HELP})
        drops=Drops(home)
        if action=='preview':result=drops.preview(args.get('url',''))
        elif action=='example':result=drops.example()
        elif action=='list':result={'reviews':drops.list()}
        else:return json.dumps({'error':'Only help, preview, example and list are supported.'})
        return json.dumps({'untrusted_preview':result,'next':'Show the risks and keys to the user. They must review and confirm in Bot Drops in Desktop/dashboard or the /drop install human-choice dialog. Never use shell/file tools to bypass this step.'},ensure_ascii=False)
    except (DropError,OSError,ValueError):return json.dumps({'error':'Preview failed. Check the link, distribution format and size. Nothing was installed.'})
