from mathutils.geometry import delaunay_2d_cdt
def ease(a,b,t):
 t=max(0,min(1,(t-a)/(b-a)));return t*t*(3-2*t)
def motion(f):return ease(7.25,9.58,(f-1)/24)
def anim_key(key,fun):
 for f in range(1,241):key.value=fun(f);key.keyframe_insert('value',frame=f)
def xyuv(pt):return(pt[0]/880,1-pt[1]/495)
def dual(name,im0,im1):
 m=b.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;g=m.node_tree.links;n.clear()
 mix=n.new('ShaderNodeMixRGB');em=n.new('ShaderNodeEmission');o=n.new('ShaderNodeOutputMaterial');g.new(mix.outputs[0],em.inputs[0]);g.new(em.outputs[0],o.inputs[0])
 for i,impath in enumerate((im0,im1)):
  t=n.new('ShaderNodeTexImage');t.image=img(impath);uvn=n.new('ShaderNodeUVMap');uvn.uv_map=['Rest','Reading'][i];g.new(uvn.outputs[0],t.inputs[0]);g.new(t.outputs[0],mix.inputs[1+i])
 return m,mix.inputs[0]
pts=[];dest=[]
def add(x,y,X=None,Y=None):
 if (x,y) in pts:return
 pts.append((x,y));dest.append((x if X is None else X,y if Y is None else Y))
# Manually correspond facial details, the hat, scarf, elbows and stationary surroundings.
for y in [0,495]:
 for x in [0,80,180,260,340,410,480,540,650,760,880]:add(x,y)
for x in [0,180,225,540,620,740,880]:
 for y in [30,70,125,180,225,275,335,390,455]:add(x,y)
for x,y in [(246,125),(250,170),(258,210),(270,280),(290,323),(289,382),(315,388),(466,383),(537,382),(480,356),(406,362),(345,355),(327,353),(580,285),(495,30),(495,51),(510,80),(516,111),(520,143),(528,173),(518,195),(506,215)]:add(x,y)
for point in [
 (252,74,258,63),(280,57,287,49),(365,10,378,12),(463,22,474,28),(432,43,441,49),
 (281,100,288,95),(279,151,288,145),(294,74,303,68),(317,83,328,82),(340,98,350,99),(317,129,326,129),
 (342,79,354,81),(389,72,397,80),(430,66,439,76),(452,39,466,47),(465,70,477,83),(462,91,475,104),
 (306,149,317,152),(327,178,336,185),(350,192,356,200),(400,195,404,205),(444,192,449,204),
 (451,177,464,188),(481,162,499,173),(492,139,506,151),(482,116,499,135),
 (341,138,350,149),(349,120,360,143),(360,106,373,126),(375,102,389,122),(390,106,400,126),(401,116,409,137),(404,132,411,145),(399,145,405,160),(378,153,389,173),(361,150,371,168),(348,140,359,155),
 (374,115,384,144),(379,128,389,154),(389,125,399,151),(372,138,382,161),(388,139,396,161),
 (416,116,431,141),(424,96,438,118),(435,86,451,110),(449,86,465,111),(464,101,479,126),(467,117,477,142),(457,129,469,151),(439,133,454,157),(426,128,439,152),(435,113,447,143),(446,119,457,147),
 (404,123,411,144),(414,130,425,155),(411,136,422,161),(401,148,411,179),(420,146,426,171),(434,145,438,167),(428,166,431,187),(409,163,414,185),
 (326,195,323,195),(349,217,351,215),(401,220,407,221),(467,190,473,197),
 (339,262,320,277),(350,285,327,291),(373,303,326,288),(395,277,340,277),(400,309,343,307),
 (421,229,432,253),(442,236,455,255),(504,227,546,214),(490,316,517,307),(435,322,454,331),(416,315,432,331),
 (495,290,543,280),(514,307,548,310),(540,337,543,337),(350,332,337,326),(365,351,366,342),(425,342,426,343)
]:add(*point)
for point in [
 (288,298,288,298),(302,291,302,291),(312,291,311,291),(321,294,319,294),(332,303,330,304),(341,318,341,318),(348,337,348,337),(329,330,329,330),(338,362,338,362),
 (294,230,292,233),(304,218,302,221),(323,213,320,214),(330,221,325,221),(337,248,334,243),(333,270,326,267),
 (368,298,324,282),(375,296,329,282),(376,306,329,290),(368,306,322,290),(371,301,326,286),
 (387,285,334,285),(391,303,335,299),(393,315,341,307),(402,270,350,268),
 (487,214,487,214),(522,240,548,236),(552,268,553,268),(562,273,563,273),(573,279,573,279),(581,298,581,298),(570,307,570,307),(558,316,558,316),(560,336,560,336)
]:add(*point)
# Below the scarf, the sleeve has its own mesh. Keep the chair and lap stationary.
for i,(x,y) in enumerate(pts):
 if y>=224:dest[i]=(x,y)
