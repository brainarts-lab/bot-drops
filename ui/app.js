/* Shared consumer flow. Built into both host adapters by scripts/build-drops-ui.py. */

/* A shared "Open in Hermes" link (hermes://drops/import?url=…) lands on #/drops/import?url=…
   in Desktop, or /drops/import?url=… in the dashboard. Only a https link is taken; the backend
   still validates host, size and contents. Opening a link previews, it never installs. */
function dropLinkFromLocation(loc) {
  try {
    const hash = String(loc && loc.hash || '');
    const query = hash.includes('?') ? hash.slice(hash.indexOf('?') + 1) : String(loc && loc.search || '').replace(/^\?/, '');
    const link = (new URLSearchParams(query).get('url') || '').trim();
    return /^https:\/\/[^\s]{4,300}$/.test(link) ? link : '';
  } catch { return ''; }
}

function createDropsApp(React, bridge) {
  const h = React.createElement;
  const {useState, useEffect, useRef} = React;
  const button = (label, action, disabled = false, kind = '') => h('button', {type: 'button', className: 'ad-button '+kind, onClick: action, disabled}, label);
  const pretty = name => String(name || '').replaceAll('-', ' ');
  return function AgentDrops() {
    const incoming = useRef(typeof window === 'undefined' ? '' : dropLinkFromLocation(window.location));
    const [boot, setBoot] = useState(null), [tab, setTab] = useState('adopt');
    const [url, setUrl] = useState(incoming.current), [review, setReview] = useState(null), [name, setName] = useState('');
    const [profile, setProfile] = useState(''), [accepted, setAccepted] = useState(false);
    const [busy, setBusy] = useState(''), [error, setError] = useState(''), [exported, setExported] = useState(null);
    const [instructions, setInstructions] = useState(null);
    const [gh, setGh] = useState(null), [owner, setOwner] = useState(''), [repoName, setRepoName] = useState(''), [published, setPublished] = useState(null);
    const [target, setTarget] = useState('new'), [existing, setExisting] = useState(''), [credit, setCredit] = useState(true);
    const running = useRef(false), mounted = useRef(true);

    async function work(label, action) {
      if (running.current) return;
      running.current = true; setBusy(label); setError('');
      try { await action(); }
      catch (e) { if (mounted.current) setError(bridge.error ? bridge.error(e) : String(e.message || 'Please try again.')); }
      finally { running.current = false; if (mounted.current) setBusy(''); }
    }
    async function refresh() {
      const data = await bridge.api('/bootstrap');
      if (mounted.current) setBoot(data);
    }
    function previewLink(link) {
      return bridge.api('/preview', {url: link}).then(async info => { select(info); await refresh(); });
    }
    useEffect(() => {
      mounted.current = true;
      const first = incoming.current;
      // A shared link opens straight into its preview (never an installation).
      work('Loading…', async () => { await refresh(); if (first) await previewLink(first); });
      const onLink = () => {
        const link = dropLinkFromLocation(window.location);
        if (!link || link === incoming.current) return;
        incoming.current = link; setUrl(link);
        work('Checking this bot…', () => previewLink(link));
      };
      window.addEventListener('hashchange', onLink);
      return () => { mounted.current = false; window.removeEventListener('hashchange', onLink); };
    }, []);
    function select(info) {
      if (!mounted.current) return;
      setReview(info); setName(info.installed_profile || info.name); setAccepted(false); setInstructions(null); setTab('adopt');
    }
    function preview(example) {
      work(example ? 'Preparing the example…' : 'Checking this bot…', async () => {
        const info = await bridge.api(example ? '/example' : '/preview', example ? {} : {url: url.trim()});
        select(info); await refresh();
      });
    }
    function install() {
      if (!accepted || !review) return;
      work('Creating your bot…', async () => {
        const consent = await bridge.api('/confirm', {action: 'install', id: review.id, name});
        const result = await bridge.api('/install', {id: review.id, name, confirmation: consent.confirmation});
        select(result); await refresh();
      });
    }
    const SLUG = /^[a-z0-9][a-z0-9-]{1,62}$/;
    function loadGithub() {
      if (gh && !gh.failed) return;
      setGh({loading: true});
      bridge.api('/github').then(info => {
        if (!mounted.current) return;
        setGh(info); setOwner(o => o || info.login || '');
      }).catch(() => mounted.current && setGh({available: false, failed: true, reason: 'GitHub could not be reached.'}));
    }
    function chooseProfile(next) {
      setProfile(next); setAccepted(false);
      setRepoName(next === 'default' ? 'my-hermes-bot' : SLUG.test(next) ? next : '');
    }
    async function makePackage() {
      // One package per chosen bot; a failed upload can be retried without packaging again.
      if (exported && exported.profile === profile && exported.credit === credit) return exported;
      const consent = await bridge.api('/confirm', {action: 'publish', name: profile});
      const result = {...await bridge.api('/publish', {name: profile, credit, confirmation: consent.confirmation}), profile, credit};
      if (mounted.current) setExported(result);
      return result;
    }
    function publish() {  // manual path, when GitHub is not available
      if (!accepted || !profile) return;
      work('Preparing your share package…', async () => {await makePackage(); if (mounted.current) setAccepted(false);});
    }
    function shareNow() {
      if (!accepted || !profile) return;
      const update = target === 'update', [destOwner, destRepo] = update ? existing.split('/') : [owner, repoName];
      if (!destOwner || !SLUG.test(destRepo || '')) return;
      work(update ? 'Updating your drop on GitHub…' : 'Publishing on GitHub…', async () => {
        const pkg = await makePackage();
        const mode = update ? 'update' : 'create';
        const consent = await bridge.api('/confirm', {action: 'github', id: pkg.id, owner: destOwner, name: destRepo, mode});
        const result = await bridge.api('/github/publish', {id: pkg.id, owner: destOwner, name: destRepo, mode, confirmation: consent.confirmation});
        if (mounted.current) {setPublished(result); setAccepted(false);}
      });
    }
    function shareTargets(result) {
      const link = result.share_url || result.pages_url || result.repo_url, text = result.post_text.split('\n')[0], e = encodeURIComponent;
      return [
        {label: 'Post on X', href: 'https://x.com/intent/post?text='+e(text)+'&url='+e(link)},
        {label: 'LinkedIn', href: 'https://www.linkedin.com/sharing/share-offsite/?url='+e(link)},
        {label: 'Reddit', href: 'https://www.reddit.com/submit?url='+e(link)+'&title='+e(pretty(result.title)+' · a Hermes bot')},
        {label: 'Bluesky', href: 'https://bsky.app/intent/compose?text='+e(result.post_text)}];
    }
    function copyText(text) {
      try { navigator.clipboard.writeText(text).catch(() => {}); } catch { /* the text is also shown for manual copy */ }
    }
    const switchTab = next => () => {setTab(next); setAccepted(false); setError(''); if (next === 'share') loadGithub();};
    const checkbox = (text) => h('label', {className: 'ad-check'}, h('input', {type: 'checkbox', checked: accepted, onChange: e => setAccepted(e.target.checked), disabled: !!busy}), h('span', null, text));
    const more = (label, ...children) => h('details', {className: 'ad-more'}, h('summary', null, label), ...children);
    const notes = (items, label) => items?.length ? h('details', {className: 'ad-warnings'}, h('summary', null, label(items.length)),
      items.map((w, i) => h('div', {key: i, className: 'ad-warning'}, h('b', null, w.title), h('p', null, w.detail), h('small', null, w.action)))) : null;
    const recent = boot?.reviews?.length ? h('aside', {className: 'ad-recent'}, h('h3', null, 'Recent'), boot.reviews.map(i => button(pretty(i.name)+(i.status === 'installed' ? ' ✓' : ''), () => work('Opening…', async () => select(await bridge.api('/reviews/'+i.id))), !!busy, 'ad-quiet'))) : null;
    const installed = review?.status === 'installed';
    const validName = /^[a-z][a-z0-9-]{1,47}$/.test(name) && !['default','hermes','test','tmp','root','sudo'].includes(name);
    const taken = boot?.profiles?.includes(name) && !installed;
    const nameHint = taken ? 'That name is taken. Pick another.' : name && !validName ? 'Use lowercase letters, numbers and hyphens.' : '';

    const discover = h('section', {className: 'ad-panel'},
      h('h2', null, 'Got a bot link?'),
      h('form', {className: 'ad-inline', onSubmit: e => {e.preventDefault(); if (url.trim()) preview(false);}},
        h('input', {type: 'text', 'aria-label': 'Bot link', placeholder: 'Paste a GitHub or GitLab link', value: url, maxLength: 300, onChange: e => setUrl(e.target.value), disabled: !!busy, autoComplete: 'off'}),
        button('Preview', () => preview(false), !!busy || !url.trim() || !boot)),
      h('p', {className: 'ad-muted'}, 'No link yet? ', h('button', {type: 'button', className: 'ad-link', onClick: () => preview(true), disabled: !!busy || !boot}, 'Try an example bot')),
      more('How does this work?', h('p', null, 'Preview downloads and checks the bot. Nothing runs or installs until you adopt it, and adopting always creates a new bot.'), boot && h('p', {className: 'ad-muted'}, boot.limits)));

    const card = review && h('section', {className: 'ad-panel'},
      h('div', {className: 'ad-cardtop'}, h('span', {className: 'ad-meta'}, 'by '+review.author+' · v'+review.version), button('← Back', () => {setReview(null); setAccepted(false);}, !!busy, 'ad-quiet')),
      h('h2', null, pretty(installed ? name : review.name)), h('p', {className: 'ad-description'}, review.description),
      installed ? h('section', {className: 'ad-success'},
        h('h3', null, 'Done — this bot is yours.'),
        h('p', null, 'Add your own model key in Hermes, then say hi.'),
        bridge.finishBot ? button('Open Bot Chat →', () => work('Opening Bot Chat…', () => bridge.finishBot(review)), !!busy) : h('p', {className: 'ad-muted'}, 'Open Hermes Desktop to chat with it.'),
        more('What happened?', h('p', null, 'A new Hermes profile was created. No message was sent and no model has run. Telegram or Discord accounts are separate connections.')))
      : null,
      h('div', {className: 'ad-chips'},
        h('span', {className: 'ad-label'}, 'Needs'),
        review.env_requires.length ? review.env_requires.map(e => h('span', {key: e.name, className: 'ad-chip', title: e.description}, e.name+(e.required ? '' : ' (optional)'))) : h('span', {className: 'ad-chip'}, 'Your own model access')),
      review.skills.length ? h('div', {className: 'ad-chips'}, h('span', {className: 'ad-label'}, 'Skills'), review.skills.map(s => h('span', {key: s.name, className: 'ad-chip', title: s.description || ''}, s.name))) : null,
      notes(review.warnings, n => n === 1 ? '1 thing was left out for safety' : n+' things were left out for safety'),
      !installed && h('section', {className: 'ad-adopt'},
        h('label', {className: 'ad-field'}, h('span', null, 'Name your bot'), h('input', {value: name, onChange: e => {setName(e.target.value); setAccepted(false);}, maxLength: 48, disabled: !!busy, autoComplete: 'off'})),
        nameHint && h('p', {className: 'ad-hint'}, nameHint),
        checkbox('I trust where this bot comes from.'),
        button('Adopt bot →', install, !!busy || !accepted || !validName || taken)),
      more('More details',
        h('p', null, review.trust_notice+' Adopting creates a new bot; existing bots are never changed.'),
        review.cron.map((j, i) => h('p', {key: i}, 'Paused task: '+j.name+' · '+j.schedule)),
        h('p', null, 'Hermes: '+review.hermes_requires),
        h('p', null, 'Source: '+review.source), h('code', null, review.commit),
        h('p', {className: 'ad-muted'}, 'This exact checked version is what gets adopted. Later changes by the creator are not pulled in.'),
        button('Read personality & skills', () => work('Loading…', async () => {const data = await bridge.api('/reviews/'+review.id+'/instructions'); if (mounted.current) setInstructions(data.files);}), !!busy, 'ad-secondary'),
        instructions && instructions.map(f => h('details', {key: f.path}, h('summary', null, f.path), h('pre', null, f.text)))));

    const drops = gh?.drops || [];
    const repoValid = SLUG.test(repoName);
    const resetShare = () => {setExported(null); setPublished(null); setAccepted(false);};
    const manualSteps = h('ol', null, h('li', null, 'Save the package and unzip it.'), h('li', null, 'Upload all files to a new public GitHub repository.'), h('li', null, 'Post the card with the repository link.'));
    const saveButtons = exported && h('div', {className: 'ad-actions'}, button('Save card', () => work('Saving…', () => bridge.download(exported, 'card')), !!busy, 'ad-secondary'), button('Save package', () => work('Saving…', () => bridge.download(exported, 'zip')), !!busy, 'ad-secondary'));
    const pickBot = h('label', {className: 'ad-field'}, h('span', null, 'Which bot?'), h('select', {value: profile, onChange: e => chooseProfile(e.target.value), disabled: !!busy}, h('option', {value: ''}, 'Choose a bot…'), ...(boot?.profiles || []).map(p => h('option', {key: p, value: p}, p)), h('option', {value: 'default'}, 'default (your main profile)')));
    const contents = h('div', {className: 'ad-lists'},
      h('div', null, h('b', null, 'Shared'), h('ul', null, h('li', null, 'Personality'), h('li', null, 'Your own skills'))),
      h('div', null, h('b', null, 'Never shared'), h('ul', null, h('li', null, 'Keys & logins'), h('li', null, 'Memory & chats'), h('li', null, 'Plugins & connections'))));
    const destination = gh?.available && h('div', {className: 'ad-dest'},
      drops.length > 0 && h('div', {className: 'ad-segment', role: 'radiogroup', 'aria-label': 'Where to publish'},
        button('New drop', () => {setTarget('new'); setAccepted(false);}, !!busy, target === 'new' ? 'ad-active' : 'ad-quiet'),
        button('Update a drop', () => {setTarget('update'); setAccepted(false); if (!existing) setExisting(drops[0].owner+'/'+drops[0].repo);}, !!busy, target === 'update' ? 'ad-active' : 'ad-quiet')),
      target === 'update' && drops.length > 0
        ? h('label', {className: 'ad-field'}, h('span', null, 'Drop to update'), h('select', {value: existing, onChange: e => {setExisting(e.target.value); setAccepted(false);}, disabled: !!busy}, drops.map(d => h('option', {key: d.owner+'/'+d.repo, value: d.owner+'/'+d.repo}, d.owner+'/'+d.repo))))
        : h('div', {className: 'ad-inline-fields'},
            gh.owners.length > 1 && h('label', {className: 'ad-field'}, h('span', null, 'GitHub account'), h('select', {value: owner, onChange: e => {setOwner(e.target.value); setAccepted(false);}, disabled: !!busy}, gh.owners.map(o => h('option', {key: o, value: o}, o)))),
            h('label', {className: 'ad-field'}, h('span', null, 'Link name'), h('input', {value: repoName, onChange: e => {setRepoName(e.target.value.toLowerCase()); setAccepted(false);}, maxLength: 63, disabled: !!busy, autoComplete: 'off'}))),
      target !== 'update' && repoName && !repoValid && h('p', {className: 'ad-hint'}, 'Use lowercase letters, numbers and hyphens.'),
      target !== 'update' && repoValid && h('p', {className: 'ad-meta'}, 'Your link: '+owner.toLowerCase()+'.github.io/'+repoName));
    const creditToggle = h('label', {className: 'ad-check ad-credit'}, h('input', {type: 'checkbox', checked: credit, onChange: e => setCredit(e.target.checked), disabled: !!busy}), h('span', null, 'Show “Made with Bot Drops” on the page and card'));
    const ready = profile && (target === 'update' ? !!existing : repoValid && owner);
    const share = published ? h('section', {className: 'ad-panel ad-share ad-success'},
      h('h2', null, published.mode === 'update' ? (published.changed ? 'Your drop is updated' : 'Already up to date') : 'Your bot is live'),
      h('p', null, 'Post it anywhere. The card shows up on its own when you share the link.'),
      h('div', {className: 'ad-sharegrid'}, shareTargets(published).map(t => h('a', {key: t.label, className: 'ad-button ad-secondary', href: t.href, target: '_blank', rel: 'noopener noreferrer'}, t.label))),
      h('div', {className: 'ad-actions'}, button('Copy link', () => copyText(published.share_url || published.pages_url || published.repo_url), !!busy, 'ad-quiet'), button('Copy post text', () => copyText(published.post_text), !!busy, 'ad-quiet')),
      more('Instagram', h('p', null, 'Instagram has no share link. Save the story image, post it as a story and add a link sticker with your link.'),
        button('Save story image', () => work('Saving…', () => bridge.download(exported, 'story')), !!busy, 'ad-secondary')),
      more('Post text and files', h('textarea', {className: 'ad-post', readOnly: true, rows: 3, value: published.post_text, 'aria-label': 'Post text', onFocus: e => e.target.select()}),
        h('p', null, 'Page: '+(published.pages_url || '—')), h('p', null, 'Repository: '+published.repo_url),
        published.pages_url ? h('p', {className: 'ad-muted'}, 'Changes to the page can take a minute to appear.') : h('p', {className: 'ad-muted'}, 'GitHub Pages could not be turned on. The repository link works as is.'),
        button('Save card', () => work('Saving…', () => bridge.download(exported, 'card')), !!busy, 'ad-secondary')),
      button('← Share another bot', resetShare, !!busy, 'ad-quiet'))
    : gh?.available ? h('section', {className: 'ad-panel ad-share'},
      h('h2', null, 'Share your bot'),
      pickBot, contents, destination, creditToggle,
      checkbox(target === 'update' ? 'Replace the public drop with this version.' : 'Publish this bot publicly on GitHub.'),
      button(target === 'update' ? 'Update drop →' : 'Share bot →', shareNow, !!busy || !accepted || !ready),
      exported && notes(exported.warnings, n => n === 1 ? '1 thing was left out' : n+' things were left out'),
      more('Prefer to do it yourself?', manualSteps, exported ? saveButtons : h('p', {className: 'ad-muted'}, 'Share once to get the package files, or publish without GitHub below.')))
    : !exported ? h('section', {className: 'ad-panel ad-share'},
      h('h2', null, 'Share your bot'),
      pickBot, contents, creditToggle,
      gh?.loading ? h('p', {className: 'ad-meta'}, 'Checking GitHub…') : h('p', {className: 'ad-muted'}, (gh?.reason || 'GitHub is not available.')+' You can still prepare the files and upload them yourself.'),
      checkbox('I looked at what is shared.'),
      button('Prepare files →', publish, !!busy || !profile || !accepted || !boot || gh?.loading))
    : h('section', {className: 'ad-panel ad-share'},
      h('h2', null, 'Upload it yourself'),
      manualSteps, saveButtons,
      more('What is in the package', h('code', null, exported.directory), h('ul', null, exported.files.map(f => h('li', {key: f}, f))),
        h('p', {className: 'ad-muted'}, 'Only these files. A key scan cannot catch every secret, so take a quick look first.')),
      notes(exported.warnings, n => n === 1 ? '1 thing was left out' : n+' things were left out'),
      button('← Back', resetShare, !!busy, 'ad-quiet'));

    return h('main', {className: 'bot-drops'}, h('style', null, DROPS_CSS),
      h('header', {className: 'ad-header'}, h('span', {className: 'ad-brand'}, 'BRAINARTS', h('b', null, ' / BOT DROPS'))),
      h('section', {className: 'ad-hero'}, h('h1', null, 'Find a bot.', h('br'), h('em', null, 'Make it yours.'))),
      h('nav', {'aria-label': 'Bot Drops', className: 'ad-tabs'}, button('Adopt', switchTab('adopt'), !!busy, tab === 'adopt' ? 'ad-active' : 'ad-quiet'), button('Share', switchTab('share'), !!busy, tab === 'share' ? 'ad-active' : 'ad-quiet')),
      busy && h('div', {role: 'status', 'aria-live': 'polite', className: 'ad-status'}, h('span', {className: 'ad-spinner'}), busy),
      error && h('div', {role: 'alert', className: 'ad-error'}, h('strong', null, 'That did not work'), h('p', null, error), button('Try again', () => work('Reloading…', refresh), !!busy, 'ad-quiet')),
      !boot && !busy && h('p', {className: 'ad-note'}, 'Bot Drops is not enabled for this Hermes profile yet.'),
      tab === 'adopt' ? h('div', {className: 'ad-layout'}, h('div', null, review ? card : discover), recent) : share,
      h('footer', {className: 'ad-footer'}, h('span', null, 'Nothing is posted automatically.'), h('span', null, boot ? 'Hermes profile: '+boot.home_name : 'Waiting for Hermes'))
    );
  };
}
