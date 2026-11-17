/* Ziyaret istatistiği: kişisel veri tutmaz. Rastgele oturum kimliği, sayfa, kaynak, cihaz. Tarayıcı "İzleme" kapalıysa çalışmaz. */
(function(){
if(navigator.doNotTrack==='1'||window.__okizle)return;window.__okizle=1;
var API=(window.OK_API||'')+'/api/public/track',sid='';
try{sid=localStorage.getItem('ok_sid')||'';if(!sid){sid='s'+Math.random().toString(36).slice(2)+Date.now().toString(36);localStorage.setItem('ok_sid',sid)}}catch(e){sid='s'+Math.random().toString(36).slice(2)+Date.now().toString(36)}
function send(o){o.sid=sid;o.path=location.pathname;o.host=location.hostname;try{fetch(API,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o),keepalive:true}).catch(function(){})}catch(e){}}
send({event:'pageview',title:document.title.slice(0,150),referrer:document.referrer||'',search:location.search||'',screen:screen.width+'x'+screen.height,lang:navigator.language||''});
setInterval(function(){if(!document.hidden)send({event:'ping'})},25000);
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href]');if(!a)return;var h=a.getAttribute('href')||'';if(h.indexOf('tel:')===0)send({event:'event',label:'call_click'});else if(h.indexOf('wa.me')>-1||h.indexOf('whatsapp')>-1)send({event:'event',label:'whatsapp_click'})},true);
window.OKTrack={event:function(l){send({event:'event',label:l})}};
})();