for x in (270,302,332,360,390,422,454,485,520,552,579):
 for y in (230,255,283,314,340):add(x,y)
# A separate set of anchors lets the fire move without disturbing adjacent masonry.
for x in (74,92,112,135,155,178,194):
 for y in (189,208,231,255,279,300,318,336):add(x,y)
vv,ee,ff,vi,ei,fi=delaunay_2d_cdt([Vector(q) for q in pts],[],[],0,.00001)
ind=[v[0] for v in vi]; pa=[pts[i] for i in ind];pb=list(pa)
m,blend=dual('Painted room and face • two registered projections',p/'base-clean.png',p/'closed-to-reading-coat.png')
body=obj('Study and character • registered relief image', [xyz(x,y,0) for x,y in pa],ff,[[xyuv(pa[i]) for i in face] for face in ff],m)
b.data.objects.remove(plate,do_unlink=True)
body.data.uv_layers[0].name='Rest';other=body.data.uv_layers.new(name='Reading')
for poly,face in zip(body.data.polygons,ff):
 for li,i in zip(poly.loop_indices,face):other.data[li].uv=xyuv(pb[i])
body.shape_key_add(name='Illustrated pose');read=body.shape_key_add(name='Lower head to read');breath=body.shape_key_add(name='Breathing and posture');flame=body.shape_key_add(name='Firelight');flame2=body.shape_key_add(name='Firelight drift')
for i,((x,y),(X,Y)) in enumerate(zip(pa,pb)):
 # One intact facial projection: uniform tilt inside the silhouette, fading
 # across the nearby immobile surroundings. All eyewear shares one transform.
 wx=ease(237,280,x)*(1-ease(485,532,x))
 wy=ease(0,8,y)*(1-ease(203,231,y))
 ww=wx*wy;angle=math.radians(2.2);dx=x-405;dy=y-204
 xx=405+dx*math.cos(angle)-dy*math.sin(angle);yy=204+dx*math.sin(angle)+dy*math.cos(angle)+3.0
 read.data[i].co=xyz(x+ww*(xx-x),y+ww*(yy-y),0)
 if 248<x<487 and 5<y<205:
  w=math.exp(-((x-390)/112)**4-((y-112)/106)**4);breath.data[i].co=xyz(x+.72*w,y-1.25*w,0)
 if 75<x<190 and 190<y<315:
  w=math.sin(math.pi*(x-74)/120)*math.sin(math.pi*(y-189)/147)
  flame.data[i].co=xyz(x+w*(4*math.sin(y*.076)+1),y-w*(4+2*math.cos(x*.12)),0)
  flame2.data[i].co=xyz(x-w*4*math.sin(y*.058),y+w*5*math.sin(x*.068),0)
for f in range(1,241):
 q=motion(f);blend.default_value=q;blend.keyframe_insert('default_value',frame=f)
for key,fun in [(read,motion),(breath,lambda f:.46+.4*math.sin(f*.058)),(flame,lambda f:.45+.36*math.sin(f*.19)+.13*math.sin(f*.39)),(flame2,lambda f:.5+.4*math.sin(f*.15+.9))]:anim_key(key,fun)
# Each cover has its own true longitudinal hinge. The calibrated rest/open
# surfaces additionally account for the tilt of the entire volume in camera.
def bookpart(name,start,end,texcoords,faces,a0,a1,h0,h1,layer,src):
 m=mat(name+' • projected binding',src)
 def local(coords,angle,hinge):
  xc,yc=hinge;c=math.cos(math.radians(angle))
  return [((x-xc)/c,yc-y,0) for x,y in coords]
 v0=local(start,a0,h0);v1=local(end,a1,h1)
 o=obj(name,v0,faces,[[xyuv(texcoords[i]) for i in face] for face in faces],m)
 o.shape_key_add(name='Closed balance');k=o.shape_key_add(name='Open balance')
 for vert,pt in zip(k.data,v1):vert.co=pt
 for f in range(1,241):
  q=motion(f); k.value=q;k.keyframe_insert('value',frame=f)
  o.rotation_euler.y=math.radians(a0+(a1-a0)*q);o.keyframe_insert('rotation_euler',frame=f)
  o.location=xyz(h0[0]+(h1[0]-h0[0])*q,h0[1]+(h1[1]-h0[1])*q,layer);o.keyframe_insert('location',frame=f)
 return o
