from base64 import b64encode
from datetime import date
from html import escape
from io import BytesIO
from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont

OUT = Path("outputs/Адвент-календарь — карточки.html")
ILLUSTRATION_FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
INK = "#29304b"
PLUM = "#584372"

def make_rebus(subject, word, operations):
    image = Image.new("RGB", (900, 460), "#f7f2fa")
    drawing = ImageDraw.Draw(image)
    drawing.rounded_rectangle((36, 35, 313, 425), 32, fill="#fffdf9", outline="#ded1e6", width=4)
    drawing.ellipse((67, 68, 283, 284), fill="#f0e8f7")
    if subject == "balloon":
        drawing.arc((145, 222, 202, 264), 20, 180, fill=PLUM, width=5)
        drawing.arc((125, 252, 185, 296), 180, 325, fill=PLUM, width=5)
        drawing.polygon([(164, 214), (153, 232), (177, 232)], fill="#b84f70")
        drawing.ellipse((95, 74, 251, 222), fill="#d25175", outline="#a44668", width=4)
        drawing.arc((113, 94, 211, 194), 183, 261, fill="#ffd7df", width=8)
    elif subject == "sea":
        drawing.rounded_rectangle((68, 97, 282, 259), 23, fill="#d5ecf3")
        drawing.ellipse((195, 113, 244, 162), fill="#f3bc61")
        for idx, blue in enumerate(("#6dbcdb", "#4094be", "#31789f")):
            baseline = 161 + 28 * idx
            wave = [(x, baseline + round(9 * math.sin(x / 15 + idx))) for x in range(71, 280)]
            drawing.polygon(wave + [(279, baseline + 43), (71, baseline + 43)], fill=blue)
        drawing.polygon([(139, 133), (114, 167), (139, 167)], fill="#fffdf9")
        drawing.line((141, 128, 141, 178), fill=PLUM, width=3)
        drawing.polygon([(110, 173), (163, 173), (154, 185), (120, 185)], fill=PLUM)
    elif subject == "clap":
        def hand(angle):
            layer = Image.new("RGBA", (150, 190))
            pen = ImageDraw.Draw(layer)
            borders = "#8e543c"
            color = "#f0ad78"
            for x, y, length in ((54, 28, 73), (74, 19, 87), (92, 31, 75), (109, 48, 64)):
                pen.rounded_rectangle((x, y, x+21, y+length), 10, fill=color, outline=borders, width=3)
            pen.rounded_rectangle((30, 84, 70, 113), 12, fill=color, outline=borders, width=3)
            pen.rounded_rectangle((49, 77, 131, 152), 28, fill=color)
            pen.line((50, 108, 51, 125, 65, 147), fill=borders, width=3)
            pen.line((128, 102, 127, 122, 118, 143), fill=borders, width=3)
            pen.rounded_rectangle((63, 141, 120, 169), 5, fill="#7b6599")
            return layer.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
        back = hand(-28)
        front = hand(33)
        image.paste(back, (46, 63), back)
        image.paste(front, (82, 66), front)
        for coords in ((119, 104, 106, 88), (161, 95, 160, 73), (200, 111, 215, 94)):
            drawing.line(coords, fill="#a37035", width=5)
    elif subject == "fox":
        drawing.polygon([(101, 163), (91, 91), (146, 140), (201, 140), (257, 91), (247, 167)], fill="#db793b", outline="#9b5332", width=4)
        drawing.polygon([(109, 122), (119, 160), (143, 147)], fill="#f7d9ce")
        drawing.polygon([(240, 122), (230, 160), (207, 147)], fill="#f7d9ce")
        drawing.polygon([(94, 173), (145, 137), (210, 139), (256, 175), (225, 220), (175, 262), (123, 220)], fill="#ec8d48", outline="#9b5332", width=4)
        drawing.polygon([(94, 174), (154, 191), (175, 217), (197, 191), (254, 174), (225, 220), (175, 259), (123, 220)], fill="#fff1df")
        drawing.arc((126, 177, 160, 206), 191, 348, fill=INK, width=5)
        drawing.arc((191, 177, 225, 206), 191, 348, fill=INK, width=5)
        drawing.ellipse((163, 215, 187, 235), fill=INK)
    drawing.text((174, 355), word, font=ImageFont.truetype(ILLUSTRATION_FONT, 48), fill=INK, anchor="mm")
    if len(operations) == 1:
        positions = [230]
    else:
        positions = [171, 288]
    for operation, y in zip(operations, positions):
        drawing.text((588, y), operation, font=ImageFont.truetype(ILLUSTRATION_FONT, 73), fill=PLUM, anchor="mm")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return "data:image/png;base64," + b64encode(output.getvalue()).decode()

