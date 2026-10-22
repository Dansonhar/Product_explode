import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import './style.css';

const BASE = import.meta.env.BASE_URL;
const catalog = await fetch(BASE+'models/catalog.json').then(r=>{if(!r.ok)throw Error('Catalogue unavailable');return r.json()});
const $=s=>document.querySelector(s);
$('#app').innerHTML=`
<header><div class="brand">CRAVE <b>ProductViu<sup>™</sup></b><span> / LINKK</span></div><div class="tag">MEGADUCT · PHOTO RECONSTRUCTION · SEPTEMBER 2026</div><button id="theme">Light / dark</button></header>
<aside><div class="eyebrow">REBUILT FROM YOUR BROCHURE</div><h1>MEGADUCT<br>Design study.</h1><p class="intro">Explore the reconstructed product and compare it directly with the supplied reference.</p>
<div class="config"><label>Core material appearance<select id="material"><option value="copper">Copper</option><option value="aluminium">Aluminium</option></select></label><label>Design variant<select id="variant"></select></label></div>
<input id="search" placeholder="Find a product…" aria-label="Search products"><div id="catalog"></div><footer>${catalog.length} REBUILT PRODUCT FAMILIES<small>Photo-based geometry · estimated unlabelled dimensions</small></footer></aside>
<main><div class="stage-head"><span id="number"></span><h2 id="title"></h2><p id="category"></p><div id="badges"><b>RECONSTRUCTED ASSEMBLY</b><b>EDITABLE BLENDER SOURCE</b></div></div><div id="canvas"></div><div id="auto-tour" hidden><div class="tour-status"><i></i><span>AUTO DETAIL TOUR</span><b id="tour-count"></b></div><svg id="tour-lines" aria-hidden="true"></svg><div id="tour-labels"></div></div><div id="flow-story" hidden><span>LIVE CONNECTION EXPLAINER</span><strong id="flow-stage">Incoming supply energises the vertical riser</strong><div class="flow-route"><b>SOURCE</b><i>→</i><b>RISER</b><i>→</i><b>OUTLET</b><i>→</i><b>TAP-OFF</b><i>→</i><b>LOAD</b></div><small>Animated pulses indicate distribution direction—not literal AC electron motion.</small></div><div id="loading">Loading reconstruction…</div><div id="hint">Drag to orbit · Scroll to zoom · Select a component</div>
<div class="toolbar"><button id="assemble" class="active">Assembled</button><button id="explode">Exploded</button><label>Separation <input id="range" type="range" min="0" max="100" value="0"></label><button id="ghost">X-ray</button><button id="section">End view</button><button id="spin">Auto rotate</button><button id="flow-toggle" hidden>Pause energy flow</button><button id="reset">Reset view</button></div></main>
<section class="details"><div class="reference"><span>SUPPLIED BROCHURE REFERENCE</span><button id="reference-open" aria-label="Enlarge source photograph"><img id="ref" alt="Supplied MEGADUCT brochure reference"></button><small id="source-name"></small></div><div class="eyebrow">ASSEMBLY COMPONENTS</div><h3 id="part-title"></h3><p id="part-desc"></p><div id="material-readout"></div><div id="facts"></div><div id="parts"></div><button id="showall">Show all components</button><button id="export">↓ Download assembled GLB</button><p class="note">Visible geometry follows the photographs. Unlabelled dimensions and ordinary internal conductor paths are representative. Hidden specialist mechanisms are omitted. This study does not specify a rated manufacturing design.</p></section>
<dialog id="reference-dialog"><button id="reference-close" aria-label="Close reference">×</button><img id="reference-large" alt="Full brochure photograph"></dialog>`;

