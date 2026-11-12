import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
import uuid

from .safety import (DropError, MAX_BYTES, MAX_FILE, MAX_FILES, NAME, PRIVATE, WINDOWS, base_env, clean_text, clone_public,
                     digest, name_ok, read_data, rel_path, remove_tree, run_bounded, secret_scan,
                     tree_files, write_text)

STANDARD = {'SOUL.md','config.yaml','mcp.json','skills','cron','distribution.yaml'}
MANIFEST_KEYS = {'name','version','description','author','license','hermes_requires','env_requires','distribution_owned','source','installed_at'}
SAFE_MODEL_PROVIDERS = {'openai','anthropic','openrouter','nous','google','groq'}
NEUTRAL_CONFIG = {'plugins':{'enabled':[]},'mcp_servers':{}}
PREVIEW_TTL = 86400          # a preview can be adopted for 24 hours
EXPORT_TTL = 7 * 86400       # share packages are local copies; old ones are removed
TAGLINE = 140
DEFAULT_DESCRIPTION = 'A shared Hermes bot'
JOB_TEXT = 20000             # longest task text a scheduled task may carry
SCHEDULE_KEYS = ('kind','expr','minutes','run_at','display')
SCHEDULE_KINDS = {'cron','interval','once'}
# Job fields that say where a task reports to or what else it runs. They never travel.
JOB_LOCAL = ('origin','deliver','failure_deliver','base_url','provider','model','script','no_agent','interpreter',
             'workdir','monitor_script','monitor_url','context_from','enabled_toolsets','attach_to_session')
PAUSED_REASON = 'Came with a shared bot. Read the task, then turn it on.'


def schedule_text(schedule):
    if not isinstance(schedule,dict): return 'Not specified'
    if schedule.get('display'): return str(schedule['display'])
    if schedule.get('kind')=='interval' and schedule.get('minutes'): return 'every '+str(schedule['minutes'])+'m'
    return str(schedule.get('expr') or schedule.get('run_at') or 'Not specified')


def portable_jobs(data):
    """Scheduled tasks as they may travel with a bot: id, name, task text, schedule and skill names, paused.
    Everything else in a Hermes job record stays home: the chat and user it was created from, delivery
    targets, scripts, working folders, model endpoints, run history and error text.
    Returns (tasks, number of tasks left out because only a script would run, names of removed fields)."""
    jobs=data.get('jobs',[]) if isinstance(data,dict) else data
    if not isinstance(jobs,list): raise DropError('Cron jobs must be a list or an object containing jobs.')
    kept=[];left=0;removed=set()
    for job in jobs:
        if not isinstance(job,dict): raise DropError('Invalid cron job.')
        removed.update(k for k in JOB_LOCAL if job.get(k) not in (None,'',[],{},False))
        prompt=job.get('prompt')
        prompt=clean_text(('' if prompt is None else str(prompt)).replace('\r\n','\n').replace('\r','\n'),JOB_TEXT)
        raw=job.get('skills')
        if raw is None: raw=[job.get('skill')] if job.get('skill') else []
        elif isinstance(raw,str): raw=[raw]
        if not isinstance(raw,list): raise DropError('Invalid skills in a scheduled task.')
        skills=[]
        for item in raw:
            item=clean_text(str(item or '').strip(),120)
            if item and item not in skills: skills.append(item)
        schedule=job.get('schedule')
        if not isinstance(schedule,dict) or schedule.get('kind') not in SCHEDULE_KINDS:
            raise DropError('A scheduled task has a schedule Bot Drops cannot read.')
        schedule={k:clean_text(schedule[k],200) if isinstance(schedule[k],str) else schedule[k]
                  for k in SCHEDULE_KEYS if k in schedule and type(schedule[k]) in (str,int)}
        if not prompt.strip() and not skills:
            left+=1;continue  # only a script would run, and scripts stay home
        identifier=str(job.get('id') or '')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',identifier): identifier=uuid.uuid4().hex[:12]
        name=clean_text(' '.join(str(job.get('name') or '').split())[:120],120) or ' '.join(prompt.split())[:50] or skills[0]
        kept.append({'id':identifier,'name':name,'prompt':prompt,'schedule':schedule,'skills':skills,
                     'enabled':False,'state':'paused','paused_reason':PAUSED_REASON})
    return kept,left,sorted(removed)


