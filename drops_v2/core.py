import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
import uuid

from .safety import (DropError, NAME, PRIVATE, clean_text, clone_public, digest, name_ok,
                     profile_credentials, read_data, run_bounded, secret_scan, tree_files)

STANDARD = {'SOUL.md','config.yaml','mcp.json','skills','cron','distribution.yaml'}
MANIFEST_KEYS = {'name','version','description','author','license','hermes_requires','env_requires','distribution_owned','source','installed_at'}
SAFE_MODEL_PROVIDERS = {'openai','anthropic','openrouter','nous','google','groq'}


def write_json(path, value):
    temp=path.with_suffix('.tmp-'+uuid.uuid4().hex)
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
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
    cron=read_data(root/'cron/jobs.json',[])
    jobs=cron.get('jobs',[]) if isinstance(cron,dict) else cron
    if not isinstance(jobs,list): raise DropError('Cron jobs must be a list or an object containing jobs.')
    cron_info=[]
    for job in jobs:
        if not isinstance(job,dict): raise DropError('Invalid cron job.')
        cron_info.append({'name':clean_text(job.get('name',job.get('id','Scheduled task')),120),
                          'schedule':json.dumps(job.get('schedule','Not specified'),ensure_ascii=False)[:400]})
    if jobs: warnings.append({'kind':'schedule','title':'Scheduled tasks','detail':f'{len(jobs)} task(s)', 'action':'Imported paused; review before enabling'})
    omitted=[]
    for file in files:
        rel=file.relative_to(root)
        if rel.parts[0]=='skills' and file.suffix.lower() not in {'.md','.txt'}:
            omitted.append(str(rel))
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


def safe_payload(source,target):
    """Create the exact installation payload shown by preview. Never copy arbitrary config."""
    info=inspect_tree(source)
    manifest=manifest_of(source)
    target.mkdir(mode=0o700)
    safe_manifest={k:manifest[k] for k in ('name','version','author','description','hermes_requires','env_requires')}
    safe_manifest['distribution_owned']=['SOUL.md','config.yaml','skills','cron','distribution.yaml']
    write_json(target/'distribution.yaml',safe_manifest)
    # An explicit config prevents fresh-profile model/credential seeding from a personal profile.
    config={'plugins':{'enabled':[]},'mcp_servers':{}}
    original=read_data(source/'config.yaml').get('model',{})
    if isinstance(original,dict) and original.get('provider') in SAFE_MODEL_PROVIDERS:
        model=original.get('default')
        if isinstance(model,str) and re.fullmatch(r'[A-Za-z0-9_.:/-]{1,160}',model):
            config['model']={'provider':original['provider'],'default':model}
    write_json(target/'config.yaml',config)
    for file in tree_files(source):
        rel=file.relative_to(source)
        if str(rel)=='SOUL.md' or (rel.parts[0]=='skills' and file.suffix.lower() in {'.md','.txt'} and not any(p.startswith('.') for p in rel.parts)):
            dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,dest)
        if str(rel)=='cron/jobs.json':
            data=read_data(file,[])
            jobs=data.get('jobs',[]) if isinstance(data,dict) else data
            for job in jobs:
                job['enabled']=False;job['state']='paused'
            (target/'cron').mkdir(exist_ok=True)
            write_json(target/'cron/jobs.json',data)
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


