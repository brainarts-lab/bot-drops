import React from 'react';
import {host,useValue,ROUTES_AREA,SIDEBAR_NAV_AREA,gatewayActivationEpoch,captureGatewayFileDownload} from '@hermes/plugin-sdk';
const DROPS_CSS = "/* Bot Drops shares one look with its cards and bot pages: deep green, lime, the Hermes typefaces.\n   The bot card is the one loud element; everything around it stays quiet. */\n.bot-drops{\n  --bg:#0c2420;--panel:#11302a;--field:#0a1e1a;--ink:#eef3e6;--muted:#9fb5ab;--line:#24423a;--lime:#c6f36a;--amber:#f2cf7a;--red:#ffab99;\n  --title:'Collapse',ui-serif,Georgia,'Times New Roman',serif;\n  --mark:'Rules Expanded',ui-sans-serif,system-ui,sans-serif;\n  --mono:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;\n  box-sizing:border-box;background:var(--bg);color:var(--ink);min-height:100%;overflow:auto;\n  font:15px/1.55 ui-sans-serif,system-ui,-apple-system,'Segoe UI',sans-serif;padding:26px clamp(16px,4vw,56px) 34px;\n}\n.bot-drops *{box-sizing:border-box}\n.bot-drops button,.bot-drops input,.bot-drops select,.bot-drops textarea{font:inherit}\n.bot-drops :focus-visible{outline:2px solid var(--lime);outline-offset:3px;border-radius:6px}\n.bot-drops p{margin:0 0 12px}\n.bot-drops a{color:var(--ink);text-underline-offset:3px}\n.bd-wrap{max-width:1060px;margin:0 auto}\n\n/* Header */\n.bd-top{display:flex;align-items:center;justify-content:space-between;gap:12px 20px;flex-wrap:wrap;margin-bottom:clamp(22px,3.6vw,38px)}\n.bd-mark{font:700 13px/1 var(--mark);letter-spacing:.06em;white-space:nowrap}\n.bd-mark b{color:var(--lime);font-weight:700;margin-left:.6em}\n.bd-top-right{display:flex;align-items:center;gap:14px;flex-wrap:wrap}\n.bd-tabs{display:inline-flex;border:1px solid var(--line);border-radius:999px;padding:4px;gap:2px}\n.bd-tabs button{border:0;background:none;border-radius:999px;min-height:38px;padding:0 20px;font-weight:600;color:var(--muted);cursor:pointer}\n.bd-tabs button[aria-selected=\"true\"]{background:var(--lime);color:var(--bg)}\n.bd-tabs button:disabled{cursor:default}\n.bd-status{display:inline-flex;align-items:center;gap:9px;font-size:13px;color:var(--muted)}\n.bd-spin{width:14px;height:14px;border:2px solid var(--line);border-top-color:var(--lime);border-radius:50%;animation:bd-spin .9s linear infinite}\n\n/* Type */\n.bd-h1{font:700 clamp(42px,4.9vw,62px)/.98 var(--title);letter-spacing:-.01em;margin:0 0 20px}\n.bd-h1 span{display:block;color:var(--lime)}\n.bd-h2{font:700 clamp(32px,4.2vw,48px)/1.02 var(--title);margin:0 0 10px;overflow-wrap:anywhere}\n.bd-lead{color:var(--muted);font-size:17px;max-width:46ch}\n.bd-muted{color:var(--muted);font-size:13px}\n.bd-by{font:700 12px/1.5 var(--mono);letter-spacing:.06em;color:var(--muted);text-transform:uppercase;margin:0 0 14px}\n\n/* Buttons and fields */\n.bd-btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:48px;padding:0 22px;border-radius:12px;border:1px solid var(--lime);background:var(--lime);color:var(--bg);font-weight:650;cursor:pointer;text-decoration:none;text-align:center;transition:filter .15s}\n.bot-drops a.bd-btn{color:var(--bg)}\n.bd-btn:hover:not(:disabled){filter:brightness(1.08)}\n.bd-btn:disabled{opacity:.38;cursor:not-allowed}\n.bd-btn.ghost,.bot-drops a.bd-btn.ghost{background:transparent;color:var(--ink);border-color:var(--line)}\n.bd-btn.ghost:hover:not(:disabled){border-color:var(--muted);filter:none}\n.bd-btn.text{background:none;border-color:transparent;color:var(--muted);padding:0 6px;min-height:40px;font-weight:500}\n.bd-btn.text:hover:not(:disabled){color:var(--ink);filter:none}\n.bd-btn.wide{width:100%}\n.bd-linkbtn{background:none;border:0;padding:0;color:var(--lime);font-weight:600;cursor:pointer;text-decoration:underline;text-underline-offset:3px}\n.bd-linkbtn:disabled{opacity:.45;cursor:not-allowed}\n.bd-field{display:flex;flex-direction:column;gap:7px;margin:0 0 16px;font-size:13px;font-weight:600}\n.bd-field small{font-weight:400;color:var(--muted)}\n.bd-field input,.bd-field select,.bd-row input,.bd-post{width:100%;min-height:48px;padding:12px 14px;background:var(--field);border:1px solid var(--line);border-radius:12px;color:var(--ink);font-weight:400;font-size:15px}\n.bd-field input::placeholder,.bd-row input::placeholder{color:#6f877c}\n.bd-field select{appearance:none;background-image:linear-gradient(45deg,transparent 50%,var(--muted) 50%),linear-gradient(135deg,var(--muted) 50%,transparent 50%);background-position:calc(100% - 20px) 21px,calc(100% - 14px) 21px;background-size:6px 6px;background-repeat:no-repeat;padding-right:40px}\n.bd-row{display:flex;gap:10px;margin:22px 0 12px;max-width:560px}\n.bd-row input{flex:1;min-width:0}\n.bd-check{display:flex;align-items:flex-start;gap:11px;font-size:14px;margin:16px 0;cursor:pointer}\n.bd-check input{width:19px;height:19px;flex-shrink:0;margin-top:1px;accent-color:var(--lime)}\n.bd-hint{font-size:13px;color:var(--amber);margin:-8px 0 12px}\n.bd-seg{display:inline-flex;border:1px solid var(--line);border-radius:12px;padding:3px;margin:0 0 14px}\n.bd-seg button{border:0;background:none;border-radius:9px;min-height:38px;padding:0 16px;color:var(--muted);font-weight:600;cursor:pointer}\n.bd-seg button[aria-checked=\"true\"]{background:var(--panel);color:var(--ink);box-shadow:inset 0 0 0 1px var(--line)}\n\n/* The card */\n.bd-card{margin:0;position:relative}\n.bd-card img,.bd-card-wait{display:block;width:100%;height:auto;aspect-ratio:1200/630;border-radius:16px;border:1px solid var(--line);background:var(--panel);box-shadow:0 30px 60px -28px #000c,0 2px 0 #ffffff08 inset}\n.bd-card img{animation:bd-drop .75s cubic-bezier(.2,.9,.25,1) both}\n.bd-card-wait{display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:14px;box-shadow:none;border-style:dashed;padding:20px;text-align:center}\n.bd-card figcaption{font-size:13px;color:var(--muted);margin-top:12px}\n.bd-example{display:block;width:100%;padding:0;border:0;background:none;cursor:pointer;text-align:left;transform:rotate(1.6deg);transition:transform .25s}\n.bd-example:hover:not(:disabled),.bd-example:focus-visible{transform:rotate(0) translateY(-3px)}\n.bd-example:disabled{cursor:default}\n.bd-example figcaption b{color:var(--lime);font-weight:600}\n\n/* Screens */\n.bd-start{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);gap:clamp(28px,5vw,64px);align-items:center}\n.bd-recent{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:26px;font-size:13px;color:var(--muted)}\n.bd-chip{display:inline-flex;align-items:center;font-size:13px;line-height:1.3;padding:5px 12px;border-radius:999px;border:1px solid var(--line);background:none;color:var(--ink);overflow-wrap:anywhere}\nbutton.bd-chip{cursor:pointer}\nbutton.bd-chip:hover:not(:disabled){border-color:var(--muted)}\n.bd-chip.on{border-color:var(--lime);color:var(--lime)}\n.bd-two{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr);gap:clamp(22px,4vw,48px);align-items:start}\n.bd-side{position:sticky;top:8px}\n.bd-panel{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:clamp(18px,2.6vw,28px)}\n.bd-panel h3{font-size:17px;margin:0 0 14px}\n.bd-facts{display:grid;grid-template-columns:auto 1fr;gap:10px 16px;align-items:start;margin:22px 0 6px;font-size:14px}\n.bd-facts dt{color:var(--muted);padding-top:5px}\n.bd-facts dd{margin:0;display:flex;flex-wrap:wrap;gap:7px}\n.bd-lists{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:4px 0 18px;font-size:14px}\n.bd-lists b{font-size:13px}\n.bd-lists ul{margin:6px 0 0;padding:0;list-style:none}\n.bd-lists li{padding-left:18px;position:relative}\n.bd-lists li::before{content:\"\";position:absolute;left:2px;top:9px;width:6px;height:6px;border-radius:50%;background:var(--lime)}\n.bd-lists div:last-child{color:var(--muted)}\n.bd-lists div:last-child li::before{background:none;border:1px solid var(--muted)}\n.bd-side .bd-lists{margin:22px 0 0;padding-top:18px;border-top:1px solid var(--line)}\n.bd-form-lists{display:none}\n.bd-pair{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:0 14px}\n.bd-pair .bd-field{margin-bottom:8px}\n.bd-url{font:12px/1.5 var(--mono);color:var(--muted);margin:0 0 14px;overflow-wrap:anywhere}\n.bd-live{text-align:center;max-width:760px;margin:0 auto}\n.bd-live .bd-card{margin:26px 0 22px}\n.bd-copy{display:flex;gap:10px;margin:0 0 14px}\n.bd-copy input{flex:1;min-width:0;min-height:48px;padding:0 14px;background:var(--field);border:1px solid var(--line);border-radius:12px;font:13px/1 var(--mono);color:var(--ink)}\n.bd-sharegrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin:0 0 8px}\n.bd-actions{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}\n.bd-done{border:1px solid var(--lime);border-radius:16px;padding:20px;margin:0 0 18px;background:#c6f36a12}\n.bd-done h3{font:700 26px/1.1 var(--title);margin:0 0 8px}\n\n/* Details, notes, errors */\n.bot-drops details{border-top:1px solid var(--line);padding:12px 0;text-align:left}\n.bot-drops summary{cursor:pointer;font-size:14px;font-weight:600;color:var(--muted)}\n.bot-drops summary:hover{color:var(--ink)}\n.bot-drops details p,.bot-drops details li{font-size:13px;color:var(--muted);overflow-wrap:anywhere}\n.bot-drops details p{margin:10px 0}\n.bot-drops code,.bot-drops pre{font:12px/1.5 var(--mono);overflow-wrap:anywhere;white-space:pre-wrap;color:var(--ink)}\n.bot-drops pre{padding:12px;background:var(--field);border:1px solid var(--line);border-radius:10px;max-height:340px;overflow:auto}\n.bot-drops details.bd-notes{border:1px solid #f2cf7a55;border-radius:12px;padding:10px 14px;margin:16px 0;background:#f2cf7a0d}\n.bd-notes summary{color:var(--amber)}\n.bd-note{border-top:1px solid #f2cf7a33;padding:10px 0 2px;margin-top:10px}\n.bd-note b{font-size:13px}\n.bd-note small{font-size:12px;color:var(--muted)}\n.bd-error{border:1px solid #ffab9966;background:#ffab9912;border-radius:14px;padding:14px 16px;margin:0 0 22px}\n.bd-error strong{color:var(--red)}\n.bd-error p{margin:6px 0 8px;font-size:14px}\n.bd-post{resize:vertical;min-height:84px;font-size:14px}\n.bd-foot{display:flex;justify-content:space-between;gap:8px 20px;flex-wrap:wrap;font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:18px;margin-top:clamp(36px,6vw,64px)}\n.bot-drops .bd-foot a{color:var(--muted)}\n\n@keyframes bd-spin{to{transform:rotate(360deg)}}\n@keyframes bd-drop{0%{opacity:0;transform:translateY(-36px) rotate(-3.5deg) scale(.96)}55%{opacity:1;transform:translateY(5px) rotate(.7deg) scale(1.004)}100%{opacity:1;transform:none}}\n@media(max-width:820px){\n  .bd-start,.bd-two{grid-template-columns:minmax(0,1fr)}\n  .bd-side{position:static}\n  .bd-two.share .bd-side{order:-1}\n  .bd-side .bd-lists{display:none}\n  .bd-form-lists{display:block}\n  .bd-example{transform:none;max-width:520px}\n}\n@media(max-width:480px){\n  .bd-row,.bd-copy{flex-direction:column}\n  .bd-lists{grid-template-columns:1fr}\n  .bd-top{justify-content:center}\n  .bd-tabs button{padding:0 26px}\n}\n@media(prefers-reduced-motion:reduce){\n  .bd-card img,.bd-spin{animation:none}\n  .bd-example,.bd-btn{transition:none}\n}\n";
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