def task_lines(jobs):
    return [{'name':j['name'],'schedule':schedule_text(j['schedule']),'prompt':j['prompt'],'skills':j['skills']} for j in jobs]


def write_json(path, value):
    temp=path.with_suffix('.tmp-'+uuid.uuid4().hex)
    write_text(temp,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    temp.chmod(0o600)
    temp.replace(path)


def manifest_of(root):
    if not (root/'distribution.yaml').is_file():
        raise DropError('This repository has no distribution.yaml. It is not a Hermes agent distribution.')
    data=read_data(root/'distribution.yaml')
    if not isinstance(data,dict): raise DropError('Distribution manifest must be an object.')
    name_ok(data.get('name'))
    for key,limit in [('description',1000),('author',120),('version',80),('hermes_requires',80)]:
        data[key]=clean_text(data.get(key,''),limit)
    env=data.get('env_requires',[])
    if not isinstance(env,list) or len(env)>30: raise DropError('Invalid environment requirements.')
    cleaned=[]
    for item in env:
        if not isinstance(item,dict) or not re.fullmatch(r'[A-Z][A-Z0-9_]{1,79}',str(item.get('name',''))):
            raise DropError('Invalid environment variable name.')
        if type(item.get('required',True)) is not bool: raise DropError('Required must be true or false.')
        cleaned.append({'name':item['name'],'description':clean_text(item.get('description',''),240),
                        'required':item.get('required',True)})
    data['env_requires']=cleaned
    owned=data.get('distribution_owned',[])
    if not isinstance(owned,list) or any(not isinstance(x,str) for x in owned): raise DropError('Invalid distribution_owned.')
    return data


def inspect_tree(root):
    files=tree_files(root)
    secret_scan(root)
    manifest=manifest_of(root)
    warnings=[]
    for key in sorted(set(manifest)-MANIFEST_KEYS):
        warnings.append({'kind':'unreviewed','title':'Unreviewed manifest field','detail':clean_text(key),'action':'Not imported'})
    owned=manifest.get('distribution_owned',[])
    for path in owned:
        if path not in STANDARD:
            warnings.append({'kind':'code','title':'Additional files / executable plugins','detail':clean_text(path),'action':'Not imported'})
    config=read_data(root/'config.yaml')
    if not isinstance(config,dict): raise DropError('config.yaml must be an object.')
    for key,value in config.items():
        if NEUTRAL_CONFIG.get(key,object())==value: continue  # the empty defaults Bot Drops itself writes
        if key=='model':
            detail=json.dumps(value,ensure_ascii=False)[:800]
            warnings.append({'kind':'endpoint','title':'Model configuration','detail':detail,
                             'action':'Only a known built-in provider and model name can be retained; endpoints and credentials are removed'})
        else:
            warnings.append({'kind':'unreviewed','title':'Configuration requiring review','detail':clean_text(key)+': '+json.dumps(value,ensure_ascii=False)[:800],
                             'action':'Not imported (includes tools, terminal, gateway, MCP and hooks settings)'})
    mcp=read_data(root/'mcp.json')
    if mcp:
        warnings.append({'kind':'execution','title':'MCP can run programs or contact servers',
                         'detail':json.dumps(mcp,ensure_ascii=False)[:1800],'action':'MCP configuration is not imported'})
    skills=[]
    for file in files:
        if file.name=='SKILL.md' and file.relative_to(root).parts[0]=='skills':
            text=file.read_text('utf-8')
            desc=next((line.split(':',1)[1].strip().strip('"') for line in text.splitlines()[:25] if line.startswith('description:')), '')
            skills.append({'name':file.parent.name,'description':clean_text(desc,600)})
    jobs,left,removed=portable_jobs(read_data(root/'cron/jobs.json',[]))
    cron_info=task_lines(jobs)
    if jobs: warnings.append({'kind':'schedule','title':'Scheduled tasks','detail':f'{len(jobs)} task(s). Read each task under Scheduled tasks.',
                              'action':'Imported paused with only their name, task text, schedule and skills'})
    if removed: warnings.append({'kind':'schedule','title':'Task settings from the sharer','detail':', '.join(removed),
                                 'action':'Removed: where tasks report to, scripts, folders and endpoints are never imported'})
    if left: warnings.append({'kind':'code','title':'Tasks that only run a script','detail':f'{left} task(s)','action':'Not imported'})
    omitted=[]
    for file in files:
        rel=file.relative_to(root)
        if rel.parts[0]=='skills' and file.suffix.lower() not in {'.md','.txt'}:
            omitted.append(rel.as_posix())
    if omitted:
        warnings.append({'kind':'code','title':'Skill attachments / programs','detail':', '.join(omitted)[:1500],
                         'action':'Only Markdown and text skill files are imported'})
    extra=sorted({p.relative_to(root).parts[0] for p in files}-STANDARD-{'README.md','LICENSE','.gitignore','drop-card.png','drop-story.png','share.txt','index.html'})
    if extra:
        warnings.append({'kind':'unreviewed','title':'Other files','detail':', '.join(extra)[:1500],'action':'Not imported'})
    return {'name':manifest['name'],'version':manifest['version'] or '0.1.0','author':manifest['author'] or 'Not specified',
            'description':manifest['description'] or 'No description supplied. Read the included instructions before adopting.',
            'hermes_requires':manifest['hermes_requires'] or 'Not specified','env_requires':manifest['env_requires'],
            'skills':skills,'cron':cron_info,'warnings':warnings,'file_count':len(files),
            'trust_notice':'Only adopt bots from sources you trust. Their personality and skills guide your agent; profiles are not a security sandbox.'}


def model_choice(config):
    """The only setting that travels with a bot: a known built-in provider and a plain model name."""
    original=config.get('model',{}) if isinstance(config,dict) else {}
    if isinstance(original,dict) and original.get('provider') in SAFE_MODEL_PROVIDERS:
        model=original.get('default')
        if isinstance(model,str) and re.fullmatch(r'[A-Za-z0-9_.:/-]{1,160}',model):
            return {'model':{'provider':original['provider'],'default':model}}
    return {}


def safe_payload(source,target):
    """Create the exact installation payload shown by preview. Never copy arbitrary config."""
    info=inspect_tree(source)
    manifest=manifest_of(source)
    target.mkdir(mode=0o700)
    safe_manifest={k:manifest[k] for k in ('name','version','author','description','hermes_requires','env_requires')}
    safe_manifest['distribution_owned']=['SOUL.md','config.yaml','skills','cron','distribution.yaml']
    write_json(target/'distribution.yaml',safe_manifest)
    # An explicit config prevents fresh-profile model/credential seeding from a personal profile.
    config=json.loads(json.dumps(NEUTRAL_CONFIG))
    config.update(model_choice(read_data(source/'config.yaml')))
    write_json(target/'config.yaml',config)
    for file in tree_files(source):
        rel=file.relative_to(source)
        if rel.as_posix()=='SOUL.md' or (rel.parts[0]=='skills' and file.suffix.lower() in {'.md','.txt'} and not any(p.startswith('.') for p in rel.parts)):
            dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,dest)
        if rel.as_posix()=='cron/jobs.json':
            jobs,_,_=portable_jobs(read_data(file,[]))
            if jobs:
                (target/'cron').mkdir(exist_ok=True)
                write_json(target/'cron/jobs.json',{'jobs':jobs})
    secret_scan(target)
    return info


