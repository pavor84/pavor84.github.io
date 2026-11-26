from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
here=Path(__file__).parent
base=here.parents[2]/'outputs'
for nm,src,w,b in [('board','storyboard-01-cinematic-25d',760,(550,50,650,137)),('end','dec01-i2v-last',880,(300,185,565,355)),('start','dec01-i2v-first',880,(275,185,555,355)),('face','dec01-i2v-last',880,(247,10,507,216))]:
 im=Image.open(base/(src+'.png')).convert('RGB')
 scale=3 if nm=='board' else 2
 h=round(im.height*w/im.width)
 im=im.resize((w*scale,h*scale),Image.Resampling.LANCZOS)
 x0,y0,x1,y1=b
 im=im.crop(tuple(v*scale for v in b))
 dr=ImageDraw.Draw(im,'RGBA')
 for x in range((x0+9)//10*10,x1,10):
  i=(x-x0)*scale;dr.line((i,0,i,im.height),fill=(255,255,255,65));dr.text((i+1,1),str(x),fill='white',stroke_width=1,stroke_fill='black')
 for y in range((y0+9)//10*10,y1,10):
  i=(y-y0)*scale;dr.line((0,i,im.width,i),fill=(255,255,255,65));dr.text((1,i+1),str(y),fill='white',stroke_width=1,stroke_fill='black')
 im.save(here/(nm+'-grid.jpg'),quality=94)