class Drops:
    def __init__(self, home, *, hermes=None):
        self.home=Path(home).resolve()
        self.root=self.home.parent.parent if self.home.parent.name=='profiles' else self.home
        self.profiles=self.root/'profiles'
        self.data=self.home/'plugin-data'/'bot-drops'
        legacy=self.home/'plugin-data'/'agent-drops'  # name before the rename to Bot Drops
        if not self.data.exists() and legacy.is_dir() and not legacy.is_symlink(): legacy.rename(self.data)
        self.data.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.hermes=hermes or shutil.which('hermes')

    @contextlib.contextmanager
    def lock(self):
        shared=self.root/'plugin-data';shared.mkdir(exist_ok=True,mode=0o700)
        with (shared/'bot-drops-operations.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
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
            info.update(id=identifier,source=origin,commit=sha,created=time.time(),expires=time.time()+86400,
                        payload_digest=digest(record/'payload'),status='review',installed_profile=None)
            # Persist the review, not arbitrary remote code or the source .git directory.
            write_json(record/'review.json',info)
            return info
        except BaseException:
            shutil.rmtree(record)
            raise

    def preview(self,url):
        self.check_capacity()
        with tempfile.TemporaryDirectory(prefix='fetch-',dir=self.data) as temp:
            source=Path(temp)/'source'
            sha=clone_public(url,source)
            return self._record(source,sha,url)

    def example(self):
        self.check_capacity()
        source=Path(__file__).resolve().parents[1]/'examples'/'carousel-writer'
        return self._record(source,'bundled:'+digest(source),'Bundled Carousel Writer example')

    def get(self,identifier):
        path=self.entry(identifier)/'review.json'
        try: info=json.loads(path.read_text())
        except (OSError,ValueError) as exc: raise DropError('Preview not found in this Hermes profile.') from exc
        if info['expires']<time.time() and info['status']!='installed': raise DropError('Preview expired. Review the source again.')
        return info

    def list(self):
        items=[]
        for path in self.data.glob('*/review.json'):
            try: items.append(self.get(path.parent.name))
            except DropError: pass
        return sorted(items,key=lambda i:i['created'],reverse=True)[:50]

    def check_capacity(self):
        # No unbounded fetch/export accumulation. Deletion is intentionally an explicit local action.
        if sum(1 for p in self.data.iterdir() if p.is_dir())>=30:
            raise DropError('Local drop storage is full (30 packages). Remove old packages from the Bot Drops data folder before continuing.')

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
            payload=self.entry(identifier)/'payload'
            if digest(payload)!=info['payload_digest']: raise DropError('Reviewed files changed. Create a new preview.')
            if not self.hermes: raise DropError('Hermes CLI is not available.')
            info['status']='installing';info['installed_profile']=name
            write_json(self.entry(identifier)/'review.json',info)
            env={k:os.environ[k] for k in ('PATH','HOME','LANG','TMPDIR') if k in os.environ}
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
        from .landing import post_text, render_landing
        package=self.export_dir(identifier)
        info=inspect_tree(package)
        version=identifier[len('export-'):][:7]  # same suffix on the page's share buttons and in the plugin
        def finish(work,repo_url,page_url):
            # Final links are known now: absolute card URL for link previews, direct Adopt button.
            try: credit=json.loads((self.data/(identifier+'.options.json')).read_text()).get('credit') is not False
            except (OSError,ValueError): credit=True
            (work/'index.html').write_text(render_landing(info,repo=repo_url,page=page_url,credit=credit,share=page_url+'?v='+version))
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

    def publish(self,profile,*,confirmed=False,credit=True):
        if confirmed is not True: raise DropError('Review and confirm the profile before preparing a share package.')
        self.check_capacity()
        # Default is intentionally available only via an explicit UI selection and confirmation.
        if profile!='default': name_ok(profile)
        source=self.root if profile=='default' else self.profiles/profile
        if not source.is_dir() or source.is_symlink(): raise DropError('Profile not found.')
        identifier=uuid.uuid4().hex
        directory=self.data/('export-'+identifier)
        with tempfile.TemporaryDirectory(prefix='publish-',dir=self.data) as temp:
            staging=Path(temp)/'source'; staging.mkdir()
            bundled=bundled_skill_dirs(source)
            for rel in ('SOUL.md','distribution.yaml','config.yaml','mcp.json','skills','cron/jobs.json'):
                p=source/rel
                if not p.exists(): continue
                if p.is_symlink(): raise DropError('Symlink in shareable profile content: '+rel)
                if p.is_dir():
                    for f in tree_files(p):
                        sub=f.relative_to(source)
                        if any(part.startswith('.') or part in PRIVATE for part in sub.parts): continue
                        # Skills that ship with Hermes belong to every installation; only the author's own are shared.
                        if any(d in f.parents for d in bundled): continue
                        dest=staging/sub;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
                else:
                    dest=staging/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
            if not (staging/'distribution.yaml').exists():
                write_json(staging/'distribution.yaml',{'name':profile if profile!='default' else 'my-agent',
                           'description':'A shared Hermes agent.','version':'1.0.0','author':'','env_requires':[]})
            manifest=read_data(staging/'distribution.yaml')
            if isinstance(manifest,dict) and not str(manifest.get('author') or '').strip():
                # Recipients should see who shared the bot: use the GitHub account when signed in.
                login=self.github_status().get('login')
                if login: manifest['author']='@'+login; write_json(staging/'distribution.yaml',manifest)
            # Scan before sanitization: a key in config or skill blocks publishing, never silently disappears.
            secret_scan(staging,profile_credentials(source))
            try: info=safe_payload(staging,directory)
            except BaseException:
                shutil.rmtree(directory,ignore_errors=True)
                raise
        try:
            from .card import render_card, render_story
            from .landing import render_landing
            credit=credit is not False
            render_card(info,directory/'drop-card.png',credit=credit)
            render_story(info,directory/'drop-story.png',credit=credit)
            (directory/'index.html').write_text(render_landing(info,credit=credit))
            write_json(self.data/('export-'+identifier+'.options.json'),{'credit':credit})
            (directory/'.gitignore').write_text('.env\n.env.*\nauth.json\nmemories/\nsessions/\nlogs/\nstate.db*\n')
            requirements='\n'.join('- '+e['name']+(' (required)' if e['required'] else ' (optional)') for e in info['env_requires']) or 'Choose your own model provider and configure its key in Hermes.'
            (directory/'README.md').write_text('# '+info['name']+'\n\n'+info['description']+'\n\n![Drop card](drop-card.png)\n\n## Requirements\n\n'+requirements+'\n\n## Adopt in Hermes\n\nOpen Bot Drops in your Hermes dashboard and paste this repository URL, or send the URL to your Hermes chat and ask to preview the bot. Advanced: `/drop preview <repository URL>`. Review the exact commit before adopting.\n\nProfiles are not a security sandbox. Only adopt bots from sources you trust.\n')
            (directory/'share.txt').write_text(f"Meet {info['name']}: {info['description']}\nPreview and adopt this agent in your own Hermes. Bring your own model access.\nLink: <paste your repository link here>\n")
            secret_scan(directory)
            return {'id':'export-'+identifier,'name':info['name'],'directory':str(directory),
                    'files':[str(p.relative_to(directory)) for p in tree_files(directory)],'warnings':info['warnings'],
                    'message':'Share package prepared locally. Nothing has been posted or pushed.'}
        except BaseException:
            shutil.rmtree(directory,ignore_errors=True)
            raise
