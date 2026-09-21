"""MEGADUCT photo reconstruction. Blender --background --python this_file -- --render.
Authored in dm under a .1 root, exported in metres. Unlabelled sizes estimated.
"""
import bpy, bmesh, math, json, sys, argparse, shutil
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'viewer/public/models';BLENDS=ROOT/'blender/products';REFS=ROOT/'viewer/public/references/brochure';RENDERS=ROOT/'viewer/public/renders'
for p in (OUT,BLENDS,REFS,RENDERS):p.mkdir(parents=True,exist_ok=True)
ap=argparse.ArgumentParser();ap.add_argument('--only',default='');ap.add_argument('--render',action='store_true')
ARGS=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
H=1.84;W=1.5;PACK=.52;T=.022;R=None;M={}

def clear():
 global R,M
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for d in list(bpy.data.meshes):
  if not d.users:bpy.data.meshes.remove(d)
 R=bpy.data.objects.new('MEGADUCT photo reconstruction',None);bpy.context.collection.objects.link(R);R.scale=(.1,)*3;R['revision']='Brochure rebuild 2026-09-17'
 M={}
 for key,color,metal in [('steel',(.55,.59,.65),.65),('edge',(.40,.45,.51),.7),('silver',(.72,.76,.80),.8),('core',(.55,.235,.10),.75),('epoxy',(.022,.027,.036),.05),('blue',(.025,.10,.39),.1),('gold',(.55,.40,.11),.75),('black',(.018,.023,.028),.05),('yellow',(.95,.75,.035),0),('red',(.72,.025,.014),.1),('white',(.69,.72,.72),0),('screen',(.6,.69,.65),.05)]:
  m=bpy.data.materials.new(key);m.diffuse_color=(*color,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=.34 if metal else .48;M[key]=m
 bpy.context.scene.unit_settings.system='METRIC'

def group(name,kind='enclosure',delta=(0,0,0),desc='',material='Formed steel / aluminium'):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.parent=R
 o['kind']=kind;o['delta']=[v*.1 for v in delta];o['material']=material;o['description']=desc or name;o['component']=True
 return o

def finish(o,name,mat,parent,bevel=.006):
 o.name=name;o.parent=parent;o.data.materials.append(M[mat])
 if bevel:
  m=o.modifiers.new('Formed edge radius','BEVEL');m.width=bevel;m.segments=2
 return o

def mesh(name,verts,faces,parent,mat='steel',bevel=.006):
 data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update();bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
 o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);return finish(o,name,mat,parent,bevel)

def box(name,size,loc,parent,mat='steel',bevel=.006):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,mat,parent,bevel)

def cyl(name,r,depth,loc,parent,mat='gold',axis=(0,0,1),n=20):
 bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=depth,location=loc);o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector(axis).to_track_quat('Z','Y');return finish(o,name,mat,parent,.002)

def tube(name,ro,ri,depth,loc,parent,mat='silver',axis=(0,0,1)):
 axis=Vector(axis).normalized();u=axis.cross(Vector((1,0,0)))
 if u.length<.1:u=axis.cross(Vector((0,1,0)))
 u.normalize();v=axis.cross(u);c=Vector(loc);vs=[];fs=[];n=24
 for z,r in [(-depth/2,ro),(depth/2,ro),(-depth/2,ri),(depth/2,ri)]:
  for i in range(n):vs.append(c+axis*z+r*(u*math.cos(i*math.tau/n)+v*math.sin(i*math.tau/n)))
 for i in range(n):
  j=(i+1)%n
  for a,b in [(0,n),(2*n,3*n),(0,2*n),(n,3*n)]:fs.append((a+i,a+j,b+j,b+i))
 return mesh(name,vs,fs,parent,mat,.001)

def subtract(o,cut):
 bpy.context.view_layer.update();m=o.modifiers.new('True opening','BOOLEAN');m.object=cut;m.operation='DIFFERENCE';bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cut,do_unlink=True)

def drill(o,loc,r=.045,depth=.3,axis=(0,0,1)):
 subtract(o,cyl('drill cutter',r,depth,loc,o.parent,'black',axis,24))

def bolt(p,loc,axis=(0,0,1),r=.029):
 a=Vector(axis);v=Vector(loc);cyl('Hex fixing',r,.024,v+a*.014,p,'gold',axis,6);tube('Captive washer',r*1.23,r*.45,.006,v,p,'silver',axis)

def frames(path,plane):
 ps=[Vector(v) for v in path];ds=[(b-a).normalized() for a,b in zip(ps,ps[1:])];ns=[Vector((-d.y,d.x,0)) if plane=='xy' else Vector((-d.z,0,d.x)) for d in ds];out=[]
 for i in range(len(ps)):
  if i==0:m=ns[0]
  elif i==len(ps)-1:m=ns[-1]
  else:m=(ns[i-1]+ns[i]).normalized();m=m/max(.1,m.dot(ns[i]))
  out.append((m,Vector((0,0,1))) if plane=='xy' else (Vector((0,1,0)),m))
 return ps,out

def rect(a,b,c,d):return [(a,c),(b,c),(b,d),(a,d)]

def sweep(name,path,profile,p,mat='steel',plane='xy',bevel=.006):
 ps,fs=frames(path,plane);n=len(profile);vs=[]
 for c,(a,b) in zip(ps,fs):vs.extend(c+a*u+b*v for u,v in profile)
 faces=[tuple(reversed(range(n))),tuple((len(ps)-1)*n+i for i in range(n))]
 for k in range(len(ps)-1):
  for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
 return mesh(name,vs,faces,p,mat,bevel)

