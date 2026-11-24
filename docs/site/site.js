const P=D.pages, $=s=>document.querySelector(s);
const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;');
const plain=md=>md.replace(/\`\`\`[\s\S]*?\`\`\`/g,'').replace(/^#.*$/gm,'').replace(/\[([^\]]+)\]\([^)]+\)/g,'$1').replace(/[\`*]/g,'').replace(/\s+/g,' ').trim();
const num=i=>String(i).padStart(2,'0');
function dark(){const t=document.documentElement.dataset.theme;return t?t==='dark':matchMedia('(prefers-color-scheme: dark)').matches}
function tok(n){return getComputedStyle(document.documentElement).getPropertyValue('--'+n).trim()}
function initMermaid(){const v=['paper','panel','ink','mid','line','accent','check','stop','you'].reduce((o,k)=>(o[k]=tok(k),o),{});mermaid.initialize({startOnLoad:false,theme:'base',securityLevel:'strict',fontFamily:tok('mono-name')||'monospace',
 flowchart:{useMaxWidth:false,nodeSpacing:36,rankSpacing:44,curve:'basis'},
 themeVariables:{fontSize:'13px',background:'transparent',primaryColor:v.paper,primaryTextColor:v.ink,primaryBorderColor:v.line,lineColor:v.mid,clusterBkg:'transparent',edgeLabelBackground:v.panel,actorBkg:v.paper,actorBorder:v.mid,actorTextColor:v.ink,actorLineColor:v.line,signalColor:v.mid,signalTextColor:v.ink,labelBoxBkgColor:v.paper,noteBkgColor:v.paper},
 themeCSS:'.you>rect,.you>polygon{stroke:'+v.you+'!important;stroke-width:1.5px!important} .check>rect,.check>polygon{stroke:'+v.check+'!important;stroke-width:1.5px!important} .stop>rect,.stop>polygon{stroke:'+v.stop+'!important;stroke-width:1.5px!important;stroke-dasharray:4 3} .node rect{rx:0;ry:0}'})}
let n=0,cur=0;
async function draw(){for(const el of document.querySelectorAll('pre.m')){const {svg}=await mermaid.render('m'+(n++),el.textContent);const f=document.createElement('figure');f.innerHTML='<div class="d">'+svg+'</div><figcaption><span>FIG. '+num(cur)+'</span><span>CLICK TO ENLARGE</span></figcaption>';f.querySelector('.d').onclick=()=>{$('#zoom').innerHTML=svg;$('#zoom').classList.add('open')};el.replaceWith(f)}}
function show(id){
 const i=Math.max(0,P.findIndex(p=>p.id===id));cur=i;const p=P[i];
 let md=p.md, fig='';
 md=md.replace(/^\`\`\`mermaid\n([\s\S]*?)\`\`\`\s*/,(_,c)=>{fig=c;return ''});
 const body=md.replace(/^# .+\n+/,'');
 const first=(body.match(/^[^#\n].+$/m)||[''])[0];
 const rest=body.replace(first,'');
 const words=plain(p.md).split(' ').length;
 const html=marked.parse(rest.replace(/\]\(([a-z-]+)\.md\)/g,'](#$1)'));
 $('#hero').innerHTML='<div class="fade"><div class="eyebrow">'+num(i)+' / '+(i?'GUIDE':'START HERE')+'</div><h1>'+esc(p.title)+'</h1><p class="stand">'+marked.parseInline(first)+'</p>'+
  '<dl class="meta"><div><dt>PAGE</dt><dd>'+num(i)+' of '+num(P.length-1)+'</dd></div><div><dt>READ</dt><dd>'+Math.max(1,Math.round(words/220))+' min</dd></div><div><dt>SOURCE</dt><dd><a href="https://github.com/aloki-alok/kagestack/blob/main/docs/concepts/'+p.file+'"><code>docs/concepts/'+p.file+'</code></a></dd></div></dl></div>';
 $('#main').innerHTML='<div class="fade">'+(fig?'<pre class="m">'+esc(fig)+'</pre>':'')+'<div class="prose">'+html+'</div>'+
  '<div class="pager">'+(i>0?'<a class="prev" href="#'+P[i-1].id+'"><div class="k">\u2190 PREVIOUS</div><div class="t">'+P[i-1].title+'</div></a>':'')+(i<P.length-1?'<a class="next" href="#'+P[i+1].id+'"><div class="k">NEXT \u2192</div><div class="t">'+P[i+1].title+'</div></a>':'')+'</div></div>';
 const hs=[...document.querySelectorAll('.prose h2')];hs.forEach(h=>{h.id=h.textContent.toLowerCase().replace(/[^a-z0-9]+/g,'-');h.insertAdjacentHTML('beforeend','<a class="anchor" href="#'+p.id+'/'+h.id+'">#</a>')});
 $('#tree').innerHTML='<div class="h">TREE</div>'+P.map((q,k)=>'<a href="#'+q.id+'" class="'+(k===i?'on':'')+'"><span class="n">'+num(k)+'</span><span>'+esc(q.title)+'</span></a>'+(k===i&&hs.length?'<div class="sub">'+hs.map(h=>'<a href="#'+p.id+'/'+h.id+'" data-h="'+h.id+'"><span>'+esc(h.childNodes[0].textContent)+'</span></a>').join('')+'</div>':'')).join('')+'<div class="prog"><i id="pbar"></i><span id="ptxt">00%</span></div>';
 initMermaid();draw();onScroll();
}
function route(){const [id,h]=location.hash.slice(1).split('/');if(id!==P[cur]?.id||!$('#main').innerHTML){show(id);scrollTo(0,0)}if(h){const el=document.getElementById(h);el&&el.scrollIntoView()}}
function onScroll(){const m=$('#main'),r=m.getBoundingClientRect(),t=Math.min(1,Math.max(0,(-r.top+64)/Math.max(1,r.height-innerHeight+64)));const b=$('#pbar');if(b){b.style.setProperty('--p',(t*100)+'%');$('#ptxt').textContent=String(Math.round(t*100)).padStart(2,'0')+'%'}
 let on=null;document.querySelectorAll('.prose h2').forEach(h=>{if(h.getBoundingClientRect().top<140)on=h.id});document.querySelectorAll('#tree a[data-h]').forEach(a=>a.classList.toggle('on',a.dataset.h===on))}
addEventListener('scroll',onScroll,{passive:true});addEventListener('hashchange',route);
$('#theme').onclick=()=>{const r=document.documentElement;r.dataset.theme=dark()?'light':'dark';try{localStorage.setItem('kagestack-docs-theme',r.dataset.theme)}catch(e){}show(location.hash.slice(1).split('/')[0]||P[0].id)};
try{const t=localStorage.getItem('kagestack-docs-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}
const idx=P.map((p,i)=>({i,p,text:plain(p.md)}));let sel=0;
function search(q){q=q.trim().toLowerCase();const r=q?idx.filter(x=>(x.p.title+' '+x.text).toLowerCase().includes(q)).slice(0,8):idx.slice(0,8);sel=0;
 $('#res').innerHTML=r.length?r.map((x,k)=>{const at=x.text.toLowerCase().indexOf(q);const sn=q&&at>=0?esc(x.text.slice(Math.max(0,at-50),at))+'<mark>'+esc(x.text.slice(at,at+q.length))+'</mark>'+esc(x.text.slice(at+q.length,at+q.length+70)):esc(x.text.slice(0,110));return '<a href="#'+x.p.id+'" class="'+(k?'':'sel')+'"><div class="rt"><span class="mono" style="color:var(--mid);font-size:12px;margin-right:10px">'+num(x.i)+'</span>'+x.p.title+'</div><div class="rs">'+sn+'</div></a>'}).join(''):'<div class="empty">No page mentions that.</div>'}
function openS(){$('#scrim').classList.add('open');$('#q').value='';search('');$('#q').focus()}
function closeS(){$('#scrim').classList.remove('open')}
$('#sbtn').onclick=openS;$('#scrim').onclick=e=>{if(e.target.id==='scrim')closeS()};$('#res').onclick=closeS;
$('#q').oninput=e=>search(e.target.value);
$('#q').onkeydown=e=>{const a=[...document.querySelectorAll('#res a')];if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();a[sel]?.classList.remove('sel');sel=(sel+(e.key==='ArrowDown'?1:a.length-1))%a.length;a[sel]?.classList.add('sel');a[sel]?.scrollIntoView({block:'nearest'})}if(e.key==='Enter'&&a[sel]){location.hash=a[sel].getAttribute('href');closeS()}if(e.key==='Escape')closeS()};
$('#zoom').onclick=()=>$('#zoom').classList.remove('open');
addEventListener('keydown',e=>{if(e.target.tagName==='INPUT')return;if(e.metaKey||e.ctrlKey)return;const k=e.key.toLowerCase();
 if(k==='/'){e.preventDefault();openS()}else if(k==='j')location.hash=P[Math.max(0,cur-1)].id;else if(k==='k')location.hash=P[Math.min(P.length-1,cur+1)].id;
 else if(k==='c')location.hash='changes';else if(k==='d')location.hash=P[0].id;else if(k==='g')location.href='https://github.com/aloki-alok/kagestack';else if(k==='t')$('#theme').click();else if(k==='escape'){$('#zoom').classList.remove('open');closeS()}});
show(location.hash.slice(1).split('/')[0]||P[0].id);
