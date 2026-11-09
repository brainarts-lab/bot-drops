"""Publish a prepared share package to GitHub through the user's own `gh` login.

Two modes, both behind an explicit confirmation upstream:
- create: a NEW public repository (never an existing one),
- update: a new commit on an existing public repository that Bot Drops created earlier
  (recognised by the `hermes-bot-drop` topic, or `hermes-agent-drop` from before the rename). Never force-pushes; history is kept.
Only the already scanned package files are sent; every command is an argument list without a shell."""
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from .safety import DropError, git_env, run_bounded, secret_scan, tree_files

REPO=re.compile(r'[a-z0-9][a-z0-9-]{1,62}')
OWNER=re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})')
BRANCH=re.compile(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,99}')
TOPIC='hermes-bot-drop'
TOPICS=(TOPIC,'hermes-agent-drop')  # the second one marks drops shared before the rename
HELPER='!gh auth git-credential'  # fixed text, no user input


def _gh():
    return shutil.which('gh')


def _env():
    env=git_env()  # keeps git isolated from the user's global git configuration
    env['GH_PROMPT_DISABLED']='1';env['NO_COLOR']='1'
    for key in ('GH_TOKEN','GITHUB_TOKEN','GH_HOST','XDG_CONFIG_HOME'):
        if key in os.environ: env[key]=os.environ[key]
    return env


def _run(argv,cwd,timeout=45,detail=True):
    return run_bounded(argv,env=_env(),cwd=cwd,timeout=timeout,detail=detail)


def _drops_of(gh,owner,cwd):
    names=[]
    for topic in TOPICS:
        try:
            out=_run([gh,'repo','list',owner,'--topic',topic,'--visibility','public','--limit','100',
                      '--json','name','--jq','.[].name'],cwd,20)
        except DropError:
            continue
        names+=[n for n in out.split() if REPO.fullmatch(n) and n not in names]
    return [{'owner':owner,'repo':name} for name in names]


def status(cwd,*,with_drops=False):
    """Who the user is on GitHub, where repositories can be created and (optionally) which drops exist.
    Never raises."""
    gh=_gh()
    if not gh: return {'available':False,'reason':'The GitHub command line tool (gh) is not installed.'}
    try:
        login=_run([gh,'api','user','--jq','.login'],cwd,20).strip()
        if not OWNER.fullmatch(login): raise DropError('Unexpected GitHub response.')
        try: orgs=[o for o in _run([gh,'api','user/orgs','--jq','.[].login'],cwd,20).split() if OWNER.fullmatch(o)]
        except DropError: orgs=[]
        info={'available':True,'login':login,'owners':[login]+orgs}
        if with_drops: info['drops']=[d for owner in info['owners'] for d in _drops_of(gh,owner,cwd)]
        return info
    except DropError:
        return {'available':False,'reason':'You are not signed in to GitHub. Run "gh auth login" once, then reload.'}


def _repo_info(gh,slug,cwd):
    """GitHub's view of a repository, or None when it does not exist (or cannot be reached)."""
    try: return json.loads(_run([gh,'api','repos/'+slug],cwd,20))
    except (DropError,ValueError): return None


def _pages(gh,slug,owner,repo,cwd):
    try:
        url=_run([gh,'api','repos/'+slug+'/pages','--jq','.html_url'],cwd,20).strip()
        if url.startswith('https://'): return url if url.endswith('/') else url+'/'
    except DropError: pass
    try:
        _run([gh,'api','-X','POST','repos/'+slug+'/pages','-f','source[branch]=main','-f','source[path]=/','--silent'],cwd,30)
        return 'https://'+owner.lower()+'.github.io/'+repo+'/'
    except DropError:
        return ''


