from pathlib import Path
import subprocess,time
p=Path(__file__).resolve().parent
args=['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-f','image2pipe','-framerate','24','-vcodec','png','-i','pipe:0','-vf','scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p','-an','-c:v','libx264','-preset','slow','-crf','17','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-movflags','+faststart',str(p/'locked.mp4')]
proc=subprocess.Popen(args,stdin=subprocess.PIPE)
for i in range(1,241):
 f=p/'frames-facial-lock'/f'shot-{i:04d}.png'
 for k in range(600):
  if f.is_file() and f.stat().st_size>100:
   with f.open('rb') as fl:
    fl.seek(-12,2);end=fl.read()
   if b'IEND' in end:break
  time.sleep(.25)
 else:raise RuntimeError(f'Frame unavailable: {i}')
 proc.stdin.write(f.read_bytes())
proc.stdin.close();assert proc.wait()==0
