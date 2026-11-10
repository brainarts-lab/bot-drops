"""Hermes-authenticated dashboard/desktop routes. Never mount on an unauthenticated server."""
import base64
import hashlib
import io
import json
import re
import secrets
import time
import zipfile
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from .core import Drops, write_json
from .safety import DropError, digest, name_ok, read_data, rel_path, tree_files


class Input(BaseModel):
    model_config=ConfigDict(extra='forbid')

class Preview(Input):
    url: str=Field(min_length=1,max_length=300)

class Confirmation(Input):
    action: Literal['install','publish','github']
    id: str=Field(default='',max_length=48)
    name: str=Field(min_length=2,max_length=64)
    owner: str=Field(default='',max_length=39)
    mode: Literal['create','update']='create'

class GitHubPublish(Input):
    id: str=Field(min_length=39,max_length=39)
    owner: str=Field(min_length=1,max_length=39)
    name: str=Field(min_length=2,max_length=64)
    mode: Literal['create','update']='create'
    confirmation: str=Field(min_length=32,max_length=100)

class Install(Input):
    id: str=Field(min_length=32,max_length=32)
    name: str=Field(min_length=2,max_length=48)
    confirmation: str=Field(min_length=32,max_length=100)

class Publish(Input):
    name: str=Field(min_length=2,max_length=48)
    credit: bool=True
    description: str|None=Field(default=None,max_length=300)
    owner: str=Field(default='',max_length=39)
    confirmation: str=Field(min_length=32,max_length=100)

class Card(Input):
    name: str=Field(min_length=2,max_length=48)
    credit: bool=True
    description: str|None=Field(default=None,max_length=300)
    owner: str=Field(default='',max_length=39)


def card_image(info,credit=True):
    """The link card as a data URI, so both hosts can show it without a second authenticated request."""
    from .card import render_card
    output=io.BytesIO()
    render_card(info,output,credit=credit)
    return 'data:image/png;base64,'+base64.b64encode(output.getvalue()).decode()