def bundled_skill_dirs(profile):
    """Skill folders that Hermes itself seeded into this profile (listed in skills/.bundled_manifest)."""
    manifest=profile/'skills'/'.bundled_manifest'
    names=set()
    try:
        for line in manifest.read_text('utf-8').splitlines():
            if ':' in line: names.add(line.split(':',1)[0].strip())
    except OSError:
        return set()
    skills=profile/'skills'
    if not skills.is_dir() or skills.is_symlink(): return set()
    return {f.parent for f in skills.rglob('SKILL.md') if f.parent.name in names and not f.is_symlink()}


def hub_skill_dirs(profile):
    """Skill folders installed from the Skills Hub (skills/.hub/lock.json). They belong to their authors;
    whoever adopts the bot installs them from the hub, so they are not republished."""
    skills=profile/'skills'
    lock=skills/'.hub'/'lock.json'
    try:
        if not lock.is_file() or lock.is_symlink() or lock.stat().st_size>MAX_FILE: return set()
        installed=json.loads(lock.read_text('utf-8')).get('installed')
    except (OSError,ValueError,AttributeError):
        return set()
    if not isinstance(installed,dict): return set()
    dirs=set()
    for name,entry in installed.items():
        path=entry.get('install_path') if isinstance(entry,dict) else None
        path=path if isinstance(path,str) and path else str(name)
        if '..' in Path(path).parts or Path(path).is_absolute(): continue
        dirs.add(skills/path)
    return dirs


