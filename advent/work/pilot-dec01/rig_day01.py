from pathlib import Path
import math
import subprocess

from PIL import Image, ImageDraw, ImageFilter
from book_motion import create as book_frame
from render import FFMPEG, FPS, DURATION, SIZE, frames, glow, smoothstep, source_frame, speech_motion

WORK = Path(__file__).resolve().parent
LAYOUT = Image.open(WORK / "greeting-source.png").convert("RGBA")
CLEAN = Image.open(WORK / "greeting-clean.png").convert("RGBA").resize(LAYOUT.size,Image.Resampling.LANCZOS)
PIVOT = (422, 233)
outline = [(407,218),(417,199),(430,188),(439,181),(448,170),(455,157),(462,145),
           (470,140),(478,141),(483,139),(491,140),(496,145),(501,149),(505,155),
           (506,161),(510,166),(509,175),(506,180),(500,188),(495,195),(490,201),
           (487,211),(480,220),(468,230),(456,242),(442,252),(432,252),(419,248),(411,237)]
limb_alpha=Image.new("L",LAYOUT.size)
ImageDraw.Draw(limb_alpha).polygon(outline,fill=255)
limb=LAYOUT.copy()
limb.putalpha(limb_alpha.filter(ImageFilter.GaussianBlur(.8)))
# Grow the removal matte past all antialiased edges of the unchanged source.
repair=limb_alpha.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(4))
background=Image.composite(CLEAN,LAYOUT,repair)
end_pose=-146
book_front=Image.new("L",LAYOUT.size)
ImageDraw.Draw(book_front).polygon([(356,253),(417,244),(451,251),(436,353),(352,364),(344,348),(348,274)],fill=255)
book_front=book_front.filter(ImageFilter.GaussianBlur(1.1))

def greeting(t):
    scene=background.copy()
    if t<.28:
        angle=-28*(1-smoothstep(t/.28))
    elif t<2.3:
        wave=smoothstep((t-.28)/.20)*(1-smoothstep((t-1.9)/.40))
        angle=11*math.sin((t-.28)*2*math.pi*1.55)*wave
    else:
        angle=end_pose*smoothstep((t-2.3)/.80)
    # Single rigid forearm, independent of face, book, chair, and background.
    scene.alpha_composite(limb.rotate(angle,resample=Image.Resampling.BICUBIC,center=PIVOT))
    if t>2.2:
        scene=Image.composite(background,scene,book_front)
    if t>2.95:
        scene=Image.blend(scene,background,smoothstep((t-2.95)/.18))
    rgb=scene.convert("RGB")
    glow(rgb,55,335,90,15+10*math.sin(t*5.3)+4*math.sin(t*9.7),(255,173,79))
    return rgb

def mouth(scene, center, amount):
    # Local offset only along the inside of the mouth and jaw transition.
    if amount<.04:
        return scene
    x,y=center
    bbox=(x-13,y-10,x+14,y+13)
    patch=scene.crop(bbox)
    h=patch.height* (1+.30*amount)
    patch=patch.resize((patch.width,round(h)),Image.Resampling.BICUBIC)
    mask=Image.new("L",patch.size)
    d=ImageDraw.Draw(mask)
    d.ellipse((4,4,patch.width-5,patch.height-7),fill=180)
    mask=mask.filter(ImageFilter.GaussianBlur(3))
    scene.paste(patch,(bbox[0],bbox[1]),mask)
    return scene

def frame_at(t):
    if t<4:
        return source_frame(0,t)
    if t<11:
        scene=greeting(t-4)
        scene=mouth(scene,(349,174),speech_motion(0,t-4,4))
        w=scene.width
        return scene.resize(SIZE,Image.Resampling.LANCZOS,box=(0,4,w,4+w*9/16))
    if t<14:
        return book_frame((t-11)*1.04).resize(SIZE,Image.Resampling.LANCZOS)
    scene=frames[3].copy()
    scene=mouth(scene,(215,160),speech_motion(1,t-14,14))
    glow(scene,30,345,62,16+7*math.sin((t-14)*6.4),(255,173,83))
    w=scene.width
    return scene.resize(SIZE,Image.Resampling.LANCZOS,box=(0,4,w,4+w*9/16))

def darken(im,alpha):
    return Image.blend(im,Image.new("RGB",im.size,(16,19,32)),alpha)

if __name__=="__main__":
    for name,t in [("wave_start",4.32),("wave_side",4.60),("wave_finish",7.67),("book_mid",12.27),("riddle",15.52)]:
        frame_at(t).resize((960,540),Image.Resampling.LANCZOS).save(WORK/f"rig-{name}.jpg",quality=88)
    p=subprocess.Popen([FFMPEG,"-y","-loglevel","error","-f","rawvideo","-pixel_format","rgb24",
                         "-video_size",f"{SIZE[0]}x{SIZE[1]}","-framerate",str(FPS),"-i","-",
                         "-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
                         "-movflags","+faststart",str(WORK/"repaired-picture.mp4")],stdin=subprocess.PIPE)
    for i in range(round(DURATION*FPS)):
        t=i/FPS
        im=frame_at(t)
        if t<.35:
            im=darken(im,1-smoothstep(t/.35))
        if t>DURATION-.35:
            im=darken(im,smoothstep((t-DURATION+.35)/.35))
        p.stdin.write(im.tobytes())
    p.stdin.close()
    assert p.wait()==0
