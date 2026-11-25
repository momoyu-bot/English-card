const fs=require('fs'),vm=require('vm');
const {createCanvas,Path2D,ImageData,DOMMatrix}=require('@napi-rs/canvas');
function runtime(file){
 const html=fs.readFileSync(file,'utf8'),nodes=new Map(),canvases=[];
 function element(tag='div',attrs='',body=''){
  const a=Object.fromEntries([...attrs.matchAll(/([\w-]+)=["']([^"']*)["']/g)].map(m=>[m[1],m[2]]));
  const e=tag==='canvas'?createCanvas(+a.width||720,+a.height||900):{};
  if(tag==='canvas')canvases.push(e);
  Object.assign(e,{tagName:tag.toUpperCase(),id:a.id||'',dataset:{},style:{setProperty(){}},classList:{add(){},remove(){},toggle(){},contains(){return false}},textContent:body.replace(/<[^>]*>/g,''),innerHTML:body,clientWidth:480,clientHeight:720,offsetWidth:480,offsetHeight:720,value:a.value||'0',checked:false,children:[],addEventListener(){},removeEventListener(){},setAttribute(k,v){this[k]=v;},getAttribute(k){return a[k]||null;},removeAttribute(){},append(...x){this.children.push(...x)},appendChild(x){this.children.push(x);return x},replaceChildren(...x){this.children=x},remove(){},scrollIntoView(){},focus(){},getBoundingClientRect(){return {width:480,height:720,left:0,top:0}},querySelector(){return element()},querySelectorAll(sel){if(sel==='[data-t]')return [...body.matchAll(/<button([^>]*data-t[^>]*)>([\s\S]*?)<\/button>/g)].map(m=>element('button',m[1],m[2]));return []}});
  for(const [k,v]of Object.entries(a))if(k.startsWith('data-'))e.dataset[k.slice(5).replace(/-([a-z])/g,(_,s)=>s.toUpperCase())]=v;
  Object.defineProperty(e,'parentElement',{get:()=>({clientWidth:480,clientHeight:800,getBoundingClientRect:()=>({width:480,height:800})})});
  return e;
 }
 for(const m of html.matchAll(/<(canvas|div|button|input|span|section|details|p|output|select|a)[^>]*\bid=["'][^"']+["'][^>]*>/g)){const attrs=m[0].slice(m[1].length+1,-1);const e=element(m[1],attrs);nodes.set(e.id,e);}
 const scenes=[...html.matchAll(/<section([^>]*class="scene"[^>]*)>([\s\S]*?)<\/section>/g)].map(m=>element('section',m[1],m[2]));
 const get=id=>{if(!nodes.has(id))nodes.set(id,element());return nodes.get(id)};
 const doc={getElementById:get,querySelector:s=>s==='canvas'?canvases[0]:s.startsWith('#')?get(s.slice(1)):element(),querySelectorAll:s=>s==='.scene'?scenes:[],createElement:element,createTextNode:text=>({textContent:text}),addEventListener(){},documentElement:element(),body:element(),fonts:{ready:Promise.resolve()},hidden:false};
 const context={console,document:doc,devicePixelRatio:1,innerWidth:480,innerHeight:900,performance:{now:()=>0},Math,Date,Number,String,Array,Object,Map,Set,Uint8Array,Uint8ClampedArray,Float32Array,ArrayBuffer,DataView,Promise,Path2D,ImageData,DOMMatrix,URL,URLSearchParams,location:{search:'',hash:'',href:'file://'+file},requestAnimationFrame:()=>1,cancelAnimationFrame(){},setTimeout:()=>1,clearTimeout(){},setInterval:()=>1,clearInterval(){},addEventListener(){},removeEventListener(){},matchMedia:()=>({matches:false,addEventListener(){}}),ResizeObserver:class{observe(){}},localStorage:{getItem(){return null},setItem(){}},getComputedStyle:()=>({width:'480px',height:'720px',getPropertyValue:()=>''}),navigator:{userAgent:'canvas-export'},screen:{width:480,height:900}};
 context.window=context;context.globalThis=context;vm.createContext(context);
 for(const m of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))vm.runInContext(m[1],context,{filename:file,timeout:10000});
 if(!context.FILM)throw Error('No FILM API: '+file);
 const f=context.FILM;f.pause?.();return {film:f,canvas:f.canvas||canvases[0],title:(html.match(/<title>(.*?)<\/title>/s)||[])[1]};
}
module.exports={runtime,createCanvas};
