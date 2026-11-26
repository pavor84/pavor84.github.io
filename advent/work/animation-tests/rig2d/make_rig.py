from pathlib import Path
import math
import subprocess

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / "work/pilot-dec01"
FFMPEG = "/opt/homebrew/bin/ffmpeg"
SIZE = (1520, 1006)
SCALE = 2
FPS = 25
SECONDS = 10
LANCZOS = Image.Resampling.LANCZOS
BICUBIC = Image.Resampling.BICUBIC
base = Image.open(HERE / "clean-plate.png").convert("RGBA").resize(SIZE, LANCZOS)
original = Image.open(OLD / "greeting-source.png").convert("RGBA").resize(SIZE, LANCZOS)
clean_original = Image.open(OLD / "greeting-clean.png").convert("RGBA").resize(SIZE, LANCZOS)
source_paws = Image.open(OLD / "paw-sprites.png").convert("RGBA")
headless = Image.open(HERE/"headless.png").convert("RGBA").resize(SIZE,LANCZOS)
head_outline = [(160,75),(220,48),(270,20),(289,9),(307,6),(384,18),(399,21),(402,27),
 (378,41),(392,45),(401,49),(406,64),(406,92),(410,104),(417,113),(433,133),
 (438,148),(434,169),(423,185),(410,194),(398,204),(392,212),(380,218),
 (355,225),(330,224),(306,220),(271,218),(247,210),(222,211),(216,200),
 (217,171),(210,154),(206,152),(207,167),(201,173),(179,173),(170,170),
 (181,135),(184,121),(184,111),(187,84),(163,81)]
head_anchor=(329,213)
head_mask=Image.new("L",SIZE)
ImageDraw.Draw(head_mask).polygon([tuple(round(n*SCALE) for n in p) for p in head_outline],fill=255)
head_mask=head_mask.filter(ImageFilter.GaussianBlur(2.4))
head_bounds=head_mask.getbbox()
replace_zone=head_mask.filter(ImageFilter.MaxFilter(17)).filter(ImageFilter.GaussianBlur(8))
main_plate=Image.composite(headless,base,replace_zone)

def px(point):
    return tuple(round(n*SCALE) for n in point)

def pick(image, polygon, anchor, bounds=None):
    alpha = Image.new("L", image.size)
    ImageDraw.Draw(alpha).polygon(polygon, fill=255)
    alpha = ImageChops.multiply(alpha.filter(ImageFilter.GaussianBlur(1.4)), image.getchannel("A"))
    art = image.copy()
    art.putalpha(alpha)
    bounds = bounds or alpha.getbbox()
    cropped = art.crop(bounds)
    local_anchor = (anchor[0]-bounds[0],anchor[1]-bounds[1])
    return cropped, local_anchor

wave_outline = [(438,183),(445,174),(450,167),(455,153),(461,145),(468,140),(475,139),
 (480,142),(485,137),(492,140),(498,145),(504,148),(507,156),(506,161),(510,167),
 (507,178),(502,184),(498,191),(490,197),(488,205),(485,213),(478,219),(467,218),
 (456,212),(446,205),(439,194)]
wave, wave_wrist = pick(original, list(map(px,wave_outline)),px((449,194)))

left_outline = [(311,337),(312,327),(321,313),(330,307),(337,307),(345,310),(354,312),
 (361,320),(365,328),(365,339),(357,349),(347,354),(337,357),(327,356),(318,349)]
left_hand, left_wrist = pick(clean_original,list(map(px,left_outline)),px((320,337)))

# Hold sprite: a separate wrist and curled paw from the reference-style asset sheet.
def sheet(x, y):
    return (round(x*source_paws.width/800), round(y*source_paws.height/400))
grip_outline = [(463,39),(576,39),(618,63),(648,100),(648,143),(649,164),
    (648,181),(635,194),(618,209),(595,238),(575,256),(548,251),(515,225),
    (488,195),(462,163),(444,125),(447,86)]
