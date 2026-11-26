from pathlib import Path
import math
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1280, 720
FPS = 25
DURATION = 3.2
SIZE = (WIDTH, HEIGHT)
base=ImageOps.fit(Image.open(HERE/"book-plate.png").convert("RGBA"),SIZE,method=Image.Resampling.LANCZOS)
sprites=Image.open(HERE/"paw-sprites.png").convert("RGBA")
SW,SH=sprites.size
paws=[]
for bounds in [(0,0,SW//2,SH),(SW//2,0,SW,SH)]:
    half=sprites.crop(bounds)
    paw=half.crop(half.getbbox())
    factor=455/paw.height
    paws.append(paw.resize((round(paw.width*factor),455), Image.Resampling.LANCZOS))
FFMPEG = "/opt/homebrew/bin/ffmpeg"
FONT="/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf"
COVER_W,COVER_L=520,730
PAPER_W,PAPER_L=520,730
BOOK_W=198
NEAR,FAR=163,-151

def smooth(x):
    x=max(0,min(1,x))
    return x*x*(3-2*x)

def texture(w,h,colour,grain=4,seed=0):
    rng=np.random.default_rng(seed)
    x=np.linspace(0,1,w)[None,:]
    y=np.linspace(0,1,h)[:,None]
    noise=rng.normal(0,grain,(h,w))
    brightness=8*(1-y)+7*(1-x)+noise
    arr=(np.asarray(colour)+brightness[:,:,None]).clip(0,255).astype("uint8")
    return Image.fromarray(arr).convert("RGBA")

cover=texture(COVER_W,COVER_L,(51,31,72),5,47)
d=ImageDraw.Draw(cover)
d.rounded_rectangle((9,8,510,721),20,outline="#271c34",width=11)
d.rounded_rectangle((26,23,493,706),12,outline="#c68f4f",width=5)
d.rounded_rectangle((38,35,480,694),9,outline="#8d5a37",width=2)
for x,y,dx,dy in [(45,43,1,1),(475,43,-1,1),(45,688,1,-1),(475,688,-1,-1)]:
    d.line((x,y+77*dy,x,y,x+77*dx,y),fill="#cf9b59",width=4)
    d.line((x+11*dx,y+57*dy,x+11*dx,y+11*dy,x+57*dx,y+11*dy),fill="#b67a42",width=2)
d.text((264,350),"1С",font=ImageFont.truetype(FONT,170),fill="#201122",anchor="mm",stroke_width=2)
d.text((260,346),"1С",font=ImageFont.truetype(FONT,170),fill="#e5b873",anchor="mm",stroke_width=1,stroke_fill="#c98a46")
inside=texture(COVER_W,COVER_L,(73,45,87),4,12)
d=ImageDraw.Draw(inside)
d.rounded_rectangle((13,12,507,717),15,outline="#9b7252",width=4)
d.rectangle((25,23,494,706),fill="#60476f")
page=texture(PAPER_W,PAPER_L,(207,169,112),1.5,7)
d=ImageDraw.Draw(page)
d.rectangle((11,13,PAPER_W-12,PAPER_L-14),outline="#cfb182",width=2)
lines=texture(450,70,(170,121,72),1.5,19)
d=ImageDraw.Draw(lines)
for y in (4,13,24,32,42,51,59,64):
 d.line((0,y,450,y), fill="#be945e", width=1)

def project(u,v,z=0):
    return (584+1.43*u+.24*v,526+.80*v-.93*z)

def quad(left,right,v0,v1,z):
    return [project(left,v0,z), project(right,v0,z), project(right,v1,z), project(left,v1,z)]

def layer(frame,skin,quad):
    dst=np.array(quad,dtype=np.float64)
    x0=max(0,math.floor(dst[:,0].min()))
    x1=min(WIDTH,math.ceil(dst[:,0].max())+2)
    y0=max(0,math.floor(dst[:,1].min()))
    y1=min(HEIGHT,math.ceil(dst[:,1].max())+2)
    if x1<=x0 or y1<=y0:
        return
    dst-=np.array((x0,y0))
    w,h=skin.size
    src=((0,0),(w,0),(w,h),(0,h))
    system=[]; data=[]
    for (x,y),(u,v) in zip(dst,src):
        system.extend(((x,y,1,0,0,0,-u*x,-u*y),(0,0,0,x,y,1,-v*x,-v*y)))
        data.extend((u,v))
    try:
        coeff=np.linalg.solve(system,data)
    except np.linalg.LinAlgError:
        return
    frame.alpha_composite(skin.transform((x1-x0,y1-y0),Image.Transform.PERSPECTIVE,list(coeff),Image.Resampling.BICUBIC),(x0,y0))

def place_paw(frame,index,grip,rotate):
    paw=paws[index]
    # Pose anchors lie near the center of the rounded tips, not at sleeve ends.
    anchor=((.78,.20),(.22,.20))[index]
    rot=paw.rotate(rotate,resample=Image.Resampling.BICUBIC,expand=True)
    a=math.radians(rotate)
    x=(anchor[0]-.5)*paw.width
    y=(anchor[1]-.5)*paw.height
    rx=rot.width/2+math.cos(a)*x+math.sin(a)*y
    ry=rot.height/2-math.sin(a)*x+math.cos(a)*y
    frame.alpha_composite(rot,(round(grip[0]-rx),round(grip[1]-ry)))

def create(t):
    frame=base.copy()
    f=smooth((t-.36)/1.64)
    theta=math.pi*f
    # A small settling movement follows the main hinge rotation.
    theta-=.030*math.sin(16*max(0,t-2.0))*math.exp(-6*max(0,t-2.0))*float(t>2)
    hinge_z=24
    corner_x=BOOK_W*math.cos(theta)
    corner_z=hinge_z+BOOK_W*math.sin(theta)
    # Contact shadow is independent of the set artwork.
    shadow=Image.new("RGBA",SIZE)
    sh=ImageDraw.Draw(shadow)
    sh.polygon([project(-10-155*f,FAR+4,0),project(BOOK_W+10,FAR+4,0),project(BOOK_W+19,NEAR+8,0),project(-15-155*f,NEAR+8,0)],fill=(20,12,21,115))
    frame.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(25)))
    # Spine, fixed back cover, and the right-hand page block.
    layer(frame,cover,quad(-12,BOOK_W+9,FAR-7,NEAR+6,0))
    side=[project(3,NEAR-5,4),project(BOOK_W,NEAR-5,4),project(BOOK_W,NEAR-5,24),project(3,NEAR-5,24)]
    layer(frame,lines,side)
    layer(frame,page,quad(4,BOOK_W-6,FAR+2,NEAR-5,24))
    # Book cover is a separate surface rotating around a rigid spine.
    hinge0=project(0,FAR-6,hinge_z)
    hinge1=project(0,NEAR+5,hinge_z)
    edge0=project(corner_x,FAR-6,corner_z)
    edge1=project(corner_x,NEAR+5,corner_z)
    skin=cover if theta<math.pi*.5 else inside
    layer(frame,skin,[hinge0,edge0,edge1,hinge1])
    d=ImageDraw.Draw(frame)
    d.line([edge0,edge1],fill="#6e4c6b",width=3)
    if f>.66:
        # A left page follows the opening cover and relaxes onto it.
        page_theta=theta-.14*(1-smooth((f-.66)/.34))
        wx=(BOOK_W-9)*math.cos(page_theta)
        wz=hinge_z+2+(BOOK_W-9)*math.sin(page_theta)
        layer(frame,page,[project(0,FAR+4,26),project(wx,FAR+4,wz),project(wx,NEAR-4,wz),project(0,NEAR-4,26)])
    left_hand=project(-13-78*smooth((f-.52)/.48),NEAR-21,12)
    on_cover=project(.81*corner_x,NEAR-20,.81*corner_z+4)
    normal=project(BOOK_W-3,NEAR-21,14)
    release=smooth((f-.48)/.34)
    right_hand=tuple((1-release)*a+release*b for a,b in zip(on_cover,normal))
    place_paw(frame,0,(left_hand[0]-8,left_hand[1]+11),-9+9*f)
    place_paw(frame,1,(right_hand[0]+10,right_hand[1]+6),8-10*math.sin(math.pi*f))
    return frame.convert("RGB")

if __name__=="__main__":
    p=subprocess.Popen([FFMPEG,"-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-video_size",f"{WIDTH}x{HEIGHT}","-framerate",str(FPS),"-i","-","-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(HERE/"opening-motion-test.mp4")],stdin=subprocess.PIPE)
    for i in range(round(DURATION*FPS)):
        p.stdin.write(create(i/FPS).tobytes())
    p.stdin.close()
    assert p.wait()==0