def coat(path,u,h,p,plane):
 ps,fs=frames(path,plane);outer=rect(u-.043,u+.043,-h/2,h/2);inner=rect(u-.035,u+.035,-h/2+.008,h/2-.008);vs=[];faces=[]
 for c,(a,b) in zip(ps,fs):vs.extend(c+a*x+b*y for x,y in outer+inner)
 for k in range(len(ps)-1):
  for j in range(4):
   jj=(j+1)%4;faces.extend([(k*8+j,k*8+jj,(k+1)*8+jj,(k+1)*8+j),(k*8+4+j,(k+1)*8+4+j,(k+1)*8+4+jj,k*8+4+jj)])
 for k in (0,len(ps)-1):
  for j in range(4):faces.append((k*8+j,k*8+(j+1)%4,k*8+4+(j+1)%4,k*8+4+j))
 return mesh('Thin hollow epoxy coat',vs,faces,p,'epoxy',.001)

def cover(s,h):
 pts=[(-.75,h/2+.105),(-.61,h/2+.105),(-.61,h/2),(.61,h/2),(.61,h/2+.105),(.75,h/2+.105),(.75,h/2+.127),(.588,h/2+.127),(.588,h/2+.022),(-.588,h/2+.022),(-.588,h/2+.127),(-.75,h/2+.127)]
 return [(a,b*s) for a,b in pts]

def terminal(end,neighbor,plane,p,h=H):
 end=Vector(end);d=(end-Vector(neighbor)).normalized();n=Vector((-d.y,d.x,0)) if plane=='xy' else Vector((0,1,0));b=Vector((0,0,1)) if plane=='xy' else d.cross(n).normalized()
 if plane=='xy' and (n.y<-.1 or (abs(n.y)<.1 and n.x<0)):n=-n
 for i in range(5):
  inner=(i-2)*.094;outer=(i-2)*.15;cs=[end-d*.06+n*inner,end+d*.18+n*inner,end+d*.39+n*outer,end+d*.82+n*outer];vs=[]
  for c in cs:vs.extend([c-n*.036-b*(h-.12)/2,c+n*.036-b*(h-.12)/2,c+n*.036+b*(h-.12)/2,c-n*.036+b*(h-.12)/2])
  fs=[(3,2,1,0),(12,13,14,15)]
  for k in range(3):
   for j in range(4):fs.append((4*k+j,4*k+(j+1)%4,4*(k+1)+(j+1)%4,4*(k+1)+j))
  mesh(f'Blade {i+1} plated spread terminal',vs,fs,p,'silver',.009)

def route(path,plane='xy',prefix='',h=H,ends=True,conductors=True):
 top=group(prefix+'Upper folded cover',delta=(0,0,.8));bot=group(prefix+'Lower folded cover',delta=(0,0,-.8))
 sweep('Continuous folded upper profile',path,cover(1,h),top,plane=plane);sweep('Continuous folded lower profile',path,cover(-1,h),bot,plane=plane)
 for s in (-1,1):
  p=group(prefix+('Near' if s<0 else 'Far')+' recessed side skin',delta=(0,s*.85,0));sweep('Recessed side sheet',path,rect(s*PACK/2-T/2,s*PACK/2+T/2,-h/2,h/2),p,plane=plane)
 ps,_=frames(path,plane)
 for a,b in zip(ps,ps[1:]):
  d=(b-a).normalized();length=(b-a).length;n=Vector((-d.y,d.x,0)) if plane=='xy' else Vector((0,1,0));up=Vector((0,0,1)) if plane=='xy' else d.cross(n)
  for t in [.20,length-.20]+([length/2] if length>3 else []):
   for side in (-1,1):
    for s,g in [(1,top),(-1,bot)]:bolt(g,a+d*t+n*side*.18+up*s*(h/2+.034),up*s,.022)
  for t in (.13,.36,.58):
   if t>=length:continue
   for base,sign in [(a,1),(b,-1)]:
    for side in (-1,1):cyl('Rail fixing recess',.018,.003,base+d*t*sign+n*.46*side+up*(h/2+.025),top,'black',up,16)
 if conductors:
  for i in range(5):
   u=(i-2)*.094;c=group(prefix+f'Conductor {i+1}','conductor',(0,(i-2)*.25,0),'Continuous schematic route; ordered section and phase assignment unverified.','Copper / aluminium core')
   sweep('Conductor core',path,rect(u-.035,u+.035,-h/2+.095,h/2-.095),c,'core',plane,.002)
   p=group(prefix+f'Epoxy coating {i+1}','insulation',(0,(i-2)*.34,.28),material='Thin epoxy coating');coat(path,u,h-.17,p,plane)
 if ends:
  for end,near,label in [(path[0],path[1],'A'),(path[-1],path[-2],'B')]:
   p=group(prefix+'Terminal stack '+label,'connection',tuple((Vector(end)-Vector(near)).normalized()*.5),material='Tin / silver plated contacts');terminal(end,near,plane,p,h)

def prism(name,poly,z,thick,p,mat='steel',plane='xy'):
 n=len(poly);vs=[(a,b,z+s*thick/2) if plane=='xy' else (a,z+s*thick/2,b) for s in (-1,1) for a,b in poly]
 return mesh(name,vs,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],p,mat)

def warning(p,loc,size=(.65,.34)):
 x,y,z=loc;w,h=size;box('Yellow danger label',(w,h,.006),loc,p,'yellow',.001);box('Black warning header',(w*.93,h*.18,.003),(x,y+h*.32,z+.005),p,'black',0)
 mesh('Hazard triangle',[(x-w*.41,y-h*.32,z+.008),(x-w*.11,y-h*.32,z+.008),(x-w*.26,y+h*.16,z+.008)],[(0,1,2)],p,'red',0)
 for i in range(3):box('Label text line',(w*.42,.012,.002),(x+w*.15,y-i*.04,z+.008),p,'black',0)

