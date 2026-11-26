from pathlib import Path
import math
import random
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
BOARD = ROOT / "outputs/storyboard-01-cinematic-25d.png"
MASTER = WORK / "picture.mp4"
FPS = 25
DURATION = 28
SIZE = (1920, 1080)
FFMPEG = "/opt/homebrew/bin/ffmpeg"

board = Image.open(BOARD).convert("RGB")
frames = [board.crop(b) for b in [(5,5,765,508),(772,5,1531,508),(5,516,765,1019),(772,516,1531,1019)]]
RESAMPLE = Image.Resampling.BICUBIC

def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x*x*(3-2*x)

def glow(im, x, y, radius, alpha, colour):
    diameter = 2*radius
    y_grid, x_grid = np.ogrid[-radius:radius,-radius:radius]
    strength = np.clip(1-(x_grid*x_grid+y_grid*y_grid)/(radius*radius), 0, 1)**2
    mask = Image.fromarray(np.uint8(strength*alpha))
    im.paste(colour, (x-radius, y-radius, x+radius, y+radius), mask)

def warp(im, regions):
    w,h=im.size
    step=28
    xs=sorted(set(range(0,w,step))|{w})
    ys=sorted(set(range(0,h,step))|{h})
    coords={}
    for y in ys:
        for x in xs:
            u,v=float(x),float(y)
            for cx,cy,rx,ry,dx,dy,angle in regions:
                nx=(x-cx)/rx
                ny=(y-cy)/ry
                weight = max(0, 1-nx*nx-ny*ny)**2
                if weight:
                    u+=weight*(dx-angle*(y-cy))
                    v+=weight*(dy+angle*(x-cx))
            coords[(x,y)]=(max(0,min(w,u)),max(0,min(h,v)))
    mesh=[]
    for y,y1 in zip(ys,ys[1:]):
        for x,x1 in zip(xs,xs[1:]):
            quad=(*coords[(x,y)],*coords[(x,y1)],*coords[(x1,y1)],*coords[(x1,y)])
            mesh.append(((x,y,x1,y1),quad))
    return im.transform(im.size,Image.Transform.MESH,mesh,RESAMPLE)

rng=random.Random(101)
flakes=[(rng.uniform(0,760),rng.uniform(0,503),rng.uniform(25,75),rng.choice((1,1,1,2)),rng.uniform(75,175)) for _ in range(73)]
OUTRO = 0.35
SPEECH_STARTS = (4.20, 14.15)

def envelope(name):
    audio = WORK / f"vasily-{name}.mp3"
    if not audio.exists():
        return np.zeros(1)
    data = subprocess.check_output([FFMPEG, "-v", "error", "-i", str(audio), "-f", "f32le", "-ac", "1", "-ar", "48000", "-"])
    samples = np.frombuffer(data, dtype="<f4")
    window = 48000 // FPS
    samples = np.pad(samples, (0, -len(samples) % window))
    rms = np.sqrt(np.mean(samples.reshape(-1,window)**2, axis=1))
    return np.clip(np.sqrt(rms/.095)-.14,0,1)

envelopes = tuple(envelope(name) for name in ("greeting","riddle"))

def speech_motion(index, shot_t, shot_start):
    time = shot_t + shot_start - SPEECH_STARTS[index]
    values = envelopes[index]
    return float(np.interp(time*FPS, np.arange(len(values)), values, left=0, right=0))


def animate(index, t):
    base=frames[index]
    if index==0:
        im=base.copy()
        # Build snow over the artwork, with reduced density around the date.
        snow=Image.new("RGBA", im.size)
        d=ImageDraw.Draw(snow)
        for n,(x,y,s,r,a) in enumerate(flakes):
            xx=(x+math.sin(.62*t+n)*10+t*(8+(n%5)))%760
            yy=(y+s*t)%503
            if 325<xx<728 and 125<yy<224:
                continue
            d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=(231,242,255,round(a)))
        im.paste(snow,(0,0),snow)
        for n,(x,y) in enumerate(((92,104),(201,116),(310,151),(393,122),(489,120),(652,71))):
            intensity=13+22*(.5+.5*math.sin(t*2+n*2))
            glow(im,x,y,14,intensity,(255,197,117))
        return im
    if index==1:
        wave=(math.sin(2*math.pi*1.75*t)*.36
              *smoothstep(t/.42)*(1-smoothstep((t-2.0)/.55)))
        breath=math.sin(t*2.2)*1.05
        speech=speech_motion(0,t,4)
        im=warp(base,[(478,173,77,80,1.8*wave,0,wave),
                      (325,299,167,163,1.6*math.sin(t*1.8),breath,.02*math.sin(t*1.8)),
                      (347,164,29,21,0,3.1*speech-.75,0),
                      (47,365,72,102,4*math.sin(t*8.1),5*math.sin(t*7.9),.09*math.cos(t*4.8))])
        glow(im,57,357,89,18+10*math.sin(t*6.2),(255,169,72))
        return im
    if index==2:
        opening=smoothstep(t/1.4)
        lift=math.sin(math.pi*opening)
        im=warp(base,[(433,302,147,103,-6*(1-opening),6*(1-opening),.13*(1-opening)),
                      (485,244,82,74,6*lift,-15*lift,-.11*lift),
                      (293,156,127,125,0,2*lift,-.019*lift),
                      (44,396,65,95,4*math.sin(t*8.8),5*math.sin(t*9.6),.07*math.sin(t*4.8))])
        glow(im,38,393,79,18+10*math.sin(t*6.2),(255,171,78))
        return im
    speech=speech_motion(1,t,14)
    gesture=math.sin(math.pi*smoothstep((t-.25)/1.9))
    im=warp(base,[(281,172,87,63,-4*gesture,1.6*gesture,.12*gesture),
                  (219,157,29,19,0,3.1*speech-.75,0),
                  (204,312,123,132,0,1.6*math.sin(t*2),.018*math.sin(t*2)),
                  (38,370,60,88,4*math.sin(t*8),5*math.sin(t*8.4),.065*math.sin(t*5))])
    glow(im,30,366,66,15+8*math.sin(t*6.4),(255,175,82))
    return im

