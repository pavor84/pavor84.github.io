from base64 import b64decode
from http import HTTPStatus
import json
from pathlib import Path
import re
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, HTTPRedirectHandler, Request, build_opener

HERE = Path(__file__).resolve().parent
URL = "https://tts.api.cloud.yandex.net/tts/v3/utteranceSynthesis"
LINES = {
    "greeting": "Привет, ребята! Я Кот Учёный. До Нового года в моей книге на каждый будний день спряталось задание. Начнём с загадки.",
    "riddle": "Бело покрывало,\nна земле лежало.\nЛето пришло,\nоно всё сошло.",
}

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None

with (Path.home()/".aistudio").open() as file:
    key=file.read().strip()
if not re.fullmatch(r"[A-Za-z0-9._-]+",key):
    raise SystemExit("Credential file does not contain a single API key")
opener = build_opener(NoRedirect(), HTTPSHandler(context=ssl.create_default_context()))

def speech(name,text):
    target=HERE/f"vasily-{name}.mp3"
    if target.is_file() and target.stat().st_size > 1000:
        print(name, "already synthesized")
        return
    body=json.dumps({
        "model": "livetts",
        "text": text,
        "hints": [{"voice":"vasily"},{"role":"sales"}],
        "outputAudioSpec": {"containerAudio":{"containerAudioType":"MP3"}},
    },ensure_ascii=False).encode("utf8")
    request=Request(URL,data=body,headers={
        "Authorization": f"Api-Key {key}",
        "Content-Type": "application/json",
    })
    try:
        with opener.open(request,timeout=25) as response:
            lines=response.read().splitlines()
    except HTTPError as error:
        payload=error.read(8192).lower()
        explanation="authentication or permission failure" if error.code in (401,403) else "request rejected"
        if b'scope' in payload:
            explanation="insufficient API key scope"
        if b'folder' in payload and b'permission' in payload:
            explanation="permission missing for the folder"
        raise SystemExit(f"SpeechKit HTTP {error.code}: {explanation}") from None
    except (URLError, TimeoutError) as error:
        reason=getattr(error,"reason",error)
        raise SystemExit(f"SpeechKit connection failed: {type(reason).__name__}") from None
    audio=[]
    for line in lines:
        item=json.loads(line)
        if item.get("error"):
            raise SystemExit(f"SpeechKit returned an error, code: {item['error'].get('code','unknown')}")
        chunk=((item.get("result") or {}).get("audioChunk") or {}).get("data")
        if chunk:
            audio.append(b64decode(chunk,validate=True))
    result=b"".join(audio)
    if len(result)<1000:
        raise SystemExit("SpeechKit returned no usable audio")
    target.write_bytes(result)
    print(name, "received", len(result), "audio bytes")

for name,text in LINES.items():
    speech(name,text)
