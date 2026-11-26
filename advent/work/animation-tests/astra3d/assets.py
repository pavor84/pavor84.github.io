from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
p=Path(__file__).resolve().parent
out=p.parents[2]/'outputs'
board=Image.open(out/'storyboard-01-cinematic-25d.png').convert('RGBA')
base=Image.open(out/'dec01-i2v-first.png').convert('RGB')
last=Image.open(out/'dec01-i2v-last.png').convert('RGB')
# Paint opacity around the original fur silhouette at native atlas resolution.
def cut(im, points, coord_w, name):
 scale=im.width/coord_w
 xy=[(round(x*scale),round(y*scale)) for x,y in points]
 mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(xy,fill=255)
 mask=mask.filter(ImageFilter.GaussianBlur(.68))
 bbox=mask.getbbox()
 tex=im.convert('RGBA');tex.putalpha(mask);tex.crop(bbox).save(p/(name+'.png'))
 return [i/scale for i in bbox]
arm_pts=[(588.8,103.8),(592.7,101.1),(594.4,98.2),(597.8,93),(600.3,90.2),(601.9,89.8),(603.3,88),(605.2,87.7),(606.4,84.7),(608,82),(609.9,78.1),(611.9,74.7),(614.3,73),(616.3,72.6),(618.4,73.4),(619.7,74.9),(621,73.3),(623.4,72.2),(625.1,72.1),(627.3,73),(628.5,74.6),(628.7,76.2),(630.7,76.6),(632.4,78.4),(632.8,80),(632.1,82.5),(633.2,83.4),(633.8,85.2),(633.5,87.1),(632.4,89.1),(631.4,90.6),(628.3,92.8),(626.8,95.2),(624.4,98.5),(622.8,100.5),(623.5,102.7),(623.5,105.3),(623.1,106.6),(623.5,108.9),(622.9,111.2),(619.1,115.8),(615.7,119.7),(611.3,124.4),(604.8,129.2),(603.3,128),(598.5,128.2),(594.5,126.1),(594.4,124.8),(592.8,123.4),(589.2,123.7),(587,120.4),(587.4,115),(588.7,109)]
print('arm',cut(board,arm_pts,760,'wave'))
left0=[(400,282),(404,278),(409,275.3),(414,275),(418,277),(422,278),(426,280),(429,281),(431,284),(434,286.7),(436.6,289),(437,292),(436,295),(435.5,299),(434,301),(433.2,304),(430.4,306),(427.7,308.7),(425,311.3),(421,312),(418,314),(414,314.5),(410,314.3),(406,312.5),(402,309),(400,305),(398.2,299),(398.7,292)]
left1=[(340,282),(344,277.5),(350,274),(355,273),(359,273.7),(363,274.7),(367,276),(370,276.7),(372,279),(373,281),(375.3,282.7),(376.5,285.7),(376.5,288.4),(378,291.5),(377.8,294.3),(376,296.2),(376.4,298.8),(375.5,301.5),(372.8,303.2),(370.5,305.8),(367,307.4),(363.8,308.4),(359,308.7),(356,308),(350,306.5),(346,304.5),(342,301.5),(339.5,297),(339,290)]
right1=[(510,288),(509.7,285.5),(511.7,281.7),(515,279.5),(515.6,277.5),(519,274),(522,273),(525,270),(528,269),(530,269.6),(533,268.4),(536.3,270),(539.3,273),(540.5,277.5),(540.1,284.7),(538.7,291.4),(537.7,295),(534.8,298.1),(530.6,301.2),(526,303.5),(522,304),(518.2,303.2),(514.2,300.4),(512.2,297.2),(510.1,294),(509.7,291.2)]
print('left0',cut(base,left0,880,'paw_left0'))
print('left1',cut(last,left1,880,'paw_left1'))
print('right1',cut(last,right1,880,'paw_right1'))
# Remove the book and visible gripping fur from each projection. The coat behind
# the hinge is filled from its own neighbouring colours across pyramid scales.
from PIL import ImageChops
import json
json.dump(cut(board,arm_pts,760,'wave'),open(p/'armbounds.json','w'))
def clean(im, polys, name):
 sc=im.width/880
 mask=Image.new('L',im.size,255);dr=ImageDraw.Draw(mask)
 for poly in polys:dr.polygon([(round(x*sc),round(y*sc)) for x,y in poly],fill=0)
 mask=mask.filter(ImageFilter.MinFilter(5))
 imA=np.asarray(im).astype(np.float32); known=np.asarray(mask).astype(np.float32)/255
 # A compact sample of the robe serves as deep fill for fully covered pixels.
 coat=im.crop(tuple(round(x*sc) for x in (346,242,374,274))).resize(im.size)
 prev=coat
 for scale in [32,16,8,4,2,1]:
  size=(im.width//scale,im.height//scale)
  def resize_arr(a):
   return np.asarray(Image.fromarray(a.astype(np.float32)).resize(size,Image.Resampling.BOX))
  k=resize_arr(known)
  cols=np.stack([resize_arr(imA[:,:,c]*known) for c in range(3)],axis=2)
  col=np.asarray(prev.resize(size,Image.Resampling.BILINEAR))*(1-k[:,:,None])+cols
  prev=Image.fromarray(np.clip(col,0,255).astype(np.uint8))
 bg=Image.composite(im,prev,mask.filter(ImageFilter.GaussianBlur(1)));bg.save(p/(name+'.png'))
book0=[(421.5,228),(429,227),(492,219.5),(496.5,224),(506,226.5),(507.5,228),(492,314),(490.2,317),(435,324),(425,323),(412,318),(412,292)]
book1=[(336,222),(342,220),(348,215.5),(360,211),(370,208),(381,210),(400,215),(416,220.5),(431,230),(443,247),(449,237),(465,225),(483,214),(504,206),(520,200),(527,200),(534,203),(538,206),(540,210.5),(550,211),(548,216),(521,304),(518,307),(456,330),(451,333),(436,333),(432,331),(369,310),(357,307)]
clean(base,[book0,left0],'base-clean');clean(last,[book1,left1,right1],'last-clean')
# Erase the foreground fur on the jacket atlas by sampling the same leather nearby.
def repair(im,polys):
 s=im.width/880;v=im.copy();tex=im.crop(tuple(round(i*s) for i in (386,267,404,289)))
 for poly in polys:
  m=Image.new('L',im.size); d=ImageDraw.Draw(m); d.polygon([(round(x*s),round(y*s)) for x,y in poly],fill=255)
  m=m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(.7))
  x0,y0,x1,y1=m.getbbox();patch=Image.new('RGB',im.size);patch.paste(tex.resize((x1-x0,y1-y0)),(x0,y0));v=Image.composite(patch,v,m)
 return v
