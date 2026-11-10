"""Bounded, non-executing inspection of untrusted distribution bytes."""
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from ruamel.yaml.events import AliasEvent

MAX_BYTES = 20 * 1024 * 1024
MAX_FILE = 1024 * 1024
MAX_FILES = 1000
NAME = re.compile(r'[a-z][a-z0-9-]{1,47}\Z')
PRIVATE = {'.env', 'auth.json', 'memories', 'memory', 'sessions', 'logs', 'vault', 'home',
           '.ssh', '.aws', '.config', 'mcp-tokens', 'backups', 'local', 'workspace', '.git'}
SECRET = re.compile(r'(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:api[_-]?key|secret|token|password)["\']?\s*[=:]\s*[\"\']?(?!\$\{|YOUR_|<|\"?\s*$)[A-Za-z0-9_./+\-]{12,})', re.I)

class DropError(ValueError):
    pass


WINDOWS = os.name == 'nt'
# What a helper program may inherit: where programs and the user's own folders are. Never keys.
ENV_KEYS = ('PATH', 'LANG', 'TMPDIR', 'HOME') + (
    ('SYSTEMROOT', 'SYSTEMDRIVE', 'WINDIR', 'COMSPEC', 'PATHEXT', 'TEMP', 'TMP', 'USERPROFILE', 'HOMEDRIVE',
     'HOMEPATH', 'APPDATA', 'LOCALAPPDATA', 'PROGRAMDATA', 'PROGRAMFILES', 'PROGRAMFILES(X86)', 'USERNAME')
    if WINDOWS else ())


def base_env():
    return {k: os.environ[k] for k in ENV_KEYS if k in os.environ}


def rel_path(path, root):
    """Relative path with forward slashes on every system (shown to people, compared and hashed)."""
    return Path(path).relative_to(root).as_posix()


def write_text(path, text):
    """UTF-8 with plain line endings everywhere; Windows would otherwise use its local code page."""
    Path(path).write_bytes(str(text).encode('utf-8'))


def remove_tree(path, ignore_errors=False):
    """Delete a folder. Git marks its object files read-only, which Windows refuses to delete as they are."""
    def retry(function, target, _):
        os.chmod(target, stat.S_IWRITE)
        function(target)
    handler = {'onexc': retry} if sys.version_info >= (3, 12) else {'onerror': retry}
    shutil.rmtree(path, ignore_errors=ignore_errors, **({} if ignore_errors else handler))


def tool(name, env=None):
    """Full path of an installed program, found on PATH without a shell."""
    found = shutil.which(name, path=(env if env is not None else os.environ).get('PATH'))
    if not found:
        raise DropError('Git is not installed. Install Git, then try again.' if name == 'git'
                        else 'A required program is not installed: ' + name)
    return found


def name_ok(name):
    if not isinstance(name, str) or not NAME.fullmatch(name) or name in {'default','hermes','test','tmp','root','sudo'}:
        raise DropError('Choose a new profile name: 2–48 lowercase letters, numbers and hyphens.')
    return name


def clean_text(value, limit=400):
    text = str(value or '')
    if len(text) > limit or any(ord(c) < 32 and c not in '\n\t' for c in text):
        raise DropError('Metadata is too long or contains control characters.')
    return text


def source_url(value, resolve=True):
    if not isinstance(value, str) or len(value) > 300:
        raise DropError('Use a public GitHub or GitLab repository URL.')
    if re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', value):
        value = 'https://github.com/' + value
    if value.startswith(('github.com/', 'gitlab.com/')):
        value = 'https://' + value
    # A GitHub Pages address of a shared bot (https://owner.github.io/repo/) names its repository.
    # The link Bot Drops hands out ends in ?v=<version>, so that is accepted here and nowhere else.
    pages = re.fullmatch(r'https://([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))\.github\.io/([A-Za-z0-9_][A-Za-z0-9_.-]*)/?(?:index\.html)?(?:\?v=[0-9a-f]{1,40})?', value)
    if pages:
        value = 'https://github.com/' + pages.group(1) + '/' + pages.group(2)
    u = urlsplit(value)
    if (u.scheme != 'https' or u.hostname not in {'github.com','gitlab.com'} or u.netloc != u.hostname
            or u.query or u.fragment or not re.fullmatch(r'/[A-Za-z0-9_][A-Za-z0-9_.-]*/[A-Za-z0-9_][A-Za-z0-9_.-]*(?:\.git)?',u.path)):
        raise DropError('Only public HTTPS GitHub/GitLab repositories are supported. No credentials, ports, redirects or local paths.')
    if '..' in u.path:
        raise DropError('Invalid repository path.')
    if resolve:
        try:
            addresses = socket.getaddrinfo(u.hostname,443,type=socket.SOCK_STREAM)
        except OSError as exc:
            raise DropError('Repository host could not be resolved.') from exc
        if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
            raise DropError('Repository host must resolve to public addresses.')
    return value.rstrip('/')