const scene=new T.Scene();scene.background=new T.Color('#e9edf0');
const camera=new T.PerspectiveCamera(35,1,.001,100);
const renderer=new T.WebGLRenderer({antialias:true,powerPreference:'high-performance'});renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1;$('#canvas').appendChild(renderer.domElement);
// Pixel budget: full device ratio on a small canvas, scaled back on a large one
// so shading cost stays roughly constant instead of growing with the window.
const PIXEL_BUDGET=2.6e6;
const pixelRatio=(w,h)=>Math.max(1,Math.min(devicePixelRatio,1.5,Math.sqrt(PIXEL_BUDGET/Math.max(w*h,1))));
scene.add(new T.HemisphereLight(0xffffff,0x637181,1.8));for(const [position,power] of [[[-3,6,-4],4],[[4,2,3],2.2],[[-2,-3,2],1.3]]){const light=new T.DirectionalLight(0xffffff,power);light.position.set(...position);scene.add(light)}
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=.03;controls.maxDistance=30;
controls.autoRotateSpeed=1.15;
if(import.meta.env.DEV)window.__megaductViewState=()=>[...camera.position.toArray(),...camera.quaternion.toArray(),...controls.target.toArray(),camera.zoom];
const EXPLODE_SCALE=1.4;
const loader=new GLTFLoader();let model,parts=[],demoParts=[],index=0,variantIndex=0,selected=null,amount=0,target=0,ghost=false,dark=false,token=0,dirty=true,tourParts=[],tourOrder=[],tourCursor=0,tourLast=0,flowGroup=null,flowCurves=[],flowMarkers=[],flowActive=false,flowElapsed=0,flowLastFrame=0,canvasW=0,canvasH=0,tourLabels=[],tourGroups=[];
const scratch=new T.Vector3();
const FLOW_DETAIL_HOLD=6500,TOUR_DETAIL_HOLD=9000;
const current=()=>catalog[index],variant=()=>current().variants[variantIndex];
const cleanName=name=>name.replaceAll('_',' ').replace(/\.?\d{3}$/,'');
function listCatalog(){
 const query=$('#search').value.toLowerCase();$('#catalog').innerHTML=catalog.map((p,i)=>p.name.toLowerCase().includes(query)?`<button class="product ${index===i?'selected':''}" data-product="${i}"><img src="${BASE}thumbs/${p.slug}.webp" loading="lazy" decoding="async" alt="" onerror="this.style.visibility='hidden'"><span><small>${String(i+1).padStart(2,'0')}</small>${p.name}</span><em>↗</em></button>`:'').join('');
}
$('#catalog').onclick=e=>{const b=e.target.closest('[data-product]');if(b)load(+b.dataset.product)};
$('#parts').onclick=e=>{const b=e.target.closest('[data-part]');if(b)select(parts[+b.dataset.part])};
function summary(){
 $('#part-title').textContent=current().name;$('#part-desc').textContent=variant().label;
 const system=current().slug==='connected-system';
 $('#material-readout').innerHTML=system?'<span>Reference-matched application</span><strong>Vertical plug-in riser with stacked tap-off units</strong><small>The lower demonstration unit aligns with the guide port and outlet before the cyan path illustrates distribution. This is explanatory animation, not an electrical simulation or current-rating calculation.</small>':'<span>Reconstruction basis</span><strong>Visible geometry from supplied photographs</strong><small>Material appearance changes the core finish; it does not change dimensions or establish a current rating.</small>';
}
function listParts(){
 $('#parts').innerHTML=parts.map((p,i)=>`<button class="part ${p===selected?'selected':''}" data-part="${i}"><i class="${p.userData.kind}"></i><span>${cleanName(p.name)}<small>${p.userData.material||''}</small></span></button>`).join('');
 if(selected)$('#parts .selected')?.scrollIntoView({block:'nearest',behavior:'smooth'});
}
function appearance(){
 for(const p of parts){
  const faded=selected&&p!==selected,xray=ghost&&p.userData.kind==='enclosure',featured=p===selected||tourParts.includes(p);
  const opacity=faded?.08:xray?.10:1,transparent=opacity<1;
  for(const m of p.userData.materials){
   // Only `transparent` rebuilds the shader program; opacity and emissive are
   // uniforms. Flagging needsUpdate unconditionally recompiled every material
   // on every selection and on every tour step.
   if(m.transparent!==transparent){m.transparent=transparent;m.depthWrite=!transparent;m.needsUpdate=true}
   m.opacity=opacity;m.emissive?.set(featured?0x3a1711:0x000000);m.emissiveIntensity=featured?.32:1;
  }
 }dirty=true;
}
function select(p){selected=selected===p?null:p;if(selected){$('#part-title').textContent=cleanName(p.name);$('#part-desc').textContent=p.userData.description||'';$('#material-readout').innerHTML=`<span>Component material</span><strong>${p.userData.material||'Reference finish'}</strong>`}else summary();appearance();listParts()}
function setMaterial(){if(!model)return;model.traverse(o=>{if(o.isMesh)for(const m of Array.isArray(o.material)?o.material:[o.material])if(/^core(?:\.|$)/.test(m.name))m.color.set($('#material').value==='copper'?'#b46e43':'#bbc4cc')});dirty=true}
function fit(direction=new T.Vector3(-1.35,1.15,1.9)){
 if(!model)return;const positions=parts.map(p=>p.position.clone());parts.forEach(p=>p.position.copy(p.userData.base).addScaledVector(p.userData.delta,target*EXPLODE_SCALE));model.updateMatrixWorld(true);
 const box=new T.Box3().setFromObject(model),center=box.getCenter(new T.Vector3()),size=box.getSize(new T.Vector3());
 const q=new T.Quaternion().setFromRotationMatrix(new T.Matrix4().lookAt(direction,new T.Vector3(),new T.Vector3(0,1,0))),inverse=q.clone().invert();
 let width=0,height=0,depth=0;for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]){const v=new T.Vector3(x,y,z).sub(center).applyQuaternion(inverse);width=Math.max(width,Math.abs(v.x)*2);height=Math.max(height,Math.abs(v.y)*2);depth=Math.max(depth,Math.abs(v.z))}
 const distance=Math.max(height/.67,width/(camera.aspect*.84))/(2*Math.tan(T.MathUtils.degToRad(camera.fov/2)))+depth;
 controls.target.copy(center);camera.position.copy(center).addScaledVector(direction.normalize(),distance*1.08);camera.near=Math.max(.0002,size.length()/2000);camera.far=Math.max(30,distance*20);camera.updateProjectionMatrix();controls.update();parts.forEach((p,i)=>p.position.copy(positions[i]));
}
function dispose(root){root.traverse(o=>{o.geometry?.dispose();if(o.material)for(const m of Array.isArray(o.material)?o.material:[o.material])m.dispose()})}
function clearFlow(){flowGroup=null;flowCurves=[];flowMarkers=[];flowActive=false;flowElapsed=0;flowLastFrame=0;$('#flow-story').hidden=true;$('#flow-toggle').hidden=true;$('#flow-toggle').textContent='Pause energy flow'}
function setupFlow(){flowGroup=new T.Group();flowGroup.name='Animated schematic energy flow';flowCurves=[
 new T.CatmullRomCurve3([new T.Vector3(0,-.82,0),new T.Vector3(0,-.35,0),new T.Vector3(0,.20,0),new T.Vector3(0,.82,0)]),
 new T.CatmullRomCurve3([new T.Vector3(0,.345,0),new T.Vector3(0,.345,.17),new T.Vector3(0,.345,.34)]),
 new T.CatmullRomCurve3([new T.Vector3(0,-.065,0),new T.Vector3(0,-.065,.17),new T.Vector3(0,-.065,.34)]),
 new T.CatmullRomCurve3([new T.Vector3(0,-.505,0),new T.Vector3(0,-.505,.17),new T.Vector3(0,-.505,.34)])
 ];
 const lineMaterial=new T.LineBasicMaterial({color:0x21bff3,transparent:true,opacity:.38,depthTest:false,blending:T.AdditiveBlending}),pulseMaterial=new T.MeshBasicMaterial({color:0x47d9ff,depthTest:false,blending:T.AdditiveBlending}),haloMaterial=new T.MeshBasicMaterial({color:0x7ce5ff,transparent:true,opacity:.18,depthWrite:false,depthTest:false,blending:T.AdditiveBlending});
 flowCurves.forEach((curve,path)=>{const line=new T.Line(new T.BufferGeometry().setFromPoints(curve.getPoints(80)),lineMaterial.clone()),count=path===0?6:2;line.renderOrder=10;flowGroup.add(line);for(let i=0;i<count;i++){const marker=new T.Group(),core=new T.Mesh(new T.SphereGeometry(.018,12,8),pulseMaterial.clone()),halo=new T.Mesh(new T.SphereGeometry(.038,12,8),haloMaterial.clone());marker.add(core,halo);marker.renderOrder=11;marker.userData={path,offset:i/count};flowGroup.add(marker);flowMarkers.push(marker)}});model.add(flowGroup);flowActive=true;flowElapsed=0;flowLastFrame=0;$('#flow-stage').textContent='Incoming supply energises the vertical riser';$('#flow-story').hidden=false;$('#flow-toggle').hidden=false}
