(function(){if(!document.getElementById('fgw'))return;

const NS='http://www.w3.org/2000/svg',ui=document.getElementById('fgui');
const el=(n,a,p)=>{const e=document.createElementNS(NS,n);for(const k in a)e.setAttribute(k,a[k]);(p||ui).appendChild(e);return e};
const RM=matchMedia('(prefers-reduced-motion:reduce)').matches;
// soldaki kutular ve görseldeki kabloları
const CH=[{b:[141,252,355,335],d:'M365 294 H435 L500 352 H640'},{b:[104,353,323,435],d:'M333 394 H425 L477 440 H560'},{b:[82,450,298,532],d:'M308 491 H470'},{b:[70,545,305,627],d:'M316 579 C350 555 390 515 450 488'}];
CH.forEach(c=>{c.hl=el('rect',{class:'hl',x:c.b[0],y:c.b[1],width:c.b[2]-c.b[0],height:c.b[3]-c.b[1],rx:26});c.p=el('path',{d:c.d,fill:'none',stroke:'none'});c.len=c.p.getTotalLength()});
// alt kutular: site özellikleri
const ICON={servis:'<path d="M14.7 6.3a4 4 0 0 0-5.4 5.2L3 17.8 6.2 21l6.3-6.3a4 4 0 0 0 5.2-5.4l-2.6 2.6-2.4-.6-.6-2.4z"/>',
randevu:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4M7.5 14h2M11 14h2M14.5 14h2M7.5 17.5h2M11 17.5h2"/>',
musteri:'<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/><circle cx="17.5" cy="9" r="2.5"/><path d="M17 14c2.8.2 4.5 2 4.5 5"/>',
kasa:'<rect x="3" y="6" width="18" height="13" rx="2.5"/><path d="M3 10h18"/><circle cx="16.5" cy="14.5" r="1.3"/>',
stok:'<path d="M12 3l8.5 4.5v9L12 21l-8.5-4.5v-9z"/><path d="M3.5 7.5L12 12l8.5-4.5M12 12v9"/>',
magaza:'<path d="M4 9l1.5-5h13L20 9M4 9v11h16V9M10 20v-5h4v5"/><path d="M4 9c0 1.7 1.3 3 2.7 3S9.4 10.7 9.4 9c0 1.7 1.3 3 2.7 3s2.7-1.3 2.7-3c0 1.7 1.3 3 2.7 3S20 10.7 20 9"/>',
pazar:'<path d="M9 3v5M15 3v5M7 8h10v3a5 5 0 0 1-10 0zM12 16v5"/>',
rapor:'<path d="M4 20V4M4 20h16M8 16v-5M12 16V8M16 16v-8"/>'};
const F=[['servis','Servis','servis.ac()'],['randevu','Randevu','randevu.ata()'],['musteri','Müşteri','musteri.bul()'],['kasa','Kasa','kasa.kapat()'],['stok','Stok','stok.say()'],['magaza','Mağaza','magaza.ac()'],['pazar','Pazaryeri','pazar.gonder()'],['rapor','Rapor','rapor.al()']];
const TB=[[58,165],[195,302],[331,438],[476,585],[622,730],[765,873],[897,1004],[1038,1152]],SX=[482,522,572,606,640,668,700,732];
const TL=F.map((f,i)=>{const x1=TB[i][0],x2=TB[i][1],cx=(x1+x2)/2;
 const g=el('g',{});const ic=el('g',{class:'ic',transform:`translate(${cx-22} 928) scale(1.85)`},g);ic.innerHTML=ICON[f[0]];
 el('text',{class:'tl',x:cx,y:1012},g).textContent=f[1];
 const hl=el('rect',{class:'hl',x:x1+1,y:911,width:x2-x1-2,height:124,rx:20});
 const p=el('path',{d:`M${SX[i]} 690 C${SX[i]} 800 ${cx} 830 ${cx} 906`,fill:'none',stroke:'none'});
 return {g,ic,hl,p,len:p.getTotalLength(),tok:f[2],cx}});
// tuval
const im=document.getElementById('fgi'),cv=document.getElementById('fgc'),ctx=cv.getContext('2d'),W=1215,H=1075,dpr=Math.min(devicePixelRatio||1,2);
let data,parts=[],tw=[],bursts=[],ptr={x:-999,y:-999};
function fit(){cv.width=cv.clientWidth*dpr;cv.height=cv.clientWidth*H/W*dpr}addEventListener('resize',fit);
document.getElementById('fgw').addEventListener('pointermove',e=>{const r=e.currentTarget.getBoundingClientRect();ptr.x=(e.clientX-r.left)/r.width*W;ptr.y=(e.clientY-r.top)/r.height*H});
document.getElementById('fgw').addEventListener('pointerleave',()=>{ptr.x=ptr.y=-999});
function go(){fit();const o=document.createElement('canvas');o.width=W;o.height=H;const x=o.getContext('2d',{willReadFrequently:true});x.drawImage(im,0,0,W,H);data=x.getImageData(0,0,W,H).data;if(!RM)requestAnimationFrame(tick);else draw0()}
im.complete?go():im.onload=go;
const px=(x,y)=>{const i=((y|0)*W+(x|0))*4;return [data[i],data[i+1],data[i+2]]};
function draw0(){TL.forEach(t=>t.hl.style.opacity=0)}
// sahne: kutu -> kablo -> figür -> komut -> özellik kutusu -> onay
const CYC=5200;let t0=null;
const ease=t=>t<0?0:t>1?1:t*t*(3-2*t);
function comet(path,len,t,col,w){const n=14;for(let k=0;k<n;k++){const tt=t-k*.012;if(tt<0||tt>1)continue;const p=path.getPointAtLength(len*tt);ctx.globalAlpha=(1-k/n)*.9;ctx.fillStyle=col;ctx.beginPath();ctx.arc(p.x,p.y,w*(1-k/n*.6),0,7);ctx.fill()}}
function pill(x,y,txt,a){ctx.globalAlpha=a;ctx.font='600 15px "IBM Plex Mono",ui-monospace,monospace';ctx.textAlign='center';ctx.textBaseline='middle';const w=ctx.measureText(txt).width+24;
 ctx.shadowColor='rgba(11,37,87,.35)';ctx.shadowBlur=10;ctx.fillStyle='#0b2557';ctx.beginPath();ctx.roundRect(x-w/2,y-15,w,30,15);ctx.fill();ctx.shadowBlur=0;ctx.fillStyle='#fff';ctx.fillText(txt,x+4,y+1);ctx.fillStyle='#f07a1a';ctx.beginPath();ctx.arc(x-w/2+11,y,3.2,0,7);ctx.fill()}
function tick(now){if(t0===null)t0=now;const k=cv.width/W;ctx.setTransform(k,0,0,k,0,0);ctx.clearRect(0,0,W,H);
 const n=Math.floor((now-t0)/CYC),s=((now-t0)%CYC)/1000,C=CH[n%4],T=TL[(n*3)%8];
 // 1) kutu parlar, sinyal kablodan figüre akar
 CH.forEach(c=>c.hl.style.opacity=c===C?Math.max(0,Math.min(1,s*4,(1.6-s)*2)):0);
 if(s<1.3)comet(C.p,C.len,ease(s/1.1),'#3b8cff',5.5);
 // 2) figür alır: giriş noktasında halka dalga, baştan aşağı ışık taraması
 if(s>1.0&&s<1.9){const e=C.p.getPointAtLength(C.len),r=(s-1)*90;ctx.globalAlpha=Math.max(0,1-(s-1)/.9)*.8;ctx.strokeStyle='#6fb1ff';ctx.lineWidth=3;ctx.beginPath();ctx.arc(e.x,e.y,r,0,7);ctx.stroke()}
 if(s>1.1&&s<2.3){const y=60+(s-1.1)/1.2*660,g=ctx.createLinearGradient(0,y-40,0,y+40);g.addColorStop(0,'rgba(150,200,255,0)');g.addColorStop(.5,'rgba(190,225,255,.55)');g.addColorStop(1,'rgba(150,200,255,0)');
  ctx.globalAlpha=1;ctx.globalCompositeOperation='screen';ctx.fillStyle=g;ctx.fillRect(560,y-40,440,80);ctx.globalCompositeOperation='source-over'}
 // 3) komut kablodan özellik kutusuna iner
 if(s>2.0&&s<3.6){const t=ease((s-2)/1.5),p=T.p.getPointAtLength(T.len*t);comet(T.p,T.len,t,'#3b8cff',4);pill(p.x,p.y-24,T.tok,Math.min(1,(s-2)*5,(3.6-s)*6))}
 // 4) kutu parlar, ikon zıplar, kare kıvılcımlar; elindeki onay halkası dalgalanır
 TL.forEach(t=>{const on=t===T&&s>3.45;const a=on?Math.max(0,Math.min(1,(s-3.45)*6,(5.1-s)*1.2)):0;t.hl.style.opacity=a;const b=on?Math.sin(Math.min(1,(s-3.45)/.35)*Math.PI)*6:0;t.ic.setAttribute('transform',`translate(${t.cx-22} ${928-b}) scale(1.85)`)});
 if(s>3.45&&s<3.5&&!T.fired){T.fired=n;for(let q=0;q<14;q++)bursts.push({x:T.cx,y:908,vx:(Math.random()-.5)*4,vy:-1-Math.random()*3,l:0,m:40+Math.random()*25,s:3+Math.random()*5})}
 if(T.fired!==undefined&&T.fired!==n)T.fired=undefined;
 if(s>3.6){const r=(s-3.6)*95+96;ctx.globalAlpha=Math.max(0,1-(s-3.6)/1.3)*.7;ctx.strokeStyle='#2d7cf0';ctx.lineWidth=3;ctx.beginPath();ctx.arc(1080,462,r,0,7);ctx.stroke();
  const g2=ctx.createRadialGradient(1080,462,10,1080,462,120);g2.addColorStop(0,'rgba(160,210,255,.55)');g2.addColorStop(1,'rgba(160,210,255,0)');ctx.globalAlpha=Math.max(0,1-(s-3.6)/1.2);ctx.globalCompositeOperation='screen';ctx.fillStyle=g2;ctx.fillRect(950,330,260,260);ctx.globalCompositeOperation='source-over'}
 bursts=bursts.filter(b=>b.l<b.m);for(const b of bursts){b.l++;b.x+=b.vx;b.y+=b.vy;b.vy+=.08;ctx.globalAlpha=1-b.l/b.m;ctx.fillStyle=b.l%10<5?'#2d7cf0':'#0b2557';ctx.fillRect(b.x,b.y,b.s,b.s)}
 // ortam: figürden sola kopan kareler (fareyle itilir), üstünde yanıp sönen pikseller
 for(let q=0;q<3;q++){const x=430+Math.random()*260,y=150+Math.random()*600,[r,g,b]=px(x,y);if(b>r+40&&r+g+b<500)parts.push({x,y,vx:-(.4+Math.random()*1.6),vy:(Math.random()-.6)*.5,l:0,m:130+Math.random()*150,s:5+Math.random()*9,c:`rgb(${r},${g},${b})`})}
 parts=parts.filter(p=>p.l<p.m);for(const p of parts){p.l++;const dx=p.x-ptr.x,dy=p.y-ptr.y,d2=dx*dx+dy*dy;if(d2<9000){const f=(9000-d2)/9000*1.8,d=Math.sqrt(d2)||1;p.x+=dx/d*f;p.y+=dy/d*f}
  p.x+=p.vx;p.y+=p.vy+Math.sin(p.l/30)*.2;ctx.globalAlpha=Math.sin(Math.PI*p.l/p.m)*.9;ctx.fillStyle=p.c;ctx.fillRect(p.x,p.y,p.s,p.s)}
 if(Math.random()<.45){const x=640+Math.random()*330,y=80+Math.random()*620,[r,g,b]=px(x,y);if(b>r+40)tw.push({x:x-x%11,y:y-y%11,l:0})}
 tw=tw.filter(t=>t.l<40);for(const t of tw){t.l++;ctx.globalAlpha=Math.sin(Math.PI*t.l/40)*.85;ctx.fillStyle='#8cc6ff';ctx.fillRect(t.x,t.y,9,9)}
 // onay halkası hafifçe süzülür
 document.getElementById('fgrg').setAttribute('transform',`translate(0 ${Math.sin(now/900)*2})`);
 ctx.globalAlpha=1;requestAnimationFrame(tick)}

})();