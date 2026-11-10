import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from drops_v2.core import Drops, inspect_tree, safe_payload, write_json
from drops_v2.safety import DropError, digest, read_data, remove_tree, run_bounded, source_url, tree_files


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

    def test_link_handed_out_after_sharing_can_be_pasted_back(self):
        # "Your bot is live" shows https://owner.github.io/repo/?v=<version>; that is what people post and paste.
        for link in ('https://example.github.io/sample/?v=8bbf949','https://example.github.io/sample/index.html?v=0'):
            self.assertEqual(source_url(link,resolve=False),'https://github.com/example/sample')
        for bad in ('https://example.github.io/sample/?v=','https://example.github.io/sample/?v=8bbf949&next=//evil.example',
                    'https://example.github.io/sample/?next=x','https://example.github.io/sample/?v=8bbf949#x','https://github.com/a/b?v=8bbf949'):
            with self.subTest(link=bad),self.assertRaises(DropError): source_url(bad,resolve=False)

    def test_files_that_vanish_while_git_works_do_not_fail_the_preview(self):
        # Seen for real on 10 Nov 2026: the size watcher met one of Git's lock files after Git had removed it again,
        # and a preview of a healthy public bot failed with "Only regular files are supported."
        root=Path(self.tmp.name)/'busy';root.mkdir();(root/'kept.txt').write_text('x')
        listing=[(str(root),[],['kept.txt','index.lock'])]  # index.lock was listed, then removed
        with patch('drops_v2.safety.os.walk',return_value=listing):
            self.assertEqual([p.name for p in tree_files(root,include_git=True,live=True)],['kept.txt'])
            with self.assertRaises(DropError): tree_files(root)  # the finished download is still checked strictly
        if hasattr(os,'mkfifo'):
            os.mkfifo(root/'pipe')
            with self.assertRaises(DropError): tree_files(root,include_git=True,live=True)  # odd files are never tolerated

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
        try: (self.source/'linked').symlink_to('/etc/passwd')
        except OSError: self.skipTest('This account may not create symlinks.')
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

    def author_profile(self):
        profile=self.drops.profiles/'author';(profile/'skills/mine').mkdir(parents=True)
        (profile/'SOUL.md').write_text('Mine.')
        (profile/'skills/mine/SKILL.md').write_text('---\nname: mine\ndescription: Mine.\n---\nDo my thing.')
        return profile

    def test_hermes_caches_and_category_notes_never_block_or_join_a_share(self):
        profile=self.author_profile()
        (profile/'skills/.hub/index-cache').mkdir(parents=True)
        (profile/'skills/.hub/index-cache/hermes-index.json').write_bytes(b'x'*(2*1024*1024))  # larger than any shareable file
        (profile/'skills/research').mkdir();(profile/'skills/research/DESCRIPTION.md').write_text('A category Hermes created.')
        self.assertEqual([s['name'] for s in self.drops.share_preview('author')['skills']],['mine'])
        files=set(self.drops.publish('author',confirmed=True)['files'])
        self.assertIn('skills/mine/SKILL.md',files)
        self.assertFalse(any('.hub' in f or 'DESCRIPTION.md' in f for f in files))
        (profile/'skills/mine/big.md').write_bytes(b'y'*(1024*1024+1))
        with self.assertRaises(DropError) as caught:self.drops.publish('author',confirmed=True)
        self.assertIn('too large',str(caught.exception))

    def test_description_written_while_sharing_reaches_card_page_and_recipient(self):
        self.author_profile()
        self.assertEqual(self.drops.share_preview('author')['description'],'A shared Hermes bot')
        self.assertEqual(self.drops.share_preview('author','  Plans   my week ')['description'],'Plans my week')
        with self.assertRaises(DropError):self.drops.share_preview('author','x'*141)
        with self.assertRaises(DropError):self.drops.publish('author',confirmed=True,description='x'*141)
        package=self.drops.publish('author',confirmed=True,description='Plans my week <b>')
        directory=Path(package['directory'])
        self.assertEqual(read_data(directory/'distribution.yaml')['description'],'Plans my week <b>')
        page=(directory/'index.html').read_text()
        self.assertIn('Plans my week &lt;b&gt;',page);self.assertNotIn('week <b>',page)
        received=self.drops._record(directory,'b'*40,'https://github.com/example/author')
        self.assertEqual(received['description'],'Plans my week <b>')
        self.assertEqual(received['warnings'],[])  # the neutral settings Bot Drops writes are not a warning

    def test_foreign_settings_still_warn(self):
        write_json(self.source/'config.yaml',{'plugins':{'enabled':['evil']},'mcp_servers':{},'terminal':{'shell':'x'}})
        details=[w['detail'] for w in self.record()['warnings']]
        self.assertEqual(len(details),2);self.assertTrue(any(d.startswith('plugins') for d in details))

    def test_storage_clears_what_can_no_longer_be_used(self):
        expired=self.record();adopted=self.record();fresh=self.record()
        for info,change in ((expired,{'expires':time.time()-5}),(adopted,{'expires':time.time()-5,'status':'installed','installed_profile':'kept'})):
            info.update(change);write_json(self.drops.entry(info['id'])/'review.json',info)
        old=self.drops.data/('export-'+'c'*32);old.mkdir();(self.drops.data/(old.name+'.zip')).write_text('z')
        os.utime(old,(time.time()-8*86400,)*2)
        recent=self.drops.data/('export-'+'d'*32);recent.mkdir()
        bystander=self.drops.profiles/'kept';bystander.mkdir(parents=True)
        self.drops.check_capacity()
        self.assertFalse(self.drops.entry(expired['id']).exists());self.assertFalse(old.exists())
        self.assertFalse((self.drops.data/(old.name+'.zip')).exists())
        for kept in (self.drops.entry(adopted['id']),self.drops.entry(fresh['id']),recent,bystander):self.assertTrue(kept.exists())

    def test_chat_preview_is_short_and_says_how_to_adopt(self):
        from drops_v2.commands import preview_text
        info=self.record();text=preview_text(info)
        self.assertTrue(text.startswith('Sample Bot'))
        self.assertIn('Needs: OPENAI_API_KEY',text);self.assertIn('Skills: writer',text)
        self.assertIn('/drop install '+info['id']+' --name sample-bot',text)
        self.assertNotIn('Not specified',text)

    def test_signed_in_profiles_with_their_own_settings_can_be_shared(self):
        profile=self.author_profile()
        token='ya29.A0'+'bC3dE4fG5hI6jK7'*3
        (profile/'auth.json').write_text(json.dumps({'active_provider':'openai-codex','providers':{'nous':{'client_id':'hermes-cli','portal_base_url':'https://portal.example.com/api','access_token':token}}}))
        (profile/'.env').write_text('HERMES_MODEL_NAME=openai-codex\nCUSTOM_API_KEY=shortkey9\n')
        (profile/'config.yaml').write_text('model:\n  provider: openai\n  default: gpt-4.1-mini\n  api_key: '+token+'\nauth:\n  provider: openai-codex\n  client: hermes-cli\n  portal: https://portal.example.com/api\n')
        (profile/'mcp.json').write_text(json.dumps({'servers':{'mine':{'command':'node','env':{'TOKEN':token}}}}))
        (profile/'SOUL.md').write_text('I run on openai-codex through hermes-cli.')
        package=Path(self.drops.publish('author',confirmed=True)['directory'])
        self.assertEqual(read_data(package/'config.yaml')['model'],{'provider':'openai','default':'gpt-4.1-mini'})
        self.assertFalse((package/'mcp.json').exists())
        for file in tree_files(package):self.assertNotIn(token.encode(),file.read_bytes())
        for leaked in (token,'shortkey9'):
            (profile/'SOUL.md').write_text('Use '+leaked+' for everything.')
            with self.subTest(leaked=leaked[:4]),self.assertRaises(DropError) as caught:self.drops.publish('author',confirmed=True)
            self.assertNotIn(leaked,str(caught.exception));self.assertIn('SOUL.md',str(caught.exception))

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

    def test_name_of_a_removed_bot_is_refused_before_anything_is_created(self):
        # Hermes 0.23.0 keeps profiles/.deleted/<name> after `hermes profile delete` and then fails half way through
        # `hermes profile install --name <name>`, leaving a broken profile behind (seen for real on 10 Nov 2026).
        info=self.record()
        (self.drops.profiles/'.deleted').mkdir(parents=True);(self.drops.profiles/'.deleted'/'old-bot').write_text('deleted\n')
        self.assertEqual(self.drops.retired_names(),['old-bot'])
        with patch('drops_v2.core.run_bounded') as installer, self.assertRaises(DropError) as raised:
            self.drops.install(info['id'],'old-bot',confirmed=True)
        installer.assert_not_called()
        self.assertIn('removed earlier',str(raised.exception))
        self.assertFalse((self.drops.profiles/'old-bot').exists())
        self.assertEqual(self.drops.get(info['id'])['status'],'review')  # the preview can still be adopted under a new name
        # Hermes 0.23.1 clears the mark itself during `hermes profile install`: the name is free again there.
        with patch('drops_v2.core.hermes_version',return_value=(0,23,1)): self.assertEqual(self.drops.retired_names(),[])
        with patch('drops_v2.core.hermes_version',return_value=(0,23,0)): self.assertEqual(self.drops.retired_names(),['old-bot'])

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
        self.assertEqual(re.findall(r'href="(https?:[^"]+)"',page),['https://x.com/chrisbrainarts']*2)  # only the credit links (card overlay, footer)
        self.assertIn('aria-label="BrainArts on X"',page)
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
        self.assertTrue(self.gone(int(pidfile.read_text())))

    def test_helper_left_behind_by_a_finished_program_is_stopped(self):
        pidfile=self.base/'pid'
        program='import subprocess,pathlib,sys; p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"]);pathlib.Path(sys.argv[1]).write_text(str(p.pid))'
        run_bounded([sys.executable,'-c',program,str(pidfile)],env=os.environ.copy(),cwd=self.base,timeout=20)
        self.assertTrue(self.gone(int(pidfile.read_text())))

    def gone(self,pid):
        """Has the process ended (or is it only waiting to be collected)? Allows a moment for the system to finish."""
        for _ in range(60):
            if os.name=='nt':
                listed=subprocess.run(['tasklist','/FI','PID eq '+str(pid),'/NH','/FO','CSV'],capture_output=True,text=True).stdout
                alive='"'+str(pid)+'"' in listed
            else:
                state=subprocess.run(['ps','-o','stat=','-p',str(pid)],capture_output=True,text=True).stdout.strip()
                alive=bool(state) and not state.startswith('Z')
            if not alive: return True
            time.sleep(.05)
        return False

    def test_operations_wait_for_each_other(self):
        order=[]
        def work(tag):
            with self.drops.lock():
                order.append(tag+' starts');time.sleep(.2);order.append(tag+' ends')
        threads=[threading.Thread(target=work,args=(tag,)) for tag in ('first','second')]
        for t in threads: t.start()
        for t in threads: t.join(10)
        self.assertEqual(len(order),4)
        self.assertEqual(order[0].split()[0],order[1].split()[0]);self.assertEqual(order[2].split()[0],order[3].split()[0])

    def test_text_beyond_ascii_survives_sharing_and_adoption(self):
        profile=self.drops.profiles/'gruss-bot';(profile/'skills'/'planer').mkdir(parents=True)
        soul='Grüße! 你好 🚀 Antworte kurz.'
        (profile/'SOUL.md').write_bytes(soul.encode('utf-8'))
        (profile/'skills'/'planer'/'SKILL.md').write_bytes('---\nname: planer\ndescription: Plant die Woche.\n---\nSchritte.'.encode('utf-8'))
        package=self.drops.publish('gruss-bot',confirmed=True,description='Plant deine Woche – übersichtlich 🚀')
        out=Path(package['directory'])
        self.assertIn('skills/planer/SKILL.md',package['files'])  # forward slashes on every system
        for name in ('index.html','README.md','distribution.yaml'):
            self.assertIn('übersichtlich 🚀',(out/name).read_bytes().decode('utf-8'))
            self.assertNotIn(b'\r\n',(out/name).read_bytes())
        info=self.drops._record(out,'local','local')
        self.assertEqual(info['description'],'Plant deine Woche – übersichtlich 🚀')
        self.assertEqual((self.drops.entry(info['id'])/'payload'/'SOUL.md').read_bytes().decode('utf-8'),soul)

    def test_folders_with_read_only_files_can_be_cleared(self):
        folder=self.base/'stale';(folder/'objects').mkdir(parents=True)
        locked=folder/'objects'/'pack';locked.write_text('x');locked.chmod(0o444)
        remove_tree(folder)
        self.assertFalse(folder.exists())


if __name__=='__main__':unittest.main()