grip, grip_wrist = pick(source_paws,[sheet(x,y) for x,y in grip_outline],sheet(608,208))
factor=119/grip.width
grip=grip.resize((119,round(grip.height*factor)),LANCZOS)
grip_wrist=tuple(round(v*factor) for v in grip_wrist)

def smooth(x):
    x=max(0,min(1,x))
    return x*x*(3-2*x)

def interp(p,q,t):
    return tuple((1-t)*a+t*b for a,b in zip(p,q))

def motion(t, poses):
    for (a,p),(b,q) in zip(poses, poses[1:]):
        if t<=b:
            return interp(p,q,smooth((t-a)/(b-a)))
    return poses[-1][1]

def texture(w,h,c,seed,scale=1.2):
    yy,xx=np.mgrid[0:h,0:w]
    norm_x=xx/(w-1)
    norm_y=yy/(h-1)
    grain=np.random.default_rng(seed).normal(0,scale,(h,w))
    weave=2*np.sin(xx*1.7)*np.sin(yy*2.1)
    bright=8*(1-norm_y)+6*(1-norm_x)+grain+weave
    rgb=(np.array(c)+bright[...,None]).clip(0,255)
    return Image.fromarray(rgb.astype("uint8")).convert("RGBA")

def sleeve(seed, upper=False):
    w,h=128,230
    # Resample original costume pixels. This keeps the wrinkles, nap, and
    # reflected fireplace light consistent with the chest and cuff.
    crop = ((269,253),(259,295),(298,309),(300,266)) if upper else ((276,309),(294,344),(323,333),(318,302))
    fabric=original.transform((w,h),Image.Transform.QUAD,tuple(v for p in crop for v in px(p)),BICUBIC)
    colour=texture(w,h,(53,32,72) if upper else (62,37,81),seed,2.6)
    img=Image.blend(fabric,colour,.17)
    a=Image.new("L",(w,h))
    ImageDraw.Draw(a).rounded_rectangle((3,1,w-4,h-2),radius=40,fill=255)
    yy,xx=np.mgrid[0:h,0:w]
    n=xx/(w-1)
    light=20*np.exp(-((n-.25)/.25)**2) - 28*np.clip((n-.48)/.53,0,1)**1.3
    rim=6*np.exp(-((n-.075)/.055)**2)
    arr=np.array(img).astype(float)
    arr[:,:,:3]+=(.64*(light+rim))[...,None]*[1.1,.69,1.15]
    img=Image.fromarray(arr.clip(0,255).astype("uint8"))
    seam=ImageDraw.Draw(img)
    seam.line([(19,30),(19,196)],fill="#634775",width=1)
    if not upper:
        seam.line([(24,198),(w-25,198)],fill="#815c96",width=2)
        seam.line([(20,205),(w-21,205)],fill="#40264e",width=3)
    img.putalpha(a.filter(ImageFilter.GaussianBlur(2.2)))
    return img

upper = sleeve(12,upper=True)
fore = sleeve(31)

# Perspective correction from the actual original closed cover preserves its stamped title.
book_rect=clean_original.transform((250,355), Image.Transform.QUAD,
    tuple(v for p in ((372,268),(360,362),(430,354),(446,257)) for v in px(p)), BICUBIC)
front=texture(250,355,(51,30,69),17)
front_mask=Image.new("L",front.size)
ImageDraw.Draw(front_mask).rounded_rectangle((1,1,248,353),radius=5,fill=255)
rect_draw=ImageDraw.Draw(front)
rect_draw.rounded_rectangle((10,10,238,345),radius=4,outline="#c58c50",width=2)
front.alpha_composite(book_rect.resize((232,335),LANCZOS),(8,10))
front.putalpha(front_mask)
decor=ImageDraw.Draw(front)
decor.rounded_rectangle((6,6,243,348),radius=4,outline="#b77c47",width=2)
inside=texture(250,355,(76,51,85),27)
ImageDraw.Draw(inside).rounded_rectangle((6,8,244,346),radius=5,outline="#b88b60",width=3)
paper=texture(246,352,(218,178,114),9)
d=ImageDraw.Draw(paper)
d.rectangle((3,4,241,347),outline="#ad8151",width=1)
for u in range(1,18):
    d.line((u,4,u,347), fill=(166+min(u*3,30),123+min(u*3,30),74+min(u*2,28)),width=1)