function updateFlow(time){if(!flowActive)return;if(flowLastFrame)flowElapsed+=Math.min(time-flowLastFrame,100);flowLastFrame=time;const speed=flowElapsed*.00016;for(const marker of flowMarkers){const t=(speed+marker.userData.offset)%1;marker.position.copy(flowCurves[marker.userData.path].getPointAt(t));const pulse=.84+.22*Math.sin((t*10+marker.userData.path)*Math.PI);marker.scale.setScalar(pulse)}const stages=['Incoming supply energises the vertical riser','Plug-in outlets provide connection points at each level','Guide ports align the tap-off before engagement','Interlocking clamps secure the tap-off unit','Power transfers through the plug-in contacts to the local load'];$('#flow-stage').textContent=stages[Math.floor(flowElapsed/FLOW_DETAIL_HOLD)%stages.length]}
function updateConnectionDemo(){if(!demoParts.length||amount>.01)return;const cycle=(flowElapsed%18000)/18000,ease=x=>x*x*(3-2*x);let travel=0;if(cycle>.22&&cycle<.42)travel=ease((cycle-.22)/.20);else if(cycle>=.42&&cycle<=.76)travel=1;else if(cycle>.76&&cycle<.94)travel=1-ease((cycle-.76)/.18);for(const p of demoParts)p.position.addScaledVector(p.userData.demoAttach,travel)}
function tourSequence(){const kinds=['connection','conductor','insulation','enclosure','protection','support'],groups=Object.fromEntries(kinds.map(k=>[k,parts.filter(p=>p.userData.kind===k)])),result=[];for(let row=0;result.length<parts.length;row++){let added=false;for(const kind of kinds)if(groups[kind][row]){result.push(groups[kind][row]);added=true}if(!added)break}return result}
function clearTourLabels(){tourParts=[];tourLabels=[];tourGroups=[];$('#tour-labels').replaceChildren();$('#tour-lines').replaceChildren();appearance()}
function buildTourGroup(){if(!tourOrder.length)return;tourParts=tourOrder.slice(tourCursor,tourCursor+3);const labels=document.createDocumentFragment(),lines=document.createDocumentFragment();tourParts.forEach((part,i)=>{const label=document.createElement('div');label.className='tour-callout';label.dataset.tour=String(i);const n=document.createElement('b');n.textContent=String(tourOrder.indexOf(part)+1).padStart(2,'0');const copy=document.createElement('span');const title=document.createElement('strong');title.textContent=cleanName(part.name);const detail=document.createElement('small');detail.textContent=part.userData.description||part.userData.material||'Reconstructed component';copy.append(title,detail);label.append(n,copy);labels.append(label);const group=document.createElementNS('http://www.w3.org/2000/svg','g');group.dataset.tour=String(i);const line=document.createElementNS('http://www.w3.org/2000/svg','line'),dot=document.createElementNS('http://www.w3.org/2000/svg','circle');dot.setAttribute('r','4');group.append(line,dot);lines.append(group)});$('#tour-labels').replaceChildren(labels);$('#tour-lines').replaceChildren(lines);
 // Measured once per tour step. Reading offsetWidth/offsetHeight inside the
 // frame loop forced a synchronous layout on every frame.
 tourLabels=[...$('#tour-labels').children];for(const l of tourLabels){l.w=l.offsetWidth;l.h=l.offsetHeight}
 tourGroups=[...$('#tour-lines').children].map(g=>({line:g.querySelector('line'),dot:g.querySelector('circle')}));
 $('#tour-count').textContent=`${tourCursor+1}–${tourCursor+tourParts.length} / ${tourOrder.length}`;appearance();dirty=true}
