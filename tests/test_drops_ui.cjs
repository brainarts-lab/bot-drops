const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('ui/bot.js','utf8');
const finish=vm.runInNewContext(source+';finishBot');
const route={profile:'drops-dev',targetProfile:'drops-dev',connectionId:'local',mode:'local'};
const info={status:'installed',installed_profile:'new-bot'};

test('adopts canonical Bot Chat without duplicate or inference',async()=>{
  const calls=[];
  const host={requestProfile:async(r,m,p)=>{calls.push(m);return m==='profiles.configure'?{applied:{ui_meta:true}}:{sessions:[{id:'stored',title:'Bot Chat'}]};},openSession:async(id)=>assert.equal(id,'stored')};
  await finish(host,route,info,()=>{});
  assert.deepEqual(calls,['profiles.configure','session.list']);
});
test('creates and titles new Bot Chat without sending a message',async()=>{
  const calls=[];
  const host={requestProfile:async(r,m,p)=>{calls.push(m);return m==='profiles.configure'?{applied:{ui_meta:true}}:m==='session.list'?{sessions:[]}:m==='session.create'?{session_id:'runtime',stored_session_id:'stored'}:{};},openSession:async()=>{calls.push('open');}};
  await finish(host,route,info,()=>{});
  assert.deepEqual(calls,['profiles.configure','session.list','session.create','session.title','open']);
});
test('failed lookup never mints a replacement chat',async()=>{
  const calls=[];
  const host={requestProfile:async(r,m)=>{calls.push(m);if(m==='profiles.configure')return {applied:{ui_meta:true}};throw new Error('lookup failed');}};
  await assert.rejects(finish(host,route,info,()=>{}));
  assert.deepEqual(calls,['profiles.configure','session.list']);
});
test('source switch prevents next mutation',async()=>{
  let current=true;const calls=[];
  const host={requestProfile:async(r,m)=>{calls.push(m);current=false;return {applied:{ui_meta:true}};}};
  await assert.rejects(finish(host,route,info,()=>{if(!current)throw new Error('Source changed');}));
  assert.deepEqual(calls,['profiles.configure']);
});