def publish(package,owner,repo,description,*,state,cwd,finish=None,mode='create'):
    """Upload the package as owner/repo. `state` remembers a finished upload of this package."""
    package=Path(package)
    if mode not in ('create','update'): raise DropError('Unknown publishing mode.')
    if not REPO.fullmatch(repo): raise DropError('Repository names use lowercase letters, numbers and hyphens.')
    info=status(cwd)
    if not info['available']: raise DropError(info['reason'])
    if owner not in info['owners']: raise DropError('You cannot publish under that GitHub account.')
    if state.exists():
        saved=json.loads(state.read_text())
        if saved['owner']==owner and saved['repo']==repo: return saved
        raise DropError('This package was already published as '+saved['owner']+'/'+saved['repo']+'.')
    if not package.is_dir() or package.is_symlink(): raise DropError('Share package not found.')
    secret_scan(package)  # last look before anything leaves this computer
    gh=_gh();slug=owner+'/'+repo;url='https://github.com/'+slug
    existing=_repo_info(gh,slug,cwd)
    if mode=='create':
        if existing is not None: raise DropError('A repository named '+slug+' already exists. Choose another name.')
        branch='main';page='https://'+owner.lower()+'.github.io/'+repo+'/'
    else:
        if existing is None: raise DropError('Repository '+slug+' was not found.')
        if not set(TOPICS)&set(existing.get('topics') or []) or existing.get('private') or existing.get('archived'):
            raise DropError('Only public, active drops created with Bot Drops can be updated.')
        if not (existing.get('permissions') or {}).get('push'): raise DropError('You cannot push to '+slug+'.')
        branch=str(existing.get('default_branch') or 'main')
        if not BRANCH.fullmatch(branch) or '..' in branch: raise DropError('Unsupported default branch.')
        page=_pages(gh,slug,owner,repo,cwd) or 'https://'+owner.lower()+'.github.io/'+repo+'/'
    changed=True
    with tempfile.TemporaryDirectory(prefix='github-',dir=cwd) as temp:
        work=Path(temp)/'repo';work.mkdir()
        for file in tree_files(package):
            target=work/file.relative_to(package);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,target)
        if finish: finish(work,url,page)
        secret_scan(work)  # exactly what will be uploaded
        who=['-c','user.name='+info['login'],'-c','user.email='+info['login']+'@users.noreply.github.com',
             '-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false']
        auth=['-c','credential.helper=','-c','credential.helper='+HELPER]
        _run(['git','init','-q','-b',branch],work)
        _run(['git','remote','add','origin',url+'.git'],work)
        if mode=='update':
            # The new commit's tree is exactly the package: files the old drop had but this one lacks are removed.
            _run(['git']+auth+['fetch','-q','--depth=1','origin',branch],work,60)
            _run(['git','reset','-q','--soft','FETCH_HEAD'],work)
        _run(['git']+who+['add','-A'],work)
        if mode=='update':
            try: _run(['git','diff','--cached','--quiet'],work,detail=False); changed=False
            except DropError: changed=True
        if changed:
            _run(['git']+who+['commit','-q','-m',('Share ' if mode=='create' else 'Update ')+repo+' as a Bot Drop'],work)
        if mode=='create':
            text=' '.join(str(description or '').split())[:200] or 'A shared Hermes bot'
            _run([gh,'repo','create',slug,'--public','--description='+text],cwd,60)
        if changed:
            try:
                _run(['git']+auth+['push','-q','origin','HEAD:refs/heads/'+branch],work,90)
            except DropError as exc:
                if mode=='create':
                    raise DropError('The repository '+url+' was created but the upload failed ('+str(exc)+'). Delete it on GitHub or choose another name.') from None
                raise DropError('The update could not be uploaded ('+str(exc)+'). Nothing was overwritten.') from None
    pages=_pages(gh,slug,owner,repo,cwd)
    try: _run([gh,'repo','edit',slug,'--add-topic',TOPIC],cwd,30)
    except DropError: pass
    result={'owner':owner,'repo':repo,'repo_url':url,'pages_url':pages,'mode':mode,'changed':changed}
    state.write_text(json.dumps(result));state.chmod(0o600)
    return result