edge=texture(250,35,(194,144,88),937)
ed=ImageDraw.Draw(edge)
for y in range(2,35,4):
    ed.line((0,y,249,y),fill="#976742",width=1)
spine=texture(50,355,(68,43,83),38)
sd=ImageDraw.Draw(spine)
for y in (32,149,280,330):
    sd.line((2,y,48,y-1),fill="#9b7049",width=2)

def layer(canvas, art, targets):
    dst=np.array([px(p) for p in targets],dtype=float)
    x0=max(0,math.floor(dst[:,0].min())-2)
    x1=min(canvas.width,math.ceil(dst[:,0].max())+2)
    y0=max(0,math.floor(dst[:,1].min())-2)
    y1=min(canvas.height,math.ceil(dst[:,1].max())+2)
    if x1<=x0 or y1<=y0:
        return
    dst-=np.array((x0,y0))
    w,h=art.size
    src=((0,0),(w,0),(w,h),(0,h))
    m=[];b=[]
    for (x,y),(u,v) in zip(dst,src):
        m.extend(((x,y,1,0,0,0,-u*x,-u*y),(0,0,0,x,y,1,-v*x,-v*y)))
        b.extend((u,v))
    try:
        c=np.linalg.solve(m,b)
    except np.linalg.LinAlgError:
        return
    patch=art.transform((x1-x0,y1-y0),Image.Transform.PERSPECTIVE,c,BICUBIC)
    canvas.alpha_composite(patch,(x0,y0))

def arm_segment(canvas, tex, p, q, first, last):
    dx,dy=(q[0]-p[0],q[1]-p[1])
    length=math.hypot(dx,dy)
    if length<2:
        return
    along=(dx/length,dy/length)
    across=(along[1],-along[0])
    p=tuple(a-b*7 for a,b in zip(p,along))
    q=tuple(a+b*7 for a,b in zip(q,along))
    layer(canvas,tex,[tuple(a-b*first for a,b in zip(p,across)),tuple(a+b*first for a,b in zip(p,across)),
                      tuple(a+b*last for a,b in zip(q,across)),tuple(a-b*last for a,b in zip(q,across))])

def place(canvas, art, anchor, target, angle=0, size=1, opacity=1):
    if opacity<=.001:
        return
    if size!=1:
        art=art.resize(tuple(round(v*size) for v in art.size),LANCZOS)
        anchor=tuple(round(v*size) for v in anchor)
    if opacity<.999:
        art=art.copy()
        art.putalpha(art.getchannel("A").point(lambda a:round(a*opacity)))
    rotated=art.rotate(angle,expand=True,resample=BICUBIC)
    a=math.radians(angle)
    x=anchor[0]-art.width*.5
    y=anchor[1]-art.height*.5
    at=(math.cos(a)*x+math.sin(a)*y+rotated.width*.5,-math.sin(a)*x+math.cos(a)*y+rotated.height*.5)
    pos=tuple(round(a-b) for a,b in zip(px(target),at))
    canvas.alpha_composite(rotated,pos)

def diffuse_shadow(canvas, points, opacity):
    a=Image.new("RGBA",canvas.size)
    ImageDraw.Draw(a).polygon(list(map(px,points)), fill=(26,12,24,opacity))
    canvas.alpha_composite(a.filter(ImageFilter.GaussianBlur(13)))

def project(u,v,z,state):
    # Face is upright while closed. The same spine tips toward the reader before opening.
    x,y,tilt=state
    return (x+88*u-12*v+30*z, y-9*u+(108-44*tilt)*v-31*z)

def plane(canvas,tex,a,b,v0,v1,z,state):
    layer(canvas,tex,[project(a,v0,z,state),project(b,v0,z,state),
                    project(b,v1,z,state),project(a,v1,z,state)])