def straight(length=10,plug=False,packs=1):
 length-=1.64  # Specified overall length includes the two 82 mm contact projections.
 for i in range(packs):
  before=set(bpy.context.scene.objects);route([(-length/2,0,0),(length/2,0,0)],prefix=f'Pack {i+1} · ' if packs>1 else '')
  for o in set(bpy.context.scene.objects)-before:
   if o.parent==R:o.location.y+=(i-(packs-1)/2)*1.50
 if plug:
  for x in (-3,3):
   p=group('Plug-in outlet '+str(x*100)+' mm','protection',(0,0,.5),material='Moulded outlet and metal shutter');box('Blue outlet block',(.86,.57,.08),(x,0,H/2+.07),p,'blue')
   for j in range(5):box('Contact access slot',(.08,.10,.009),(x+(j-2)*.13,0,H/2+.116),p,'black')
   box('Closed hinged shutter',(1.05,1.05,.045),(x,0,H/2+.16),p);cyl('Shutter hinge',.026,1,(x-.52,0,H/2+.16),p,'silver',(0,1,0));warning(p,(x,0,H/2+.189))

def hood(p,loc,size):
 x,y,z=loc;l,w,h=size;box('Removable hood top',(l,w,T),(x,y,z+h/2),p)
 for s in (-1,1):box('Hood side panel',(l,T,h),(x,y+s*w/2,z),p)
 for xx in (-l*.42,0,l*.42):
  for yy in (-w*.42,w*.42):bolt(p,(x+xx,y+yy,z+h/2+.02))

def hood_end(p,x,w,h):
 # Close the end around the narrow busduct neck instead of leaving a hollow tunnel.
 for s in (-1,1):box('Hood end side infill',(T,(w-PACK)/2,h),(x,s*(w+PACK)/4,0),p)
 for s in (-1,1):box('Hood end upper lower infill',(T,PACK,(h-H)/2),(x,0,s*(h+H)/4),p)

def tee(flat=False):
 a=3.2;b=3.1
 if flat:
  poly=[(-a,-H/2),(a,-H/2),(a,H/2),(H/2,H/2),(H/2,b),(-H/2,b),(-H/2,H/2),(-a,H/2)]
  for s in (-1,1):p=group(('Near' if s<0 else 'Far')+' continuous T side',delta=(0,s*.8,0));prism('T-shaped side sheet',poly,s*PACK/2,T,p,plane='xz')
  for j,aa in enumerate(poly):
   bb=poly[(j+1)%len(poly)]
   if (aa[0]==bb[0] and abs(aa[0])==a) or aa[1]==bb[1]==b:continue
   p=group(f'Folded T edge {j}',delta=(0,0,.6 if aa[1]+bb[1]>0 else -.6));va=Vector((aa[0],0,aa[1]));vb=Vector((bb[0],0,bb[1]));d=vb-va
   o=box('Perimeter flange',(d.length,1.5,T),(va+vb)/2,p);o.rotation_euler.y=-math.atan2(d.z,d.x)
   for s in (-1,1):o=box('Flange return',(d.length,T,.09),(va+vb)/2+Vector((0,s*.72,0)),p);o.rotation_euler.y=-math.atan2(d.z,d.x)
  paths=[[(-a,0,0),(a,0,0)],[(0,0,0),(0,0,b)]];ends=[(-a,0,0),(a,0,0),(0,0,b)];plane='xz'
 else:
  poly=[(-a,-.75),(a,-.75),(a,.75),(.75,.75),(.75,b),(-.75,b),(-.75,.75),(-a,.75)]
  for s in (-1,1):
   p=group(('Upper' if s>0 else 'Lower')+' T cover',delta=(0,0,s*.8));prism('T-shaped cover',poly,s*H/2,T,p)
   for j,aa in enumerate(poly):
    bb=poly[(j+1)%len(poly)]
    if (aa[0]==bb[0] and abs(aa[0])==a) or aa[1]==bb[1]==b:continue
    va=Vector((*aa,s*(H/2+.06)));vb=Vector((*bb,s*(H/2+.06)));o=box('Folded perimeter lip',((vb-va).length,T,.12),(va+vb)/2,p);o.rotation_euler.z=math.atan2(vb.y-va.y,vb.x-va.x)
  poly=[(-a,-PACK/2),(a,-PACK/2),(a,PACK/2),(PACK/2,PACK/2),(PACK/2,b),(-PACK/2,b),(-PACK/2,PACK/2),(-a,PACK/2)];p=group('Recessed T side skins',delta=(0,-.8,0))
  for j,aa in enumerate(poly):
   bb=poly[(j+1)%len(poly)]
   if (aa[0]==bb[0] and abs(aa[0])==a) or aa[1]==bb[1]==b:continue
   va=Vector((*aa,0));vb=Vector((*bb,0));o=box('T side skin',((vb-va).length,T,H),(va+vb)/2,p);o.rotation_euler.z=math.atan2(vb.y-va.y,vb.x-va.x)
  p=group('Raised central tee cover',delta=(0,0,1.2))
  box('Raised tee top',(2.65,2.05,T),(0,.40,H/2+.24),p)
  for s in (-1,1):
   a1=Vector((s*1.325,.40,H/2+.24));b1=Vector((s*1.62,.40,H/2));d=b1-a1;o=box('Tee sloping cover transition',(d.length,2.05,T),(a1+b1)/2,p);o.rotation_euler.y=-math.atan2(d.z,d.x)
  for y in (-.625,1.425):box('Tee raised cover return',(2.65,T,.24),(0,y,H/2+.12),p)
  paths=[[(-a,0,0),(a,0,0)],[(0,0,0),(0,b,0)]];ends=[(-a,0,0),(a,0,0),(0,b,0)];plane='xy'
 for i in range(5):
  p=group(f'T branch conductor {i+1}','conductor',(0,(i-2)*.25,0),'Branch connection is schematic; internal joint is not visible.','Insulated conductor')
  for path in paths:sweep('Schematic T conductor',path,rect((i-2)*.094-.04,(i-2)*.094+.04,-H/2+.09,H/2-.09),p,'epoxy',plane)
 for i,end in enumerate(ends):p=group(f'Terminal stack {i+1}','connection',tuple(Vector(end).normalized()*.5),material='Plated contact');terminal(end,(0,0,0),plane,p)