def _visible_files(root):
    """Regular files below root, without hidden or private folders (Hermes keeps large caches such as skills/.hub there)."""
    files=[]
    for current,dirs,names in os.walk(root,followlinks=False):
        dirs[:]=sorted(d for d in dirs if not d.startswith('.') and d not in PRIVATE)
        for n in dirs+names:
            if n.startswith('.') or n in PRIVATE: continue
            path=Path(current)/n
            if path.is_symlink(): raise DropError('Symlinks are not supported: '+rel_path(path,root))
            if n in names:
                if not path.is_file(): raise DropError('Only regular files are supported.')
                files.append(path)
    return sorted(files)


def shareable_files(source):
    """(file, relative path) of everything a share package takes from a profile.
    Skills: only the author's own skill folders, not what Hermes seeded and not loose category notes.
    Settings and connections (config.yaml, mcp.json) are never taken; see model_choice."""
    excluded=bundled_skill_dirs(source)|hub_skill_dirs(source)
    count=total=0
    for rel in ('SOUL.md','distribution.yaml','skills','cron/jobs.json'):
        p=source/rel
        if not p.exists(): continue
        if p.is_symlink(): raise DropError('Symlink in shareable profile content: '+rel)
        if p.is_dir():
            files=_visible_files(p)
            own={f.parent for f in files if f.name=='SKILL.md' and not any(e==f.parent or e in f.parents for e in excluded)}
            chosen=[f for f in files if any(d==f.parent or d in f.parents for d in own)]
        else:
            chosen=[p]
        for f in chosen:
            size=f.stat().st_size;count+=1;total+=size
            if size>MAX_FILE or total>MAX_BYTES or count>MAX_FILES:
                raise DropError('This bot is too large to share (20 MB in total, 1 MB per file, 1,000 files): '+rel_path(f,source))
            yield f,f.relative_to(source)


def tagline(text):
    """One line the sharer writes about the bot; shown on the card and the page."""
    text=' '.join(str(text or '').split())
    if len(text)>TAGLINE: raise DropError('Keep the description under '+str(TAGLINE)+' characters.')
    return clean_text(text,TAGLINE)


_LOGIN={'at':0.0,'login':'','owners':[]}