def link(label, url, css_class=""):
    return f'<a class="{css_class}" href="{escape(url, quote=True)}">{escape(label)}</a>'

def card(day, name, body, css_class=""):
    heading = f"<h3>{escape(name)}</h3>" if name else ""
    return f'<article class="card {css_class}" id="date-{day}"><time datetime="2026-12-{day:02}">{day} декабря</time>{heading}{body}</article>'

def answer(solution, source=None):
    cite = " " + link("Источник текста", source, "source") if source else ""
    return f"<details><summary>Показать ответ</summary><p><strong>{escape(solution)}</strong>{cite}</p></details>"

def section(anchor, name, cards):
    return f'<section id="{anchor}" aria-labelledby="{anchor}-title"><h2 id="{anchor}-title">{name}</h2><div class="cards">{ "".join(cards) }</div></section>'

riddles = [
    (1, "Бело покрывало\nНа земле лежало,\nЛето пришло,\nОно всё сошло.", "Снег", "https://klassikpoez.narod.ru/zagadki.htm"),
    (9, "Без досок, без топоров\nЧерез речку мост готов.\nМост — как синее стекло:\nСкользко, весело, светло!", "Лёд", "https://files.sheba.spb.ru/bib/pozharova-rucheek-1948.htm"),
    (16, "Ароматный и сказочный плод,\nКак оранжевый шарик блестящий,\nБез него не придёт Новый год,\nОн нам праздник несёт настоящий.", "Мандарин", "https://millionzagadok.ru/zag/ny/new.html"),
    (24, "Всё лето стояли,\nЗимы ожидали.\nДождались поры —\nПомчались с горы.", "Санки", "https://infourok.ru/sbornik-zagadok-o-zime-zimnih-yavleniyah-zabavah-zimnih-vidah-sporta-dlya-detey-4-7-let-aj-da-zimushka-zima-5766252.html"),
    (29, "Побелел под снегом сад,\nВсе деревья крепко спят.\nТолько ей одной не спится:\nНовый год проспать боится.", "Ёлка", "https://www.mossalit.ru/wd_docs/mb-4-18-2015-final.pdf#page=91"),
]
riddle_cards = [card(d, "", '<p class="verse">' + escape(verse).replace("\n", "<br>") + "</p>" + answer(solution, source), "riddle")
                for d, verse, solution, source in riddles]

movies = [
    (4, "Дед Мороз и лето", "19 мин 26 с", "https://www.youtube.com/watch?v=YGFUcJVsrPY",
     "https://avatars.mds.yandex.net/get-vthumb/2332830/b1693bd0b4f814274aaba147faaf3fb1/800x450"),
    (10, "Снеговик-почтовик", "17 мин 58 с", "https://www.youtube.com/watch?v=8FJJpGJ4qFU",
     "https://static.kinoafisha.info/k/movie_shots/1920x1080/upload/movie_shots/9/8/4/8359489/1fb9bb06405e10960fcbcbeb4a5b075b.jpg"),
    (15, "Умка на ёлке", "7 мин 16 с", "https://www.youtube.com/watch?v=pc1RrpGbdMI",
     "https://www.karusel-tv.ru/media/suit/900x506/media/video_cover/2019/12/1577700821645502_vlcsnap_2019_12_30_12h52m19s990.png"),
    (23, "Зима в Простоквашино", "15 мин 44 с", "https://www.youtube.com/watch?v=21YR06EifBo",
     "https://static.kinoafisha.info/upload/articles/699607661200.jpg"),
    (30, "Новогоднее путешествие", "10 мин 10 с", "https://www.youtube.com/watch?v=iPBpvu27xEY",
     "https://images.iptv.rt.ru/images/d2o76c3ir4sqiatduqhg.jpg"),
]
movie_cards = []
for d, name, length, url, frame in movies:
    movie_cards.append(card(d, name,
        f'<figure class="movie-frame"><img src="{escape(frame, quote=True)}" '
        f'alt="Кадр из мультфильма «{escape(name, quote=True)}»" referrerpolicy="no-referrer">'
        f'<figcaption>{link("Кадр в полном размере", frame, "source")}</figcaption></figure>'
        f'<div class="movie-meta"><span>{length}</span>{link("Смотреть на YouTube", url, "button")}</div>', "movie"))

