import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
random.seed(145)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def material(name, rgb, roughness=.55, metallic=0, emission=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*rgb, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    if emission:
        shader.inputs["Emission Color"].default_value = (*rgb, 1)
        shader.inputs["Emission Strength"].default_value = emission
    return mat

fur = material("Gray-brown tabby wool", (.31, .237, .195))
darkfur = material("Dark markings", (.081, .058, .048))
midfur = material("Warm muzzle gray", (.45, .357, .284))
cream = material("Oat-colored paws and muzzle", (.87, .733, .57))
pink = material("Peach suede toe pads", (.69, .255, .221))
brown = material("Nose and mouth", (.117, .044, .038))
eye_white = material("Cream eye whites", (.94, .87, .72), .26)
iris = material("Amber iris", (.68, .34, .056), .28)
iris_outer = material("Iris limbal ring", (.31, .145, .032), .2)
pupil = material("Ink pupils", (.013, .008, .006), .19)
glint = material("Eyeball highlights", (.98, .96, .885), .16, emission=.25)
brass = material("Old brass", (.52, .27, .08), .31, .62)
gold = material("Book foil and tassel", (.83, .45, .075), .3, .5)
hat_mat = material("Aubergine cap", (.127, .047, .23))
jacket = material("Purple jacket", (.156, .083, .263), .7)
lavender = material("Lavender scarf", (.4, .274, .56), .81)
lavender_hi = material("Scarf stitching", (.54, .365, .654), .79)
cover = material("Violet clothbound cover", (.172, .06, .278), .66)
paper = material("Book paper", (.82, .687, .468), .83)
paper_line = material("Page edges", (.53, .403, .242), .8)
wood = material("Chair walnut", (.19, .075, .028), .45)
wood_hi = material("Mantel wooden trim", (.294, .12, .041), .53)
wood_dark = material("Wood floor shade", (.086, .031, .014), .62)
seat_mat = material("Chair garnet upholstery", (.32, .083, .081), .75)
wall_mat = material("Carved oak plaster", (.26, .14, .072), .89)
mortar = material("Fireplace mortar", (.113, .071, .053))
stone = [material("Hearth stone %d" % i, (v*1.21, v*.93, v*.72), .92) for i,v in enumerate((.18,.22,.26,.29,.34))]
fire_dark = material("Firebox", (.027,.013,.009))
floor_mats = [material("Floorboard %d"%i, (v*1.3,v*.64,v*.33), .75) for i,v in enumerate((.16,.18,.22,.24,.26))]
rug_m = material("Braided rug maroon", (.24,.065,.09), .85)
rug_line = material("Rug borders", (.59,.233,.144), .77)
tree_mats = [material("Fir green %d" % i, (.034,.11+i*.022,.051+i*.01),.91) for i in range(4)]
pine_dark = material("Verdigris pine shadows", (.018,.075,.038))
berry = material("Cranberry red", (.59,.075,.052), .32)
gift_mats = [berry, hat_mat, lavender, wood_hi]
warm_glow = material("Fairy lights", (1,.47,.116), .28, emission=5)
fire_mats = [material("Flame %d" % i, rgb, roughness=.45, emission=5+i) for i,rgb in enumerate(((.9,.12,.007),(1,.32,.015),(1,.7,.105)))]
window_glass = material("Blue winter window", (.067,.155,.38), .59, emission=.34)
snow_m = material("Snow beyond window", (.59,.76,.93), .83, emission=.48)

def surface_grain(mat, scale, strength, variation=.11, stretch=(1,1,1)):
    graph=mat.node_tree
    nodes,links=graph.nodes,graph.links
    bsdf=nodes.get("Principled BSDF")
    rgb=bsdf.inputs["Base Color"].default_value[:3]
    coords=nodes.new("ShaderNodeTexCoord")
    stretch_node=nodes.new("ShaderNodeVectorMath")
    stretch_node.operation="MULTIPLY"
    stretch_node.inputs[1].default_value=stretch
    links.new(coords.outputs["Generated"],stretch_node.inputs[0])
    noise=nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value=scale
    noise.inputs["Detail"].default_value=2
    links.new(stretch_node.outputs["Vector"],noise.inputs["Vector"])
    ramp=nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color=(*(c*(1-variation) for c in rgb),1)
    ramp.color_ramp.elements[1].color=(*(min(1,c*(1+variation)) for c in rgb),1)
    links.new(noise.outputs["Fac"],ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"],bsdf.inputs["Base Color"])
    bump=nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value=strength
    bump.inputs["Distance"].default_value=.011
    links.new(noise.outputs["Fac"],bump.inputs["Height"])
    links.new(bump.outputs["Normal"],bsdf.inputs["Normal"])

for mat in floor_mats+[wood,wood_dark,wood_hi]:
    surface_grain(mat,12,.15,.22,stretch=(3.2,1.4,.18))
for mat in stone:
    surface_grain(mat,7,.19,.20)
for mat in [fur,midfur,jacket,lavender,lavender_hi,seat_mat,rug_m,cover]:
    surface_grain(mat,36,.15,.11)

def decorate(obj, name, mat, smooth=False):
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    if smooth and obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    return obj

def empty(name, loc=(0,0,0), parent=None):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.location = loc
    return obj

def uv(name, loc, scale, mat, parent=None, detail=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=detail, ring_count=12, location=loc)
    obj = decorate(bpy.context.object,name,mat,True)
    obj.parent = parent
    obj.location = loc
    obj.scale = scale
    return obj

def box(name, loc, dims, mat, bevel=.03, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = decorate(bpy.context.object,name,mat)
    obj.parent = parent
    obj.location = loc
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("Rounded edges","BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod = obj.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return obj

def line(name, points, radius, mat, parent=None, poly=False):
    data = bpy.data.curves.new(name,"CURVE")
    data.dimensions = "3D"
    data.resolution_u = 10
    data.bevel_depth = radius
    data.bevel_resolution = 3
    if poly:
        spline = data.splines.new("POLY")
        spline.points.add(len(points)-1)
        for item, pt in zip(spline.points, points):
            item.co = (*pt,1)
    else:
        spline = data.splines.new("BEZIER")
        spline.bezier_points.add(len(points)-1)
        for item, pt in zip(spline.bezier_points, points):
            item.co = pt
            item.handle_left_type = item.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(mat)
    return obj

def tapered(name, start, end, radius1, radius2, mat, parent=None, vertices=22):
    start, end = Vector(start), Vector(end)
    delta = end-start
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=delta.length)
    obj = decorate(bpy.context.object,name,mat,True)
    obj.parent = parent
    obj.location = (start+end)/2
    obj.rotation_euler = delta.to_track_quat('Z','Y').to_euler()
    return obj

def ellipse(name, cx, cy, cz, rx, ry, radius, mat, parent=None, plane="XZ"):
    points = []
    for i in range(65):
        dx = rx*math.cos(2*math.pi*i/64)
        dy = ry*math.sin(2*math.pi*i/64)
        points.append((cx+dx,cy,cz+dy) if plane=="XZ" else (cx+dx,cy+dy,cz))
    return line(name, points, radius, mat,parent,poly=True)

def mesh(name, vertices, faces, mat, parent=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    return decorate(obj,name,mat,True)

# Curved room and carved wooden fireplace.
box("Floor base",(0,0,-.14),(15,13,.25),wood_dark)
for i in range(24):
    box("Oak floorboard",(i*.47-5.4,-.7,-.029),(.454,8,.075),floor_mats[i%5],.008)
box("Warm wooden back wall",(0,2.47,2.65),(13,.35,5.6),wall_mat,.03)
for i in range(24):
    x = -.24+i*.5-5.6
    box("Wall board, bevel",(x,2.25,2.65),(.475,.1,5.6),floor_mats[(3*i+1)%5],.017)
box("Wall skirt",(0,2.11,.23),(13,.15,.32),wood_hi,.045)
for x in (-4.9,4.9):
    line("Rising oak rib",[(x,2.15,0),(x,2.12,2.8),(x*.78,2.07,4.55),(x*.50,2,5.9)],.13,wood_dark)
uv("Wool rug",(0,-.81,.03),(2.34,1.49,.045),rug_m)
for i in range(4):
    ellipse("Braided rug rings",0,-.81,.066,2.29-i*.055,1.45-i*.04,.014,rug_line,plane="XY")
fire_x = -2.66
box("Hearth slab",(fire_x,.68,.13),(2.47,1.36,.24),stone[2],.07)
box("Fireplace dark interior",(fire_x,1.34,.86),(1.63,.21,1.57),fire_dark,.03)
box("Chimney breast",(fire_x,1.75,2.25),(2.42,.47,2.6),mortar,.06)
for j in range(8):
    for i in range(6):
        x = fire_x -1.03 + i*.41
        z = 1.87+j*.277
        box("Irregular stone joints",(x,1.455+.014*((i+j)%3),z),(.393,.36,.264),random.choice(stone),.035)
for side in [-1,1]:
    for j in range(5):
        box("Stone jamb",(fire_x+side*.96,.92,.30+j*.265),(.47,.68,.25),stone[(j+(side>0))%len(stone)],.042)
for i in range(9):
    theta = math.pi*i/8
    block = box("Arch voussoir", (fire_x+.89*math.cos(theta),.93,1.18+.62*math.sin(theta)),(.31,.66,.34),stone[(3*i+2)%len(stone)],.046)
    block.rotation_euler.y = -theta+math.pi/2
box("Thick oak mantel",(fire_x,.89,2.07),(2.56,1.02,.22),wood_hi,.077)
for i in range(5):
    x = fire_x-.92+i*.48
    tapered("Log",(x,.57,.27),(x+.49,1.00,.37),.085,.077,wood_dark)
for i in range(8):
    x = fire_x + (i-3.5)*.157
    tapped = tapered("Grate iron bar",(x,.37,.23),(x,.37,.52),.015,.015,brown)
line("Grate crossbar",[(fire_x-.62,.37,.45),(fire_x+.62,.37,.45)],.022,brown,poly=True)

def flame(name, x, y, z, height, width, material):
    vertices = [(0,0,0)]
    levels = [(0.06,.53),(0.24,1),(0.46,.78),(.66,.53),(.85,.28),(.97,.08)]
    for t, scale in levels:
        for i in range(10):
            theta = 2*math.pi*i/10
            vertices.append((t*t*width*.75+width*scale*math.cos(theta),width*.54*scale*math.sin(theta),t*height))
    vertices.append((width*.84,0,height))
    faces=[(0,1+i,1+(i+1)%10) for i in range(10)]
    for j in range(len(levels)-1):
        for i in range(10):
            a=1+j*10+i
            b=1+j*10+(i+1)%10
            faces.append((a,b,b+10,a+10))
    faces += [(len(vertices)-1,51+i,51+(i+1)%10) for i in range(10)]
    obj=mesh(name,vertices,faces,material)
    sub=obj.modifiers.new("Soft sculpt","SUBSURF")
    sub.levels=sub.render_levels=1
    obj.location=(x,y,z)
    amp=random.uniform(.05,.21)
    phase=random.uniform(0,6)
    for f in range(1,242,8):
        obj.scale=(1+amp*math.sin(f*.23+phase),1,1+amp*math.cos(f*.18+phase))
        obj.keyframe_insert("scale",frame=f)
    return obj

for i in range(8):
    x = fire_x+(i-3.5)*.14
    flame("Animated flame",x,.63+.04*(i%2),.28,.58+random.random()*.57,.10+random.random()*.045,fire_mats[i%3])
for i in range(13):
    x = fire_x-1.05+i*.17
    uv("Mantel bough",(x,.42,2.15),(.21,.135,.104),tree_mats[i%4],detail=12)
    if i%2==0:
        uv("Holly berry",(x,.29,2.18),(.047,.042,.044),berry,detail=12)
for x in [fire_x-.77,fire_x+.72]:
    box("Candle", (x,.66,2.38), (.135,.135,.49),cream,.032)
    flame("Candle flame",x,.66,2.62,.19,.047,warm_glow)

# One arched winter window and a Christmas tree.
window_x=3.63
base_z=1.13
def arch_points(x,y,z,w,h):
    pts=[(x-w/2,y,z),(x+w/2,y,z),(x+w/2,y,z+h)]
    pts += [(x+w/2*math.cos(i*math.pi/24),y,z+h+w/2*math.sin(i*math.pi/24)) for i in range(1,25)]
    pts.append(pts[0])
    return pts

pts=arch_points(window_x,2.056,base_z,1.94,2.03)
mesh("Arched snow window",pts[:-1],[tuple(range(len(pts)-1))],window_glass)
line("Wood surround",[(x,y-.12,z) for x,y,z in pts],.095,wood_dark,poly=True)
box("Window sill",(window_x,1.94,base_z-.035),(2.23,.43,.15),wood_hi,.052)
box("Window upright",(window_x,1.99,2.59),(.085,.11,2.89),wood_dark,.013)
for z in (1.96,2.79,3.17):
    box("Window crosspiece",(window_x,1.982,z),(1.96,.102,.079),wood_dark,.009)
for i in range(63):
    x = random.uniform(window_x-.92,window_x+.92)
    z = random.uniform(base_z,base_z+2.93)
    if z < base_z+2.03 or (x-window_x)**2+(z-base_z-2.03)**2 < .86:
        r=random.uniform(.008,.025)
        uv("Snow flake behind glass",(x,2.023,z),(r,.008,r),snow_m,detail=10)
tree_x, tree_y = 2.14, 1.03
tapered("Tree trunk",(tree_x,tree_y,.09),(tree_x,tree_y,1.99),.14,.069,wood)
for j in range(5):
    z=.46+j*.5
    r=.87-j*.147
    tapered("Sculpted evergreen tier",(tree_x,tree_y,z),(tree_x,tree_y,z+.98),r,.027,tree_mats[j%4],vertices=36)
    for i in range(10):
        theta=i*2*math.pi/10+j*.21
        obs=(tree_x+(r*.68)*math.cos(theta),tree_y+(r*.68)*math.sin(theta),z+.115)
        obj=uv("Rounded conifer bough",obs,(r*.44,r*.26,.17),tree_mats[(i+j)%4],detail=16)
        obj.rotation_euler.z=theta
    for i in range(11):
        theta=i*2*math.pi/11+j*.72
        x=tree_x+r*.89*math.cos(theta)
        y=tree_y+r*.89*math.sin(theta)
        zv=z+.115+(i%2)*.079
        rad=.04 if i%3 else .084
        uv("Bauble or fairy light",(x,y,zv),(rad,rad,rad),[berry,gold,warm_glow][i%3],detail=14)
def star(name,x,y,z,r,mat):
    points=[(x,y,z)]
    for i in range(10):
        theta=math.pi/2+i*math.pi/5
        edge=(r if i%2==0 else r*.43)
        points.append((x+edge*math.cos(theta),y,z+edge*math.sin(theta)))
    obj=mesh(name,points,[(0,1+i,1+(i+1)%10) for i in range(10)],mat)
    mod=obj.modifiers.new("Star volume","SOLIDIFY")
    mod.thickness=.064
    mod=obj.modifiers.new("Rounded star edge","BEVEL")
    mod.width=.013
    mod.segments=3
star("Candlelight tree star",tree_x,tree_y-.08,3.51,.235,warm_glow)
for i,(x,y,h) in enumerate([(2.51,.36,.39),(1.69,.55,.32),(2.95,.61,.51),(3.31,.81,.34)]):
    box("Wrapped present",(x,y,h/2),(.55,.47,h),gift_mats[i],.035)
    box("Gold ribbon",(x,y-.239,h/2),(.085,.014,h+.004),gold,.006)
    box("Gold ribbon",(x,y,h+.008),(.085,.475,.014),gold,.004)
    for side in [-1,1]:
        loop=ellipse("Present ribbon loop",x+.10*side,y,h+.053,.12,.055,.023,gold)
        loop.rotation_euler.y=0

# Curved chair and seated cat.
box("High chair back wood",(0,.49,1.98),(1.92,.27,2.44),wood,.19)
box("Padded chair back",(0,.32,2.06),(1.7,.2,2.22),seat_mat,.18)
box("Upholstered seat",(0,-.1,.85),(1.99,1.62,.27),seat_mat,.129)
box("Chair apron",(0,-.1,.67),(2.0,1.62,.21),wood,.077)
for side in [-1,1]:
    s=side
    for y in (-.752,.53):
        line("Turned chair leg",[(s*.82,y,.67),(s*.85,y-.015,.36),(s*.92,y-.07,.08)],.104,wood)
    line("Chair scroll arm",[(s*.94,.43,1.72),(s*1.07,.1,1.53),(s*1.15,-.31,1.49),(s*1.17,-.73,1.54),(s*1.14,-.92,1.49),(s*1.10,-.91,1.41)],.098,wood_hi)
    line("Turned arm support",[(s*.91,-.70,.76),(s*1.05,-.71,1.18),(s*1.15,-.72,1.49)],.078,wood)
    for i in range(10):
        uv("Brass upholstery tack",(s*.783,.167,1.13+i*.208),(.024,.019,.024),brass,detail=12)
for i in range(12):
    uv("Brass tack heel",(i*.146-.80,-.912,.83),(.023,.017,.023),brass,detail=12)
body=empty("Seated body")
uv("Fur at hips",(0,-.16,1.03),(.68,.53,.32),fur,body)
uv("Rounded purple coat",(0,-.112,1.59),(.68,.44,.79),jacket,body)
uv("Shirt front",(0,-.497,1.67),(.48,.11,.59),jacket,body)
for side in (-1,1):
    s=side
    uv("Gray hind leg",(s*.42,-.447,1.029),(.34,.51,.295),fur,body)
    uv("Large cream hind paw",(s*.47,-.753,.963),(.297,.343,.181),cream,body)
    for k in range(3):
        uv("Cream hind toe",(s*.47+(k-1)*.13,-.962,.931),(.105,.137,.124),cream,body)
    for i in range(3):
        uv("Jacket button",(s*.48,-.445,1.49+i*.145),(.051,.025,.051),brass,body,detail=14)
tail=empty("Cat tail pivot",(-.5,.01,1.06))
line("Rounded plush tail",[(0,0,0),(-.42,-.11,-.04),(-.66,-.36,-.13),(-.58,-.64,-.18),(-.42,-.79,-.17)],.18,fur,tail)
for i,(x,y,z) in enumerate([(-.44,-.10,-.04),(-.65,-.34,-.125),(-.58,-.60,-.18)]):
    obj=uv("Tail tabby band",(x,y,z),(.177,.048,.181),darkfur,tail,detail=16)
    obj.rotation_euler.z=.55-i*.24
uv("Tail tip",(-.415,-.79,-.17),(.178,.168,.169),darkfur,tail)

uv("Folded scarf collar",(0,-.185,2.22),(.67,.49,.195),lavender,body)
for i in range(4):
    uv("Scarf wrap ridge",(0,-.255,2.126+i*.055),(.632,.462,.048),lavender_hi if i%3==0 else lavender,body)
scarf=box("Long scarf end",(.24,-.517,1.95),(.31,.135,.6),lavender,.105,body)
scarf.rotation_euler.y=-.31
for i in range(5):
    x=.19+i*.052
    line("Fine scarf fringe",[(x,-.605,1.73),(x+.03,-.614,1.63)],.016,lavender_hi,body)
head=empty("Head tilt pivot",(0,-.25,2.47))
uv("Cat head",(0,0,.26),(.756,.532,.64),fur,head)
uv("Cheek puff L",(-.38,-.284,.132),(.345,.286,.301),midfur,head)
uv("Cheek puff R",(.38,-.284,.132),(.345,.286,.301),midfur,head)
uv("Lower cream face",(0,-.442,.025),(.50,.194,.263),cream,head)
for s in (-1,1):
    q=uv("Rounded triangular ear base",(s*.516,.025,.755),(.227,.181,.33),fur,head)
    q.rotation_euler.y=s*.34
    # Rounded triangular outer and inner rest shape.
    for label, width, y, depth, ma in [("Ear casing",1,-.015,.09,fur),("Ear inner suede",.76,-.12,.039,pink)]:
        pts=[(s*.37,y,.62),(s*.72,y,.65),(s*.701,y,1.095 if width==1 else 1.01)]
        if width<1:
            pts=[(s*.43,y,.68),(s*.68,y,.7),(s*.67,y,.99)]
        a,b,c=pts
        verts=[a,b,c,((a[0]+b[0]+c[0])/3,y-depth,(a[2]+b[2]+c[2])/3),((a[0]+b[0]+c[0])/3,y+depth,(a[2]+b[2]+c[2])/3)]
        q=mesh(label,verts,[(0,1,3),(1,2,3),(2,0,3),(0,4,1),(1,4,2),(2,4,0)],ma,head)
        bevel=q.modifiers.new("Ear rounded outline","BEVEL")
        bevel.width=.029
        bevel.segments=3
        q.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    for i in range(3):
        line("Tabby cheek marking",[(s*(.709-i*.014),-.306,.338-i*.095),(s*(.655-i*.035),-.422,.309-i*.087),(s*(.596-i*.036),-.485,.28-i*.077)],.021 if i else .028,darkfur,head)
    eyex = s*.305
    uv("Ivory eye white",(eyex,-.438,.425),(.247,.13,.245),eye_white,head)
    uv("Dark outline iris",(eyex+s*.004,-.547,.426),(.156,.060,.179),iris_outer,head)
    uv("Amber iris",(eyex+s*.004,-.590,.428),(.136,.047,.159),iris,head)
    uv("Round curious pupil",(eyex+s*.004,-.624,.435),(.092,.034,.121),pupil,head)
    uv("Large catchlight",(eyex-.037,-.65,.493),(.042,.013,.045),glint,head)
    uv("Small catchlight",(eyex+.047,-.655,.410),(.018,.008,.019),glint,head)
    line("Tabby eyebrow",[(eyex-.11,-.434,.68),(eyex,-.467,.728),(eyex+.10,-.437,.693)],.027,darkfur,head)
    ellipse("Round brass eyeglasses",eyex,-.660,.431,.247,.251,.028,brass,head)
    line("Glasses temple",[(s*.552,-.655,.439),(s*.69,-.451,.471),(s*.72,-.22,.492)],.023,brass,head)
    uv("Muzzle cheek",(s*.119,-.584,.172),(.187,.101,.125),cream,head)
    for j in range(3):
        y=-.646
        x=s*(.205+.06*(j%2))
        z=.175-.027*j
        uv("Muzzle freckles",(x,y,z),(.016,.009,.016),midfur,head,detail=10)
        line("Fine whisker",[(x,y+.004,z),(s*.441,-.656,z+.021-.018*j),(s*.737,-.606,z+.091-.074*j)],.007,cream,head)
line("Spectacle bridge",[(-.061,-.657,.470),(0,-.679,.519),(.061,-.657,.470)],.021,brass,head)
for i in (-1,0,1):
    line("Tabby forehead stripe",[(i*.155,-.335,.815),(i*.121,-.427,.758),(i*.055,-.488,.688)],.028,darkfur,head)
uv("Smile opening",(0,-.579,.036),(.154,.064,.112),brown,head)
uv("Smile tongue",(0,-.626,-.01),(.088,.018,.032),pink,head)
uv("Pink nose",(0,-.686,.195),(.092,.042,.059),pink,head)
line("Muzzle split",[(0,-.704,.171),(0,-.68,.125),(0,-.651,.106)],.009,brown,head)
for eyex in (-.305,.305):
    blink=empty("Blink eyelid", (eyex,0,.427),head)
    for unit in list(head.children):
        if unit.name.startswith(("Ivory eye white","Dark outline iris","Amber iris","Round curious pupil","Large catchlight","Small catchlight")) and abs(unit.location.x-eyex)<.15:
            world_local=unit.location.copy()
            unit.parent=blink
            unit.location=world_local-blink.location
    for close_frame in (56,116,168,218):
        for offset, aperture in ((-3,1),(0,.07),(3,1)):
            blink.scale.z=aperture
            blink.keyframe_insert("scale",frame=close_frame+offset)
cap=empty("Scholar cap",(0,-.014,.827),head)
cap.rotation_euler=(.025,-.125,-.105)
uv("Velvet cap band",(0,0,.042),(.466,.355,.201),hat_mat,cap)
box("Mortarboard",(0,0,.228),(1.22,1.02,.092),hat_mat,.019,cap)
uv("Tassel button",(0,0,.278),(.064,.058,.024),brass,cap,detail=14)
line("Tassel tied cord",[(0,0,.279),(-.32,-.36,.282),(-.56,-.46,.25),(-.585,-.474,-.137)],.015,gold,cap)
uv("Tassel cap",(-.583,-.473,-.14),(.04,.04,.054),gold,cap)
tapered("Fringed scholar tassel",(-.585,-.477,-.35),(-.585,-.477,-.164),.061,.038,gold,cap)
for i in range(9):
    t=2*math.pi*i/9
    line("Tassel strand",[(-.585+.037*math.cos(t),-.477+.035*math.sin(t),-.17),(-.585+.066*math.cos(t),-.477+.061*math.sin(t),-.36)],.006,brass,cap)

# Book remains seated in the holding paw. Its border and grip follow the actual hinge.
book=empty("Book upright in supporting paw",(.055,-.771,1.527))
book.rotation_euler=(-.205,.008,-.048)
bw,bh=.79,.937
box("Book back board",(0,.067,0),(bw,.054,bh),cover,.013,book)
box("Paper block",(.018,0,0),(bw-.063,.112,bh-.055),paper,.017,book)
for i in range(7):
    yy=.012*(i-3)
    line("Leaf edges",[(bw/2-.017,yy,-bh/2+.036),(bw/2-.017,yy,bh/2-.034)],.0025,paper_line,book,poly=True)
tapered("Rounded cloth spine",(-bw/2,0,-bh/2),(-bw/2,0,bh/2),.078,.078,cover,book)
for z in (-.39,-.32,.33,.40):
    ellipse("Spine gold band",-bw/2,0,z,.074,.074,.0037,gold,book,plane="XY")
hinge=empty("Front board hinge / axis through spine",(-bw/2,-.081,0),book)
hinge.rotation_mode="XYZ"
box("Hinged front cover",(bw/2,-.012,0),(bw,.061,bh),cover,.014,hinge)
box("Front endpaper inlay",(bw/2,.020,0),(bw-.063,.015,bh-.064),paper,.009,hinge)
for margin in (.051,.074):
    lo,hi=margin,bw-margin
    lower,upper=-bh/2+margin,bh/2-margin
    line("Gold-tooled frame",[(lo,-.044,lower),(hi,-.044,lower),(hi,-.044,upper),(lo,-.044,upper),(lo,-.044,lower)],.0046,gold,hinge,poly=True)
text_data=bpy.data.curves.new("1С gold leaf","FONT")
text_data.body="1C"
text_data.align_x="CENTER"
text_data.align_y="CENTER"
text_data.size=.43
text_data.extrude=.0027
text_data.bevel_depth=.0014
text_obj=bpy.data.objects.new("1С on purple book",text_data)
bpy.context.collection.objects.link(text_obj)
text_obj.parent=hinge
text_obj.location=(bw/2,-.047,0)
text_obj.rotation_euler.x=math.pi/2
text_data.materials.append(gold)
for i in range(11):
    z=.33-i*.062
    line("Printed lines inside book",[(-.258,-.059,z),(.292-.041*(i%4),-.059,z)],.0028,paper_line,book,poly=True)

# The two articulated arms have upper-arm, forearm and hand bones.
# Rigid sleeve sections are bound to the corresponding pose bones.
arm=bpy.data.armatures.new("Cat arm skeleton")
arm_obj=bpy.data.objects.new("Kinematic cat arms",arm)
bpy.context.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active=arm_obj
arm_obj.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
limbs={"open":(-.535,-.18,2.13),"hold":(.535,-.18,2.13)}
sizes=(.53,.631)
for side,anchor in limbs.items():
    for i,(part,length) in enumerate(zip(("upper","forearm","paw"),(*sizes,.2))):
        bone=arm.edit_bones.new(side+"_"+part)
        bone.head=(anchor[0],anchor[1]+i*.055,anchor[2])
        bone.tail=(anchor[0],anchor[1]+i*.055+length,anchor[2])
bpy.ops.object.mode_set(mode="OBJECT")
for side in limbs:
    for part in ("upper","forearm","paw"):
        node=empty(side+"_"+part+"_geometry")
        c=node.constraints.new("COPY_TRANSFORMS")
        c.target=arm_obj
        c.subtarget=side+"_"+part
        if part=="upper":
            tapered("Velvet upper sleeve",(0,.01,0),(0,.528,0),.204,.159,jacket,node)
            uv("Rounded sleeve shoulder",(0,.07,0),(.214,.161,.194),jacket,node)
        elif part=="forearm":
            tapered("Velvet articulated forearm",(0,-.03,0),(0,.606,0),.166,.124,jacket,node)
            uv("Rounded elbow joint",(0,.001,0),(.164,.128,.157),jacket,node)
            tapered("Lavender wrist cuff",(0,.527,0),(0,.582,0),.127,.126,lavender,node)
            tapered("Cream cuff piping",(0,.578,0),(0,.601,0),.126,.122,cream,node)
        else:
            uv("Soft mitten paw",(0,.03,0),(.156,.158,.103),cream,node)
            uv("Central toe pad",(0,.039,.084),(.084,.079,.019),pink,node,detail=16)
            for i in range(3):
                x=(i-1)*.093
                y=.139+.013*(1-abs(i-1))
                uv("Rounded paw toe",(x,y,.001),(.058,.067,.085),cream,node,detail=16)
                uv("Peach toe bean",(x,y,.075),(.039,.040,.015),pink,node,detail=14)
            thumb=uv("Rounded curled thumb",(.111,.015,-.002),(.073,.078,.081),cream,node)
            thumb.rotation_euler.z=-.26

def axes(x,y,z):
    return Matrix((x,y,z)).transposed().to_quaternion()

def orient(dir_y, normal_z):
    y=Vector(dir_y).normalized()
    z=Vector(normal_z)
    x=y.cross(z).normalized()
    return axes(x,y,x.cross(y).normalized())

def pose_bone(name, point, rotation):
    pb=arm_obj.pose.bones[name]
    pb.matrix=Matrix.Translation(point) @ rotation.to_matrix().to_4x4()
    pb.rotation_mode="QUATERNION"
    pb.keyframe_insert("location",frame=frame)
    pb.keyframe_insert("rotation_quaternion",frame=frame)

def ik(side, center, rotation):
    start=Vector(limbs[side])
    wrist=center-rotation@Vector((0,.008,0))
    aim=wrist-start
    distance=aim.length
    if distance>=sum(sizes)-.001:
        raise RuntimeError(f"Out of reach at frame {frame}: {side} {distance:.5f}")
    d=aim.normalized()
    outward=-1 if side=="open" else 1
    bend=Vector((outward*.5,.16,-.6))
    bend=(bend-d*bend.dot(d)).normalized()
    l1,l2=sizes
    along=(l1*l1-l2*l2+distance*distance)/(2*distance)
    elbow=start+d*along+bend*math.sqrt(l1*l1-along*along)
    pose_bone(side+"_upper",start,orient(elbow-start,(0,-1,0)))
    pose_bone(side+"_forearm",elbow,orient(wrist-elbow,(0,-1,0)))
    pose_bone(side+"_paw",wrist,rotation)

def ease(x):
    x=max(0,min(1,x))
    return x*x*(3-2*x)

def interp(lo,hi,t):
    return Vector(lo).lerp(Vector(hi),t)

# At 7s the opening hand reaches for the front board, takes contact, follows
# a point on the inside plane throughout opening, and settles at the end.
for frame in range(1,241):
    t=(frame-1)/24
    angle=-math.radians(147)*ease((t-7.52)/1.99)
    hinge.rotation_euler.z=angle
    hinge.keyframe_insert("rotation_euler",frame=frame)
    head.rotation_euler=(6*math.pi/180*math.sin(t*1.8)*math.sin(min(t,7)/7*math.pi)+.145*ease((t-6.95)/.85),.05*math.sin(t*1.1),.057*math.sin(t*.92))
    head.keyframe_insert("rotation_euler",frame=frame)
    tail.rotation_euler.z=.06*math.sin(t*1.9)
    tail.keyframe_insert("rotation_euler",frame=frame)
    # Update transforms then compute wrist goals relative to the book and cover.
    hinge.update_tag()
    book.update_tag()
    bpy.context.view_layer.update()
    hold_pose=orient((-.55,.18,.41),(0,1,0))
    hold_contact = book.matrix_world @ Vector((bw*.496,-.106,-bh*.23))
    ik("hold",hold_contact,hold_pose)
    grip_rot=book.rotation_euler.to_quaternion() @ Quaternion((0,0,1),angle) @ orient((.12,-.20,-.95),(0,1,0))
    # Matching fingertip contact locator built from the cover's local coordinates.
    cover_rot=book.rotation_euler.to_quaternion() @ Quaternion((0,0,1),angle)
    grip=book.matrix_world @ (Vector(hinge.location) + Quaternion((0,0,1),angle) @ Vector((.47,-.039,bh*.479)))
    paw_at_grip=grip + cover_rot @ Vector((0,-.071,.049))
    base=Vector((-.70,-.61,1.92))
    wave_pace=ease((t-.28)/.61)*(1-ease((t-5.08)/1.10))
    wx=.105*math.sin(t*6.3)+.027*math.sin(t*12.6)
    wave=Vector((-.93+wx,-.64,2.57+.06*math.cos(t*6.3)))
    wave_rot=orient((wx*4.3,.11,.95),(0,-1,0))
    rest_rot=orient((.24,-.44,-.64),(0,-1,0))
    palm=base.lerp(wave,wave_pace)
    palm_rot=rest_rot.slerp(wave_rot,wave_pace)
    reach=ease((t-7)/.52)
    palm=palm.lerp(paw_at_grip,reach)
    palm_rot=palm_rot.slerp(grip_rot,reach)
    ik("open",palm,palm_rot)

def light(name, kind, pos, energy, color, size):
    data=bpy.data.lights.new(name,kind)
    data.energy=energy
    data.color=color
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.location=pos
    if kind=="AREA":
        data.shape="DISK"
        data.size=size
    else:
        data.shadow_soft_size=size
    return obj

def aim(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()

aim(light("Large warm key","AREA",(-3.1,-4.8,5.45),420,(1,.76,.53),4.0),(0,0,1.65))
aim(light("Soft icy fill","AREA",(4.5,-3.1,4.6),240,(.63,.75,1),4.0),(0,0,1.7))
aim(light("Golden cap rim","AREA",(-.7,1.37,5.24),265,(1,.67,.34),3.2),(0,0,2))
aim(light("Soft face catchlight","AREA",(-.1,-5,3.6),70,(1,.83,.7),2.2),(0,0,2.3))
light("Firebox bounce","POINT",(fire_x,.16,.8),135,(1,.291,.039),.43)
light("Tree star bounce","POINT",(tree_x,.43,3.15),30,(1,.56,.18),.72)

scene=bpy.context.scene
scene.world.use_nodes=True
scene.world.node_tree.nodes.get("Background").inputs[0].default_value=(.30,.27,.28,1)
scene.world.node_tree.nodes.get("Background").inputs[1].default_value=.31
cam_data=bpy.data.cameras.new("Fixed whole-character camera")
camera=bpy.data.objects.new("Fixed whole-character camera",cam_data)
bpy.context.collection.objects.link(camera)
camera.location=(.57,-10.6,4.13)
aim(camera,(-.08,.16,1.83))
cam_data.type="ORTHO"
cam_data.ortho_scale=7.47
scene.camera=camera
scene.view_settings.view_transform="AgX"
scene.view_settings.look="AgX - Medium High Contrast"
scene.view_settings.exposure=.28
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=5
scene.cycles.use_denoising=True
scene.cycles.max_bounces=4
scene.cycles.diffuse_bounces=2
scene.cycles.glossy_bounces=2
scene.render.resolution_x=832
scene.render.resolution_y=468
scene.render.resolution_percentage=100
scene.render.fps=24
scene.frame_start=1
scene.frame_end=240
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGB"
scene.render.image_settings.compression=15
scene.render.filepath=str(HERE/"frames"/"frame")
scene.frame_set(37)
bpy.context.preferences.filepaths.save_version=0
bpy.context.preferences.filepaths.use_file_compression=True
bpy.ops.wm.save_as_mainfile(filepath=str(WORKSPACE/"outputs"/"dec01-test-3d-rig.blend"))
if "--preview" in sys.argv:
    scene.render.resolution_percentage=65
    scene.cycles.samples=4
    for still in (37,182,211,238):
        scene.frame_set(still)
        scene.render.filepath=str(HERE/f"preview-{still}.png")
        bpy.ops.render.render(write_still=True)