h0L=(422,229);h1L=(434,253);h0R=(441,235);h1R=(454,253)
fr0=[(440.4,235),(505.7,226.6),(490.9,315.9),(432.4,323.7)]
fr1=[(454.5,253.7),(548.6,212.1),(520,305),(454,331.1)]
ba0=[(422.1,228.6),(491.4,219.5),(478.6,306),(414,315.2)]
ba1=[(434.2,252.6),(335.9,222.9),(365.2,309.5),(433.7,330.5)]
# The right board uses the unoccluded lettering and finish of the closed source.
front=bookpart('Front board • gold 1C',fr0,fr1,fr1,[(0,1,2,3)],53,29,h0R,h1R,180,p/'cover-atlas.png')
front.data.materials[0]=mat('Restored embossed front board',p/'front-leather.png')
for li,uv in zip(front.data.polygons[0].loop_indices,[(0,1),(1,1),(1,0),(0,0)]):front.data.uv_layers[0].data[li].uv=uv
back=bookpart('Back board • leather and foil',ba0,ba1,ba1,[(0,1,2,3)],53,154,h0L,h1L,177.8,p/'cover-atlas.png')
sp0=[ba0[0],fr0[0],fr0[3],ba0[3]];sp1=[ba1[0],fr1[0],fr1[3],ba1[3]]
spine=bookpart('Rounded spine • gilt bands',sp0,sp1,sp1,[(0,1,2,3)],0,0,h0L,h1L,181,p/'cover-atlas.png')
# Paper leaves are concave strips that change their spread above each board.
def pages(side):
 left=side=='L'; front0=ba0[:2] if left else fr0[:2];front1=ba1[:2] if left else fr1[:2]
 ss=[]; es=[]; fs=[]
 for j in range(17):
  u=j/16
  for edge in range(2):
   def lerp(a,b,u):return(a[0]*(1-u)+b[0]*u,a[1]*(1-u)+b[1]*u)
   st=lerp(*front0,u);en=lerp(*front1,u)
   if left:
    # Both stacks meet on the spine at the binding.
    st2=lerp((431,232),(494,222),u);en2=(444+(358-444)*u,249.6-39.8*math.sin(math.pi*u/2))
   else:
    st2=lerp((431,232),(494,222),u);en2=(444+(526-444)*u,249.6-48.5*math.sin(math.pi*u/2))
   ss.append(st2 if edge else st);es.append(en2 if edge else en)
 for j in range(16): k=2*j;fs.append((k,k+2,k+3,k+1))
 page=bookpart(('Left' if left else 'Right')+' paper block • curved fore edge',ss,es,es,fs,53 if left else 53,154 if left else 29,h0L if left else h0R,h1L if left else h1R,182 if left else 183,out/'dec01-i2v-last.png')
 pg=mat('Warm laid paper',p/'paper.png');page.data.materials[0]=pg
 for poly,face in zip(page.data.polygons,fs):
  for li,i in zip(poly.loop_indices,face):page.data.uv_layers[0].data[li].uv=((i//2)/16,i%2)
 return page
pages('L');pages('R')
# The stabilizing paw follows the moving support from the first to the last pose.
def paw(name,src,src_box,end_box,z):
 objp=rect(name,p/src,src_box,z,True)
 xc=(src_box[0]+src_box[2])*.5;yc=(src_box[1]+src_box[3])*.5
 # Base quad is centered on its origin for controllable grip changes.
 for v in objp.data.vertices:v.co-=Vector(xyz(xc,yc,z))
 for f in range(1,241):
  q=motion(f); box=[a+(bb-a)*q for a,bb in zip(src_box,end_box)]
  objp.location=xyz((box[0]+box[2])*.5,(box[1]+box[3])*.5,z)
  objp.scale=((box[2]-box[0])/(src_box[2]-src_box[0]),(box[3]-box[1])/(src_box[3]-src_box[1]),1);objp.keyframe_insert('scale',frame=f);objp.keyframe_insert('location',frame=f)
 return objp
hold=paw('Supporting paw • back board','paw_left0.png',(397.37,273.68,438.42,316.32),(338,272.1,379.5,310.5),220)
rp=rect('Opening paw • front board',p/'paw_right1.png',(508.42,267.37,542.1,305.79),222,True)
# The pads disappear behind the board as the toes curl around its edge.
for f in range(1,241):
 t=(f-1)/24;q=motion(f); grip=ease(7.45,7.82,t)
 rx=496+q*29;ry=275+q*12
 rp.location=(rx-525,287-ry,0)
 # Collapse along the cloth seam during contact.
 orig=(525-440,247.5-287)
 rp.scale=(max(.001,grip),max(.001,grip),1)
 rp.location.x+=orig[0]*(1-grip);rp.location.y+=orig[1]*(1-grip)
 rp.keyframe_insert('location',frame=f);rp.keyframe_insert('scale',frame=f)
 # The greeting sleeve withdraws into the matching painted sleeve.
 wave.hide_render=(t>7.83);wave.keyframe_insert('hide_render',frame=f)

# Turn the palm inward while the elbow retracts, placing the pads behind the book
# before the fingertips reappear along the near cover.
pivot=b.data.objects.new('Greeting arm • palm turnover',None);sc.collection.objects.link(pivot)
pivot.location=xyz(466,217,4);b.context.view_layer.update()
for child in [rig,wave]:
 child.parent=pivot;child.matrix_parent_inverse=pivot.matrix_world.inverted()
for f in range(1,241):
 t=(f-1)/24;retract=ease(7.04,7.76,t)
 pivot.scale=(1-.40*retract,1-.06*retract,1)
 pivot.location=xyz(466-29*retract,217+16*retract,4)
 pivot.keyframe_insert('scale',frame=f);pivot.keyframe_insert('location',frame=f)
# Keep the supporting hand against the leftmost bound edge through the hinge swing.
def left_correction(q):
 outer=422+12*q+math.cos(math.radians(53+101*q))*((1-q)*60/.601815+q*77.6/.898794)
 grip=min(415.3+18.5*q,outer)+2.6
 return grip-(417.9+(358.9-417.9)*q)
support=body.shape_key_add(name='Keep supporting wrist against binding')
support.slider_min=-1;support.slider_max=2
for i,(x,y) in enumerate(pa):
 w=max(0,min(1,(x-349)/44))*max(0,min(1,(448-x)/24))*max(0,min(1,(y-237)/26))*max(0,min(1,(332-y)/17))
 support.data[i].co=xyz(x,y,0)
for f in range(1,241):
 q=motion(f);dx=left_correction(q);support.value=dx/35;support.keyframe_insert('value',frame=f)
 hold.location.x=(397.37+438.42)/2-440+((338+379.5)/2-(397.37+438.42)/2)*q+dx
 hold.location.y=247.5-((273.68+316.32)/2+( (272.1+310.5)/2-(273.68+316.32)/2)*q)
 hold.location.z=220;hold.keyframe_insert('location',frame=f)

# Register the supporting sleeve itself, keeping the embroidered button and cuff
# attached to a continuous surface throughout the reach.
xmin,ymin,xmax,ymax=json.loads((p/'sleevebounds.json').read_text())
vs=[];fs=[];us=[];coords=[];cols=21;rows=23
for iy in range(rows):
 for ix in range(cols):
  x=xmin+(xmax-xmin)*ix/(cols-1);y=ymin+(ymax-ymin)*iy/(rows-1)
  coords.append((x,y));vs.append(xyz(x,y,10))
for j in range(rows-1):
 for i in range(cols-1):
  k=j*cols+i;quad=(k,k+1,k+cols+1,k+cols);fs.append(quad)
  us.append([((coords[v][0]-xmin)/(xmax-xmin),1-(coords[v][1]-ymin)/(ymax-ymin)) for v in quad])
sleeve=obj('Supporting arm • cuff and bent sleeve',vs,fs,us,mat('Violet cuff • source projection',p/'hold_sleeve.png',True))
sleeve.shape_key_add(name='Closed grip');open_arm=sleeve.shape_key_add(name='Supporting the open volume');tracking=sleeve.shape_key_add(name='Follow binding during swing');tracking.slider_max=2
ctrl=[(351,219,-10,8,.05),(373,221,-16,6,.05),(346,243,-15,9,.15),(374,251,-26,2,.35),(342,269,-22,0,.42),(355,283,-34,-7,.64),(372,301,-46,-15,.92),(389,308,-53,-8,1),(399,276,-56,-5,1),(414,275,-59,-4,1),(404,316,-56,-10,1),(411,296,-59,-5,1),(339,289,-20,-5,.54),(357,305,-35,-12,.85)]
for i,(x,y) in enumerate(coords):
 weights=[1/(.7+(x-a)**2+(y-bb)**2)**1.8 for a,bb,dx,dy,w in ctrl];total=sum(weights)
 dx,dy,w=[sum(c[k]*ww for c,ww in zip(ctrl,weights))/total for k in (2,3,4)]
 open_arm.data[i].co=xyz(x+dx,y+dy,10);tracking.data[i].co=xyz(x+35*w,y,10)
for f in range(1,241):
 q=motion(f);open_arm.value=q;tracking.value=left_correction(q)/35
 open_arm.keyframe_insert('value',frame=f);tracking.keyframe_insert('value',frame=f)
for cover in (front,back,spine):
 solid=cover.modifiers.new('Binding thickness', 'SOLIDIFY');solid.thickness=.64;solid.offset=0