rebuses = [
    (3, "balloon", "ШАР", ["+ Ф"], "Рисунок шара. К слову ШАР добавьте Ф.", "ШАРФ"),
    (7, "sea", "МОРЕ", ["Е → О", "+ З"], "Рисунок моря. В слове МОРЕ замените Е на О, затем добавьте З в конце.", "МОРОЗ"),
    (17, "clap", "ХЛОПОК", ["− ОК", "+ УШКА"], "Рисунок хлопающих ладоней. В слове ХЛОПОК уберите ОК, затем добавьте УШКА в конце.", "ХЛОПУШКА"),
    (22, "fox", "ЛИСА", ["− А", "И → Е"], "Рисунок лисы. В слове ЛИСА уберите последнюю А, затем замените И на Е.", "ЛЕС"),
]
rebus_cards = [
    card(d, "", f'<img class="rebus-picture" src="{make_rebus(subject, word, ops)}" alt="{escape(alt, quote=True)}" width="900" height="460">' + answer(solution), "rebus")
    for d, subject, word, ops, alt, solution in rebuses
]

activities = [
    (2, "Снежинки, замри", "В классе", "На слово «летим» плавно машите руками, на слово «замри» — останавливайтесь. Можно играть сидя."),
    (8, "След в след", "На прогулке", "Пройдите змейкой за ведущим, повторяя его маршрут. Если на площадке есть снег, можно наступать в его следы."),
    (14, "Зимняя почта", "На прогулке", "По очереди дойдите с варежкой до отметки и обратно. Передайте варежку следующему участнику."),
    (21, "Ёлочки — пенёчки", "В классе · танец-игра", "На «ёлочки» выпрямитесь и соедините ладони над головой. На «пенёчки» слегка присядьте. Повторяйте движения по командам или под одноимённую песню."),
]
activity_cards = [card(d, name, f'<p class="note">{place}</p><p>{description}</p>', "activity") for d, name, place, description in activities]

crafts = [
    (11, "Письмо Деду Морозу", "Напишите короткое письмо Деду Морозу. Поздоровайтесь, подпишите своё имя и напишите или нарисуйте одно новогоднее желание.", "Бумага и карандаши"),
    (18, "Бумажные снежинки", "Сложите квадратный лист бумаги по диагонали, а затем ещё дважды пополам. Вырежьте небольшие треугольники по краям. Разверните бумагу и посмотрите, какой узор получился.", "Квадратный лист обычной бумаги и детские ножницы"),
    (25, "Гирлянда «Звери в хороводе»", "Соберите из готового набора гирлянду так, чтобы звери встали в хоровод. Используйте инструкцию к набору.", "Готовый набор для гирлянды"),
    (28, "Зимняя Москва", "Нарисуйте любимое место в зимней Москве: свой двор, парк или дорогу к школе.", "Бумага и карандаши"),
]
craft_cards = [card(d, name, f"<p>{description}</p><p class='note'><strong>Материалы</strong> {materials}</p>", "craft")
               for d, name, description, materials in crafts]
sections = [("riddles", "Загадки", riddle_cards), ("movies", "Мультфильмы", movie_cards),
            ("rebuses", "Ребусы", rebus_cards), ("activities", "Активности", activity_cards),
            ("crafts", "Творческие задания", craft_cards)]
dates = [entry[0] for group in (riddles, movies, rebuses, activities, crafts) for entry in group]
assert sorted(dates) == [d for d in range(1, 31) if date(2026, 12, d).weekday() < 5]

portrait = Image.open("outputs/cat-reference.jpg").convert("RGB")
portrait = portrait.crop((0, 0, 695, portrait.height))
portrait.thumbnail((340, 410), Image.Resampling.LANCZOS)
photo = BytesIO()
portrait.save(photo, format="JPEG", quality=87, optimize=True)
portrait_src = "data:image/jpeg;base64," + b64encode(photo.getvalue()).decode()
css = Path("work/calendar.css").read_text()
nav = "".join(link(title, "#" + anchor) for anchor, title, cards in sections)
content = "\n".join(section(*group) for group in sections)
OUT.write_text(f"""<!doctype html>
<html lang="ru">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Адвент-календарь Кота Учёного</title><style>{css}</style></head>
<body>
<header class="cover"><div class="cover-body">
<div><p class="date-range">1–30 декабря 2026</p><h1>Адвент-календарь<br>Кота Учёного</h1><p class="intro">22 задания для первоклассников</p></div>
<img class="portrait" src="{portrait_src}" alt="Кот Учёный в круглых очках с книгой и свитком" width="{portrait.width}" height="{portrait.height}">
</div></header>
<nav aria-label="Разделы календаря">{nav}</nav>
<main>{content}</main>
</body></html>""", encoding="utf-8")
