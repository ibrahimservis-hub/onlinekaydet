(function(){var g=document.querySelector('.tem.tv');if(!g)return;
function fit(){g.querySelectorAll('.ft').forEach(function(f){var i=f.querySelector('iframe');if(i)i.style.transform='scale('+(f.clientWidth/1280)+')'})}
fit();addEventListener('resize',fit);addEventListener('load',fit)})();