def tree_files(root, *, include_git=False, live=False):
    """Regular files below root, within the limits. `live` is for a folder a program is still writing to:
    a file that is gone again by the time it is looked at (Git's temporary and lock files) is skipped."""
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise DropError('Drop must be an existing regular directory.')
    total = 0
    files = []
    for current, dirs, names in os.walk(root, followlinks=False):
        if not include_git:
            dirs[:] = [d for d in dirs if d != '.git']
        for n in dirs + names:
            if any(ord(c)<32 for c in n):
                raise DropError('File names must not contain control characters.')
            p = Path(current)/n
            if p.is_symlink():
                raise DropError('Symlinks are not supported: '+rel_path(p,root))
        for n in names:
            p=Path(current)/n
            try: found=p.lstat()
            except OSError:
                if live: continue
                raise DropError('Only regular files are supported.') from None
            if not stat.S_ISREG(found.st_mode):
                raise DropError('Only regular files are supported.')
            size=found.st_size
            total+=size
            files.append(p)
            if (not include_git and size > MAX_FILE) or total > MAX_BYTES or len(files)>MAX_FILES:
                raise DropError('Drop exceeds the limit (20 MB, 1 MB per file, 1,000 files).')
    return sorted(files)


def digest(root):
    h=hashlib.sha256()
    for p in tree_files(root):
        h.update(rel_path(p,root).encode()+b'\0'+p.read_bytes()+b'\0')
    return h.hexdigest()


PLACEHOLDER = re.compile(r'your|example|placeholder|change-?me|redacted|dummy|sample|xxxx|\*\*\*|\.\.\.|<|\$\{', re.I)


def looks_like_secret(match):
    """Filter documentation placeholders and ordinary hyphenated words without weakening real-key detection."""
    text = match.group(0)
    if PLACEHOLDER.search(text):
        return False
    value = re.split(r'[=:]\s*["\']?', text, maxsplit=1)[-1] if re.search(r'[=:]', text) else text
    if len(set(re.sub(r'[^A-Za-z0-9]', '', value).lower())) <= 3:
        return False
    # Plain "sk-..." words such as "sk-concurrency-diagnosis" are not keys; real keys contain digits.
    if text.lower().startswith('sk-') and not re.search(r'\d', text):
        return False
    return True


def contains_secret(content):
    return any(looks_like_secret(m) for m in SECRET.finditer(content))


def secret_scan(root, known_values=()):
    for p in tree_files(root):
        rel=p.relative_to(root)
        if any(part in PRIVATE or part.startswith('.env.') for part in rel.parts):
            raise DropError('Private data is not shareable: '+rel.as_posix())
        content=p.read_bytes().decode('utf-8',errors='ignore')
        if contains_secret(content) or any(value in content for value in known_values):
            raise DropError('Possible credential found in '+rel.as_posix()+'. Remove it before sharing. The value was not logged.')


SECRET_NAME = re.compile(r'key|token|secret|passw|credential|cookie|session|private|signature|bearer|jwt', re.I)


def _is_secret(name, value):
    """Is this stored value something that must never leave the computer?
    Login stores also hold plain facts (provider names, client ids, service addresses) that appear
    in ordinary files; treating those as credentials would block sharing for every signed-in user."""
    if len(value) < 8 or re.fullmatch(r'https?://[^\s@?#]+', value):
        return False
    if SECRET_NAME.search(name):
        return True
    return len(value) >= 20 and ' ' not in value and bool(re.search(r'\d', value)) and bool(re.search(r'[A-Za-z]', value))


def profile_credentials(source):
    """Read only bounded local secret stores for exact-match scanning, never return their values to UI."""
    values=set()
    def collect(name,value):
        if isinstance(value,str):
            if _is_secret(name,value): values.add(value)
        elif isinstance(value,dict):
            for k,v in value.items(): collect(str(k),v)
        elif isinstance(value,list):
            for v in value: collect(name,v)
    for name in ('.env','auth.json'):
        path=source/name
        if not path.exists(): continue
        if path.is_symlink() or path.stat().st_size>MAX_FILE:
            raise DropError('Cannot scan the local credential store. Export was stopped.')
        try:
            content=path.read_text('utf-8')
            if name.endswith('.json'): collect('',json.loads(content))
            else:
                for line in content.splitlines():
                    if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                        key,value=line.split('=',1)
                        collect(key.strip(),value.strip().strip('\"\''))
        except (OSError,ValueError) as exc:
            raise DropError('Cannot scan the local credential store. Export was stopped.') from exc
    return values


def _text_keys(value):
    if isinstance(value,dict):
        if not all(isinstance(k,str) for k in value): raise DropError('Duplicate or non-text configuration key.')
        for v in value.values(): _text_keys(v)
    elif isinstance(value,list):
        for v in value: _text_keys(v)