def create_router(home_provider):
    def service(): return Drops(home_provider())

    def boundary(request: Request):
        # Hermes owns authentication and profile/plugin authorization. This supplements its gate.
        if request.method!='GET':
            origin=request.headers.get('origin')
            if origin and origin.rstrip('/')!=str(request.base_url).rstrip('/'):
                raise HTTPException(403,'Cross-origin writes are not allowed.')
            if request.headers.get('content-type','').split(';')[0]!='application/json':
                raise HTTPException(415,'JSON is required.')

    router=APIRouter(dependencies=[Depends(boundary)])

    def call(fn):
        try:return fn()
        except DropError as exc:raise HTTPException(400,str(exc)) from None
        except (OSError,UnicodeError,ValueError):
            raise HTTPException(400,'The local operation could not be completed. No automatic retry was started.') from None

    def intent(drops,action,identifier,name,owner='',mode='create'):
        if action=='github':
            drops.export_dir(identifier)
            return {'action':action,'id':identifier,'owner':owner,'name':name,'mode':mode}
        if action=='install':
            info=drops.get(identifier);name_ok(name)
            return {'action':action,'id':identifier,'name':name,'digest':info['payload_digest']}
        if name!='default':name_ok(name)
        if name not in drops.profile_names()+['default']:raise DropError('Profile not found.')
        return {'action':action,'id':'','name':name}

    def consume(drops,token,expected):
        if not re.fullmatch(r'[A-Za-z0-9_-]{43}',token):raise DropError('Invalid confirmation.')
        path=drops.data/('confirm-'+hashlib.sha256(token.encode()).hexdigest()+'.json')
        with drops.lock():
            try: saved=json.loads(path.read_text('utf-8'))
            except (OSError,ValueError):raise DropError('Confirmation expired or already used.') from None
            if saved['expires']<time.time() or saved['intent']!=expected:
                raise DropError('Confirmation does not match this action. Review it again.')
            path.unlink()

    @router.get('/bootstrap')
    def bootstrap():
        drops=service()
        return {'profiles':drops.profile_names(),'retired':drops.retired_names(),'reviews':drops.list(),
                'home_name':drops.home.name,'data_directory':str(drops.data),
                'limits':'Public GitHub/GitLab repositories only. 20 MB total, 1 MB per file, 1,000 files. A preview can be adopted for 24 hours.'}

    @router.post('/preview')
    def preview(body: Preview):return call(lambda:service().preview(body.url.strip()))

    @router.post('/example')
    def example():return call(lambda:service().example())

    @router.get('/example/card')
    def example_card():
        from .core import inspect_tree
        from pathlib import Path
        return call(lambda:{'image':card_image(inspect_tree(Path(__file__).resolve().parents[1]/'examples'/'carousel-writer'))})

    @router.get('/reviews/{identifier}/card')
    def review_card(identifier: str):return call(lambda:{'image':card_image(service().get(identifier))})

    @router.post('/card')
    def card(body: Card):
        def render():
            info=service().share_preview(body.name,body.description,body.owner or None)
            return {'image':card_image(info,body.credit),'description':info['saved_description'],'author':info['author'],'skills':len(info['skills'])}
        return call(render)

    @router.get('/reviews/{identifier}')
    def get(identifier: str):return call(lambda:service().get(identifier))

    @router.get('/reviews/{identifier}/instructions')
    def instructions(identifier: str):
        def read():
            drops=service();info=drops.get(identifier);payload=drops.entry(identifier)/'payload'
            if digest(payload)!=info['payload_digest']:raise DropError('Reviewed files changed.')
            return {'files':[{'path':rel_path(p,payload),'text':p.read_text('utf-8')} for p in tree_files(payload) if p.suffix.lower() in {'.md','.txt'}]}
        return call(read)

    @router.post('/confirm')
    def confirm(body: Confirmation):
        def prepare():
            drops=service();expected=intent(drops,body.action,body.id,body.name,body.owner,body.mode)
            token=secrets.token_urlsafe(32)
            with drops.lock():
                for path in drops.data.glob('confirm-*.json'):
                    if path.stat().st_mtime<time.time()-300:path.unlink()
                if sum(1 for _ in drops.data.glob('confirm-*.json'))>=30:raise DropError('Too many pending confirmations. Try again in five minutes.')
                write_json(drops.data/('confirm-'+hashlib.sha256(token.encode()).hexdigest()+'.json'),{'intent':expected,'expires':time.time()+300})
            return {'confirmation':token,'expires_in':300}
        return call(prepare)

    @router.post('/install')
    def install(body: Install):
        def act():
            drops=service();consume(drops,body.confirmation,intent(drops,'install',body.id,body.name))
            return drops.install(body.id,body.name,confirmed=True)
        return call(act)

    @router.post('/publish')
    def publish(body: Publish):
        def act():
            drops=service();consume(drops,body.confirmation,intent(drops,'publish','',body.name))
            result=drops.publish(body.name,confirmed=True,credit=body.credit,description=body.description,owner=body.owner or None)
            package=drops.data/result['id'];archive=drops.data/(result['id']+'.zip')
            with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as output:
                for file in tree_files(package):output.write(file,rel_path(file,package))
            archive.chmod(0o600)
            result['archive']=str(archive)
            return result
        return call(act)

    @router.get('/github')
    def github_status():return call(lambda:service().github_status(with_drops=True))

    @router.post('/github/publish')
    def github_publish(body: GitHubPublish):
        def act():
            drops=service();consume(drops,body.confirmation,intent(drops,'github',body.id,body.name,body.owner,body.mode))
            return drops.publish_github(body.id,body.owner,body.name,confirmed=True,mode=body.mode)
        return call(act)

    @router.get('/download/{identifier}/{kind}')
    def download(identifier: str,kind: Literal['zip','card','story']):
        def read():
            if not re.fullmatch(r'export-[0-9a-f]{32}',identifier):raise DropError('Invalid export identifier.')
            path=service().data/identifier
            files=tree_files(path)
            if kind in ('card','story'):
                name='drop-'+kind+'.png'
                return Response((path/name).read_bytes(),media_type='image/png',headers={'Content-Disposition':'attachment; filename="'+name+'"','Cache-Control':'no-store'})
            output=io.BytesIO()
            with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
                for p in files:archive.write(p,rel_path(p,path))
            return Response(output.getvalue(),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="bot-drop.zip"','Cache-Control':'no-store'})
        return call(read)

    return router
