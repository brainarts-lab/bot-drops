"""Build the two zero-dependency host adapters from one reviewed UI source."""
from pathlib import Path
import json

root=Path(__file__).resolve().parents[1]
shared='const DROPS_CSS = '+json.dumps((root/'ui/style.css').read_text())+';\n'+(root/'ui/app.js').read_text()
dashboard=r'''
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
'''
desktop=r'''
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
'''
(root/'dashboard/dist').mkdir(parents=True,exist_ok=True)
(root/'desktop').mkdir(exist_ok=True)
(root/'dashboard/dist/index.js').write_text(shared+dashboard)
(root/'desktop/plugin.js').write_text("import React from 'react';\nimport {host,useValue,ROUTES_AREA,SIDEBAR_NAV_AREA,gatewayActivationEpoch,captureGatewayFileDownload} from '@hermes/plugin-sdk';\n"+shared+'\n'+(root/'ui/bot.js').read_text()+'\n'+desktop)