def end_cover():
 p=group('Folded end cap',delta=(-.5,0,0))
 for s in (-1,1):
  o=box('Cap face',(1.75,1.56,T),(0,0,s*H/2),p)
  for yy in (-.64,.64):drill(o,(.55,yy,s*H/2))
  for yy in (-.78,.78):box('Cap return lip',(1.75,T,.08),(0,yy,s*(H/2-.04)),p)
 box('Cap back',(T,1.56,H),(-.875,0,0),p);p=group('Separate closing insert','protection',(.7,0,0),material='Folded closing plate');box('Inset end plate',(T,.85,H-.05),(.68,0,0),p,'edge')
 for yy in (-.425,.425):box('Insert fold',(.14,T,H-.05),(.62,yy,0),p,'edge')

def flange(cable=False):
 route([(0,0,0),(0,0,2.6)],'xz',ends=False);p=group('Upper terminal stack','connection',(0,0,.6),material='Plated contacts');terminal((0,0,2.6),(0,0,0),'xz',p)
 p=group('Equipment mounting flange',delta=(0,0,-.4));o=box('Mounting flange',(H+.75,2,.06),(0,0,0),p);subtract(o,box('throat',(H,PACK,1),(0,0,0),p,'black',0))
 for x in (-1.05,1.05):
  for y in (-.8,0,.8):drill(o,(x,y,0),.05);bolt(p,(x,y,.045))
 p=group('Spread drilled lugs','connection',(0,0,-.7),material='Plated terminals')
 for i in range(5):
  y=(i-2)*.29;o=box(f'Cable lug {i+1}',(1.15,.07,1.7),(0,y,-.90),p,'silver')
  for x in (-.32,.32):
   for z in (-1.30,-.82):drill(o,(x,y,z),.075,.3,(0,1,0))
 if cable:
  p=group('Cable termination box',delta=(0,-.7,0));box('Box base',(3.8,3.2,T),(0,0,-4.15),p)
  for s in (-1,1):box('Box side',(T,3.2,4.1),(s*1.9,0,-2.1),p)
  for s in (-1,1):
   p=group(('Front' if s<0 else 'Rear')+' removable panel',delta=(0,s*.85,0));box('Removable panel',(3.8,T,4.1),(0,s*1.6,-2.1),p)
   for x in (-1.65,1.65):
    for z in (-3.85,-2.1,-.35):bolt(p,(x,s*1.625,z),(0,s,0))
  p=group('Cable box top',delta=(0,0,.5));o=box('Top sheet',(3.8,3.2,T),(0,0,-.05),p);subtract(o,box('throat',(H,PACK,.5),(0,0,0),p,'black',0))
  for s in (-1,1):box('Neck reinforcing angle',(H+.9,.04,.20),(0,s*.85,.08),p)

def wall_flange():
 for s in (-1,1):
  p=group(('Left' if s<0 else 'Right')+' split wall flange',delta=(0,s*.65,0));o=box('Split plate',(.035,1.5,3.2),(0,s*.75,0),p)
  for size,loc in [((.5,1.6,.32),(0,0,.94)),((.5,1.6,.32),(0,0,-.94)),((.5,.59,1.9),(0,0,0))]:subtract(o,box('I-cutout',size,loc,p,'black',0))
  for y,z in [(s*1.23,-1.32),(s*.33,-1.32),(s*1.23,0),(s*1.23,1.32),(s*.33,1.32)]:drill(o,(0,y,z),.075,.3,(1,0,0))

def reducer():
 route([(-3.18,0,-.22),(-.4,0,-.22)],h=1.4,ends=False);route([(.4,0,0),(3.18,0,0)],ends=False);p=group('Sloped reducer transition',delta=(0,0,.6))
 for s in (-1,1):
  a=Vector((-.4,0,-.22+s*.7));b=Vector((.4,0,s*H/2));d=b-a;o=box('Sloped cover',(d.length,1.5,T),(a+b)/2,p);o.rotation_euler.y=-math.atan2(d.z,d.x)
 for s in (-1,1):prism('Reducer side',[(-.4,-.92),(.4,-.92),(.4,.92),(-.4,.48)],s*PACK/2,T,p,plane='xz')
 for end,near,h in [((-3.18,0,-.22),(0,0,-.22),1.4),((3.18,0,0),(0,0,0),H)]:p=group('Reducer plated end','connection',tuple((Vector(end)-Vector(near)).normalized()*.5),material='Plated contact');terminal(end,near,'xy',p,h)

def specialist(expansion=False):
 half=5.18 if expansion else 4.68;route([(-half,0,0),(-2.65,0,0)],ends=False,conductors=False);route([(2.65,0,0),(half,0,0)],ends=False,conductors=False)
 for s in (-1,1):p=group('Specialist terminal','connection',(s*.5,0,0),material='Plated contact');terminal((s*half,0,0),(0,0,0),'xy',p)
 if expansion:
  for s in (-1,1):p=group(('Left' if s<0 else 'Right')+' expansion hood',delta=(s*.6,0,.5));hood(p,(s*1.55,0,0),(2.72,2.75,2.50));hood_end(p,s*2.91,2.75,2.50)
  p=group('Corrugated centre','protection',(0,-.8,0),'Exterior corrugation only; hidden flexible links omitted.','Unverified flexible cover material')
  for x in (-.24,-.12,0,.12,.24):
   for y in (-1.36,1.36):box('Side rib',(.07,.06,2.45),(x,y,0),p,'black')
   for z in (-1.24,1.24):box('Upper lower rib',(.07,2.75,.07),(x,0,z),p,'black')
 else:
  p=group('Wide transposition chamber',delta=(0,0,.8),desc='Exterior only; phase crossings cannot be derived from the photograph.');hood(p,(0,0,0),(5.3,2.6,2.25))
  for s in (-1,1):hood_end(p,s*2.65,2.6,2.25)
  for s in (-1,1):box('Lower chamber flange',(5.3,.22,.06),(0,s*1.33,-1.12),p)