// Public Hermes Desktop RPCs. The caller owns a captured source and activation guard.
async function finishBot(host, sourceRoute, info, assertScope) {
  const name = info.installed_profile;
  if (!name || info.status !== 'installed') throw new Error('Adopt the agent before setting up Bot Mode.');
  assertScope();
  const call = async (route, method, params) => {
    assertScope();
    const result = await host.requestProfile(route, method, params, undefined, {spawnPriority: 'foreground'});
    assertScope();
    return result;
  };
  const configured = await call(sourceRoute, 'profiles.configure', {
    name, ui_meta: {'hermes-bots': {title: name.replaceAll('-', ' '), created: Date.now()}}
  });
  if (!configured?.applied?.ui_meta) throw new Error('Agent installed; Bot Mode presentation could not be saved. You can retry.');
  const route = {...sourceRoute, profile: name, targetProfile: name};
  const existing = await call(route, 'session.list', {profile: name, title: 'Bot Chat', include_hidden: true, limit: 200});
  if (!Array.isArray(existing?.sessions)) throw new Error('Could not check the existing Bot Chat. No new chat was created.');
  const found = existing.sessions.find(s => s.title === 'Bot Chat');
  let stored = found?.resolved_id || found?.id;
  if (!stored) {
    const created = await call(route, 'session.create', {profile: name, title: 'Bot Chat', hidden: true, follow_profile_config: true});
    if (!created?.session_id || !created?.stored_session_id) throw new Error('The Bot Chat was not created. Open Bot Mode to continue.');
    await call(route, 'session.title', {session_id: created.session_id, title: 'Bot Chat'});
    stored = created.stored_session_id;
  }
  assertScope();
  await host.openSession(stored, {profile: name, route, intent: 'in-place'});
  // No kickoff prompt: the first paid model run is always the user's own message.
  return {profile: name, session: stored};
}


