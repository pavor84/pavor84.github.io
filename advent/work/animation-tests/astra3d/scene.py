import bpy, math, sys
from pathlib import Path
from mathutils import Vector, Quaternion
p=Path(__file__).resolve().parent
out=p.parents[2]/'outputs'
b=bpy; b.ops.wm.read_factory_settings(use_empty=True)
sc=b.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=1; sc.cycles.use_denoising=False
sc.cycles.device='CPU'; sc.render.resolution_x=1280; sc.render.resolution_y=720; sc.render.resolution_percentage=100
sc.render.fps=24;sc.frame_start=1;sc.frame_end=240
sc.view_settings.view_transform='Standard'; sc.render.image_settings.file_format='PNG'
def obj(name,verts,faces,uvs,mat):
 mesh=b.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(mat);mesh.update()
 uv=mesh.uv_layers.new()
 for polygon,ts in zip(mesh.polygons,uvs):
  for i,t in zip(polygon.loop_indices,ts):uv.data[i].uv=t
 o=b.data.objects.new(name,mesh);sc.collection.objects.link(o);return o
def xyz(x,y,z):return (x-440,247.5-y,z)
def img(path):
 return b.data.images.load(str(path),check_existing=True)
def mat(name,path,alpha=False):
 m=b.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;g=m.node_tree.links;n.clear()
 tx=n.new('ShaderNodeTexImage');tx.image=img(path);e=n.new('ShaderNodeEmission');g.new(tx.outputs['Color'],e.inputs[0]);o=n.new('ShaderNodeOutputMaterial')
 if alpha:
  t=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');g.new(tx.outputs['Alpha'],mix.inputs[0]);g.new(t.outputs[0],mix.inputs[1]);g.new(e.outputs[0],mix.inputs[2]);g.new(mix.outputs[0],o.inputs[0])
 else:g.new(e.outputs[0],o.inputs[0])
 return m
def rect(name,tex,bounds,z,alpha=False):
 x0,y0,x1,y1=bounds; ps=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
 return obj(name,[xyz(*t,z) for t in ps],[(0,1,2,3)],[[(0,1),(1,1),(1,0),(0,0)]],mat(name,tex,alpha))
cam=b.data.cameras.new('Locked orthographic lens');cam.type='ORTHO';cam.ortho_scale=880; cam.clip_end=2000
co=b.data.objects.new('Camera • locked full view',cam);sc.collection.objects.link(co);co.location=(0,0,800);sc.camera=co
plate=rect('Illustrated study • master projection',out/'dec01-i2v-first.png',(0,0,880,495),0)
# Slight dimensional roll across the greeting sleeve, skinned between shoulder and wrist.
im=img(p/'wave.png'); sx,sy,ex,ey=586.0,71.25,635.31,130.63
# Re-read measured opacity crop.
import json
if (p/'armbounds.json').exists():sx,sy,ex,ey=json.loads((p/'armbounds.json').read_text())
def to_screen(x,y):return(467+(x-589)*1.76,215+(y-105)*1.76)
wave_mat=mat('Fur and brocade • reference projection',p/'wave.png',True)
vs=[]; fs=[]; us=[]; influence=[]
for iy in range(13):
 v=iy/12
 for ix in range(9):
  u=ix/8;x=sx+(ex-sx)*u;y=sy+(ey-sy)*v;px,py=to_screen(x,y)
  vs.append(xyz(px,py,4+2*math.sin(math.pi*u)));influence.append((x,y))
for iy in range(12):
 for ix in range(8):
  k=iy*9+ix;fs.append((k,k+1,k+10,k+9));us.append([(ix/8,1-iy/12),((ix+1)/8,1-iy/12),((ix+1)/8,1-(iy+1)/12),(ix/8,1-(iy+1)/12)])
wave=obj('Greeting arm • weighted sleeve and paw',vs,fs,us,wave_mat)
arm=b.data.armatures.new('Greeting articulation'); rig=b.data.objects.new('Shoulder and wrist',arm);sc.collection.objects.link(rig);b.context.view_layer.objects.active=rig;rig.select_set(True);b.ops.object.mode_set(mode='EDIT')
pts=[to_screen(590,115),to_screen(605,102),to_screen(615,91),to_screen(624,77)]
bones=['Upper arm','Forearm','Wrist']
for i,n in enumerate(bones):
 bone=arm.edit_bones.new(n);bone.head=xyz(*pts[i],4);bone.tail=xyz(*pts[i+1],4)
 if i:bone.parent=arm.edit_bones[bones[i-1]];bone.use_connect=True
b.ops.object.mode_set(mode='OBJECT');mod=wave.modifiers.new('Soft joint deformation','ARMATURE');mod.object=rig
groups=[wave.vertex_groups.new(name=n) for n in bones]
for i,(x,y) in enumerate(influence):
 # Projection onto the shoulder-to-paw axis.
 t=((x-590)*.67-(y-115)*.73)
 sw=lambda x:max(0,min(1,x))
 a=sw((t-11)/14); c=sw((t-29)/13)
 for g,w in zip(groups,[1-a,a*(1-c),a*c]):
  if w>0:g.add([i],w,'REPLACE')
def bone_angle(pb,deg,frame):
 pb.rotation_mode='QUATERNION'; axis=pb.bone.matrix_local.to_3x3().inverted()@Vector((0,0,1));pb.rotation_quaternion=Quaternion(axis,math.radians(deg));pb.keyframe_insert('rotation_quaternion',frame=frame)
for f in range(1,241):
 t=(f-1)/24
 envelope=min(1,t/.6)*min(1,max(0,(6.9-t)/.65))
 cycle=math.sin(2*math.pi*t*.65)*envelope
 settling=max(0,min(1,(t-6.65)/1.05));settling=settling*settling*(3-2*settling)
 for n,a in zip(bones,[2*cycle-44*settling,4*cycle-37*settling,11*cycle-19*settling]):bone_angle(rig.pose.bones[n],a,f)

exec(compile((p/'finish.py').read_text(),str(p/'finish.py'),'exec'))
sc.render.resolution_percentage=75
for f in [12,171,181,193,203,217,239]:
 sc.frame_set(f);sc.render.filepath=str(p/f'proof-{f:03d}.png');b.ops.render.render(write_still=True)
# Re-openable camera scene, including every texture used by a material.
sc.render.resolution_percentage=100;sc.cycles.samples=4;sc.cycles.use_adaptive_sampling=False
sc.frame_set(1)
for o in sc.objects:o.select_set(False)
b.context.view_layer.objects.active=front
for ws in b.data.screens:
 for area in ws.areas:
  if area.type=='VIEW_3D':
   space=area.spaces.active;space.region_3d.view_perspective='CAMERA';space.region_3d.view_camera_zoom=7;space.overlay.show_overlays=False
   space.shading.type='MATERIAL'
sc.render.image_settings.media_type='VIDEO';sc.render.ffmpeg.format='MPEG4';sc.render.ffmpeg.codec='H264';sc.render.ffmpeg.constant_rate_factor='HIGH';sc.render.ffmpeg.audio_codec='NONE'
sc.render.filepath='//dec01-test-3d-astra.mp4'
b.data.orphans_purge(do_recursive=True)
for tex in b.data.images:
 if tex.source=='FILE' and not tex.packed_file:tex.pack()
b.context.preferences.filepaths.save_version=0
b.ops.wm.save_as_mainfile(filepath=str(p/'packed.blend'),compress=True)
sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.compression=10
frames=p/'frames-facial-lock';frames.mkdir(exist_ok=True);sc.render.filepath=str(frames/'shot-')
b.ops.render.render(animation=True)