def helix(p,loc):
 c=Vector(loc);curve=bpy.data.curves.new('Helical spring','CURVE');curve.dimensions='3D';curve.bevel_depth=.022;curve.bevel_resolution=3;s=curve.splines.new('POLY');s.points.add(240)
 for i,pt in enumerate(s.points):t=i/240;pt.co=(*(c+Vector((.12*math.cos(t*20*math.pi),.12*math.sin(t*20*math.pi),.96*(t-.5)))),1)
 o=bpy.data.objects.new('Compression spring - ten turns',curve);bpy.context.collection.objects.link(o);o.parent=p;o.data.materials.append(M['gold']);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')

def support(spring=False,wall=False):
 route([(0,0,-2.2),(0,0,4.8)],'xz');p=group('Building C channels','support',(0,0,-.6),material='Structural channels by others')
 for x in (-1.28,1.28):
  box('Channel web',(.055,3.5,.34),(x,0,-.35),p,'edge')
  for z in (-.52,-.18):box('Channel flange',(.36,3.5,.045),(x,0,z),p,'edge')
  if wall:
   box('Wall anchor plate',(.68,.08,1.5),(x,1.78,-.82),p)
   for z in (-.40,-1.3):bolt(p,(x,1.84,z),(0,1,0),.055)
 p=group('Riser restraint collar','support',(0,0,.55),material='Folded steel; M6 × 20 screws shown')
 for s in (-1,1):
  box('Clamping cheek',(H+.05,.045,1.35),(0,s*.80,.78),p);box('Upper bearing angle',(H+.60,.40,.055),(0,s*.93,1.17 if spring else .30),p)
  for x in (-.68,.68):
   for z in (.5,1.1):bolt(p,(x,s*.83,z),(0,s,0))
 p=group('Lower bearing plates','support',(0,0,-.25))
 for s in (-1,1):box('Cross plate',(2.65,.43,.07),(0,s*.96,.05),p)
 for x in (-1.04,1.04):
  for y in (-.97,.97):
   p=group('Spring station' if spring else 'Fixed stud','support',(0,0,.35),material='Passivated steel');cyl('Guide stud',.035,1.30 if spring else .45,(x,y,.65 if spring else .22),p)
   for z in (.12,1.20 if spring else .34):bolt(p,(x,y,z),r=.07);tube('Load washer',.13,.04,.028,(x,y,z-.025),p)
   if spring:helix(p,(x,y,.66))

def horizontal():
 route([(-9,0,0),(9,0,0)])
 for x in (-7.5,7.5):
  p=group('Horizontal support station','support',(0,0,-.5),material='M10 rods, L-channel and folded clips');box('Bearing channel',(.12,2.30,.10),(x,0,-H/2-.23),p,'edge');box('Channel leg',(.10,2.30,.25),(x+.10,0,-H/2-.32),p,'edge')
  for y in (-1.02,1.02):
   cyl('M10 hanger rod',.05,3.4,(x,y,.49),p)
   for z in (-H/2-.29,-H/2-.12):bolt(p,(x,y,z),r=.08)
  for y in (-.68,.68):box('Clip toe',(.36,.24,.04),(x,y,-H/2+.025),p);box('Clip downstand',(.36,.04,.16),(x,y+(.12 if y>0 else -.12),-H/2-.035),p)

def tapoff(kind='single',entry='bottom'):
 sx,sy,sz=3.5,2.5,2.3;p=group('Tap-off folded body',delta=(0,0,-.45));box('Rear mounting panel',(sx,sy,T),(0,0,-sz/2),p)
 for s in (-1,1):box('End sheet',(T,sy,sz),(s*sx/2,0,0),p);box('Side sheet',(sx,T,sz),(0,s*sy/2,0),p)
 p=group('Overhanging lid',delta=(0,0,.9));box('Lid sheet',(sx+.12,sy+.12,.035),(0,0,sz/2+.035),p)
 for s in (-1,1):box('Lid long return',(sx+.12,.028,.09),(0,s*(sy/2+.045),sz/2-.005),p);box('Lid end return',(.028,sy+.12,.09),(s*(sx/2+.045),0,sz/2-.005),p)
 for x in (-1.1,1.1):bolt(p,(x,.78,sz/2+.062),r=.033)
 warning(p,(-1.08,-.71,sz/2+.058),(.85,.46))
 sign=-1 if entry=='bottom' else 1;x=sign*(sx/2+.015);p=group('Cable entry '+entry+' plate','connection',(sign*.5,0,0),'Removable gland plate. Hole positions are project-specific.','Sheet metal');box('Gland plate',(.025,sy*.74,sz*.68),(x,0,-.05),p)
 for y in (-.77,.77):
  for z in (-.7,.6):bolt(p,(x+sign*.015,y,z),(sign,0,0),.025)
 p=group('External '+kind+' control','protection',(0,-.5,.3),material='Operating handle and interface')
 if kind in ('single','double'):
  for y in ([-sy/2-.1] if kind=='single' else [-sy/2-.1,sy/2+.1]):
   s=1 if y>0 else -1;box('Pivot plate',(.36,.06,.64),(.14,y,0),p);cyl('Pivot',.08,.09,(.14,y+s*.05,.1),p,'gold',(0,1,0));box('Long lever',(1.66,.07,.17),(.94,y+s*.07,.32),p);box('Lever return',(.10,.27,.17),(1.70,y-s*.035,.32),p)
   mesh('Red position triangle',[(-.05,y+s*.012,.12),(.36,y+s*.012,.12),(.16,y+s*.012,.66)],[(0,1,2)],p,'red',0);o=box('Lock tab',(.37,.05,.17),(-.12,y+s*.07,-.22),p);drill(o,(-.18,y+s*.07,-.22),.036,.3,(0,1,0))
 else:
  box('Switch escutcheon',(.85,.75,.055),(.37,.16,sz/2+.09),p,'black')
  if kind=='rotary':cyl('Rotary base',.25,.10,(.37,.16,sz/2+.17),p,'red');box('Red rotary grip',(.43,.14,.25),(.37,.16,sz/2+.29),p,'red',.03)
  else:
   box('Black outlet control',(.25,.18,.25),(.37,.16,sz/2+.25),p,'black');box('Display bezel',(.61,.53,.06),(-.60,-.12,sz/2+.10),p,'black');box('Display face',(.49,.37,.012),(-.60,-.08,sz/2+.139),p,'screen')
   for xx in (-.76,-.62):cyl('Display button',.031,.015,(xx,-.33,sz/2+.15),p,'red')
 p=group('Plug-in fingers and earth clips','connection',(0,0,-.8),'Contact fingers and separate earth clips from bottom-view diagram.','Plated contacts')
 for i in range(5):
  y=(i-2)*.22
  for s in (-1,1):sweep('Contact finger',[(0,y+s*.07,-1.13),(0,y+s*.07,-1.48),(0,y+s*.045,-1.64),(0,y+s*.08,-1.72)],rect(-.16,.16,-.016,.016),p,'silver','xz')
 for x in (-1.36,1.36):box('Earth clip',(.22,.4,.06),(x,0,-1.2),p,'gold');box('Earth return',(.07,.4,.35),(x,0,-1.36),p,'gold')
 p=group('Self-interlocking clamps','support',(0,.5,-.2),material='Passivated clamp steel')
 for x in (-1.3,1.3):
  for y in (-.9,.9):box('Interlocking clamp',(.18,.32,.08),(x,y,-1.18),p,'gold')

