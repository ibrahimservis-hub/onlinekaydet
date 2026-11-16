import {geoOrthographic,geoPath,geoGraticule10} from 'd3-geo';
import LAND from './land.json';
(function(){var c=document.getElementById('dunya');if(!c)return;var X=c.getContext('2d');
var az=matchMedia('(prefers-reduced-motion:reduce)').matches,ACC='#E8866A';
var CITY=[[29,41],[32.9,39.9],[27,38.4],[13.4,52.5],[-0.1,51.5],[2.3,48.9],[-3.7,40.4],[37.6,55.7],[55.3,25.2],[31.2,30],[3.4,6.5],[72.8,19],[139.7,35.7],[151.2,-33.9],[-74,40.7],[-79.4,43.7],[-46.6,-23.5],[-118.2,34],[116.4,39.9],[100.5,13.7],[18.4,-33.9],[-99.1,19.4],[126.9,37.6],[106.8,-6.2]];
var W,H,R,cx,cy,dpr,mob,run=false,rot=35,sp=1,last=0,th=[],bd=[],rowE=[],nextB=0,arr=[0,0,0,0],rowT=[-9e3,-9e3,-9e3,-9e3],hov=false;
var proj=geoOrthographic().clipAngle(90).precision(.4),path=geoPath(proj,X),grat=geoGraticule10(),TILT=-18;
function vis(lo,la){var l=(lo-rot)*Math.PI/180,p=la*Math.PI/180,t=-TILT*Math.PI/180;return Math.sin(p)*Math.sin(t)+Math.cos(p)*Math.cos(l)*Math.cos(t)}
function size(){dpr=Math.min(devicePixelRatio||1,2);var r=c.getBoundingClientRect();W=r.width;H=r.height;c.width=W*dpr;c.height=H*dpr;X.setTransform(dpr,0,0,dpr,0,0);mob=W<700;
 R=mob?Math.min(W*.34,132):Math.min(H*.43,236);cx=mob?W/2:R+40;cy=mob?R+16:H/2;proj.scale(R).translate([cx,cy]);
 var k=document.getElementById('dunyakart');rowE=[];if(k){var cr=c.getBoundingClientRect(),kr=k.getBoundingClientRect(),L=k.querySelectorAll('li');
  for(var i=0;i<4&&i<L.length;i++){var lr=L[i].getBoundingClientRect();rowE.push(mob?[kr.left-cr.left+kr.width*(i+1)/5,kr.top-cr.top+2]:[kr.left-cr.left+6,lr.top-cr.top+lr.height/2])}}
 if(!th.length)th=CITY.map(function(ct,i){return {c:ct,a:0,row:i%4,p:[0,0],z:0}})}
function ease(t){return t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2}
function bz(a,b,c2,d,t){var u=1-t;return [u*u*u*a[0]+3*u*u*t*b[0]+3*u*t*t*c2[0]+t*t*t*d[0],u*u*u*a[1]+3*u*u*t*b[1]+3*u*t*t*c2[1]+t*t*t*d[1]]}
function ctl(p,E){var dx=p[0]-cx,dy=p[1]-cy,d=Math.sqrt(dx*dx+dy*dy)||1,o=mob?40:R*.75;var c1=[p[0]+dx/d*o,p[1]+dy/d*o-(mob?0:R*.25)],c2=mob?[E[0],E[1]-80]:[E[0]-130,E[1]];return [c1,c2]}
function draw(now,dt){X.clearRect(0,0,W,H);proj.rotate([-rot,TILT,0]);
 X.fillStyle='rgba(43,51,64,.06)';X.beginPath();X.ellipse(cx,cy+R+14,R*.7,9,0,0,6.2832);X.fill();
 // okyanus
 var g=X.createRadialGradient(cx-R*.35,cy-R*.4,R*.05,cx,cy,R);g.addColorStop(0,'#ffffff');g.addColorStop(1,'#dfe9f3');X.fillStyle=g;X.beginPath();X.arc(cx,cy,R,0,6.2832);X.fill();
 X.beginPath();path(grat);X.strokeStyle='rgba(43,51,64,.07)';X.lineWidth=.7;X.stroke();
 // kara
 X.beginPath();path(LAND);X.fillStyle='#b9c3cf';X.fill();X.strokeStyle='#8f9bab';X.lineWidth=.8;X.lineJoin='round';X.stroke();
 // küre kenarı ve hacim
 var s=X.createRadialGradient(cx-R*.3,cy-R*.35,R*.5,cx,cy,R);s.addColorStop(0,'rgba(43,51,64,0)');s.addColorStop(1,'rgba(43,51,64,.13)');X.fillStyle=s;X.beginPath();X.arc(cx,cy,R,0,6.2832);X.fill();
 X.strokeStyle='rgba(43,51,64,.28)';X.lineWidth=1.2;X.beginPath();X.arc(cx,cy,R,0,6.2832);X.stroke();
 X.lineCap='round';
 for(var j=0;j<th.length;j++){var t=th[j],z=vis(t.c[0],t.c[1]),E=rowE[t.row];t.z=z;if(z>0)t.p=proj(t.c)||t.p;var v=z>.15;t.a+=((v?1:0)-t.a)*Math.min(dt/180,1);if(!E)continue;
  if(z>.02){X.fillStyle='#2b3340';X.beginPath();X.arc(t.p[0],t.p[1],2.6,0,6.2832);X.fill();X.strokeStyle='#fff';X.lineWidth=1;X.stroke()}
  if(t.a<.02)continue;var cs=ctl(t.p,E);X.strokeStyle='rgba(43,51,64,'+(.2*t.a).toFixed(2)+')';X.lineWidth=1;X.beginPath();X.moveTo(t.p[0],t.p[1]);X.bezierCurveTo(cs[0][0],cs[0][1],cs[1][0],cs[1][1],E[0],E[1]);X.stroke()}
 if(!az&&now>=nextB&&bd.length<(mob?6:14)){var vs=th.filter(function(t){return t.z>.15&&t.a>.5});if(vs.length){var t2=vs[Math.floor(Math.random()*vs.length)];bd.push({t:t2,s:now,d:2200+Math.random()*900,P0:t2.p.slice()})}nextB=now+(mob?420:240)+Math.random()*160}
 for(var b=bd.length-1;b>=0;b--){var d=bd[b],E2=rowE[d.t.row];if(!E2){bd.splice(b,1);continue}var u=Math.min((now-d.s)/d.d,1);if(d.t.z>0)d.P0=d.t.p.slice();
  var cs2=ctl(d.P0,E2),e=ease(u),tail=.16;
  for(var q=0;q<10;q++){var a0=Math.max(e-tail*(1-q/10),0),a1=Math.max(e-tail*(1-(q+1)/10),0),pa=bz(d.P0,cs2[0],cs2[1],E2,a0),pb=bz(d.P0,cs2[0],cs2[1],E2,a1);X.strokeStyle='rgba(232,134,106,'+(.7*q/10).toFixed(2)+')';X.lineWidth=2.2;X.beginPath();X.moveTo(pa[0],pa[1]);X.lineTo(pb[0],pb[1]);X.stroke()}
  var h=bz(d.P0,cs2[0],cs2[1],E2,e),h2=bz(d.P0,cs2[0],cs2[1],E2,Math.max(e-.02,0)),ang=Math.atan2(h[1]-h2[1],h[0]-h2[0]),k2=u>.95?Math.max((1-u)/.05,0):1;
  X.fillStyle=ACC;X.save();X.translate(h[0],h[1]);X.rotate(ang);X.scale(k2,k2);X.beginPath();X.moveTo(8,0);X.lineTo(-4,-5);X.lineTo(-1.5,0);X.lineTo(-4,5);X.closePath();X.fill();X.restore();
  if(u>=1){arr[d.t.row]=now;var L=document.querySelectorAll('#dunyakart li')[d.t.row];if(L&&now-rowT[d.t.row]>500){rowT[d.t.row]=now;L.classList.add('yn');(function(l){setTimeout(function(){l.classList.remove('yn')},820)})(L)}bd.splice(b,1)}}
 for(var r2=0;r2<rowE.length;r2++){var E3=rowE[r2],age=now-arr[r2],sc=age<420?1+.6*Math.sin(Math.min(age/420,1)*Math.PI):1;X.fillStyle=ACC;X.beginPath();X.arc(E3[0],E3[1],3*sc,0,6.2832);X.fill()}}
function frame(now){var dt=Math.min(now-last,50);last=now;sp+=((hov?.35:1)-sp)*Math.min(dt/700,1);rot+=dt/1000*7*sp;draw(now,dt);if(run)requestAnimationFrame(frame)}
size();addEventListener('resize',function(){size();if(az)stat()});
function stat(){var now=performance.now();th.forEach(function(t){t.z=vis(t.c[0],t.c[1]);t.a=t.z>.15?1:0});proj.rotate([-rot,TILT,0]);th.forEach(function(t){if(t.z>0)t.p=proj(t.c)});bd=[];th.filter(function(t){return t.a}).slice(0,6).forEach(function(t,i){bd.push({t:t,s:now-(.3+i*.1)*2600,d:2600,P0:t.p.slice()})});draw(now,1000)}
var sh=c.parentNode;sh.addEventListener('mouseenter',function(){hov=true});sh.addEventListener('mouseleave',function(){hov=false});
if(az)stat();else new IntersectionObserver(function(es){var v=es[0].isIntersecting;if(v&&!run){run=true;last=performance.now();requestAnimationFrame(frame)}else if(!v)run=false}).observe(c);
})();
