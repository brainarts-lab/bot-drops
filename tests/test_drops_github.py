"""GitHub publishing with a stand-in `gh` and GitHub remotes redirected to local bare repositories.

Real git runs (init, fetch, commit, push); nothing reaches the network."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from drops_v2.core import Drops, write_json
from drops_v2.safety import DropError, read_data

DROP_REPO = '{"topics":["hermes-agent-drop"],"permissions":{"push":true},"default_branch":"main","private":false}'
OTHER_REPO = '{"topics":[],"permissions":{"push":true},"default_branch":"main","private":false}'
FAKE_GH = """#!/bin/sh
echo "gh $*" >> "__BASE__/log"
case "$*" in
  "api user --jq .login") [ -e "__BASE__/signedout" ] && exit 1; echo tester;;
  "api user/orgs --jq .[].login") echo acme;;
  "api repos/tester/taken") echo '__OTHER__';;
  "api repos/tester/old-drop") echo '__DROP__';;
  "api repos/"*"/pages --jq .html_url") exit 1;;
  "api repos/"*) [ -d "__BASE__/remotes/${2#repos/}.git" ] && { echo '__DROP__'; exit 0; }; exit 1;;
  "repo list tester "*) echo old-drop;;
  "repo create "*) /usr/bin/git init -q --bare "__BASE__/remotes/$3.git";;
  *) exit 0;;
esac
"""
# Redirect https://github.com/<owner>/<repo>.git to a local bare repository; everything else is real git.
FAKE_GIT = """#!/bin/sh
n=$#
for a in "$@"; do
  case "$a" in https://github.com/*) a="__BASE__/remotes/${a#https://github.com/}";; esac
  set -- "$@" "$a"
