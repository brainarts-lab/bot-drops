import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from drops_v2.core import Drops, inspect_tree, safe_payload, write_json
from drops_v2.safety import DropError, digest, read_data, run_bounded, source_url, tree_files


class DropsV2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.base=Path(self.tmp.name)
        self.home=self.base/'home'/'.hermes'
        self.drops=Drops(self.home,hermes='/test/hermes')
        signed_out=patch('drops_v2.github.status',return_value={'available':False,'reason':'test'})
        signed_out.start();self.addCleanup(signed_out.stop)  # no network in unit tests
        self.source=self.base/'source';self.source.mkdir()
        write_json(self.source/'distribution.yaml',{'name':'sample-bot','description':'Writes useful things.','env_requires':[{'name':'OPENAI_API_KEY','required':True}]})
        (self.source/'SOUL.md').write_text('You are a concise writing assistant.')
        skill=self.source/'skills'/'writer';skill.mkdir(parents=True)
        (skill/'SKILL.md').write_text('---\nname: writer\ndescription: Write a clear article.\n---\nUse only supplied facts.')

    def tearDown(self): self.tmp.cleanup()

    def record(self): return self.drops._record(self.source,'a'*40,'https://github.com/example/sample')

    def test_rejects_unsafe_sources(self):
        for url in ['--upload-pack=evil','file:///tmp/repo','https://127.0.0.1/a/b','https://github.com@localhost/a/b','https://github.com:443/a/b','https://github.com/a/b?x=y','https://github.com/a/../b','git@github.com:a/b','https://gitlab.com/a/b#branch']:
            with self.subTest(url=url),self.assertRaises(DropError): source_url(url,resolve=False)
        self.assertEqual(source_url('example/sample',resolve=False),'https://github.com/example/sample')
        for page in ('https://example.github.io/sample/','https://example.github.io/sample','https://example.github.io/sample/index.html'):
            self.assertEqual(source_url(page,resolve=False),'https://github.com/example/sample')
        for bad in ('https://example.github.io/a/b/','https://evil.example/example.github.io/sample/','http://example.github.io/sample/'):
            with self.assertRaises(DropError): source_url(bad,resolve=False)

    def test_private_dns_rejected(self):
        with patch('drops_v2.safety.socket.getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]),self.assertRaises(DropError):
            source_url('example/sample')

    def test_risks_visible_and_inactive_in_payload(self):
        write_json(self.source/'config.yaml',{'model':{'provider':'custom','base_url':'https://example.com/v1'},'terminal':{'backend':'local'},'future_setting':True})
        write_json(self.source/'mcp.json',{'servers':{'evil':{'command':'curl','args':['https://example.com']}}})
        (self.source/'cron').mkdir();write_json(self.source/'cron/jobs.json',{'jobs':[{'id':'job','name':'Mail','schedule':{'kind':'cron','expr':'0 8 * * *'},'enabled':True}]})
        manifest=read_data(self.source/'distribution.yaml');manifest.update(distribution_owned=['plugins'],future=True);write_json(self.source/'distribution.yaml',manifest)
        (self.source/'skills'/'writer'/'run.py').write_text('raise RuntimeError("never run")')
        info=self.record(); payload=self.drops.entry(info['id'])/'payload'
        self.assertGreaterEqual(len(info['warnings']),6)
        self.assertFalse((payload/'mcp.json').exists());self.assertFalse((payload/'skills/writer/run.py').exists())
        self.assertNotIn('model',read_data(payload/'config.yaml'))
        self.assertFalse(read_data(payload/'cron/jobs.json')['jobs'][0]['enabled'])
        self.assertEqual(info['env_requires'][0]['name'],'OPENAI_API_KEY')

    def test_symlinks_and_oversize_rejected(self):
        (self.source/'linked').symlink_to('/etc/passwd')
        with self.assertRaises(DropError): self.record()
        (self.source/'linked').unlink();(self.source/'huge').write_bytes(b'a'*(1024*1024+1))
        with self.assertRaises(DropError): self.record()

    def test_manifest_required_and_yaml_aliases_duplicate_rejected(self):
        for value in ['name: sample-bot\nname: other-bot','name: sample-bot\nx: &x [1]\ny: *x']:
            (self.source/'distribution.yaml').write_text(value)
            with self.assertRaises(DropError): self.record()
        (self.source/'distribution.yaml').unlink()
        with self.assertRaises(DropError): self.record()

    def test_secret_in_skill_blocks_without_value_in_error(self):
        secret='sk-proj-'+'a1B2c3D4e5F6'*4
        (self.source/'skills/writer/SKILL.md').write_text(secret)
        with self.assertRaises(DropError) as caught:self.record()
        self.assertIn('SKILL.md',str(caught.exception));self.assertNotIn(secret,str(caught.exception))

    def test_documentation_placeholders_and_plain_words_are_not_credentials(self):
        from drops_v2.safety import contains_secret
        harmless=['export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx','TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"',
                  'secret: "your-webhook-secret-here"','Use the sk-concurrency-diagnosis checklist','api_key: ${OPENAI_API_KEY}',
                  'password = <your password here>','API_KEY=changeme-changeme']
        for text in harmless:
            with self.subTest(text=text): self.assertFalse(contains_secret(text))
        for text in ['OPENAI_API_KEY=sk-proj-'+'a1B2c3D4e5F6'*3,'{"api_key": "opaque-credential-123456789"}',
                     'token: ghp_'+'Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8','AKIA'+'ABCDEFGH12345678','password: "correct-horse-battery-9"']:
            with self.subTest(text=text): self.assertTrue(contains_secret(text))

    def test_publish_skips_skills_bundled_with_hermes(self):
        profile=self.drops.profiles/'author';(profile/'skills/mine').mkdir(parents=True);(profile/'skills/cat/hermes-agent').mkdir(parents=True)
        (profile/'SOUL.md').write_text('Mine.')
        (profile/'skills/mine/SKILL.md').write_text('---\nname: mine\ndescription: Mine.\n---\nDo my thing.')
        (profile/'skills/cat/hermes-agent/SKILL.md').write_text('---\nname: hermes-agent\n---\nexport KEY=sk-xxxxxxxxxxxxxxxxxxxx')
        (profile/'skills/.bundled_manifest').write_text('hermes-agent:4ab125a008a021cdc898d5b4e56b2585\n')
        package=self.drops.publish('author',confirmed=True)
        files=set(package['files'])
        self.assertIn('skills/mine/SKILL.md',files)
        self.assertFalse(any('hermes-agent' in f for f in files))

    def test_json_credential_assignment_is_not_echoed_in_preview(self):
        write_json(self.source/'config.yaml',{'provider':{'api_key':'opaque-credential-123456789'}})
        with self.assertRaises(DropError) as caught:self.record()
        self.assertNotIn('opaque-credential',str(caught.exception))

    def test_install_requires_human_confirmation_and_new_name(self):
        info=self.record()
        with self.assertRaises(DropError):self.drops.install(info['id'],'new-bot')
        with self.assertRaises(DropError):self.drops.install(info['id'],'default',confirmed=True)
        (self.drops.profiles/'existing-bot').mkdir(parents=True)
        with self.assertRaises(DropError):self.drops.install(info['id'],'existing-bot',confirmed=True)

    def test_snapshot_is_pinned_and_success_idempotent(self):
        info=self.record();original=(self.source/'SOUL.md').read_text()
        (self.source/'SOUL.md').write_text('Author changed remote source after preview')
        calls=[]
        def installer(argv,**kwargs):
            calls.append(argv);shutil.copytree(Path(argv[3]),self.drops.profiles/'new-bot')
        with patch('drops_v2.core.run_bounded',side_effect=installer):
            installed=self.drops.install(info['id'],'new-bot',confirmed=True)
            again=self.drops.install(info['id'],'new-bot',confirmed=True)
        self.assertEqual(installed,again);self.assertEqual(len(calls),1)
        self.assertEqual((self.drops.profiles/'new-bot/SOUL.md').read_text(),original)
        self.assertEqual(installed['commit'],'a'*40)

    def test_changed_preview_payload_is_rejected(self):
        info=self.record();(self.drops.entry(info['id'])/'payload/SOUL.md').write_text('tampered')
        with self.assertRaises(DropError):self.drops.install(info['id'],'new-bot',confirmed=True)

    def test_expired_and_cross_home_previews_rejected(self):
        info=self.record();info['expires']=0;write_json(self.drops.entry(info['id'])/'review.json',info)
        with self.assertRaises(DropError):self.drops.get(info['id'])
        other=Drops(self.base/'other')
        with self.assertRaises(DropError):other.get(info['id'])

    def test_partial_install_never_retried(self):
        info=self.record()
        def installer(*a,**kw):
            (self.drops.profiles/'new-bot').mkdir(parents=True)
            raise DropError('interrupted')
        with patch('drops_v2.core.run_bounded',side_effect=installer):
            with self.assertRaises(DropError):self.drops.install(info['id'],'new-bot',confirmed=True)
        with self.assertRaisesRegex(DropError,'uncertain'):self.drops.install(info['id'],'new-bot',confirmed=True)

    def test_example_contains_real_instructions(self):
        info=self.drops.example()
        self.assertEqual(info['name'],'carousel-writer');self.assertEqual(len(info['skills']),1)
        self.assertIn('five',(self.drops.entry(info['id'])/'payload/SOUL.md').read_text().lower())

    def test_publish_excludes_private_data_and_creates_card(self):
        profile=self.drops.profiles/'author-bot';shutil.copytree(self.source,profile)
        for relative in ['.env','auth.json','memories/MEMORY.md','sessions/private.json']:
            p=profile/relative;p.parent.mkdir(exist_ok=True,parents=True);p.write_text('PRIVATE_CANARY')
        (profile/'auth.json').write_text('{"access_token":"PRIVATE_CANARY"}')
        result=self.drops.publish('author-bot',confirmed=True);package=Path(result['directory'])
        from PIL import Image
        with Image.open(package/'drop-card.png') as card:self.assertEqual(card.size,(1200,630))
        for file in tree_files(package):self.assertNotIn(b'PRIVATE_CANARY',file.read_bytes())
        self.assertTrue((package/'share.txt').is_file())

    def test_landing_page_is_self_contained_and_escapes_author_text(self):
        from drops_v2.landing import render_landing
        page=render_landing({'name':'x<script>alert(1)</script>','description':'a "quote" & <b>','env_requires':[{'name':'OPENROUTER_API_KEY'}]})
        self.assertNotIn('<script>alert(1)</script>',page.lower());self.assertNotIn('& <b>',page)
        self.assertIn('OPENROUTER_API_KEY',page);self.assertIn('drop-card.png',page)
        import re
        self.assertEqual(re.findall(r'src="(https?:[^"]+)"',page),[])  # no external assets
        self.assertEqual(re.findall(r'href="(https?:[^"]+)"',page),['https://x.com/chrisbrainarts'])  # only the credit link
        self.assertIn('rel="noopener noreferrer"',page)
        plain=render_landing({'name':'x','description':'d','env_requires':[]},credit=False)
        self.assertNotIn('BrainArts',plain);self.assertEqual(re.findall(r'href="(https?:[^"]+)"',plain),[])
        profile=self.drops.profiles/'author-bot';shutil.copytree(self.source,profile)
        package=Path(self.drops.publish('author-bot',confirmed=True)['directory'])
        self.assertTrue((package/'index.html').is_file())

    def test_shared_package_names_the_github_account_when_no_author_is_set(self):
        profile=self.drops.profiles/'author-bot';shutil.copytree(self.source,profile)
        with patch('drops_v2.github.status',return_value={'available':True,'login':'tester','owners':['tester']}):
            package=Path(self.drops.publish('author-bot',confirmed=True)['directory'])
        self.assertEqual(read_data(package/'distribution.yaml')['author'],'@tester')
        self.assertIn('by @tester',(package/'index.html').read_text())
        from PIL import Image
        with Image.open(package/'drop-story.png') as story:self.assertEqual(story.size,(1080,1920))

    def test_sharer_can_turn_off_the_credit_line(self):
        profile=self.drops.profiles/'author-bot';shutil.copytree(self.source,profile)
        on=Path(self.drops.publish('author-bot',confirmed=True)['directory'])
        off=Path(self.drops.publish('author-bot',confirmed=True,credit=False)['directory'])
        self.assertIn('chrisbrainarts',(on/'index.html').read_text());self.assertNotIn('BrainArts',(off/'index.html').read_text())
        self.assertNotEqual((on/'drop-card.png').read_bytes(),(off/'drop-card.png').read_bytes())

    def test_data_from_before_the_rename_is_carried_over(self):
        home=self.base/'legacy'/'.hermes';old=home/'plugin-data'/'agent-drops';old.mkdir(parents=True)
        (old/'marker').write_text('kept')
        drops=Drops(home,hermes='/test/hermes')
        self.assertEqual((drops.data/'marker').read_text(),'kept');self.assertFalse(old.exists())

    def test_exact_export_credential_canary_blocks(self):
        profile=self.drops.profiles/'author-bot';shutil.copytree(self.source,profile)
        secret='unusual!opaque@canary#value'
        (profile/'.env').write_text('CUSTOM_API_KEY='+secret)
        (profile/'skills/writer/SKILL.md').write_text('Accidentally pasted '+secret)
        with self.assertRaises(DropError) as caught:self.drops.publish('author-bot',confirmed=True)
        self.assertNotIn(secret,str(caught.exception));self.assertIn('SKILL.md',str(caught.exception))

    def test_timeout_kills_children(self):
        pidfile=self.base/'pid'
        program='import subprocess,time,pathlib,sys; p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"]);pathlib.Path(sys.argv[1]).write_text(str(p.pid));time.sleep(30)'
        with self.assertRaises(DropError):run_bounded([sys.executable,'-c',program,str(pidfile)],env=os.environ.copy(),cwd=self.base,timeout=.4)
        pid=int(pidfile.read_text())
        result=subprocess.run(['ps','-o','stat=','-p',str(pid)],capture_output=True,text=True)
        self.assertTrue(not result.stdout.strip() or result.stdout.strip().startswith('Z'))


if __name__=='__main__':unittest.main()