export default {
  id:'bot-drops',name:'Bot Drops',defaultEnabled:false,
  register(ctx) {
    function Page() {
      const profile=useValue(host.state.profile);
      const connection=useValue(host.state.connectionId);
      const epoch=gatewayActivationEpoch();
      // host.profileRoutes() is async: resolve the active local route before mounting the app.
      const [source,setSource]=React.useState(undefined);
      React.useEffect(()=>{
        let live=true;setSource(undefined);
        Promise.resolve().then(()=>host.profileRoutes()).then(routes=>{
          if (live) setSource((Array.isArray(routes)?routes:[]).find(r=>r.profile===profile && r.connectionId===connection)||null);
        }).catch(()=>{if (live) setSource(null);});
        return ()=>{live=false;};
      },[profile,connection,epoch]);
      const Component=React.useMemo(()=>{
        if (source===undefined) return null;
        const assertScope=()=>{
          if (gatewayActivationEpoch()!==epoch) throw new Error('The active Hermes source changed. Reload Bot Drops before continuing.');
          if (!source || source.mode!=='local') throw new Error('This release supports local Hermes bots. Select a local profile with Bot Drops enabled.');
        };
        const bridge={
          api:async(path,body)=>{
            assertScope();
            const download=captureGatewayFileDownload();
            const result=await ctx.rest(path,body===undefined?{}:{method:'POST',body,timeoutMs:120000});
            assertScope();
            if (result?.archive) result.saveFile=download;
            return result;
          },
          finishBot:info=>finishBot(host,source,info,assertScope),
          download:async(result,kind)=>{
            if (!result.saveFile) throw new Error('Prepare the export again before downloading.');
            await result.saveFile(kind==='zip'?result.archive:result.directory+'/drop-'+kind+'.png',kind==='zip'?'bot-drop.zip':'drop-'+kind+'.png');
          },
          error:e=>{
            const message=String(e.message||e);
            try{return JSON.parse(message.slice(message.indexOf('{'))).detail||'Operation failed.';}catch{return message.slice(0,500);}
          }
        };
        return createDropsApp(React,bridge);
      },[source,epoch]);
      if (!Component) return React.createElement('div',{style:{padding:32,opacity:.7}},'Connecting to Hermes…');
      return React.createElement(Component,{key:profile+':'+connection+':'+epoch});
    }
    ctx.registerMany([
      {id:'page',area:ROUTES_AREA,data:{path:'/drops/import'},render:()=>React.createElement(Page)},
      {id:'nav',area:SIDEBAR_NAV_AREA,data:{path:'/drops/import',label:'Bot Drops',codicon:'package'}}
    ]);
  }
};
