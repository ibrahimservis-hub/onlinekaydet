(function(){
var L='<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
X='<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>',
AR='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg>',
SUB={'Ürün':'Platform ve özellikler','Sektörler':'Kombi, klima, beyaz eşya…','Web Sitesi':'Hazır tema, kendi alan adınız','Usta Uygulaması':'Sahada fotoğraf, imza, SMS','Fiyatlar':'Paketler ve karşılaştırma','SSS':'Sık sorulan sorular'};
var b=document.querySelector('.burger'),nav=document.querySelector('nav.m');if(!b||!nav)return;
b.innerHTML=L;b.setAttribute('aria-expanded','false');
var home=/(^|\/)(index\.html)?$/.test(location.pathname)||/page3\.html$/.test(location.pathname);
var rows='';[].forEach.call(nav.querySelectorAll('a'),function(a,i){
 var h=a.getAttribute('href'),t=a.textContent.trim();
 if(h.charAt(0)=='#'&&!document.querySelector(h))h='index.html'+h;
 rows+='<a href="'+h+'"><b>'+('0'+(i+1)).slice(-2)+'</b><span>'+t+'<small>'+(SUB[t]||'')+'</small></span>'+AR+'</a>';});
var m=document.createElement('div');m.className='mnu';m.id='mobil-menu';
m.innerHTML='<div class="mn-l">'+rows+'</div><div class="mn-f"><a class="mn-g" href="/giris">Giriş yap</a><a class="mn-c" href="#kayit">Ücretsiz Dene</a></div>';
document.body.appendChild(m);
var kayit=document.getElementById('kayit');if(!kayit)m.querySelector('.mn-c').href='index.html#kayit';
var lg=document.querySelector('header .lg2');if(lg)m.querySelector('.mn-g').href=lg.getAttribute('href');
function open(o){if(o){scrollTo(0,0);m.style.top=document.querySelector('header').getBoundingClientRect().bottom+'px'}
 m.classList.toggle('on',o);b.innerHTML=o?X:L;b.setAttribute('aria-expanded',o);b.setAttribute('aria-label',o?'Menüyü kapat':'Menü');document.body.style.overflow=o?'hidden':'';[].forEach.call(document.querySelectorAll('main,footer,.vb'),function(e){if(o)e.setAttribute('inert','');else e.removeAttribute('inert')});if(o){var f=m.querySelector('a');if(f)f.focus()}}
b.addEventListener('click',function(){open(!m.classList.contains('on'))});
m.addEventListener('click',function(e){if(e.target.closest('a'))open(false)});
document.addEventListener('keydown',function(e){if(e.key=='Escape'&&m.classList.contains('on')){open(false);b.focus()}if(e.key=='Tab'&&m.classList.contains('on')){var els=[b].concat([].slice.call(m.querySelectorAll('a'))),i=els.indexOf(document.activeElement);if(e.shiftKey&&i<=0){e.preventDefault();els[els.length-1].focus()}else if(!e.shiftKey&&i==els.length-1){e.preventDefault();els[0].focus()}}});
addEventListener('resize',function(){if(innerWidth>900)open(false)});
})();
