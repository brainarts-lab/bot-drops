const DROPS_CSS = ".bot-drops{--ad-ink:#19352b;--ad-muted:#56685e;--ad-line:#d5ded1;box-sizing:border-box;background:#f5f5ed;color:var(--ad-ink);font-family:ui-sans-serif,system-ui,-apple-system,sans-serif;padding:30px clamp(18px,4vw,64px);min-height:100%;overflow:auto;font-size:15px;line-height:1.55}.bot-drops *{box-sizing:border-box}.bot-drops button,.bot-drops input,.bot-drops select{font:inherit}.bot-drops button:focus-visible,.bot-drops input:focus-visible,.bot-drops select:focus-visible,.bot-drops summary:focus-visible{outline:3px solid #527a28;outline-offset:3px}.ad-header,.ad-footer,.ad-cardtop{display:flex;align-items:center;justify-content:space-between;gap:16px}.ad-brand{font-size:12px;letter-spacing:.12em}.ad-brand b{font-weight:500;color:var(--ad-muted)}.ad-tag,.ad-pill{font-size:10px;letter-spacing:.07em;padding:6px 10px;border:1px solid var(--ad-line);border-radius:20px;white-space:nowrap}.ad-hero{max-width:760px;margin:54px 0 30px}.ad-eyebrow,.ad-step{font-size:11px;letter-spacing:.15em;font-weight:650;color:#607653}.ad-hero h1{font-size:clamp(40px,5vw,68px);line-height:1.04;letter-spacing:-.055em;margin:16px 0 22px;font-weight:650}.ad-hero em{font-family:Georgia,serif;font-weight:400}.ad-hero p:last-child{max-width:540px;color:var(--ad-muted);font-size:17px}.ad-tabs{display:flex;gap:8px;border-bottom:1px solid var(--ad-line);padding-bottom:18px;margin-bottom:24px}.ad-button{border:1px solid var(--ad-ink);border-radius:9px;background:var(--ad-ink);color:#f9fff6;padding:12px 19px;font-weight:600;cursor:pointer;line-height:1.35;text-align:center;min-height:44px;transition:background .15s,transform .15s}.ad-button:hover:not(:disabled){background:#2c5040;transform:translateY(-1px)}.ad-button:disabled{opacity:.45;cursor:not-allowed}.ad-secondary{background:#d6f492;color:#19352b;border-color:#bed681}.ad-secondary:hover:not(:disabled){background:#c9e985}.ad-quiet{background:transparent;color:var(--ad-ink);border-color:transparent;font-weight:500}.ad-quiet:hover:not(:disabled){background:#e6ecdf}.ad-active{background:#d6f492;color:#19352b;border-color:#bed681}.ad-layout{display:grid;grid-template-columns:minmax(0,1fr) 215px;gap:28px;align-items:start;max-width:1200px}.ad-panel{background:#fffef8;border:1px solid var(--ad-line);border-radius:18px;padding:clamp(20px,3vw,36px);box-shadow:0 8px 30px #20391c04;min-width:0}.ad-panel h2{font-size:28px;line-height:1.2;letter-spacing:-.035em;margin:14px 0 18px;overflow-wrap:anywhere}.ad-panel h3,.ad-recent h3{font-size:16px;font-weight:650;margin:24px 0 12px}.ad-panel p{margin:9px 0 16px}.ad-field{display:flex;flex-direction:column;gap:8px;margin:20px 0 14px;font-size:13px;font-weight:600}.ad-field input,.ad-field select{width:100%;padding:13px 14px;background:#fffefb;border:1px solid #b9c7b5;border-radius:8px;color:#19352b;min-height:48px}.ad-muted,.ad-limits{font-size:12px;color:var(--ad-muted)}.ad-example{display:flex;justify-content:space-between;align-items:center;gap:20px;border-top:1px solid var(--ad-line);margin-top:30px;padding-top:25px}.ad-example p{font-size:13px;color:var(--ad-muted);margin-bottom:0}.ad-example button{flex-shrink:0}.ad-recent{padding:0 4px}.ad-recent h3{margin-top:6px}.ad-recent button{display:block;text-align:left;width:100%;font-size:12px;overflow-wrap:anywhere}.ad-facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;padding:20px 0;border-bottom:1px solid var(--ad-line);margin-bottom:24px}.ad-facts small{display:block;font-size:10px;letter-spacing:.1em;color:var(--ad-muted)}.ad-facts b{font-size:13px;overflow-wrap:anywhere}.ad-keys{padding:0;list-style:none}.ad-keys li{border:1px solid var(--ad-line);border-radius:10px;padding:14px;margin:10px 0}.ad-keys code{font-size:12px;margin-right:10px}.ad-keys p{font-size:13px;margin:9px 0 0}.ad-pill{background:#edf4e6}.bot-drops code,.bot-drops pre{font:12px/1.5 ui-monospace,SFMono-Regular,monospace;overflow-wrap:anywhere;white-space:pre-wrap}.bot-drops pre{padding:12px;background:#eff1e9;border-radius:6px;max-height:350px;overflow:auto}.bot-drops details{border-bottom:1px solid var(--ad-line);padding:12px 0}.bot-drops summary{cursor:pointer;font-size:13px;font-weight:600;overflow-wrap:anywhere}.bot-drops details p{font-size:12px;overflow-wrap:anywhere;white-space:pre-wrap}.bot-drops details strong{font-size:12px}.ad-warnings{background:#fff5d9;border:1px solid #e7d9a8;border-radius:10px;padding:4px 16px 12px}.ad-warnings h3{margin-top:14px}.ad-source{margin:20px 0}.ad-instructions{margin:22px 0}.ad-adopt{border-top:1px solid var(--ad-line);margin-top:28px;padding-top:4px}.ad-check{display:flex;align-items:flex-start;gap:11px;font-size:13px;margin:20px 0;max-width:680px}.ad-check input{width:18px;height:18px;flex-shrink:0;margin-top:2px;accent-color:#294c37}.ad-trust,.ad-note{font-size:13px;background:#eaf0df;padding:14px;border-radius:8px}.ad-status,.ad-error{border-radius:10px;padding:16px;margin-bottom:20px;font-size:13px}.ad-status{background:#e4efda;display:flex;align-items:center;gap:12px}.ad-error{background:#fff0e8;border:1px solid #d7aa94;color:#76391f}.ad-error p{margin:8px 0}.ad-spinner{width:15px;height:15px;border:2px solid #abbfa0;border-top-color:#27482e;border-radius:50%;animation:ad-spin 1s linear infinite}.ad-success{background:#eaf4df;border:1px solid #c2d6ae;border-radius:12px;padding:20px;margin:20px 0}.ad-success h3{margin-top:0}.ad-success li{margin-bottom:8px}.ad-actions{display:flex;flex-wrap:wrap;gap:10px}.ad-share{max-width:850px}.ad-footer{font-size:11px;color:var(--ad-muted);border-top:1px solid var(--ad-line);padding-top:22px;margin-top:42px}.ad-limits{margin:12px 0 0;font-size:10px;max-width:800px}.ad-description{color:var(--ad-muted)}@keyframes ad-spin{to{transform:rotate(360deg)}}@media(max-width:850px){.ad-layout{grid-template-columns:minmax(0,1fr)}.ad-recent{border-top:1px solid var(--ad-line);padding-top:18px}.ad-recent button{width:auto;display:inline-block}.ad-tag{display:none}.ad-hero{margin-top:36px}.ad-footer{align-items:flex-start;flex-direction:column;gap:6px}}@media(max-width:480px){.ad-example{flex-direction:column;align-items:flex-start}.ad-facts{grid-template-columns:1fr 1fr}.ad-hero h1{font-size:44px}.ad-tabs button{flex:1;padding:12px 10px}.ad-cardtop{align-items:flex-start}.ad-panel{padding:20px}.ad-button{max-width:100%}}@media(prefers-reduced-motion:reduce){.ad-spinner{animation:none}.ad-button{transition:none}}\n.ad-hero{margin:34px 0 24px}.ad-hero h1{font-size:clamp(34px,4.6vw,58px);margin:0}.ad-panel h2{margin-top:0}.ad-inline{display:flex;gap:10px;margin:18px 0 8px}.ad-inline input{flex:1;min-width:0;padding:13px 14px;background:#fffefb;border:1px solid #b9c7b5;border-radius:8px;color:#19352b;min-height:48px}.ad-link{background:none;border:0;padding:0;color:var(--ad-ink);text-decoration:underline;text-underline-offset:3px;cursor:pointer;font-weight:600}.ad-link:disabled{opacity:.45;cursor:not-allowed}.ad-meta{font-size:12px;color:var(--ad-muted)}.ad-cardtop{margin-bottom:6px}.ad-chips{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:12px 0}.ad-label{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--ad-muted);min-width:52px}.ad-chip{font-size:12px;padding:5px 11px;border-radius:20px;background:#edf4e6;border:1px solid var(--ad-line);overflow-wrap:anywhere}.bot-drops .ad-warnings{border:1px solid #e7d9a8;border-radius:10px;padding:10px 16px;margin:16px 0}.ad-warning{border-top:1px solid #efe3b8;padding:10px 0 2px}.ad-warning b{font-size:13px}.bot-drops .ad-warning p{margin:4px 0}.ad-warning small{font-size:12px;color:var(--ad-muted)}.ad-adopt{margin-top:20px}.ad-hint{font-size:12px;color:#76391f;margin:-6px 0 6px}.bot-drops .ad-more{margin-top:14px;border-bottom:0}.ad-more summary{color:var(--ad-muted);font-weight:500}.bot-drops .ad-more p{font-size:13px;margin:10px 0}.ad-lists{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:8px 0 4px}.ad-lists b{font-size:13px}.ad-lists ul{margin:6px 0 0;padding-left:18px;font-size:14px}.ad-lists div:last-child ul{color:var(--ad-muted)}.ad-success ol{padding-left:20px}@media(max-width:480px){.ad-inline{flex-direction:column}.ad-lists{grid-template-columns:1fr}}\n.ad-post{width:100%;margin:12px 0;padding:12px;border:1px solid var(--ad-line);border-radius:8px;background:#fffefb;color:var(--ad-ink);font:inherit;font-size:14px;resize:vertical}.ad-chip{text-decoration:none;color:var(--ad-ink)}\n.ad-sharegrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin:16px 0 10px}.ad-sharegrid .ad-button{text-align:center;text-decoration:none;display:flex;align-items:center;justify-content:center}\n.ad-dest{margin:8px 0 4px}.ad-segment{display:flex;gap:8px;margin:4px 0 14px}.ad-inline-fields{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0 14px}\n";
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