done
shift $n
unset GIT_ALLOW_PROTOCOL
exec /usr/bin/git "$@"
"""


def git(*args, cwd=None):
    return subprocess.run(['/usr/bin/git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def install_fakes(base):
    """Write the stand-in gh/git into base/bin and return that directory."""
    bin_dir = Path(base) / 'bin'; bin_dir.mkdir(exist_ok=True)
    for name, body in (('gh', FAKE_GH), ('git', FAKE_GIT)):
        text = body.replace('__BASE__', str(base)).replace('__DROP__', DROP_REPO).replace('__OTHER__', OTHER_REPO)
        (bin_dir / name).write_text(text); (bin_dir / name).chmod(0o700)
    (Path(base) / 'log').write_text('')
    return bin_dir


class GitHubPublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = base = Path(self.tmp.name)
        self.log = base / 'log'
        env = patch.dict(os.environ, {'PATH': str(install_fakes(base)) + os.pathsep + os.environ['PATH']})
        env.start(); self.addCleanup(env.stop)
        # An earlier drop on "GitHub": one commit with a file the new version no longer has.
        old = base / 'old'; old.mkdir(); (old / 'old-file.txt').write_text('from the first version')
        git('init', '-q', '-b', 'main', cwd=old)
        git('-c', 'user.name=t', '-c', 'user.email=t@x', 'add', '-A', cwd=old)
        git('-c', 'user.name=t', '-c', 'user.email=t@x', 'commit', '-q', '-m', 'first', cwd=old)
        git('clone', '-q', '--bare', str(old), str(base / 'remotes' / 'tester' / 'old-drop.git'))
        self.drops = Drops(base / 'home' / '.hermes', hermes='/test/hermes')
        profile = self.drops.profiles / 'author-bot'
        (profile / 'skills' / 'writer').mkdir(parents=True)
        (profile / 'SOUL.md').write_text('You write short posts.')
        (profile / 'skills' / 'writer' / 'SKILL.md').write_text('---\nname: writer\ndescription: Write.\n---\nSteps.')
        write_json(profile / 'distribution.yaml', {'name': 'author-bot', 'description': 'Writes posts.', 'version': '1.0.0'})
        self.package = self.drops.publish('author-bot', confirmed=True)
        self.id = self.package['id']

    def commands(self): return self.log.read_text().splitlines()
    def created(self): return [c for c in self.commands() if c.startswith('gh repo create')]
    def remote(self, slug): return self.base / 'remotes' / (slug + '.git')
    def files(self, slug): return git('ls-tree', '-r', '--name-only', 'main', cwd=self.remote(slug)).split()

    def test_status_lists_login_organisations_and_existing_drops(self):
        self.assertEqual(self.drops.github_status(), {'available': True, 'login': 'tester', 'owners': ['tester', 'acme']})
        self.assertEqual(self.drops.github_status(with_drops=True)['drops'], [{'owner': 'tester', 'repo': 'old-drop'}])

    def test_status_when_signed_out_or_missing(self):
        (self.base / 'signedout').write_text('')
        info = self.drops.github_status()
        self.assertFalse(info['available']); self.assertIn('gh auth login', info['reason'])
        (self.base / 'signedout').unlink()
        with patch('drops_v2.github.shutil.which', return_value=None):
            self.assertFalse(self.drops.github_status()['available'])

    def test_requires_explicit_confirmation(self):
        with self.assertRaises(DropError): self.drops.publish_github(self.id, 'tester', 'author-bot')
        self.assertEqual(self.created(), [])

    def test_shared_package_names_the_github_account(self):
        self.assertEqual(read_data(Path(self.package['directory']) / 'distribution.yaml')['author'], '@tester')

    def test_creates_public_repo_uploads_package_enables_pages(self):
        result = self.drops.publish_github(self.id, 'acme', 'author-bot', confirmed=True)
        self.assertEqual(result['repo_url'], 'https://github.com/acme/author-bot')
        self.assertEqual(result['pages_url'], 'https://acme.github.io/author-bot/')
        self.assertEqual(len(self.created()), 1)
        self.assertIn('--public', self.created()[0]); self.assertIn('acme/author-bot', self.created()[0])
        files = self.files('acme/author-bot')
        for name in ('index.html', 'drop-card.png', 'drop-story.png', 'README.md', 'distribution.yaml', 'SOUL.md', 'skills/writer/SKILL.md'):
            self.assertIn(name, files)
        log = self.commands()
        self.assertTrue(any('/pages' in c and 'POST' in c for c in log)); self.assertTrue(any('--add-topic hermes-bot-drop' in c for c in log))
        self.assertIn('https://acme.github.io/author-bot/', result['post_text'])
        page = git('show', 'main:index.html', cwd=self.remote('acme/author-bot'))
        self.assertIn('og:image" content="https://acme.github.io/author-bot/drop-card.png', page)
        self.assertIn('data-repo="https://github.com/acme/author-bot"', page)
        self.assertIn('x.com/chrisbrainarts', page)

    def test_credit_choice_survives_until_the_upload(self):
        package = self.drops.publish('author-bot', confirmed=True, credit=False)
        self.drops.publish_github(package['id'], 'tester', 'quiet-bot', confirmed=True)
        self.assertNotIn('BrainArts', git('show', 'main:index.html', cwd=self.remote('tester/quiet-bot')))

    def test_repeating_the_same_request_does_not_create_a_second_repository(self):
        first = self.drops.publish_github(self.id, 'tester', 'author-bot', confirmed=True)
        again = self.drops.publish_github(self.id, 'tester', 'author-bot', confirmed=True)
        self.assertEqual(first, again); self.assertEqual(len(self.created()), 1)
        with self.assertRaises(DropError): self.drops.publish_github(self.id, 'tester', 'another-name', confirmed=True)
        self.assertEqual(len(self.created()), 1)

    def test_create_never_touches_an_existing_repository(self):
        for name in ('taken', 'old-drop'):
            with self.subTest(name=name), self.assertRaises(DropError) as caught:
                self.drops.publish_github(self.id, 'tester', name, confirmed=True)
            self.assertIn('already exists', str(caught.exception))
        self.assertEqual(self.created(), [])
        self.assertEqual(self.files('tester/old-drop'), ['old-file.txt'])

    def test_update_adds_a_commit_with_exactly_the_new_package(self):
        before = git('rev-parse', 'main', cwd=self.remote('tester/old-drop')).strip()
        result = self.drops.publish_github(self.id, 'tester', 'old-drop', confirmed=True, mode='update')
        self.assertTrue(result['changed']); self.assertEqual(self.created(), [])
        files = self.files('tester/old-drop')
        self.assertNotIn('old-file.txt', files); self.assertIn('index.html', files)
        parent = git('rev-parse', 'main^', cwd=self.remote('tester/old-drop')).strip()
        self.assertEqual(parent, before)  # history kept, no force push

    def test_update_with_identical_content_creates_no_commit(self):
        self.drops.publish_github(self.id, 'tester', 'old-drop', confirmed=True, mode='update')
        head = git('rev-parse', 'main', cwd=self.remote('tester/old-drop')).strip()
        again = self.drops.publish('author-bot', confirmed=True)
        result = self.drops.publish_github(again['id'], 'tester', 'old-drop', confirmed=True, mode='update')
        self.assertFalse(result['changed'])
        self.assertEqual(git('rev-parse', 'main', cwd=self.remote('tester/old-drop')).strip(), head)

    def test_update_refuses_repositories_not_created_as_drops_or_missing(self):
        for name in ('taken', 'missing-repo'):
            with self.subTest(name=name), self.assertRaises(DropError):
                self.drops.publish_github(self.id, 'tester', name, confirmed=True, mode='update')
        self.assertEqual(self.created(), [])
        self.assertEqual(self.files('tester/old-drop'), ['old-file.txt'])

    def test_foreign_owner_and_bad_names_are_rejected(self):
        for owner, repo in (('someone-else', 'author-bot'), ('tester', 'Bad Name'), ('tester', '../x'), ('tester', '-x')):
            with self.subTest(owner=owner, repo=repo), self.assertRaises(DropError):
                self.drops.publish_github(self.id, owner, repo, confirmed=True)
        self.assertEqual(self.created(), [])

    def test_secret_added_after_packaging_blocks_before_anything_is_sent(self):
        (Path(self.package['directory']) / 'README.md').write_text('key: sk-proj-' + 'a1B2c3D4e5F6' * 4)
        with self.assertRaises(DropError): self.drops.publish_github(self.id, 'tester', 'author-bot', confirmed=True)
        with self.assertRaises(DropError): self.drops.publish_github(self.id, 'tester', 'old-drop', confirmed=True, mode='update')
        self.assertEqual(self.created(), []); self.assertEqual(self.files('tester/old-drop'), ['old-file.txt'])

    def test_unknown_or_traversing_package_id_is_rejected(self):
        for bad in ('export-' + '0' * 32, '../../etc', 'export-../x'):
            with self.subTest(bad=bad), self.assertRaises(DropError):
                self.drops.publish_github(bad, 'tester', 'author-bot', confirmed=True)


if __name__ == '__main__':
    unittest.main()
