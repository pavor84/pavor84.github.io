from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
p=Path(__file__).parent
# Check static camera corners, frame cadence, and inspect poses across the cut-free shot.
files=sorted((p/'frames-facial-lock').glob('shot-*.png'));assert len(files)==240
prev=None;motion=[]
for k in [1,12,28,73,148,163,171,177,181,186,190,193,198,203,209,214,222,232,240]:
 a=Image.open(files[k-1]);assert a.size==(1280,720)
 if k in [1,163,177,181,186,190,193,198,203,209,214,222]:
  c=a.crop((420,292,872,538));c.thumbnail((312,180))
  motion.append((k,c.copy()))
sheet=Image.new('RGB',(4*312,3*196),'#18141a');d=ImageDraw.Draw(sheet)
for i,(k,c) in enumerate(motion):
 x=(i%4)*312;y=(i//4)*196;sheet.paste(c,(x,y));d.text((x+4,y+170),f'{(k-1)/24:.2f} s',fill='white')
sheet.save(p/'verified-contacts.jpg',quality=93)