(function () {
  const sdk=window.__HERMES_PLUGIN_SDK__;
  if (!sdk || !window.__HERMES_PLUGINS__) return;
  const bridge={
    api: (path, body) => sdk.fetchJSON('/api/plugins/bot-drops'+path, body === undefined ? undefined : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),
    error: e => {
      // Hermes' fetchJSON already extracts the server's message; its raw JSON is in e.body.
      const generic='Hermes could not complete this request. Check that Bot Drops is enabled for this profile, then reload.';
      if (![400,413,415,429].includes(e && e.status)) return generic;
      try{const detail=JSON.parse(e.body||'').detail; if (typeof detail==='string' && detail) return detail.slice(0,500);}catch{}
      return String(e.message||generic).slice(0,500);
    },
    download: async (result,kind) => {
      const response=await sdk.authedFetch('/api/plugins/bot-drops/download/'+result.id+'/'+kind);
      if (!response.ok) throw new Error('Download failed.');
      const url=URL.createObjectURL(await response.blob());
      const a=document.createElement('a'); a.href=url; a.download=kind==='zip'?'bot-drop.zip':'drop-'+kind+'.png';
      a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
    }
  };
  window.__HERMES_PLUGINS__.register('bot-drops',createDropsApp(sdk.React,bridge));
})();
