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

/* First free bot name: carousel-writer, carousel-writer-2, … */
function freeBotName(base, taken) {
  if (!taken.includes(base)) return base;
  for (let i = 2; i < 100; i++) {
    const next = base.slice(0, 44) + '-' + i;
    if (!taken.includes(next)) return next;
  }
  return base;
}

function createDropsApp(React, bridge) {
  const h = React.createElement;
  const {useState, useEffect, useRef} = React;
  const button = (label, action, disabled = false, kind = '') => h('button', {type: 'button', className: 'bd-btn '+kind, onClick: action, disabled}, label);
  const pretty = name => String(name || '').replaceAll('-', ' ');
  const titled = name => pretty(name).replace(/\b[a-z]/g, c => c.toUpperCase());
  const SLUG = /^[a-z0-9][a-z0-9-]{1,62}$/;
  const TAGLINE = 140;
  return function BotDrops() {
    const incoming = useRef(typeof window === 'undefined' ? '' : dropLinkFromLocation(window.location));
    const [boot, setBoot] = useState(null), [tab, setTab] = useState('adopt');
    const [url, setUrl] = useState(incoming.current), [review, setReview] = useState(null), [name, setName] = useState('');
    const [profile, setProfile] = useState(''), [accepted, setAccepted] = useState(false);
    const [busy, setBusy] = useState(''), [error, setError] = useState(''), [exported, setExported] = useState(null);
    const [instructions, setInstructions] = useState(null);
    const [gh, setGh] = useState(null), [owner, setOwner] = useState(''), [repoName, setRepoName] = useState(''), [published, setPublished] = useState(null);
    const [target, setTarget] = useState('new'), [existing, setExisting] = useState(''), [credit, setCredit] = useState(true);
    const [cards, setCards] = useState({}), [tagline, setTagline] = useState(''), [touched, setTouched] = useState(false), [copied, setCopied] = useState('');
    const running = useRef(false), mounted = useRef(true), profiles = useRef([]);

    async function work(label, action) {
      if (running.current) return;
      running.current = true; setBusy(label); setError('');
      try { await action(); }
      catch (e) { if (mounted.current) setError(bridge.error ? bridge.error(e) : String(e.message || 'Please try again.')); }
      finally { running.current = false; if (mounted.current) setBusy(''); }
    }
    async function refresh() {
      const data = await bridge.api('/bootstrap');
      profiles.current = (data.profiles || []).concat(data.retired || []);  // names a new bot cannot take
      if (mounted.current) setBoot(data);
    }
    function previewLink(link) {
      return bridge.api('/preview', {url: link}).then(async info => { select(info); await refresh(); });
    }
    useEffect(() => {
      mounted.current = true;
      const first = incoming.current;
      // A shared link opens straight into its preview (never an installation).
      work(first ? 'Checking this bot…' : 'Loading…', async () => { await refresh(); if (first) await previewLink(first); });
      const onLink = () => {
        const link = dropLinkFromLocation(window.location);
        if (!link || link === incoming.current) return;
        incoming.current = link; setUrl(link);
        work('Checking this bot…', () => previewLink(link));
      };
      window.addEventListener('hashchange', onLink);
      return () => { mounted.current = false; window.removeEventListener('hashchange', onLink); };
    }, []);
    // Cards are drawn by the plugin itself from checked facts; a shared repository's own images are never shown.
    const ready = !!boot;
    useEffect(() => {
      if (!ready) return;
      bridge.api('/example/card').then(r => mounted.current && setCards(c => ({...c, example: r.image}))).catch(() => {});
    }, [ready]);
    const reviewId = review ? review.id : '';
    useEffect(() => {
      if (!reviewId) return;
      bridge.api('/reviews/'+reviewId+'/card').then(r => mounted.current && setCards(c => ({...c, review: {id: reviewId, src: r.image}}))).catch(() => {});
    }, [reviewId]);
    const typed = touched ? tagline : null;
    // The card names the account the bot is shared under: your own, or an organization you choose.
    const sharedAs = target === 'update' ? (existing.split('/')[0] || '') : owner;
    useEffect(() => {
      if (tab !== 'share' || !profile) return;
      let live = true;
      const timer = setTimeout(() => {
        bridge.api('/card', {name: profile, credit, ...(sharedAs ? {owner: sharedAs} : {}), ...(typed === null ? {} : {description: typed})}).then(r => {
          if (!live || !mounted.current) return;
          setCards(c => ({...c, share: {profile, src: r.image}}));
          if (typed === null) setTagline(r.description || '');
        }).catch(() => {});
      }, typed === null ? 0 : 350);
      return () => { live = false; clearTimeout(timer); };
    }, [tab, profile, credit, typed, sharedAs]);

    function select(info) {
      if (!mounted.current) return;
      setReview(info); setName(info.installed_profile || freeBotName(info.name, profiles.current)); setAccepted(false); setInstructions(null); setTab('adopt');
    }
    function preview(example) {
      work(example ? 'Opening the example…' : 'Checking this bot…', async () => {
        const info = await bridge.api(example ? '/example' : '/preview', example ? {} : {url: url.trim()});
        select(info); await refresh();
      });
    }
    function install() {
      if (!accepted || !review) return;
      work('Adopting your bot…', async () => {
        const consent = await bridge.api('/confirm', {action: 'install', id: review.id, name});
        const result = await bridge.api('/install', {id: review.id, name, confirmation: consent.confirmation});
        select(result); await refresh();
      });
    }
    function loadGithub() {
      if (gh && !gh.failed) return;
      setGh({loading: true});
      bridge.api('/github').then(info => {
        if (!mounted.current) return;
        setGh(info); setOwner(o => o || info.login || '');
      }).catch(() => mounted.current && setGh({available: false, failed: true, reason: 'GitHub could not be reached.'}));
    }
    function chooseProfile(next) {
      setProfile(next); setAccepted(false); setTagline(''); setTouched(false); setCards(c => ({...c, share: null}));
      setRepoName(next === 'default' ? 'my-hermes-bot' : SLUG.test(next) ? next : '');
    }
    async function makePackage() {
      // One package per chosen bot; a failed upload can be retried without packaging again.
      if (exported && exported.profile === profile && exported.credit === credit && exported.tagline === tagline && exported.owner === sharedAs) return exported;
      const consent = await bridge.api('/confirm', {action: 'publish', name: profile});
      const result = {...await bridge.api('/publish', {name: profile, credit, description: tagline.trim(), ...(sharedAs ? {owner: sharedAs} : {}), confirmation: consent.confirmation}), profile, credit, tagline, owner: sharedAs};
      if (mounted.current) setExported(result);
      return result;
    }
    function publish() {  // manual path, when GitHub is not available
      if (!accepted || !profile) return;
      work('Preparing your files…', async () => {await makePackage(); if (mounted.current) setAccepted(false);});
    }
    function shareNow() {
      if (!accepted || !profile) return;
      const update = target === 'update', [destOwner, destRepo] = update ? existing.split('/') : [owner, repoName];
      if (!destOwner || !SLUG.test(destRepo || '')) return;
      work(update ? 'Updating your drop…' : 'Publishing your bot…', async () => {
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
        {label: 'Reddit', href: 'https://www.reddit.com/submit?url='+e(link)+'&title='+e(titled(result.title)+' · a Hermes bot')},
        {label: 'Bluesky', href: 'https://bsky.app/intent/compose?text='+e(result.post_text)}];
    }
    function copyText(text, key) {
      try { navigator.clipboard.writeText(text).catch(() => {}); } catch { /* the text is also shown for manual copy */ }
      setCopied(key); setTimeout(() => mounted.current && setCopied(c => c === key ? '' : c), 1600);
    }
    const switchTab = next => () => {setTab(next); setAccepted(false); setError(''); if (next === 'share') loadGithub();};
    const checkbox = text => h('label', {className: 'bd-check'}, h('input', {type: 'checkbox', checked: accepted, onChange: e => setAccepted(e.target.checked), disabled: !!busy}), h('span', null, text));
    const more = (label, ...children) => h('details', null, h('summary', null, label), ...children);
    const notes = (items, label) => items?.length ? h('details', {className: 'bd-notes'}, h('summary', null, label(items.length)),
      items.map((w, i) => h('div', {key: i, className: 'bd-note'}, h('b', null, w.title), h('p', null, w.detail), h('small', null, w.action)))) : null;
    const cardView = (src, alt, wait, caption) => h('figure', {className: 'bd-card'},
      src ? h('img', {src, alt, width: 1200, height: 630}) : h('div', {className: 'bd-card-wait'}, wait),
      caption && h('figcaption', null, caption));

    const installed = review?.status === 'installed';
    const validName = /^[a-z][a-z0-9-]{1,47}$/.test(name) && !['default','hermes','test','tmp','root','sudo'].includes(name);
    const retired = boot?.retired?.includes(name) && !installed;
    const taken = (boot?.profiles?.includes(name) || retired) && !installed;
    const nameHint = retired ? 'A bot with that name was removed earlier. Choose another name.' : taken ? 'You already have a bot with that name.' : name && !validName ? 'Use lowercase letters, numbers and hyphens.' : '';

    // Start: paste a link, or pick up the example card.
    const seen = new Set();
    const recentItems = (boot?.reviews || []).filter(i => {
      if (i.status === 'installed' && !(boot?.profiles || []).includes(i.installed_profile)) return false;  // that bot was removed since
      const key = i.installed_profile || i.name;
      if (seen.has(key)) return false;
      seen.add(key); return true;
    }).slice(0, 5);
    const start = h('div', {className: 'bd-start'},
      h('div', null,
        h('h1', {className: 'bd-h1'}, 'Find a bot', h('span', null, 'Make it yours')),
        h('p', {className: 'bd-lead'}, 'Paste a link someone shared. You see what is inside before anything is added to your Hermes.'),
        h('form', {className: 'bd-row', onSubmit: e => {e.preventDefault(); if (url.trim()) preview(false);}},
          h('input', {type: 'text', 'aria-label': 'Bot link', placeholder: 'Paste a bot link', value: url, maxLength: 300, onChange: e => setUrl(e.target.value), disabled: !!busy, autoComplete: 'off'}),
          button('Preview', () => preview(false), !!busy || !url.trim() || !boot)),
        recentItems.length > 0 && h('div', {className: 'bd-recent'}, h('span', null, 'Recent'),
          recentItems.map(i => h('button', {key: i.id, type: 'button', className: 'bd-chip'+(i.status === 'installed' ? ' on' : ''), disabled: !!busy,
            onClick: () => work('Opening…', async () => select(await bridge.api('/reviews/'+i.id)))}, pretty(i.installed_profile || i.name)+(i.status === 'installed' ? ' ✓' : ''))))),
      h('button', {type: 'button', className: 'bd-example', onClick: () => preview(true), disabled: !!busy || !boot, 'aria-label': 'Try the example bot Carousel Writer'},
        cardView(cards.example, '', boot ? 'Loading the example…' : '', h('span', null, 'No link yet? ', h('b', null, 'Try this example bot')))));

    // Preview of one bot: its card, what it brings, and the one decision.
    const author = review && review.author && review.author !== 'Not specified' ? review.author : '';
    const reviewCard = review && cards.review && cards.review.id === review.id ? cards.review.src : '';
    const adoptPanel = review && (installed
      ? h('section', {className: 'bd-done'},
          h('h3', null, 'Done, this bot is yours'),
          h('p', null, 'Add your own model key in Hermes, then say hi.'),
          bridge.finishBot ? button('Open Bot Chat', () => work('Opening Bot Chat…', () => bridge.finishBot(review)), !!busy, 'wide')
            : h('p', {className: 'bd-muted'}, 'Switch to “'+name+'” in the Hermes profile menu to chat with it.'),
          more('What happened?', h('p', null, 'A new Hermes profile was created. No message was sent and no model has run. Telegram or Discord accounts are separate connections.')))
      : h('section', {className: 'bd-panel'},
          h('h3', null, 'Make it yours'),
          h('label', {className: 'bd-field'}, h('span', null, 'Name your bot'), h('input', {value: name, onChange: e => {setName(e.target.value.toLowerCase()); setAccepted(false);}, maxLength: 48, disabled: !!busy, autoComplete: 'off'})),
          nameHint && h('p', {className: 'bd-hint'}, nameHint),
          checkbox('I trust where this bot comes from'),
          button('Adopt this bot', install, !!busy || !accepted || !validName || taken, 'wide'),
          h('p', {className: 'bd-muted', style: {margin: '12px 0 0'}}, 'Creates a new bot. Your other bots, keys and chats stay as they are.')));
    const card = review && h('div', null,
      button('← All bots', () => {setReview(null); setAccepted(false);}, !!busy, 'text'),
      h('div', {className: 'bd-two', style: {marginTop: 10}},
        h('div', null,
          cardView(reviewCard, 'Card of the bot '+titled(review.name), 'Drawing the card…'),
          h('dl', {className: 'bd-facts'},
            author && h('dt', null, 'Shared by'), author && h('dd', null, h('span', {className: 'bd-chip'}, author)),
            h('dt', null, 'Needs'), h('dd', null, review.env_requires.length ? review.env_requires.map(e => h('span', {key: e.name, className: 'bd-chip', title: e.description}, e.name+(e.required ? '' : ' (optional)'))) : h('span', {className: 'bd-chip'}, 'Your own model access')),
            review.skills.length > 0 && h('dt', null, 'Skills'), review.skills.length > 0 && h('dd', null, review.skills.map(s => h('span', {key: s.name, className: 'bd-chip', title: s.description || ''}, s.name)))),
          notes(review.warnings, n => n === 1 ? '1 thing was left out for safety' : n+' things were left out for safety'),
          more('Read its personality and skills',
            instructions ? instructions.map(f => h('details', {key: f.path}, h('summary', null, f.path), h('pre', null, f.text)))
              : button('Show the files', () => work('Loading…', async () => {const data = await bridge.api('/reviews/'+review.id+'/instructions'); if (mounted.current) setInstructions(data.files);}), !!busy, 'ghost')),
          more('More details',
            h('p', null, review.trust_notice),
            review.cron.map((j, i) => h('p', {key: i}, 'Paused task: '+j.name+' · '+j.schedule)),
            h('p', null, 'Version '+review.version+' · Hermes '+review.hermes_requires),
            h('p', null, 'Source: '+review.source), h('code', null, review.commit),
            h('p', null, 'This exact checked version is what gets adopted. Later changes by the creator are not pulled in.'))),
        h('div', {className: 'bd-side'}, adoptPanel)));

    // Share: the card builds itself while the form is filled in.
    const drops = gh?.drops || [];
    const repoValid = SLUG.test(repoName);
    const resetShare = () => {setExported(null); setPublished(null); setAccepted(false);};
    const manualSteps = h('ol', null, h('li', null, 'Save the package and unzip it.'), h('li', null, 'Upload all files to a new public GitHub repository.'), h('li', null, 'Post the card with the repository link.'));
    const saveButtons = exported && h('div', {className: 'bd-actions'}, button('Save card', () => work('Saving…', () => bridge.download(exported, 'card')), !!busy, 'ghost'), button('Save package', () => work('Saving…', () => bridge.download(exported, 'zip')), !!busy, 'ghost'));
    const pickBot = h('label', {className: 'bd-field'}, h('span', null, 'Which bot?'), h('select', {value: profile, onChange: e => chooseProfile(e.target.value), disabled: !!busy}, h('option', {value: ''}, 'Choose a bot…'), ...(boot?.profiles || []).map(p => h('option', {key: p, value: p}, p)), h('option', {value: 'default'}, 'default (your main profile)')));
    const say = profile && h('label', {className: 'bd-field'}, h('span', null, 'What does it do? ', h('small', null, (TAGLINE - tagline.length)+' left')),
      h('input', {value: tagline, maxLength: TAGLINE, placeholder: 'One line for the card', onChange: e => {setTagline(e.target.value); setTouched(true); setAccepted(false);}, disabled: !!busy, autoComplete: 'off'}));
    const contents = h('div', {className: 'bd-lists'},
      h('div', null, h('b', null, 'Shared'), h('ul', null, h('li', null, 'Personality'), h('li', null, 'Your own skills'))),
      h('div', null, h('b', null, 'Never shared'), h('ul', null, h('li', null, 'Keys and logins'), h('li', null, 'Memory and chats'), h('li', null, 'Plugins and connections'))));
    const seg = (label, value) => h('button', {type: 'button', role: 'radio', 'aria-checked': target === value, disabled: !!busy, onClick: () => {setTarget(value); setAccepted(false); if (value === 'update' && !existing) setExisting(drops[0].owner+'/'+drops[0].repo);}}, label);
    const destination = gh?.available && h('div', null,
      drops.length > 0 && h('div', {className: 'bd-seg', role: 'radiogroup', 'aria-label': 'Where to publish'}, seg('New drop', 'new'), seg('Update a drop', 'update')),
      target === 'update' && drops.length > 0
        ? h('label', {className: 'bd-field'}, h('span', null, 'Drop to update'), h('select', {value: existing, onChange: e => {setExisting(e.target.value); setAccepted(false);}, disabled: !!busy}, drops.map(d => h('option', {key: d.owner+'/'+d.repo, value: d.owner+'/'+d.repo}, d.owner+'/'+d.repo))))
        : h('div', {className: 'bd-pair'},
            gh.owners.length > 1 && h('label', {className: 'bd-field'}, h('span', null, 'GitHub account'), h('select', {value: owner, onChange: e => {setOwner(e.target.value); setAccepted(false);}, disabled: !!busy}, gh.owners.map(o => h('option', {key: o, value: o}, o)))),
            h('label', {className: 'bd-field'}, h('span', null, 'Link name'), h('input', {value: repoName, onChange: e => {setRepoName(e.target.value.toLowerCase()); setAccepted(false);}, maxLength: 63, disabled: !!busy, autoComplete: 'off'}))),
      target !== 'update' && repoName && !repoValid && h('p', {className: 'bd-hint', style: {marginTop: 0}}, 'Use lowercase letters, numbers and hyphens.'),
      target !== 'update' && repoValid && owner && h('p', {className: 'bd-url'}, 'Your link: '+owner.toLowerCase()+'.github.io/'+repoName));
    const creditToggle = h('label', {className: 'bd-check'}, h('input', {type: 'checkbox', checked: credit, onChange: e => setCredit(e.target.checked), disabled: !!busy}), h('span', null, 'Show “by BrainArts” on the card and page'));
    const canShare = profile && (target === 'update' ? !!existing : repoValid && owner);
    const shareCard = cards.share && cards.share.profile === profile ? cards.share.src : '';
    const livePreview = h('div', {className: 'bd-side'}, cardView(shareCard, 'Card of your bot', profile ? 'Drawing your card…' : 'Choose a bot to see its card', 'This card shows up wherever you post the link.'), contents);
    const link = published && (published.share_url || published.pages_url || published.repo_url);
    const share = published ? h('section', {className: 'bd-live'},
      h('h2', {className: 'bd-h2'}, published.mode === 'update' ? (published.changed ? 'Your drop is updated' : 'Already up to date') : 'Your bot is live'),
      h('p', {className: 'bd-lead', style: {margin: '0 auto'}}, 'Post the link anywhere. The card comes along on its own.'),
      cardView(shareCard, 'Card of your bot', ''),
      h('div', {className: 'bd-copy'}, h('input', {readOnly: true, value: link, 'aria-label': 'Your link', onFocus: e => e.target.select()}), button(copied === 'link' ? 'Copied' : 'Copy link', () => copyText(link, 'link'), false)),
      h('div', {className: 'bd-sharegrid'}, shareTargets(published).map(t => h('a', {key: t.label, className: 'bd-btn ghost', href: t.href, target: '_blank', rel: 'noopener noreferrer'}, t.label))),
      more('Instagram', h('p', null, 'Instagram has no share link. Save the story image, post it as a story and add a link sticker with your link.'),
        button('Save story image', () => work('Saving…', () => bridge.download(exported, 'story')), !!busy, 'ghost')),
      more('Post text and files', h('textarea', {className: 'bd-post', readOnly: true, rows: 3, value: published.post_text, 'aria-label': 'Post text', onFocus: e => e.target.select()}),
        h('div', {className: 'bd-actions'}, button(copied === 'post' ? 'Copied' : 'Copy post text', () => copyText(published.post_text, 'post'), false, 'ghost'), button('Save card', () => work('Saving…', () => bridge.download(exported, 'card')), !!busy, 'ghost')),
        h('p', null, 'Page: '+(published.pages_url || '—')), h('p', null, 'Repository: '+published.repo_url),
        published.pages_url ? h('p', null, 'A new page can take a minute to appear.') : h('p', null, 'GitHub Pages could not be turned on. The repository link works as is.')),
      button('Share another bot', resetShare, !!busy, 'text'))
    : exported && !gh?.available ? h('section', {className: 'bd-two share'},
        h('div', {className: 'bd-panel'},
          h('h2', {className: 'bd-h2'}, 'Upload it yourself'),
          manualSteps, saveButtons,
          more('What is in the package', h('code', null, exported.directory), h('ul', null, exported.files.map(f => h('li', {key: f}, f))),
            h('p', null, 'Only these files. A key scan cannot catch every secret, so take a quick look first.')),
          notes(exported.warnings, n => n === 1 ? '1 thing was left out' : n+' things were left out'),
          button('← Back', resetShare, !!busy, 'text')),
        livePreview)
    : h('section', {className: 'bd-two share'},
        h('div', null,
          h('h2', {className: 'bd-h2'}, 'Share your bot'),
          h('p', {className: 'bd-lead', style: {marginBottom: 22}}, 'One link and one card. Anyone with Hermes can adopt their own copy.'),
          pickBot, say, h('div', {className: 'bd-form-lists'}, contents),
          !gh || gh.loading ? h('p', {className: 'bd-status'}, h('span', {className: 'bd-spin'}), 'Checking GitHub…')
          : gh.available ? h('div', null,
              destination, creditToggle,
              checkbox(target === 'update' ? 'Replace the public drop with this version' : 'Publish this bot publicly on GitHub'),
              button(target === 'update' ? 'Update drop' : 'Share bot', shareNow, !!busy || !accepted || !canShare),
              exported && notes(exported.warnings, n => n === 1 ? '1 thing was left out' : n+' things were left out'),
              more('Prefer to do it yourself?', manualSteps, exported ? saveButtons : h('p', null, 'Share once to get the package files.')))
          : h('div', null,
              h('p', {className: 'bd-muted'}, (gh.reason || 'GitHub is not available.')+' You can still prepare the files and upload them yourself.'),
              creditToggle, checkbox('I looked at what is shared'),
              button('Prepare files', publish, !!busy || !profile || !accepted || !boot))),
        livePreview);

    return h('main', {className: 'bot-drops'}, h('style', null, DROPS_CSS), h('div', {className: 'bd-wrap'},
      h('header', {className: 'bd-top'},
        h('span', {className: 'bd-mark'}, 'BOT DROPS', h('b', null, 'FOR HERMES')),
        h('div', {className: 'bd-top-right'},
          h('div', {role: 'status', 'aria-live': 'polite', className: 'bd-status'}, busy && h('span', {className: 'bd-spin'}), busy),
          h('nav', {'aria-label': 'Bot Drops', className: 'bd-tabs', role: 'tablist'},
            h('button', {type: 'button', role: 'tab', 'aria-selected': tab === 'adopt', onClick: switchTab('adopt'), disabled: !!busy}, 'Adopt'),
            h('button', {type: 'button', role: 'tab', 'aria-selected': tab === 'share', onClick: switchTab('share'), disabled: !!busy}, 'Share')))),
      error && h('div', {role: 'alert', className: 'bd-error'}, h('strong', null, 'That did not work'), h('p', null, error), button('Try again', () => work('Reloading…', refresh), !!busy, 'ghost')),
      !boot && !busy && !error && h('p', {className: 'bd-muted'}, 'Bot Drops is not enabled for this Hermes profile yet.'),
      tab === 'adopt' ? (review ? card : start) : share,
      h('footer', {className: 'bd-foot'},
        h('span', null, 'Nothing is posted or installed without your click'),
        h('span', null, boot ? 'Profile: '+boot.home_name+' · ' : '', 'by ', h('a', {href: 'https://x.com/chrisbrainarts', target: '_blank', rel: 'noopener noreferrer'}, 'BrainArts')))
    ));
  };
}