def cover_point(s,v,angle,state):
    return project(s*math.cos(angle),v,s*math.sin(angle)+.01,state)

def book(canvas,t,state):
    angle=math.pi*smooth((t-7.17)/1.72)
    progress=angle/math.pi
    x0=-.1-.63*progress
    diffuse_shadow(canvas,[project(u,v,-.31,state) for u,v in ((x0,0),(1.13,0),(1.15,1.08),(x0,1.08))],89)
    plane(canvas,front,-.035,1.05,-.035,1.025,-.18,state)
    layer(canvas,edge,[project(-.005,0,-.15,state),project(1.025,0,-.15,state),
                       project(1.025,0,-.007,state),project(-.005,0,-.007,state)])
    plane(canvas,paper,.013,.99,.011,.99,-.012,state)
    cover_shape=[cover_point(s,v,angle,state) for s,v in ((0,0),(1,0),(1,1),(0,1))]
    (x0,y0),(x1,y1),_,(x3,y3)=cover_shape
    front_facing=(x1-x0)*(y3-y0)-(y1-y0)*(x3-x0)>0
    layer(canvas,front if front_facing else inside,cover_shape)
    if not front_facing:
        # The pages follow the inner cover around the same binding with a slight delay.
        a=angle-.045*(1-smooth((progress-.54)/.46))
        amount=smooth((progress-.594)/.085)
        skin=paper.copy()
        skin.putalpha(round(amount*255))
        layer(canvas,skin,[cover_point(s,v,a,state) for s,v in ((.018,.015),(.95,.015),(.95,.985),(.018,.985))])
    # Opaque width at an edge-on angle keeps the binding visible.
    line=ImageDraw.Draw(canvas)
    line.line([px(cover_point(1,.0,angle,state)),px(cover_point(1,1,angle,state))],fill="#684660",width=round(2.2*SCALE))
    plane(canvas,spine,-.104,.008,-.019,1.03,.014,state)
    return angle

closed_eyes=Image.open(HERE/"closed-eyes.png").convert("RGBA").resize(SIZE,LANCZOS)
eyelid_layers=[]
for cx,cy,rx,ry in [(301,144,24,24),(377.5,126.5,22,23)]:
    bbox=(*px((cx-rx-4,cy-ry-4)),*px((cx+rx+4,cy+ry+4)))
    eye=closed_eyes.crop(bbox)
    alpha=Image.new("L",eye.size)
    ImageDraw.Draw(alpha).ellipse((9,9,eye.width-9,eye.height-9),fill=255)
    alpha=alpha.filter(ImageFilter.GaussianBlur(5))
    eyelid_layers.append((eye,alpha,bbox[:2]))

def gaze_blink(canvas,t):
    if not any(abs(t-c)<.054 for c in (1.06,4.42,6.83,9.6)):
        return
    for art,alpha,p in eyelid_layers:
        a=art.copy()
        a.putalpha(alpha)
        canvas.alpha_composite(a,p)

def nod_head(canvas,t):
    nod=math.sin(math.pi*smooth((t-.52)/1.17))
    toward_book=smooth((t-6.42)/1.47)*(1-.14*smooth((t-9.26)/.7))
    turn=1.4*nod+2.9*toward_book
    drift=(.45*math.sin(2.8*t),.3*math.sin(2.4*t))
    head=base.copy()
    gaze_blink(head,t)
    head.putalpha(head_mask)
    head=head.crop(head_bounds)
    anchor=tuple(a-b for a,b in zip(px(head_anchor),head_bounds[:2]))
    place(canvas,head,anchor,(head_anchor[0]+drift[0]+4.8*toward_book,
             head_anchor[1]+drift[1]+2*nod+2.9*toward_book),angle=-turn)

