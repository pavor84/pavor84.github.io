import json
import struct
import subprocess
from pathlib import Path

here=Path(__file__).resolve().parent
destination=here.parents[2]/"outputs"/"dec01-test-3d-rig.mp4"
timeline=here/"frames"
expected=[timeline/f"frame{index:04}.png" for index in range(1,241)]
assert sorted(timeline.glob("frame*.png"))==expected, "Incomplete Blender frame sequence"
for frame in expected:
    with frame.open("rb") as file:
        header=file.read(24)
        assert header[:8]==b"\x89PNG\r\n\x1a\n", frame
        assert struct.unpack(">II",header[-8:])==(832,468), frame

ffmpeg="/opt/homebrew/bin/ffmpeg"
ffprobe="/opt/homebrew/bin/ffprobe"
staged=here/"encoded-and-validated.mp4"
subprocess.run([ffmpeg,"-hide_banner","-loglevel","error","-y","-framerate","24","-start_number","1","-i",str(timeline/"frame%04d.png"),"-frames:v","240","-an","-vf","scale=out_color_matrix=bt709,format=yuv420p","-c:v","libx264","-preset","fast","-crf","17","-movflags","+faststart","-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709",str(staged)],check=True)
subprocess.run([ffmpeg,"-hide_banner","-loglevel","error","-xerror","-i",str(staged),"-f","null","-"],check=True)
properties=json.loads(subprocess.check_output([ffprobe,"-v","error","-count_frames","-show_entries","stream=codec_name,codec_type,width,height,r_frame_rate,nb_read_frames:format=duration,nb_streams","-of","json",str(staged)]))
assert properties["format"]=={"nb_streams":1,"duration":"10.000000"},properties
assert properties["streams"]==[dict(codec_name="h264",codec_type="video",width=832,height=468,r_frame_rate="24/1",nb_read_frames="240")],properties
staged.replace(destination)
print(json.dumps(properties,indent=2))
