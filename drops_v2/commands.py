import json
import shlex

from .core import Drops
from .safety import DropError

HELP='''Bot Drops for Hermes · Share a bot. Make it yours.
Open Bot Drops in Hermes Desktop, or /drops/import in your Hermes dashboard.
You can also ask: "Preview this agent: <GitHub URL>" or "Help me share my bot".

/drop example — preview the bundled Carousel Writer
/drop preview <repository URL> — inspect without installing
/drop install <preview ID> [--name new-bot] — review and confirm adoption
/drop publish <profile name> — confirm a local share package
/drop list — recent previews
No model call, publication, or message is started by these commands.'''


def preview_text(info):
    lines=[f"{info['name']} · {info['version']} by {info['author']}",info['description'],
           'Source: '+info['source'],'Commit: '+info['commit'],'Hermes: '+info['hermes_requires'],
           'Keys: '+(', '.join(e['name']+(' (required)' if e['required'] else ' (optional)') for e in info['env_requires']) or 'Choose your own provider access'),
           'Skills: '+(', '.join(s['name']+': '+s['description'] for s in info['skills']) or 'None')]
    for warning in info['warnings']:
        lines.append(warning['title']+': '+warning['detail']+' → '+warning['action'])
    for job in info['cron']:lines.append('Paused task: '+job['name']+' · '+job['schedule'])
    lines.extend([info['trust_notice'],'Review ID: '+info['id'],
                  'Review the full instructions in Bot Drops before adopting.',
                  f"Continue in Bot Drops, or /drop install {info['id']} --name {info['name']}"])
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
            choice=ctx.ask_choice(preview_text(info)+f'\nAdopt into a NEW bot named {name}? No model run will start.',
                                  [{'value':'adopt','label':'Adopt new bot'},{'value':'cancel','label':'Cancel'}])
            if choice!='adopt':return 'Nothing installed. Confirm in Bot Drops in Desktop/dashboard if this chat cannot show choices.'
            result=drops.install(info['id'],name,confirmed=True)
            return f"Agent adopted as {result['installed_profile']}. Open Bot Drops in Desktop to set up Bot Mode and its Bot Chat. Configure your own provider before the first message."
        if len(args)==2 and args[0]=='publish':
            choice=ctx.ask_choice(f'Prepare a share package from {args[1]}? Personality and text skills are copied. Credentials, memory and chats are excluded. Review every file before publishing. Nothing is pushed.',
                                  [{'value':'publish','label':'Prepare share package'},{'value':'cancel','label':'Cancel'}])
            if choice!='publish':return 'Nothing exported. Confirm in Bot Drops in Desktop/dashboard if this chat cannot show choices.'
            result=drops.publish(args[1],confirmed=True)
            return result['message']+'\n'+result['directory']+'\nReview README.md, drop-card.png and share.txt before sharing.'
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