def read_data(path, fallback=None):
    """Safe YAML/JSON read with ruamel.yaml (ships with Hermes): no aliases, no duplicate or non-text keys."""
    if not path.exists():
        return {} if fallback is None else fallback
    try:
        text=path.read_text('utf-8')
        # Forbid aliases before constructing anything (expansion bombs, ambiguous previews).
        if any(isinstance(event,AliasEvent) for event in YAML(typ='safe',pure=True).parse(text)):
            raise DropError('YAML aliases are not supported.')
        value=YAML(typ='safe',pure=True).load(text)  # duplicate keys raise DuplicateKeyError
        _text_keys(value)
    except DropError: raise
    except YAMLError as exc:
        if type(exc).__name__=='DuplicateKeyError': raise DropError('Duplicate or non-text configuration key.') from exc
        raise DropError('Invalid YAML/JSON: '+path.name) from exc
    except (UnicodeError,RecursionError) as exc:
        raise DropError('Invalid YAML/JSON: '+path.name) from exc
    try: json.dumps(value,allow_nan=False)
    except (TypeError,ValueError,RecursionError) as exc:
        raise DropError('Configuration must contain plain JSON-compatible values.') from exc
    return value if value is not None else ({} if fallback is None else fallback)


def _spawn(argv, env, cwd, output):
    """Start a program in its own group so that it and everything it starts can be stopped together."""
    common = dict(env=env, cwd=cwd, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT)
    if not WINDOWS:
        return subprocess.Popen(argv, start_new_session=True, **common), None
    proc = subprocess.Popen(argv, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW, **common)
    job = None
    try:
        # A job object keeps track of descendants even after their parent has exited.
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateJobObjectW.restype = wintypes.HANDLE
        kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel.TerminateJobObject.restype = wintypes.BOOL
        kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.CreateJobObjectW(None, None)
        if handle and kernel.AssignProcessToJobObject(handle, int(proc._handle)):
            job = (kernel, handle)
        elif handle:
            kernel.CloseHandle(handle)
    except (OSError, AttributeError, ValueError):
        job = None
    return proc, job


def _stop(proc, job):
    """End the program and its descendants. Never raises."""
    if not WINDOWS:
        try: os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError): pass
    else:
        if proc.poll() is None:
            taskkill = os.path.join(os.environ.get('SYSTEMROOT', r'C:\Windows'), 'System32', 'taskkill.exe')
            try:
                subprocess.run([taskkill, '/F', '/T', '/PID', str(proc.pid)], stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            except (OSError, subprocess.SubprocessError): pass
        if job:
            kernel, handle = job
            kernel.TerminateJobObject(handle, 1)
            kernel.CloseHandle(handle)
        if proc.poll() is None:
            try: proc.kill()
            except OSError: pass
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired: pass


def run_bounded(argv, *, env, cwd, monitored=None, timeout=45, detail=False):
    """No shell. Stops the whole process group, including descendants after the parent has exited."""
    argv = [str(a) for a in argv]
    if not os.path.isabs(argv[0]):
        argv[0] = tool(argv[0], env)
    if WINDOWS and argv[0].lower().endswith(('.cmd', '.bat')) and any(re.search(r'[&|<>^%"\r\n]', a) for a in argv[1:]):
        # Windows hands batch files to its command interpreter, which would read these characters as commands.
        raise DropError('This text contains characters that cannot be passed on safely on Windows: & | < > ^ % "')
    with tempfile.TemporaryFile() as output:
        proc, job = _spawn(argv, env, cwd, output)
        try:
            deadline=time.monotonic()+timeout
            while proc.poll() is None:
                if time.monotonic()>deadline:
                    raise DropError('Operation timed out. No automatic retry was started.')
                if monitored and Path(monitored).exists():
                    tree_files(monitored,include_git=True,live=True)
                if output.tell()>MAX_FILE:
                    raise DropError('Operation produced too much output.')
                time.sleep(.05)
            if proc.returncode:
                if detail:
                    output.seek(0)
                    text=' '.join(output.read(2000).decode('utf-8',errors='replace').split())[:300]
                    raise DropError('GitHub said: '+(text or 'the operation failed.'))
                raise DropError('Operation failed. Check repository access or the requested profile name.')
            output.seek(0)
            return output.read(MAX_FILE).decode('utf-8',errors='replace')
        finally:
            _stop(proc, job)


def git_env():
    env=base_env()
    # Git for Windows reads "/dev/null" as its null device too.
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_TERMINAL_PROMPT='0',
               GIT_LFS_SKIP_SMUDGE='1',GIT_ALLOW_PROTOCOL='https')
    return env


# Without the system configuration, Git for Windows has no certificate list of its own: use the Windows store.
GIT_SAFE = ['-c','core.hooksPath=/dev/null'] + (['-c','http.sslBackend=schannel'] if WINDOWS else [])


def clone_public(url, target):
    url=source_url(url)
    args=['git','-c','http.followRedirects=false','-c','credential.helper=']+GIT_SAFE+['-c','protocol.file.allow=never']
    env=git_env()
    run_bounded(args+['clone','--depth','1','--no-checkout','--',url,str(target)],env=env,
                cwd=target.parent,monitored=target)
    sha=run_bounded(args+['rev-parse','HEAD'],env=env,cwd=target).strip()
    entries=run_bounded(args+['ls-tree','-r','HEAD'],env=env,cwd=target)
    if any(line.startswith(('120000 ','160000 ')) for line in entries.splitlines()):
        raise DropError('Symlinks and Git submodules are not supported.')
    run_bounded(args+['checkout','--force','HEAD'],env=env,cwd=target,monitored=target)
    tree_files(target)
    return sha
