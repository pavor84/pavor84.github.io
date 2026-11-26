from html import escape
from pathlib import Path

items = [
    ("ЁЛОЧКА", [("🦔","ЁЖ",1),("🛶","ЛОДКА","Д → Ч")], "Ё + ЛОЧКА"),
    ("МЕТЕЛЬ", [("chalk","МЕЛ",1),("shadow","ТЕНЬ","Н → Л")], "МЕ + ТЕЛЬ"),
    ("СУГРОБ", [("🥣","СУП","П → Г"),("🤖","РОБОТ",2)], "СУГ + РОБ"),
    ("САНКИ", [("🦊","ЛИСА","3, 4"),("🧦","НОСКИ",[1,2])], "СА + НКИ"),
    ("КОНЬКИ", [("🪟","ОКНО","2, 1, 3"),("","Ь",None),("🐋","КИТ",1)], "КОН + Ь + КИ"),
    ("ГИРЛЯНДА", [("weight","ГИРЯ",1),("🏖️","ПЛЯЖ","2, 3"),("🐼","ПАНДА",[0,1])], "ГИР + ЛЯ + НДА"),
    ("ПОДАРОК", [("pillow","ПОДУШКА",4),("🍉","АРБУЗ",3),("🐈","КОТ","2, 1")], "ПОД + АР + ОК"),
    ("СНЕЖИНКА", [("❄️","СНЕГ","Г → Ж"),("🧺","КОРЗИНКА",[0,1,2,3])], "СНЕЖ + ИНКА"),
    ("СНЕГОВИК", [("🐦","СНЕГИРЬ",3),("🐑","ОВЦА",2),("roe","ИКРА",2)], "СНЕГ + ОВ + ИК"),
    ("ИНЕЙ", [("🦃","ИНДЮК",3),("watering","ЛЕЙКА","2, 3")], "ИН + ЕЙ"),
]

def token(data):
    icon, word, operation = data
    if not icon:
        return f'<div class="join letter" aria-label="Добавьте мягкий знак">{word}</div>'
    if icon.isascii():
        drawing = f'<span class="symbol shape {icon}" aria-hidden="true"></span>'
    else:
        drawing = f'<span class="symbol" aria-hidden="true">{icon}</span>'
    spoken = word
    if isinstance(operation, int):
        operation = list(range(len(word) - operation, len(word)))
    if isinstance(operation, list):
        letters = "".join(f"<s>{char}</s>" if i in operation else char for i,char in enumerate(word))
        spoken += ", уберите " + ", ".join(word[i] for i in operation)
        rule = ""
    else:
        letters = word
        rule = f'<span class="rule">{escape(operation)}</span>'
        spoken += ", " + operation
    return f'<div class="token" role="img" aria-label="{escape(spoken, quote=True)}">{drawing}<strong>{letters}</strong>{rule}</div>'

cards = []
for n,(answer,parts,steps) in enumerate(items,1):
    assert "".join(steps.split(" + ")) == answer
    tokens = '<span class="join" aria-hidden="true">+</span>'.join(token(part) for part in parts)
    cards.append(f'<article><h2>Вариант {n}</h2><div class="rebus">{tokens}</div><details><summary>Показать ответ</summary><p>{escape(steps)} = <strong>{answer}</strong></p></details></article>')

style = """
:root { color-scheme:light; color:#272239; background:#f8f4ed; font:17px/1.5 system-ui,sans-serif; }
* { box-sizing:border-box; }
body { margin:0; }
main { width:min(100%,1120px); margin:auto; padding:28px 20px 48px; }
h1 { margin:0; font:700 clamp(1.8rem,5vw,3rem)/1.1 Georgia,serif; }
header p { margin:12px 0 22px; max-width:66ch; color:#5b4a69; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,390px),1fr)); gap:14px; }
article { border:1px solid #ddd2e3; border-radius:12px; padding:15px; background:#fffefa; }
h2 { margin:0 0 10px; font-size:1.03rem; }
.rebus { display:flex; align-items:center; justify-content:center; gap:5px; min-height:120px; }
.token { min-width:0; padding:7px; border-radius:8px; text-align:center; background:#f5eff9; align-self:stretch; min-height:108px; }
.token strong { display:block; letter-spacing:.03em; font-size:clamp(.69rem,2.7vw,1.22rem); }
.token s { text-decoration-color:#a14960; text-decoration-thickness:2px; }
.rule { color:#574173; font-weight:700; font-size:.9rem; white-space:nowrap; }
.join { font-weight:700; color:#574173; font-size:1.2rem; }
.letter { padding-inline:4px; }
.symbol { display:block; height:51px; font-size:34px; }
.shape { position:relative; }
.shape:before,.shape:after { position:absolute; content:''; }
.chalk:before { width:42px; height:14px; top:19px; left:50%; transform:translateX(-50%) rotate(-24deg); border-radius:4px; background:#fffefa; border:1px solid #97849d; box-shadow:2px 3px #d6ccd9; }
.shadow:before { content:'✋'; font-size:29px; top:2px; left:50%; transform:translateX(-62%) rotate(-22deg); filter:grayscale(1) brightness(.4); opacity:.7; }
.weight:before { width:29px; height:25px; border-radius:50% 50% 43% 43%; top:20px; left:50%; transform:translateX(-50%); background:#4e5165; }
.weight:after { width:18px; height:16px; border-radius:6px; top:10px; left:50%; transform:translateX(-50%); border:4px solid #4e5165; }
.pillow:before { width:43px; height:29px; border-radius:9px 14px 8px 13px; top:11px; left:50%; transform:translateX(-50%) rotate(-13deg); background:#e7d4f1; border:1px dashed #9a74b3; box-shadow:2px 3px #c9b6d2; }
.roe:before { width:43px; height:20px; top:22px; left:50%; transform:translateX(-50%); border-radius:4px 4px 50% 50%; background:#e9cab6; }
.roe:after { width:35px; height:15px; top:15px; left:50%; transform:translateX(-50%); border-radius:50%; background:radial-gradient(circle,#ffd277 23%,transparent 29%) 0 0/6px 6px,#eb8650; }
.watering:before { width:29px; height:23px; top:17px; left:48%; transform:translateX(-50%); border-radius:4px 4px 8px 7px; background:#70ad8d; }
.watering:after { width:22px; height:7px; top:17px; right:7%; border-radius:2px; transform:rotate(-36deg); background:#70ad8d; }
details { margin-top:9px; } summary { color:#574173; cursor:pointer; } details p { margin:4px 0 0; }
@media print { article { break-inside:avoid; } }
"""
out = Path("outputs/Новогодние ребусы — 10 вариантов.html")
out.write_text(f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Новогодние ребусы</title><style>{style}</style></head>
<body><main><header><h1>Новогодние ребусы</h1><p>10 вариантов для четырёх выпусков. Зачёркнутые буквы пропускаем. Стрелка показывает замену. Цифры указывают, какие буквы взять слева направо и в каком порядке их поставить. Плюс соединяет части.</p></header><div class="grid">{''.join(cards)}</div></main></body></html>""", encoding="utf-8")
