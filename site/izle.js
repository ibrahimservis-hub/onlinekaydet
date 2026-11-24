/* Ziyaret istatistiği: kişisel veri tutmaz. Rastgele oturum kimliği, sayfa, kaynak, cihaz. Tarayıcı "İzleme" kapalıysa çalışmaz. */
(function(){
if(navigator.doNotTrack==='1'||window.__okizle)return;
var izinli=function(){try{var c=JSON.parse(localStorage.getItem('ok_cerez')||'null');return !!(c&&c.olcum)}catch(e){return false}};
if(!izinli()){document.addEventListener('ok-cerez',function h(e){if(e.detail&&e.detail.olcum){document.removeEventListener('ok-cerez',h);var x=document.createElement('script');x.src='/izle.js?k=1';document.head.appendChild(x)}});return}
window.__okizle=1;
var API=(window.OK_API||'')+'/api/public/track',sid='';
try{sid=localStorage.getItem('ok_sid')||'';if(!sid){sid='s'+Math.random().toString(36).slice(2)+Date.now().toString(36);localStorage.setItem('ok_sid',sid)}}catch(e){sid='s'+Math.random().toString(36).slice(2)+Date.now().toString(36)}
function send(o){o.sid=sid;o.path=location.pathname;o.host=location.hostname;try{fetch(API,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o),keepalive:true}).catch(function(){})}catch(e){}}
send({event:'pageview',title:document.title.slice(0,150),referrer:document.referrer||'',search:location.search||'',screen:screen.width+'x'+screen.height,lang:navigator.language||''});
setInterval(function(){if(!document.hidden)send({event:'ping'})},25000);
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href]');if(!a)return;var h=a.getAttribute('href')||'';if(h.indexOf('tel:')===0)send({event:'event',label:'call_click'});else if(h.indexOf('wa.me')>-1||h.indexOf('whatsapp')>-1)send({event:'event',label:'whatsapp_click'})},true);
window.OKTrack={event:function(l){send({event:'event',label:l});if(l==='form_submit'&&window.__okLead)try{window.__okLead()}catch(e){}}};
/* Reklam ve ölçüm etiketleri: yönetim panelindeki Bağlantılar ekranında açılanlar yüklenir. Tarayıcı "İzleme" kapalıysa yüklenmez. */
function js(u,cb){var x=document.createElement('script');x.async=true;x.src=u;if(cb)x.onload=cb;document.head.appendChild(x)}
function etiket(o){
 var L=[];
 if(o.gtm&&o.gtm.id){window.dataLayer=window.dataLayer||[];dataLayer.push({'gtm.start':Date.now(),event:'gtm.js'});js('https://www.googletagmanager.com/gtm.js?id='+encodeURIComponent(o.gtm.id))}
 else if((o.ga4&&o.ga4.id)||(o.google_ads&&o.google_ads.id)){
  var gid=(o.ga4&&o.ga4.id)||o.google_ads.id;window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());
  js('https://www.googletagmanager.com/gtag/js?id='+encodeURIComponent(gid));
  if(o.ga4&&o.ga4.id)gtag('config',o.ga4.id);if(o.google_ads&&o.google_ads.id)gtag('config',o.google_ads.id);
  L.push(function(){if(o.ga4&&o.ga4.id)gtag('event','generate_lead');if(o.google_ads&&o.google_ads.id&&o.google_ads.label)gtag('event','conversion',{send_to:o.google_ads.id+'/'+o.google_ads.label})});
 }
 if(o.meta_pixel&&o.meta_pixel.id){!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init',o.meta_pixel.id);fbq('track','PageView');L.push(function(){fbq('track','Lead')})}
 if(o.tiktok_pixel&&o.tiktok_pixel.id){var tid=o.tiktok_pixel.id;!function(w,d,t){w.TiktokAnalyticsObject=t;var ttq=w[t]=w[t]||[];ttq.methods=['page','track','identify'];ttq.setAndDefer=function(t,e){t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}};for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);ttq.load=function(e){ttq._i=ttq._i||{};ttq._i[e]=[];var n=d.createElement('script');n.async=!0;n.src='https://analytics.tiktok.com/i18n/pixel/events.js?sdkid='+e+'&lib='+t;d.head.appendChild(n)};ttq.load(tid);ttq.page()}(window,document,'ttq');L.push(function(){window.ttq&&ttq.track('SubmitForm')})}
 if(o.clarity&&o.clarity.id){(function(c,l,a,r,i){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};js('https://www.clarity.ms/tag/'+i)})(window,document,'clarity','script',o.clarity.id)}
 if(o.linkedin&&o.linkedin.id){window._linkedin_data_partner_ids=[o.linkedin.id];js('https://snap.licdn.com/li.lms-analytics/insight.min.js')}
 window.__okLead=function(){L.forEach(function(f){try{f()}catch(e){}})};
}
try{fetch((window.OK_API||'')+'/api/public/olcum',{credentials:'omit'}).then(function(r){return r.ok?r.json():{}}).then(etiket).catch(function(){})}catch(e){}
})();