def joint():
 def layer(name,y,t,mat,w=2.9,h=1.84,kind='connection'):
  p=group(name,kind,(0,y*2,0),material=mat);o=box('Layer plate',(w,t,h),(0,y,0),p,mat)
  for x in (-.88,.88):drill(o,(x,y,0),.09,2.5,(0,1,0))
  return p
 for i in range(6):layer('Joint phase insulator '+str(i+1),(i-2.5)*.14,.035,'blue',3.02,1.93,'insulation')
 for i in range(5):layer('Joint conductor bar '+str(i+1),(i-2)*.14,.055,'silver',2.87,1.74)
 for s in (-1,1):
  layer('Joint end insulator',s*.47,.06,'blue',3.05,1.96,'insulation');p=layer('Joint backing plate',s*.57,.07,'steel',3.18,1.92)
  for z in (-.69,.69):box('Pressed stiffening rib',(3.1,.12,.11),(0,s*.60,z),p)
 layer('Joint Earth Bar',-.425,.025,'core',2.95,1.78)
 for x in (-.88,.88):
  p=group('Joint bolt','connection',(0,-4.4,0),material='Steel bolt');cyl('Long bolt shaft',.06,1.64,(x,0,0),p,'gold',(0,1,0));cyl('Bolt hex head',.14,.10,(x,-.87,0),p,'gold',(0,1,0),6)
  p=group('Fiber tube','insulation',(0,-3.0,0),material='Fibre insulating tube');tube('Hollow fibre tube',.087,.063,1.23,(x,0,0),p,'white',(0,1,0))
  for s in (-1,1):p=group('Belleville disc','connection',(0,s*1.35,0),material='Spring steel disc');tube('Annular spring disc',.26,.085,.055,(x,s*.70,0),p,'silver',(0,1,0))
  p=group('Nylon lock nut','connection',(0,2.1,0),material='Steel nut and nylon insert');o=cyl('Hex nut',.13,.13,(x,.87,0),p,'gold',(0,1,0),6);drill(o,(x,.87,0),.062,.4,(0,1,0));tube('Nylon insert',.092,.062,.025,(x,.946,0),p,'white',(0,1,0))

def ip_assembly(outdoor=False):
 route([(-6,0,0),(-.12,0,0)],ends=False);route([(.12,0,0),(6,0,0)],ends=False);joint()
 for s in (-1,1):p=group('Exposed run contact','connection',(s*.5,0,0),material='Plated contact');terminal((s*6,0,0),(0,0,0),'xy',p)
 p=group('Upper joint cover',delta=(0,0,.85));box('Joint cover',(3.7,2.10,.04),(0,0,H/2+.15),p);warning(p,(0,0,H/2+.174),(.86,.43))
 for x in (-1.5,1.5):
  for y in (-.64,.64):bolt(p,(x,y,H/2+.19),r=.045)
 p=group('Lower joint cover',delta=(0,0,-.7));box('Joint underside',(3.7,2.10,.04),(0,0,-H/2-.12),p)
 for s in (-1,1):
  p=group('Joint side cover',delta=(0,s*.8,0));box('Side cover',(3.7,.04,H+.16),(0,s*1.04,0),p);p=group('Joint gasket','insulation',(0,s*.52,0),material='Gasket / sealant interface')
  for z in (-H/2,H/2):box('Gasket edge',(3.7,.022,.033),(0,s*1.015,z),p,'black')
 if outdoor:
  for x in (-3.08,3.08):p=group('Outdoor external cover',delta=(0,0,1.35),desc='Additional outer weather cover shown in outdoor reference.');hood(p,(x,0,.02),(6.05,2.3,H+.65))
  p=group('External cover overlap',delta=(0,0,1.65));hood(p,(0,0,.025),(.45,2.39,H+.74))

def installed_tapoff():
 route([(0,0,-4.7),(0,0,4.7)],'xz')
 before=set(bpy.context.scene.objects);tapoff()
 rot=Matrix(((0,-1,0),(0,0,-1),(1,0,0)))
 for o in set(bpy.context.scene.objects)-before:
  if o.parent==R:o.rotation_euler=rot.to_euler();o.location.y=-1.66;o['delta']=list(rot@Vector(o['delta']))
 p=group('Spare plug-in outlet','protection',(0,-.5,0),material='Moulded outlet block')
 box('Blue spare outlet',(1.3,.10,.8),(0,-.35,-3.15),p,'blue')
 for x in (-.42,-.21,0,.21,.42):box('Outlet access',( .09,.01,.35),(x,-.406,-3.15),p,'black')