repair(last,[left1,right1]).save(p/'cover-atlas.png')
uu,vv=np.meshgrid(np.linspace(0,1,640),np.linspace(0,1,160))
fibre=np.sin(vv*96+uu*.85)*1.8+np.cos(vv*197+uu*1.6)*2
stripe=np.exp(-((np.mod(vv*7.5+.05*np.sin(3*uu),1)-.4)/.10)**2)
shadow=12*np.exp(-uu*5)+5*np.cos(vv*2*3.14)+stripe*16
pg=np.stack([252-shadow*.5+fibre,224-shadow*.85+fibre,177-shadow+fibre],axis=2)
Image.fromarray(np.clip(pg,0,255).astype(np.uint8)).save(p/'paper.png')
def flatten(im,quad,size):
 coords=np.array(quad)*im.width/880
 a=[];b=[]
 for (u,v),(x,y) in zip([(0,0),(size[0],0),(size[0],size[1]),(0,size[1])],coords):
  a.extend([[u,v,1,0,0,0,-x*u,-x*v],[0,0,0,u,v,1,-y*u,-y*v]]);b.extend([x,y])
 return im.transform(size,Image.Transform.PERSPECTIVE,tuple(np.linalg.solve(a,b)),Image.Resampling.BICUBIC)
a=flatten(base,[(440.4,235),(505.7,226.6),(490.9,315.9),(432.4,323.7)],(240,330));a.save(p/'raw-board.png')
arm_hold0=[(343,227),(348,221.2),(353,219.5),(363,219),(372,219.5),(377,222.5),(381,229),(381.5,239),(382,249),(384,255.5),(390,258),(400,261),(409,264.8),(415,268.5),(417.8,273),(418,277),(416,284),(417,303),(413,313.2),(408,316.8),(403,318),(394,317.6),(387,316),(379,313),(370,310),(362,308),(355,305),(350,302),(344.5,299),(339.8,295),(336.6,290),(335.2,284),(334.9,278),(335.6,270),(337,260),(338.2,251),(339.4,243),(340.8,235)]
arm_hold1=[(344,225),(351,222),(360,225),(360,244),(371,265),(372,283),(373,304),(368,310),(356,310),(345,308.5),(337.5,306),(332,301.5),(326.7,295),(323,290.2),(320.4,287.2),(318,281.2),(317.3,274),(317.8,267.3),(321.1,259),(326,252),(332.8,245),(338.4,239),(341,232)]
bb=cut(base,arm_hold0,880,'hold_sleeve');(p/'sleevebounds.json').write_text(json.dumps(bb))
clean(base,[book0,left0,arm_hold0],'base-clean')
clean(last,[book1,left1,right1,arm_hold1],'last-clean')
# Restore the obscured six pixels of binding from its uninterrupted lower edge.
a=Image.open(p/'raw-board.png');a.paste(a.crop((0,266,15,308)).resize((15,74)),(0,192));a=a.crop((1,8,240,329));a.save(p/'front-leather.png')
# Keep all face and glasses pixels from a single source. Restrict the alternate
# projection to the shoulder area below the scarf and behind the opening volume.
first_bg=Image.open(p/'base-clean.png');last_bg=Image.open(p/'last-clean.png')
Y,X=np.mgrid[0:first_bg.height,0:first_bg.width].astype(np.float32);X*=880/first_bg.width;Y*=495/first_bg.height
def sm(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
mask=sm(211,235,Y)*(1-sm(324,348,Y))*sm(285,317,X)*(1-sm(544,560,X))
final_bg=Image.composite(last_bg,first_bg,Image.fromarray((255*mask).astype('uint8')))
final_bg.save(p/'closed-to-reading-coat.png')
