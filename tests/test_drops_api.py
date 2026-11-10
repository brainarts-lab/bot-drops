from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


class DropsApiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.home=Path(self.temp.name)/'.hermes'
        from drops_v2.api import create_router
        app=FastAPI();app.include_router(create_router(lambda:self.home))
        self.client=TestClient(app,base_url='http://testserver')

    def tearDown(self):self.temp.cleanup()

    def test_example_is_read_only_until_explicit_bound_confirmation(self):
        info=self.client.post('/example',json={}).json()
        self.assertEqual(info['name'],'carousel-writer')
        body={'id':info['id'],'name':'my-carousel'}
        self.assertEqual(self.client.post('/install',json=body).status_code,422)
        token=self.client.post('/confirm',json={'action':'install',**body}).json()['confirmation']
        with patch('drops_v2.api.Drops.install',return_value={'status':'installed','installed_profile':'my-carousel'}) as install:
            self.assertEqual(self.client.post('/install',json={**body,'name':'changed-name','confirmation':token}).status_code,400)
            self.assertFalse(install.called)
            response=self.client.post('/install',json={**body,'confirmation':token})
            self.assertEqual(response.status_code,200)
            self.assertEqual(self.client.post('/install',json={**body,'confirmation':token}).status_code,400)
            self.assertEqual(install.call_count,1)

    def test_public_repository_needs_a_confirmation_bound_to_owner_and_name(self):
        export='export-'+'a'*32;(self.home/'plugin-data'/'bot-drops'/export).mkdir(parents=True)
        base={'id':export,'owner':'tester','name':'my-bot'}
        self.assertEqual(self.client.post('/github/publish',json=base).status_code,422)
        token=self.client.post('/confirm',json={'action':'github',**base}).json()['confirmation']
        with patch('drops_v2.api.Drops.publish_github',return_value={'repo_url':'u','pages_url':''}) as publish,\
             patch('drops_v2.api.read_data',return_value={'description':'d'}):
            for changed in ({'owner':'acme'},{'name':'other-bot'}):
                self.assertEqual(self.client.post('/github/publish',json={**base,**changed,'confirmation':token}).status_code,400)
            self.assertFalse(publish.called)
            token=self.client.post('/confirm',json={'action':'github',**base}).json()['confirmation']
            self.assertEqual(self.client.post('/github/publish',json={**base,'confirmation':token}).status_code,200)
            self.assertEqual(self.client.post('/github/publish',json={**base,'confirmation':token}).status_code,400)
            self.assertEqual(publish.call_count,1)
        self.assertEqual(self.client.post('/confirm',json={'action':'github','id':'export-'+'b'*32,'owner':'t','name':'my-bot'}).status_code,400)

    def test_cards_are_drawn_locally_and_never_read_other_profiles_by_path(self):
        import base64
        def png(response):
            self.assertEqual(response.status_code,200,response.text)
            image=response.json()['image'];self.assertTrue(image.startswith('data:image/png;base64,'))
            self.assertEqual(base64.b64decode(image.split(',',1)[1])[:8],b'\x89PNG\r\n\x1a\n')
            return response.json()
        png(self.client.get('/example/card'))
        info=self.client.post('/example',json={}).json()
        png(self.client.get('/reviews/'+info['id']+'/card'))
        self.assertEqual(self.client.get('/reviews/'+'0'*32+'/card').status_code,400)
        profile=self.home/'profiles'/'my-bot';profile.mkdir(parents=True);(profile/'SOUL.md').write_text('Hi.')
        with patch('drops_v2.github.status',return_value={'available':False,'reason':'test'}):
            self.assertEqual(png(self.client.post('/card',json={'name':'my-bot','description':'Plans my week'}))['skills'],0)
            for bad in ({'name':'../my-bot'},{'name':'missing-bot'},{'name':'my-bot','description':'x'*141}):
                self.assertEqual(self.client.post('/card',json=bad).status_code,400,bad)

    def test_sharing_a_bot_with_a_description_needs_its_own_confirmation(self):
        profile=self.home/'profiles'/'my-bot';profile.mkdir(parents=True);(profile/'SOUL.md').write_text('Hi.')
        body={'name':'my-bot','credit':False,'description':'Plans my week'}
        with patch('drops_v2.github.status',return_value={'available':False,'reason':'test'}):
            self.assertEqual(self.client.post('/publish',json=body).status_code,422)
            token=self.client.post('/confirm',json={'action':'publish','name':'my-bot'}).json()['confirmation']
            response=self.client.post('/publish',json={**body,'confirmation':token})
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(self.client.post('/publish',json={**body,'confirmation':token}).status_code,400)  # single use
        package=Path(response.json()['directory'])
        self.assertIn('Plans my week',(package/'index.html').read_text())
        self.assertNotIn('BrainArts',(package/'index.html').read_text())
        self.assertEqual(self.client.get('/download/'+response.json()['id']+'/card').content[:4],b'\x89PNG')

    def test_cross_origin_and_form_posts_rejected(self):
        self.assertEqual(self.client.post('/example',json={},headers={'Origin':'https://evil.example'}).status_code,403)
        self.assertEqual(self.client.post('/example',data={}).status_code,415)

    def test_identifier_download_traversal_and_unknown_action_rejected(self):
        self.assertEqual(self.client.get('/reviews/unknown').status_code,400)
        self.assertNotEqual(self.client.get('/download/..%2F..%2Fetc/passwd').status_code,200)
        self.assertEqual(self.client.post('/confirm',json={'action':'shell','id':'x','name':'x'}).status_code,422)


if __name__=='__main__':unittest.main()