def render(t):
    canvas=main_plate.copy()
    open_pose=smooth((t-6.38)/.74)
    settle=smooth((t-9.35)/.6)
    state=(365-15*open_pose,248+41*open_pose+4*settle,open_pose)
    angle=math.pi*smooth((t-7.17)/1.72)
    left_root=(275,249)
    left_elbow=(275+3*open_pose,316+14*open_pose)
    left_w=(328-9*open_pose,333+3*open_pose)
    # Pose changes at shoulder, elbow and wrist have independent ease curves.
    right_root=(408-7*open_pose,237+5*open_pose)
    right_pose=[
        (0,(462,190,443,230)),(.35,(465,187,442,229)),(.64,(481,187,448,224)),(.97,(460,176,444,222)),
        (1.28,(480,183,448,222)),(1.60,(459,177,444,222)),(1.91,(477,185,447,222)),
        (2.24,(463,189,446,227)),(2.61,(464,227,450,242)),
        (3.12,(443,298,444,279)),(3.44,(435,324,440,291)),(5.95,(435,324,440,291)),
        (6.37,(448,306,451,290)),(6.82,(441,283,450,269)),(7.10,(436,311,447,287)),
    ]
    if t<6.6:
        wx,wy,ex,ey=motion(t,right_pose)
        r_w=(wx,wy)
        r_e=(ex,ey)
        blend=smooth((t-2.69)/.29)
    else:
        grip_anchor=cover_point(.90,.49,angle,state)
        w_target=(grip_anchor[0]+15,grip_anchor[1]+14)
        rw,ry,ew,ey=motion(t,right_pose)
        reach=smooth((t-6.60)/.54)
        r_w=interp((rw,ry),w_target,reach)
        r_e=interp((ew,ey),(434-21*smooth((t-7.35)/1.25),294+26*math.sin(angle*.75)),reach)
        release=smooth((t-8.90)/.48)
        r_w=interp(r_w,(441,346),release)
        r_e=interp(r_e,(444,307),release)
        blend=1
    arm_segment(canvas,upper,left_root,left_elbow,20,17)
    arm_segment(canvas,fore,left_elbow,left_w,17,12)
    arm_segment(canvas,upper,right_root,r_e,16.5,16.5)
    arm_segment(canvas,fore,r_e,r_w,15,12.3)
    book(canvas,t,state)
    # Overlap only the nearest forearm segment, where the wrist grips the cover.
    # The sleeve remains visibly attached as the paw crosses the book.
    if t>=6.7:
        arm_segment(canvas,upper,right_root,r_e,16.5,16)
        arm_segment(canvas,fore,r_e,r_w,15.5,12)
    # Paw and cuff cover the edge of the cover, while the left hand anchors the spine.
    place(canvas,left_hand,left_wrist,left_w,0-4*open_pose,1.06)
    if blend<.999:
        bend=math.degrees(math.atan2(r_w[0]-r_e[0],-(r_w[1]-r_e[1])))
        place(canvas,wave,wave_wrist,r_w,24-bend,size=.88,opacity=1-blend)
    if blend>.001:
        place(canvas,grip,grip_wrist,r_w,-12+24*math.sin(angle),size=.76,opacity=blend)
    nod_head(canvas,t)
    return canvas.convert("RGB")

if __name__=="__main__":
    for i,t in enumerate((0,.65,1.28,2.62,3.6,6.7,7.24,7.79,8.25,8.67,9.10,9.76,4.42,8.86,1.06)):
        render(t).resize((760,503),LANCZOS).save(HERE/f"review-{i:02}.jpg",quality=93)
    # One camera, one uninterrupted render, no audio or edit track.
    output=HERE/"rig2d-preview.mp4"
    cmd=[FFMPEG,"-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24",
         "-s",f"{SIZE[0]}x{SIZE[1]}","-r",str(FPS),"-i","-","-an","-c:v","libx264",
         "-crf","18","-preset","fast","-pix_fmt","yuv420p","-movflags","+faststart",str(output)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(FPS*SECONDS):
            proc.stdin.write(render(i/FPS).tobytes())
    finally:
        proc.stdin.close()
    assert proc.wait()==0