@contextlib.contextmanager
def file_lock(path):
    """One Bot Drops operation at a time, across all Hermes processes on this computer."""
    with open(path,'a+b') as handle:
        if WINDOWS:
            import msvcrt
            while True:
                handle.seek(0)
                try: msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1);break
                except OSError: time.sleep(.05)
            try: yield
            finally:
                handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl
            fcntl.flock(handle,fcntl.LOCK_EX)
            yield


def hermes_program():
    """The Hermes command: on PATH, or next to the Python that runs Hermes (apps start with a short PATH)."""
    found=shutil.which('hermes')
    if found: return found
    for name in ('hermes.exe','hermes'):
        candidate=Path(sys.executable).parent/name
        if candidate.is_file(): return str(candidate)
    return None


def hermes_version():
    """(major, minor, patch) of the Hermes this plugin is running in; None when it runs on its own, as in tests."""
    loaded=sys.modules.get('hermes_cli')
    try: found=re.match(r'(\d+)\.(\d+)\.(\d+)',str(getattr(loaded,'__version__','')))
    except Exception: found=None
    return tuple(int(part) for part in found.groups()) if found else None


class Drops:
    def __init__(self, home, *, hermes=None):
        self.home=Path(home).resolve()
        self.root=self.home.parent.parent if self.home.parent.name=='profiles' else self.home
        self.profiles=self.root/'profiles'
        self.data=self.home/'plugin-data'/'bot-drops'
        legacy=self.home/'plugin-data'/'agent-drops'  # name before the rename to Bot Drops
        if not self.data.exists() and legacy.is_dir() and not legacy.is_symlink(): legacy.rename(self.data)
        self.data.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.hermes=hermes or hermes_program()

    @contextlib.contextmanager
    def lock(self):
        shared=self.root/'plugin-data';shared.mkdir(exist_ok=True,mode=0o700)
        with file_lock(shared/'bot-drops-operations.lock'):
            yield

    def entry(self,identifier):
        if not re.fullmatch(r'[0-9a-f]{32}',str(identifier)):
            raise DropError('Invalid preview identifier.')
        return self.data/identifier

    def _record(self,source,sha,origin):
        identifier=uuid.uuid4().hex
        record=self.entry(identifier); record.mkdir(mode=0o700)
        try:
            info=safe_payload(source,record/'payload')
            info.update(id=identifier,source=origin,commit=sha,created=time.time(),expires=time.time()+PREVIEW_TTL,
                        payload_digest=digest(record/'payload'),status='review',installed_profile=None)
            # Persist the review, not arbitrary remote code or the source .git directory.
            write_json(record/'review.json',info)
            return info
        except BaseException:
            remove_tree(record,ignore_errors=True)
            raise

    def preview(self,url):
        self.check_capacity()
        with tempfile.TemporaryDirectory(prefix='fetch-',dir=self.data,ignore_cleanup_errors=True) as temp:
            source=Path(temp)/'source'
            sha=clone_public(url,source)
            return self._record(source,sha,url)

    def example(self):
        self.check_capacity()
        source=Path(__file__).resolve().parents[1]/'examples'/'carousel-writer'
        return self._record(source,'bundled:'+digest(source),'Bundled Carousel Writer example')

    def get(self,identifier):
        path=self.entry(identifier)/'review.json'
        try: info=json.loads(path.read_text('utf-8'))
        except (OSError,ValueError) as exc: raise DropError('Preview not found in this Hermes profile.') from exc
        if info['expires']<time.time() and info['status']!='installed': raise DropError('Preview expired. Review the source again.')
        return info

    def list(self):
        items=[]
        for path in self.data.glob('*/review.json'):
            try: items.append(self.get(path.parent.name))
            except DropError: pass
        return sorted(items,key=lambda i:i['created'],reverse=True)[:50]

    def prune(self):
        """Remove what can no longer be used: expired previews, old share packages, stale work folders.
        Adopted bots keep their record. Never touches profiles."""
        now=time.time()
        with self.lock():
            for path in list(self.data.iterdir()):
                try:
                    if path.is_symlink() or not path.is_dir(): continue
                    name=path.name;age=now-path.stat().st_mtime
                    if re.fullmatch(r'[0-9a-f]{32}',name):
                        try: info=json.loads((path/'review.json').read_text('utf-8'))
                        except (OSError,ValueError): info=None
                        if info is None: stale=age>PREVIEW_TTL
                        else: stale=info.get('status')=='review' and info.get('expires',0)<now
                    elif re.fullmatch(r'export-[0-9a-f]{32}',name): stale=age>EXPORT_TTL
                    elif name.startswith(('fetch-','publish-','github-')): stale=age>PREVIEW_TTL
                    else: stale=False
                    if not stale: continue
                    remove_tree(path)
                    if name.startswith('export-'):
                        for suffix in ('.zip','.options.json','.github.json'): (self.data/(name+suffix)).unlink(missing_ok=True)
                except OSError:
                    continue

    def check_capacity(self):
        self.prune()
        pending=0
        for path in self.data.iterdir():
            if not path.is_dir(): continue
            try: adopted=json.loads((path/'review.json').read_text('utf-8')).get('status')=='installed'
            except (OSError,ValueError): adopted=False
            pending+=not adopted
        if pending>=40:
            raise DropError('Too many open previews and share packages. They clear on their own within a day; try again later.')

    def install(self,identifier,name,*,confirmed=False):
        if confirmed is not True: raise DropError('Explicit confirmation is required before adoption.')
        name_ok(name)
        with self.lock():
            info=self.get(identifier)
            if info['status']=='installed':
                if name!=info['installed_profile']: raise DropError('This preview was already adopted with a different name.')
                return info
            if info['status']=='installing': raise DropError('The earlier installation has an uncertain outcome. Inspect it before retrying.')
            target=self.profiles/name
            if target.exists() or target.is_symlink(): raise DropError('That profile already exists. Choose another name.')
            if name in self.retired_names():
                raise DropError('A bot with that name was removed earlier, and Hermes does not reuse the name. Choose another name.')
            payload=self.entry(identifier)/'payload'
            if digest(payload)!=info['payload_digest']: raise DropError('Reviewed files changed. Create a new preview.')
            if not self.hermes: raise DropError('Hermes CLI is not available.')
            info['status']='installing';info['installed_profile']=name
            write_json(self.entry(identifier)/'review.json',info)
            env=base_env()
            env.update(HERMES_HOME=str(self.home),HERMES_ENABLE_PROJECT_PLUGINS='0')
            try:
                run_bounded([self.hermes,'profile','install',str(payload),'--name',name,'-y'],
                            env=env,cwd=self.data,timeout=90)
                if not (target/'distribution.yaml').is_file(): raise DropError('Hermes did not create the expected profile.')
                target.chmod(0o700)
                # Do not restore the remote update URL: re-review is required for every changed source.
                info['status']='installed'
                write_json(self.entry(identifier)/'review.json',info)
                return info
            except BaseException:
                # No delete/overwrite of an uncertain target; never retry automatically.
                if not target.exists():
                    info['status']='review'; info['installed_profile']=None
                    write_json(self.entry(identifier)/'review.json',info)
                raise

    def github_status(self,with_drops=False):
        from . import github
        return github.status(self.data,with_drops=with_drops)

    def export_dir(self,identifier):
        if not re.fullmatch(r'export-[0-9a-f]{32}',str(identifier)): raise DropError('Invalid export identifier.')
        path=self.data/identifier
        if not path.is_dir() or path.is_symlink(): raise DropError('Share package not found. Prepare it again.')
        return path

    def publish_github(self,identifier,owner,repo,*,confirmed=False,mode='create'):
        if confirmed is not True: raise DropError('Explicit confirmation is required before creating a public repository.')
        from . import github
        from .landing import post_text, render_landing, render_readme
        package=self.export_dir(identifier)
        info=inspect_tree(package)
        version=identifier[len('export-'):][:7]  # same suffix on the page's share buttons and in the plugin
        def finish(work,repo_url,page_url):
            # Final links are known now: absolute card URL for link previews, direct Adopt button.
            try: credit=json.loads((self.data/(identifier+'.options.json')).read_text('utf-8')).get('credit') is not False
            except (OSError,ValueError): credit=True
            write_text(work/'index.html',render_landing(info,repo=repo_url,page=page_url,credit=credit,share=page_url+'?v='+version))
            write_text(work/'README.md',render_readme(info,page_url))
        with self.lock():
            result=github.publish(package,owner,repo,info['description'],state=self.data/(identifier+'.github.json'),
                                  cwd=self.data,finish=finish,mode=mode)
        # X and other networks cache link previews for days: a version suffix makes them fetch the new card.
        link=result['pages_url'] or result['repo_url']
        if result['pages_url']: link+='?v='+version
        result['share_url']=link
        result['post_text']=post_text(info,link)
        result['title']=info['name']
        return result

    def profile_names(self):
        if not self.profiles.exists(): return []
        return sorted(p.name for p in self.profiles.iterdir() if p.is_dir() and not p.is_symlink() and NAME.fullmatch(p.name))

    def retired_names(self):
        """Names of bots that were removed earlier and cannot be taken again on this Hermes.
        Hermes 0.23.0 keeps a mark for each removed profile and stops half way when a shared bot is installed
        under such a name; adoption asks for another name instead. Hermes 0.23.1 clears the mark itself."""
        version=hermes_version()
        if version is not None and version>=(0,23,1): return []
        marks=self.profiles/'.deleted'
        if not marks.is_dir() or marks.is_symlink(): return []
        return sorted(p.name for p in marks.iterdir() if NAME.fullmatch(p.name))

    def _source(self,profile):
        # Default is intentionally available only via an explicit UI selection and confirmation.
        if profile!='default': name_ok(profile)
        source=self.root if profile=='default' else self.profiles/profile
        if not source.is_dir() or source.is_symlink(): raise DropError('Profile not found.')
        return source

    def _account(self,owner=None,fresh=False):
        """The GitHub name a bot is shared under: the chosen account or organization, else the signed-in user."""
        if fresh or time.time()-_LOGIN['at']>300:
            info=self.github_status()
            _LOGIN.update(at=time.time(),login=info.get('login') or '',owners=info.get('owners') or [])
        return owner if owner and owner in _LOGIN['owners'] else _LOGIN['login']

    def share_preview(self,profile,description=None,owner=None):
        """What the card and the share form show: names, counts and task texts. Packages nothing."""
        source=self._source(profile)
        manifest={}
        path=source/'distribution.yaml'
        if path.is_file() and not path.is_symlink():
            data=read_data(path)
            if isinstance(data,dict): manifest=data
        name=manifest.get('name') if isinstance(manifest.get('name'),str) and NAME.fullmatch(manifest.get('name')) else (profile if profile!='default' else 'my-agent')
        saved=' '.join(str(manifest.get('description') or '').split())[:TAGLINE]
        text=(tagline(description) if description is not None else '') or saved
        author=str(manifest.get('author') or '').strip()[:120]
        if not author:
            login=self._account(owner)
            author='@'+login if login else ''
        env=[{'name':str(e.get('name')),'required':e.get('required',True) is not False}
             for e in manifest.get('env_requires') or [] if isinstance(e,dict) and re.fullmatch(r'[A-Z][A-Z0-9_]{1,79}',str(e.get('name','')))]
        files=list(shareable_files(source))
        skills=[{'name':f.parent.name} for f,sub in files if f.name=='SKILL.md' and sub.parts[0]=='skills']
        tasks=[];task_problem=''
        for f,sub in files:
            if sub.as_posix()=='cron/jobs.json':
                try: tasks=task_lines(portable_jobs(read_data(f,[]))[0])
                except DropError as exc: task_problem=str(exc)
        hub=sorted({d.name for d in hub_skill_dirs(source) if (d/'SKILL.md').is_file()})
        return {'name':name,'description':text or DEFAULT_DESCRIPTION,'saved_description':saved,'author':author,'env_requires':env,'skills':skills,
                'cron':tasks,'cron_problem':task_problem,'hub_skills':hub}

    def publish(self,profile,*,confirmed=False,credit=True,description=None,owner=None):
        if confirmed is not True: raise DropError('Review and confirm the profile before preparing a share package.')
        self.check_capacity()
        source=self._source(profile)
        if description is not None: description=tagline(description)
        identifier=uuid.uuid4().hex
        directory=self.data/('export-'+identifier)
        with tempfile.TemporaryDirectory(prefix='publish-',dir=self.data,ignore_cleanup_errors=True) as temp:
            staging=Path(temp)/'source'; staging.mkdir()
            for f,sub in shareable_files(source):
                dest=staging/sub;dest.parent.mkdir(parents=True,exist_ok=True)
                if sub.as_posix()=='cron/jobs.json':
                    # Never the live job file: only what portable_jobs lets travel.
                    jobs,_,_=portable_jobs(read_data(f,[]))
                    if jobs: write_json(dest,{'jobs':jobs})
                    continue
                shutil.copyfile(f,dest)
            if not (staging/'distribution.yaml').exists():
                write_json(staging/'distribution.yaml',{'name':profile if profile!='default' else 'my-agent',
                           'description':DEFAULT_DESCRIPTION,'version':'1.0.0','author':'','env_requires':[]})
            manifest=read_data(staging/'distribution.yaml')
            if isinstance(manifest,dict):
                changed=False
                if description: manifest['description']=description;changed=True
                elif not str(manifest.get('description') or '').strip(): manifest['description']=DEFAULT_DESCRIPTION;changed=True
                if not str(manifest.get('author') or '').strip():
                    # Recipients should see who shared the bot: the GitHub account or organization it is shared under.
                    login=self._account(owner,fresh=True)
                    if login: manifest['author']='@'+login;changed=True
                if changed: write_json(staging/'distribution.yaml',manifest)
            # The profile's settings stay home. Only the model choice travels, as plain names.
            try: choice=model_choice(read_data(source/'config.yaml')) if not (source/'config.yaml').is_symlink() else {}
            except (DropError,OSError): choice={}
            if choice: write_json(staging/'config.yaml',choice)
            # A key pasted into the personality, a skill or a task blocks sharing; it never silently disappears.
            # Hermes' own credential stores (.env, auth.json) are never opened: the scan looks for key patterns.
            secret_scan(staging)
            try: info=safe_payload(staging,directory)
            except BaseException:
                shutil.rmtree(directory,ignore_errors=True)
                raise
        try:
            from .card import render_card, render_story
            from .landing import render_landing, render_readme
            credit=credit is not False
            render_card(info,directory/'drop-card.png',credit=credit)
            render_story(info,directory/'drop-story.png',credit=credit)
            write_text(directory/'index.html',render_landing(info,credit=credit))
            write_json(self.data/('export-'+identifier+'.options.json'),{'credit':credit})
            write_text(directory/'.gitignore','.env\n.env.*\nauth.json\nmemories/\nsessions/\nlogs/\nstate.db*\n')
            write_text(directory/'README.md',render_readme(info))
            write_text(directory/'share.txt',f"Meet {info['name']}: {info['description']}\nPreview and adopt this agent in your own Hermes. Bring your own model access.\nLink: <paste your repository link here>\n")
            secret_scan(directory)  # the finished package, card and page included
            return {'id':'export-'+identifier,'name':info['name'],'directory':str(directory),
                    'files':[rel_path(p,directory) for p in tree_files(directory)],'warnings':info['warnings'],
                    'message':'Share package prepared locally. Nothing has been posted or pushed.'}
        except BaseException:
            shutil.rmtree(directory,ignore_errors=True)
            raise
