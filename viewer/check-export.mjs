import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {readFile,writeFile,access} from 'node:fs/promises';
import assert from 'node:assert/strict';
const catalog=JSON.parse(await readFile('public/models/catalog.json','utf8'));
const loader=new GLTFLoader(),report=[];
for(const product of catalog)for(const variant of product.variants){
 const file=await readFile('public/models/'+variant.file),gltf=await loader.parseAsync(file.buffer.slice(file.byteOffset,file.byteOffset+file.byteLength),'');
 const components=[];let meshes=0;gltf.scene.updateMatrixWorld(true);
 gltf.scene.traverse(o=>{if(o.userData.component){components.push(o);assert.equal(o.userData.delta.length,3)}if(o.isMesh){meshes++;assert(Array.from(o.geometry.attributes.position.array).every(Number.isFinite),'non-finite vertex');assert(o.geometry.attributes.position.count>0)}});
 assert(meshes>=2,variant.file+' missing meshes');assert(components.length>0);const box=new T.Box3().setFromObject(gltf.scene),size=box.getSize(new T.Vector3());assert([...size].every(v=>Number.isFinite(v)&&v>0&&v<10),variant.file+' world bounds');
 const originals=components.map(o=>o.position.clone());for(const o of components){const d=o.userData.delta;o.position.add(new T.Vector3(d[0]*10,d[2]*10,-d[1]*10))}assert(!new T.Box3().setFromObject(gltf.scene).isEmpty());components.forEach((o,i)=>o.position.copy(originals[i]));
 await access('../blender/products/'+variant.blend);await access('public/references/brochure/'+variant.photo);await access('public/renders/'+variant.render);
 const names=components.map(o=>o.name.replaceAll('_',' '));
 if(product.slug==='joint'){for(const kind of ['Joint bolt','Joint backing plate','Joint Earth Bar','Joint end insulator','Joint conductor bar','Joint phase insulator','Belleville disc','Nylon lock nut','Fiber tube'])assert(names.some(n=>n.startsWith(kind)),kind)}
 if(product.slug==='spring-support'){let springs=0;gltf.scene.traverse(o=>{if(o.isMesh&&o.name.startsWith('Compression_spring'))springs++});assert.equal(springs,4)}
 if(product.slug==='connected-system'){for(const name of ['Upper installed tap-off','Lower installed tap-off','Demonstration tap-off','Plug-in outlets and location guides','Riser mounting spine'])assert(names.some(n=>n.startsWith(name)),name+' missing from connected-system sequence')}
 if(product.slug==='feeder'&&variant.key===''){assert(Math.abs(size.x-1.000)<.002,'1000 mm feeder including terminals');assert(Math.abs(size.z-.150)<.003,'150 mm flange width')}
 report.push({product:product.name,variant:variant.label,file:variant.file,components:components.length,meshes,metreBounds:size.toArray(),bytes:file.length});
}
await writeFile('public/models/validation.json',JSON.stringify(report,null,2));
console.log(JSON.stringify({families:catalog.length,assemblies:report.length,meshes:report.reduce((a,r)=>a+r.meshes,0),result:'All GLBs parsed; finite geometry, source files, reference images and key component counts verified'}));