def combination():
 route([(-3,0,0),(0,0,0),(0,.94,0)],'xy',ends=False)
 p=group('Compound entry','connection',(-.5,0,0),material='Plated contacts');terminal((-3,0,0),(0,0,0),'xy',p)
 before=set(bpy.context.scene.objects)
 route([(-1.46,0,0),(0,0,0),(0,0,3)],'xz',prefix='Rising leg · ',ends=False)
 p=group('Compound upper exit','connection',(0,0,.5),material='Plated contacts');terminal((0,0,3),(0,0,0),'xz',p)
 for o in set(bpy.context.scene.objects)-before:
  if o.parent==R:
   o.rotation_euler.z=math.pi/2;o.location.y=2.4
   dx,dy,dz=o['delta'];o['delta']=[-dy,dx,dz]

def connected_system():
 # Match the supplied vertical plug-in reference: one riser, two installed
 # tap-off boxes and a third unit demonstrating alignment with an outlet.
 route([(0,0,-8.2),(0,0,8.2)],'xz',prefix='Vertical plug-in riser · ')
 rot=Matrix(((0,-1,0),(0,0,-1),(1,0,0)))
 def add_tapoff(label,z,detached=False):
  before=set(bpy.context.scene.objects);tapoff('single')
  shift=Vector((-3.7,-3.35,z)) if detached else Vector((0,-1.66,z))
  attach=Vector((3.7,1.69,0)) if detached else Vector((0,0,0))
  for o in set(bpy.context.scene.objects)-before:
   if o.parent==R:
    o.name=label+' · '+o.name;o.rotation_euler=rot.to_euler();o.location+=shift;o['delta']=list(rot@Vector(o['delta']))
    if detached:o['demoAttach']=[attach.x*.1,attach.z*.1,-attach.y*.1]
 add_tapoff('Upper installed tap-off',3.45)
 add_tapoff('Lower installed tap-off',-.65)
 add_tapoff('Demonstration tap-off',-5.05,True)
 p=group('Plug-in outlets and location guides','protection',(0,-.45,0),'Moulded outlets and guide ports align each tap-off before contact engagement.','Moulded insulating outlet blocks')
 for z in (3.45,-.65,-5.05):
  box('Blue plug-in outlet',(1.18,.12,.72),(0,-.88,z),p,'blue')
  for x in (-.37,-.12,.12,.37):box('Outlet access',(.10,.025,.30),(x,-.955,z),p,'black')
  box('Location guide port',(.42,.34,.42),(0,-1.02,z-.67),p,'edge')
 p=group('Riser mounting spine','support',(0,.45,0),'Vertical support spine shown behind the plug-in busduct.','Galvanised support steel')
 for x in (-1.02,1.02):box('Continuous rear rail',(.08,.14,15.6),(x,.72,0),p,'edge')
 for z in (-6.8,-2.7,1.4,5.5):box('Rear cross tie',(2.12,.18,.12),(0,.72,z),p,'edge')