# Each shot is framed by crossing the four original panels; the verse card stays locked.
starts=(0,4,11,14)
shot_tops=(20,4,6,4)
def source_frame(index, t):
    im=animate(index,t)
    width,height=im.size
    scale=(1+.034*smoothstep(t/4)) if index==0 else (1+.025*smoothstep(t/9))
    if index==3:
        scale=1
    w=width/scale
    h=w*9/16
    x=(width-w)/2
    y=shot_tops[index]+(width-w)*.26
    return im.resize(SIZE, Image.Resampling.LANCZOS,box=(x,y,x+w,y+h))

def render():
    process=subprocess.Popen([FFMPEG,"-y","-hide_banner","-loglevel","error","-f","rawvideo","-pixel_format","rgb24","-video_size",f"{SIZE[0]}x{SIZE[1]}","-framerate",str(FPS),"-i","-","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(MASTER)],stdin=subprocess.PIPE)
    try:
        for i in range(DURATION*FPS):
            now=i/FPS
            index=max(j for j,s in enumerate(starts) if now>=s)
            t=now-starts[index]
            im=source_frame(index,t)
            if index==1 and t<.24:
                im=Image.blend(source_frame(0,4),im,smoothstep(t/.24))
            if now<.36:
                im=Image.blend(Image.new('RGB',SIZE,(16,19,32)),im,smoothstep(now/.36))
            if now>DURATION-OUTRO:
                im=Image.blend(im,Image.new('RGB',SIZE,(16,19,32)),smoothstep((now-DURATION+OUTRO)/OUTRO))
            process.stdin.write(im.tobytes())
    finally:
        process.stdin.close()
    if process.wait():
        raise RuntimeError("Video encoding failed")

def soundtrack():
    sr=48000
    samples=np.zeros((DURATION*sr,2),np.float32)
    def add(t,s,amp,pan=0):
        start=round(t*sr)
        length=min(len(s),len(samples)-start)
        if length>0:
            samples[start:start+length,0]+=s[:length]*(amp*math.sqrt((1-pan)/2))
            samples[start:start+length,1]+=s[:length]*(amp*math.sqrt((1+pan)/2))
    def bell(midi,length):
        t=np.arange(round(length*sr))/sr
        f=440*2**((midi-69)/12)
        env=(1-np.exp(-t*250))*np.exp(-t*3.2)
        end=np.clip((length-t)/.08,0,1)
        return env*end*(.76*np.sin(2*np.pi*f*t)+.17*np.sin(2*np.pi*f*2*t)*np.exp(-t*3)+.10*np.sin(2*np.pi*f*3.98*t)*np.exp(-t*6))
    # Original celesta phrase. The same short motif can be reused on every title.
    notes=[(.14,72),(.47,76),(.80,79),(1.22,81),(1.63,79),(1.97,76),(2.32,74),(2.68,76),(3.08,72)]
    for i,(offset,midi) in enumerate(notes):
        tone=bell(midi,1.17)
        add(offset,tone,.20,(-1)**i*.25)
        add(offset+.108,tone,.032,(-1)**(i+1)*.41)
    for start,chord in [(0,(48,55,64)),(1.65,(45,52,60)),(2.65,(43,55,62)),(3.18,(48,55,64))]:
        for j,midi in enumerate(chord):
            add(start+j*.04,bell(midi,1.6),.078,(j-1)*.35)
    audio_rng=np.random.default_rng(42)
    # Warm crackling texture and quick paper rustle in the reading room.
    for start in np.arange(4.18,DURATION-.21,.32):
        k=int(audio_rng.integers(360,3500))
        t=np.arange(k)/sr
        noise=audio_rng.normal(size=k)
        softened=np.convolve(noise,np.ones(6)/6,mode='same')
        click=(softened+.3*np.sin(t*2*np.pi*129))*np.exp(-t*81)*(1-np.exp(-t*700))
        add(start+float(audio_rng.uniform(0,.24)),click,float(audio_rng.uniform(.005,.030)),-.46)
    length=round(.66*sr)
    t=np.arange(length)/sr
    paper=np.convolve(audio_rng.normal(0,1,length),np.ones(5)/5,mode='same')
    paper*=np.sin(np.pi*t/.66)**1.8*(.35+.65*np.sin(t*104)**2)
    add(12.54,paper,.042,.10)
    for i,midi in enumerate((67,72,76)):
        add(14.02+i*.06,bell(midi,.87),.038,(i-1)*.18)
    for i,midi in enumerate((72,76,72)):
        add(26.18+i*.34,bell(midi,1.3),.057,(i-1)*.25)
    fade=round(.36*sr)
    samples[-fade:]*=np.linspace(1,0,fade)[:,None]
    with wave.open(str(WORK/"music-and-ambience.wav"),'wb') as target:
        target.setnchannels(2)
        target.setsampwidth(2)
        target.setframerate(sr)
        target.writeframes(np.int16(np.clip(samples,-1,1)*32767).tobytes())

if __name__=="__main__":
    soundtrack()
    render()
