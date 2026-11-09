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