CAT=[]
def item(slug,name,photo,fn,facts,variants=[],label='Reference assembly'):CAT.append(dict(slug=slug,name=name,photo=photo,fn=fn,facts=facts,variants=variants,label=label))
item('feeder','Feeder','144637',straight,['Recessed I section; five spread plated contacts','1000 mm overall study length · 150 mm flange width','Catalogue: 3000 mm standard; 500 mm minimum'],[('standard','3000 mm standard length',lambda:straight(30),'144637'),('double-pack','Double pack section',lambda:straight(packs=2),'144709'),('triple-pack','Triple pack section',lambda:straight(packs=3),'144709')])
item('plug-in-feeder','Plug-In Busduct','144637',lambda:straight(15,True),['600 mm opening pitch on 1500 mm study sample','Catalogue: 3000 mm standard; 900 mm minimum','Maximum 4 front / 8 front and back openings'])
item('edgewise-elbow','Edgewise Elbow','145020',lambda:route([(-2.35,0,0),(0,0,0),(0,2.35,0)]),['Horizontal L profile','Continuous mitred folded flanges','310 mm dimension shown in reference'])
item('edgewise-offset','Edgewise Offset','145053',lambda:route([(-2.35,0,0),(0,0,0),(0,2.35,0),(2.35,2.35,0)]),['Horizontal Z profile','Three 310 mm dimensions shown in reference'])
item('edgewise-tee','Edgewise Tee','145024',tee,['Horizontal T branch','Raised central junction cover','Three open terminal stacks'])
item('flatwise-elbow','Flatwise Elbow','144835',lambda:route([(-3,0,0),(0,0,0),(0,0,3)],'xz'),['Vertical L profile','Continuous recessed L-shaped side sheets'])
item('flatwise-offset','Flatwise Offset','144845',lambda:route([(-3,0,0),(0,0,0),(0,0,2.8),(3,0,2.8)],'xz'),['Vertical Z profile','Two continuous flatwise direction changes'])
item('flatwise-tee','Flatwise Tee','144849',lambda:tee(True),['Vertical T branch','Continuous T-shaped side profile'])
item('flange-end','Flange End','144740',flange,['Equipment mounting flange','Spread lugs with through-holes'])
item('end-feed-box','End Feed Cable Box','144825',lambda:flange(True),['Hollow termination enclosure','Flanged neck; removable bolted panels'])
item('end-cover','End Cover','144940',end_cover,['Folded cap with separate insert','156 × 175 mm cover plan; variable height'])
item('combination-elbow','Combination Elbow','144930',combination,['Combined horizontal and vertical route','Internal compound transition is schematic'])
item('reducer','Reducer','145120',reducer,['Different end heights; sloping transition','800 mm overall study length'])
item('transposition','Phase Transposition Unit','145038',specialist,['1100 mm overall study length','Wide central chamber; hidden crossings omitted'])
item('expansion','Expansion Unit','145132',lambda:specialist(True),['Two bolted hoods and corrugated centre','Catalogue: 1200 (+25 mm)','Hidden flexible links omitted'])
item('tap-off','Tap-Off Unit','144450',tapoff,['External handle; hollow body and overhanging lid','Plug-in fingers, earth clips and clamps','Double handle specified above 300 A'],[('double-bottom','Double handle · bottom entry',lambda:tapoff('double'),'144450'),('single-top','Single handle · top entry',lambda:tapoff('single','top'),'144457'),('double-top','Double handle · top entry',lambda:tapoff('double','top'),'144457'),('rotary-bottom','Rotary · bottom entry',lambda:tapoff('rotary'),'144515'),('rotary-top','Rotary · top entry',lambda:tapoff('rotary','top'),'144518'),('outlet-bottom','Outlet · bottom entry',lambda:tapoff('outlet'),'144522'),('outlet-top','Outlet · top entry',lambda:tapoff('outlet','top'),'144525')])
CAT[-1]['variants'].append(('installed','Installed on vertical plug-in busduct',installed_tapoff,'145253'))
item('horizontal-support','Horizontal Support','145306',horizontal,['M10 rods; L-channel and flange clips','1500 mm support spacing'])
item('fixed-support','Vertical Fixed Support','145321',support,['Riser restraint and fixed bearing plates','C-channels supplied by others'],[('wall','Wall-mounted',lambda:support(wall=True),'145321')])
item('spring-support','Vertical Spring Hanger','145432',lambda:support(True),['Four helical compression springs','Guide rods, washers and bearing plates'],[('wall','Wall-mounted',lambda:support(True,True),'145500')])
item('joint','Joint Assembly','144436',joint,['Two insulated bolt axes','Nine named component types from the drawing','Blue phase and end insulators'])
item('wall-flange','Wall Flange','145002',wall_flange,['Two halves; I-shaped cut-out','300 mm overall width; height varies by section'])
item('indoor-joint','Indoor Joint Covers','144538',ip_assembly,['Top, bottom and side joint covers','Gasket interfaces','IP54–IP66 drawing; IP42 omits side cover'])
item('outdoor-cover','Outdoor External Cover','144553',lambda:ip_assembly(True),['Additional exterior weather shell','Overlap at joint','Outdoor IP66 reference construction'])
item('connected-system','Vertical Plug-In Connection Animation','145253',connected_system,['Vertical plug-in riser matched to the supplied reference','Two installed tap-off units plus one guided connection demonstration','Moving pulses show distribution direction, not literal AC electron motion'],label='Animated plug-in application sequence')

def render(slug):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;bpy.context.view_layer.update()
 vs=[o.matrix_world@Vector(c) for o in scene.objects if o.type=='MESH' for c in o.bound_box];lo=Vector(tuple(min(v[i] for v in vs) for i in range(3)));hi=Vector(tuple(max(v[i] for v in vs) for i in range(3)));center=(lo+hi)/2;span=max(hi-lo)
 bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.location=center+Vector((-1.35,-1.9,1.15)).normalized()*span*2.7;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO'
 inv=cam.rotation_euler.to_quaternion().inverted();projected=[inv@(v-center) for v in vs];pw=max(v.x for v in projected)-min(v.x for v in projected);ph=max(v.y for v in projected)-min(v.y for v in projected);cam.data.ortho_scale=max(pw,ph*720/560)*1.18
 for pos,power,size in [((-1,-1,2),80,2),((1,1,1),60,1.5),((0,-2,.5),30,1.5)]:
  bpy.ops.object.light_add(type='AREA',location=center+Vector(pos)*span);o=bpy.context.object;o.data.energy=power*span*span;o.data.shape='DISK';o.data.size=size*span;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
 scene.world.color=(.45,.45,.45);scene.view_settings.view_transform='AgX';scene.render.resolution_x=720;scene.render.resolution_y=560;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(RENDERS/(slug+'.png'));bpy.ops.render.render(write_still=True)

manifest=[]
for product in CAT:
 entry={k:v for k,v in product.items() if k not in ('fn','variants','label')};entry['variants']=[]
 for key,label,fn,photo in [('', product['label'],product['fn'],product['photo'])]+product['variants']:
  slug=product['slug']+('-'+key if key else '');entry['variants'].append(dict(key=key,label=label,file=slug+'.glb',blend=slug+'.blend',photo=photo+'.jpg',render=slug+'.png'))
  shutil.copy2(Path('/Users/crave/Downloads/Megaduct images')/('IMG20260917'+photo+'.jpg'),REFS/(photo+'.jpg'))
  if ARGS.only and slug not in ARGS.only.split(','):continue
  clear();fn();scene=bpy.context.scene;scene['source']='IMG20260917'+photo+'.jpg';scene['accuracy']='Photo reconstruction; unlabelled dimensions estimated; not manufacturing CAD';R['source']=scene['source'];R['product']=product['name']
  bpy.ops.object.select_all(action='DESELECT');R.select_set(True);bpy.context.view_layer.objects.active=R;bpy.context.preferences.filepaths.save_version=0
  bpy.ops.wm.save_as_mainfile(filepath=str(BLENDS/(slug+'.blend')))
  bpy.ops.export_scene.gltf(filepath=str(OUT/(slug+'.glb')),export_format='GLB',export_extras=True,export_apply=True,export_cameras=False,export_lights=False)
  if ARGS.render:render(slug)
  print('REBUILT '+slug,flush=True)
 manifest.append(entry)
(OUT/'catalog.json').write_text(json.dumps(manifest,indent=2))
print('Catalogue families:',len(manifest))