function startAutoTour(reset=true){if(!parts.length)return;selected=null;summary();listParts();$('#auto-tour').hidden=false;tourOrder=tourSequence();if(reset)tourCursor=0;tourLast=performance.now();buildTourGroup();$('#spin').textContent='Stop detail tour'}
function stopAutoTour(){clearTourLabels();$('#auto-tour').hidden=true;$('#spin').textContent='Auto detail tour';dirty=true}
function updateTourOverlay(){
 if(!controls.autoRotate||!tourParts.length)return;
 const w=canvasW,h=canvasH;
 // Cached part centre + cached canvas size: no getBoundingClientRect, no
 // offsetWidth, and no Box3.setFromObject rebuild per label per frame.
 tourParts.forEach((part,i)=>{
  const label=tourLabels[i],refs=tourGroups[i];if(!label||!refs)return;
  scratch.copy(part.userData.center).applyMatrix4(part.matrixWorld).project(camera);
  const ax=(scratch.x*.5+.5)*w,ay=(-scratch.y*.5+.5)*h;
  const right=ax<w/2,labelX=right?w-label.w-20:20,slots=[h*.30,h*.50,h*.70],labelY=Math.max(100,Math.min(h-label.h-100,slots[i]));
  label.style.transform=`translate3d(${labelX}px,${labelY}px,0)`;label.classList.toggle('right',right);
  const endX=right?labelX:labelX+label.w,endY=labelY+label.h/2;
  refs.line.setAttribute('x1',ax);refs.line.setAttribute('y1',ay);refs.line.setAttribute('x2',endX);refs.line.setAttribute('y2',endY);refs.dot.setAttribute('cx',ax);refs.dot.setAttribute('cy',ay);
 });
}
function chrome(){
 const system=current().slug==='connected-system';
 $('#title').textContent=current().name;$('#category').textContent=variant().label;$('#number').textContent=`PRODUCT ${String(index+1).padStart(2,'0')} / ${catalog.length}`;
 $('#badges').innerHTML=system?'<b>ANIMATED APPLICATION</b><b>CONNECTED PRODUCTS</b>':'<b>RECONSTRUCTED ASSEMBLY</b><b>EDITABLE BLENDER SOURCE</b>';
 $('#hint').textContent=system?'Follow the cyan energy path · Drag to orbit · Scroll to zoom':'Drag to orbit · Scroll to zoom · Select a component';
 $('#variant').innerHTML=current().variants.map((v,i)=>`<option value="${i}" ${i===variantIndex?'selected':''}>${v.label}</option>`).join('');$('#variant').disabled=current().variants.length===1;
 const ref=BASE+'references/web/'+variant().photo.replace(/\.jpg$/i,'.webp');$('#ref').src=ref;$('#reference-large').src=ref;$('#source-name').textContent='IMG20260917'+variant().photo;
 $('#facts').innerHTML='<div class="facts-title">REFERENCE DETAILS</div>'+current().facts.map(f=>`<div class="fact">${f}</div>`).join('');summary();listParts();listCatalog();
}
async function load(i,v=0){
 const mine=++token;index=i;variantIndex=v;selected=null;amount=target=0;ghost=false;$('#range').value=0;$('#ghost').classList.remove('active');$('#assemble').classList.add('active');$('#explode').classList.remove('active');
 clearTourLabels();$('#auto-tour').hidden=true;clearFlow();
 if(model){scene.remove(model);dispose(model)}model=null;parts=[];demoParts=[];chrome();$('#loading').hidden=false;$('#loading').textContent='Loading reconstruction…';
 try{
  const gltf=await loader.loadAsync(BASE+'models/'+variant().file);if(mine!==token){dispose(gltf.scene);return}
  model=new T.Group();model.name=current().name;model.userData={source:'IMG20260917'+variant().photo,variant:variant().label,accuracy:'Photo reconstruction; estimated unlabelled dimensions'};model.add(gltf.scene);model.updateMatrixWorld(true);
  const components=[];gltf.scene.traverse(o=>{if(o.userData.component)components.push(o)});const order=['enclosure','connection','protection','support','conductor','insulation'];components.sort((a,b)=>order.indexOf(a.userData.kind)-order.indexOf(b.userData.kind));
  for(const p of components){const d=p.userData.delta||[0,0,0],a=p.userData.demoAttach;model.attach(p);p.userData.base=p.position.clone();p.userData.delta=new T.Vector3(d[0],d[2],-d[1]);if(a){p.userData.demoAttach=new T.Vector3(...a);demoParts.push(p)}
  // One clone per (part, source material) instead of one per mesh. Parts still
  // fade independently, but the renderer stops switching material state on
  // every one of the ~230 meshes in a model.
  const clones=new Map(),materials=[];
  p.traverse(o=>{if(!o.isMesh)return;const list=(Array.isArray(o.material)?o.material:[o.material]).map(m=>{let c=clones.get(m);if(!c){c=m.clone();clones.set(m,c);materials.push(c)}return c});o.material=list.length===1?list[0]:list});
  p.userData.materials=materials;
  p.updateMatrixWorld(true);p.userData.center=p.worldToLocal(new T.Box3().setFromObject(p).getCenter(new T.Vector3()));
  parts.push(p)}
  gltf.scene.removeFromParent();if(current().slug==='connected-system')setupFlow();scene.add(model);setMaterial();chrome();fit(current().slug==='connected-system'?new T.Vector3(-1,.18,2):undefined);if(controls.autoRotate)startAutoTour();$('#loading').hidden=true;window.dispatchEvent(new CustomEvent('megaduct-loaded',{detail:{slug:current().slug,variant:variant().key}}));
 }catch(e){$('#loading').textContent='Unable to load this model: '+e.message;console.error(e)}
}
function separation(value){target=value;dirty=true;$('#range').value=value*100;$('#assemble').classList.toggle('active',value===0);$('#explode').classList.toggle('active',value>0)}
// Assembly state changes only move parts. Camera angle, orbit target and zoom
// remain exactly where the user left them until Reset view is requested.
$('#assemble').onclick=()=>separation(0);$('#explode').onclick=()=>separation(1);$('#range').oninput=e=>separation(+e.target.value/100);
$('#ghost').onclick=()=>{ghost=!ghost;$('#ghost').classList.toggle('active',ghost);appearance()};$('#section').onclick=()=>fit(new T.Vector3(-1,0,.001));$('#reset').onclick=()=>fit();$('#spin').onclick=()=>{controls.autoRotate=!controls.autoRotate;$('#spin').classList.toggle('active',controls.autoRotate);if(controls.autoRotate)startAutoTour();else stopAutoTour()};
$('#search').oninput=listCatalog;$('#variant').onchange=e=>load(index,+e.target.value);$('#material').onchange=setMaterial;$('#showall').onclick=()=>{selected=null;ghost=false;$('#ghost').classList.remove('active');summary();appearance();listParts()};
$('#theme').onclick=()=>{dark=!dark;document.body.classList.toggle('dark',dark);scene.background.set(dark?'#202932':'#e9edf0');dirty=true};
$('#flow-toggle').onclick=()=>{flowActive=!flowActive;flowLastFrame=0;$('#flow-toggle').textContent=flowActive?'Pause energy flow':'Resume energy flow';dirty=true};
$('#reference-open').onclick=()=>$('#reference-dialog').showModal();$('#reference-close').onclick=()=>$('#reference-dialog').close();$('#reference-dialog').onclick=e=>{if(e.target===$('#reference-dialog'))$('#reference-dialog').close()};
$('#export').onclick=async()=>{
 if(!model)return;const button=$('#export');button.disabled=true;
 try{const {GLTFExporter}=await import('three/addons/exporters/GLTFExporter.js');const copy=model.clone(true);copy.userData.coreAppearance=$('#material').value;copy.getObjectByName('Animated schematic energy flow')?.removeFromParent();copy.children.filter(p=>p.userData.component).forEach((p,i)=>p.position.copy(parts[i].userData.base));copy.traverse(o=>{if(o.isMesh){o.material=(Array.isArray(o.material)?o.material:[o.material]).map(m=>{const c=m.clone();c.opacity=1;c.transparent=false;c.depthWrite=true;c.emissive?.set(0);return c});if(o.material.length===1)o.material=o.material[0]}});
 const data=await new GLTFExporter().parseAsync(copy,{binary:true});const url=URL.createObjectURL(new Blob([data],{type:'model/gltf-binary'}));const a=document.createElement('a');a.href=url;a.download=`MEGADUCT-${current().slug}-${variant().key||'reference'}-${$('#material').value}.glb`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }catch(e){console.error(e);$('#hint').textContent='Download failed. Please try again.'}finally{button.disabled=false}
};
const ray=new T.Raycaster(),pointer=new T.Vector2();let down;
renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);renderer.domElement.addEventListener('pointerup',e=>{if(!model||!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const r=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);ray.setFromCamera(pointer,camera);const hit=ray.intersectObjects(parts,true).find(h=>{let p=h.object;while(p.parent&&p.parent!==model)p=p.parent;return !(ghost&&p.userData.kind==='enclosure')});if(hit){let p=hit.object;while(p.parent!==model)p=p.parent;select(p)}});
function resize(){const r=$('#canvas').getBoundingClientRect();if(!r.width||!r.height)return;canvasW=r.width;canvasH=r.height;renderer.setPixelRatio(pixelRatio(r.width,r.height));renderer.setSize(r.width,r.height);camera.aspect=r.width/r.height;camera.updateProjectionMatrix();$('#tour-lines').setAttribute('viewBox',`0 0 ${r.width} ${r.height}`);dirty=true;fit()}
// Coalesced to one resize per frame: a window drag otherwise refit the camera
// and rebuilt the model bounding box on every observer callback.
let resizeQueued=false;
new ResizeObserver(()=>{if(resizeQueued)return;resizeQueued=true;requestAnimationFrame(()=>{resizeQueued=false;resize()})}).observe($('#canvas'));resize();await load(0);
controls.addEventListener('change',()=>dirty=true);
renderer.setAnimationLoop(time=>{let moving=Math.abs(target-amount)>.0005;if(!moving&&amount!==target){amount=target;dirty=true}const changed=controls.update();if(!dirty&&!moving&&!changed&&!controls.autoRotate&&!flowActive)return;if(moving)amount+=(target-amount)*.12;
 if(controls.autoRotate&&time-tourLast>TOUR_DETAIL_HOLD){tourCursor=(tourCursor+tourParts.length)%tourOrder.length;tourLast=time;buildTourGroup()}
 // Rest positions do not change while the user is only orbiting, so rewrite
 // them while the explosion eases, and otherwise only the demo parts that
 // updateConnectionDemo offsets from their base each frame.
 const demo=demoParts.length&&amount<=.01;
 if(moving||dirty)for(const p of parts)p.position.copy(p.userData.base).addScaledVector(p.userData.delta,amount*EXPLODE_SCALE);
 else if(demo)for(const p of demoParts)p.position.copy(p.userData.base).addScaledVector(p.userData.delta,amount*EXPLODE_SCALE);
 updateFlow(time);updateConnectionDemo();
 // The renderer updates the scene graph itself; only the overlay needs world
 // matrices early, and an unforced update skips the untouched branches.
 if(tourParts.length)model?.updateMatrixWorld();
 updateTourOverlay();renderer.render(scene,camera);dirty=false});
