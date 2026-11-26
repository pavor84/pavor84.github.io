from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.shared import Inches, Pt, RGBColor
from lxml import html

work = Path("work")
calendar_path = Path("outputs/Адвент-календарь — карточки.html")
calendar = html.fromstring(calendar_path.read_bytes(), parser=html.HTMLParser(encoding="utf8"))
cards = {int(card.get("id").split("-")[-1]): card for card in calendar.xpath("//main//article")}
scenes = {}
for line in (work / "current-scenes.txt").read_text().splitlines():
    number, *fields = line.split("|")
    assert len(fields) == 7, (number, fields)
    scenes[int(number)] = fields

planned_days = [n for n in range(1, 31) if date(2026, 12, n).weekday() < 5]
assert set(cards) == set(scenes) == set(planned_days) and len(planned_days) == 22
weeks = [tuple(n for n in planned_days if date(2026, 12, n).isocalendar().week == week)
         for week in sorted({date(2026, 12, n).isocalendar().week for n in planned_days})]
locations = {
    "Дом": "Дом внутри дуба",
    "Камин": "Дом внутри дуба 2",
    "Поляна": "Поляна у дуба",
    "Озеро": "Замёрзшее озеро",
}
kinds = {
    "riddle": "Загадка",
    "rebus": "Ребус",
    "movie": "Мультфильм",
    "activity": "Активность",
    "craft": "Творчество",
}
rebus_replies = {
    3: "На картинке шар. Добавьте к слову «шар» в конце букву «эф». Какое зимнее слово получится?",
    7: "На картинке море. В слове «море» замените последнюю букву «е» на «о» и добавьте в конце «зэ». Что получилось?",
    17: "На рисунке хлопают ладони. Уберите из слова «хлопо́к» последние две буквы, «о» и «ка». Добавьте в конце «ушка». Какое слово получилось?",
    22: "На картинке лиса. В слове «лиса» уберите последнюю букву «а». Потом замените «и» на «е». Какое слово получилось?",
}

doc = Document()
doc.core_properties.title = "Адвент-календарь Кота Учёного"
doc.core_properties.subject = "Сценарии 22 выпусков на будние дни с 1 по 30 декабря 2026 года"
section = doc.sections[0]
section.page_width, section.page_height = Inches(8.5), Inches(11)
section.left_margin = section.right_margin = Inches(.77)
section.top_margin, section.bottom_margin = Inches(.64), Inches(.61)
section.footer_distance = Inches(.33)

for name, size in (("Normal", 11), ("Title", 30), ("Heading 1", 21), ("Heading 2", 14)):
    style = doc.styles[name]
    style.font.name = "Arial"
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.13
    properties = style.element.get_or_add_pPr()
    border = properties.find(qn("w:pBdr"))
    if border is not None:
        properties.remove(border)
doc.styles["Heading 1"].paragraph_format.space_before = Pt(0)
doc.styles["Heading 2"].paragraph_format.space_before = Pt(11)

footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
field = OxmlElement("w:fldSimple")
field.set(qn("w:instr"), "PAGE")
footer._p.append(field)

compact_style = doc.styles.add_style("Compact", doc.styles["Normal"].type)
compact_style.base_style = doc.styles["Normal"]
compact_style.font.size = Pt(10.5)

def paragraph(label, body=None, compact=False, keep_next=False):
    p = doc.add_paragraph()
    if body is None:
        p.add_run(label)
    else:
        p.add_run(label + "  ").bold = True
        p.add_run(body)
    if compact:
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = Pt(12.6)
        p.style = doc.styles["Compact"]
    p.paragraph_format.keep_together = True
    p.paragraph_format.keep_with_next = keep_next
    return p

def link(p, label, url):
    rel = p.part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), rel)
    run = OxmlElement("w:r")
    prop = OxmlElement("w:rPr")
    col = OxmlElement("w:color")
    col.set(qn("w:val"), "294768")
    prop.append(col)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    prop.append(underline)
    run.append(prop)
    content = OxmlElement("w:t")
    content.text = label
    run.append(content)
    h.append(run)
    p._p.append(h)

def top(text):
    heading = doc.add_heading(text, 1)
    heading.paragraph_format.page_break_before = True

doc.add_heading("Адвент-календарь Кота Учёного", 0)
paragraph("Будние дни с 1 по 30 декабря 2026 года  ·  Для первоклассников Москвы")
paragraph("Сценарии 22 выпусков. В каждом Кот Учёный здоровается с ребятами, открывает книгу и даёт одно задание. В календаре пять загадок, пять мультфильмов, четыре ребуса, четыре подвижных и четыре творческих задания.")
p = paragraph("")
link(p, "Календарь с карточками и иллюстрациями", "https://pavor84.github.io/advent/")
doc.add_heading("Персонаж и стиль", 2)
paragraph("Предлагается 2.5D-анимация. Кот выглядит объёмным, как на присланном изображении, а глаза, рот, лапы, шарф, кисточка и книга движутся отдельными слоями. Для основных сцен используется один ракурс в три четверти. Для озера готовится дополнительная поза в полный рост на коньках.")
paragraph("Узнаваемые детали", "Полосатая шерсть, белая мордочка и лапы, янтарные глаза, круглые очки, фиолетовая академическая шапочка с золотой кисточкой, жакет, сиреневый шарф и свиток. Золотую надпись «1С» закрепляем на слое фиолетовой обложки, чтобы она двигалась вместе с книгой.")
photo = doc.add_picture("outputs/cat-reference.jpg", width=Inches(2.40))
photo._inline.docPr.set("descr", "Кот Учёный в круглых очках, фиолетовой академической шапочке и сиреневом шарфе держит книгу 1С и свиток.")
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_heading("Четыре места действия", 2)
paragraph("Дом внутри дуба", "Тёплая лампа, книжная полка, хвойная гирлянда и стол для поделок.", compact=True)
paragraph("Дом внутри дуба 2", "Тёплый свет от камина, тихий треск поленьев. Кот сидит в кресле-качалке, на заднем плане украшенная ёлка.", compact=True)
paragraph("Поляна у дуба", "Заснеженный лес, большой дуб и свободное место для движений.", compact=True)
paragraph("Замёрзшее озеро", "Сказочный каток у подсвеченного берега. В общем плане кот скользит на коньках, останавливается и уже в среднем плане здоровается.", compact=True)

top("Как устроен выпуск")
paragraph("0–4 с", "Одна новогодняя заставка на весь месяц. На снежном дубе загорается гирлянда, звучит тихая инструментальная фраза с колокольчиками, крупно появляется дата выпуска, например «3 декабря».")
paragraph("Следующие 4–8 с", "Переход в локацию дня. Кот смотрит на ребят и здоровается. На озере перед приветствием есть 2–3 секунды скольжения, перед остановкой у берега.")
paragraph("Книга и задание", "Одна лапа поддерживает корешок, другая поднимает обложку. На пометке [книга] кот делает паузу, открывает книгу, и справа появляется карточка. Затем он озвучивает задание. Знак ∕ обозначает перенос строки. Пометка в квадратных скобках на карточке ребуса — это рисунок.")
paragraph("Финал", "После реплики карточка остаётся на экране ещё 5–6 секунд. Для загадок и ребусов оставляем около 8 секунд. Ответы указаны в примечаниях для взрослого. Типовой выпуск длится 25–35 секунд. Время под заголовками сценариев относится к самим заданиям или просмотру мультфильма.")
doc.add_heading("Голос Кота Учёного", 2)
paragraph("Первая проба", "«Захар» из Yandex SpeechKit. Спокойная доброжелательная подача, темп 90–95% от обычного, радостная интонация в пробе и короткая пауза перед заданием. Для сравнения подойдёт «Александр». Пробу стоит сделать на репликах 1 и 3 декабря, чтобы услышать вопросы и отдельные буквы.")
p = paragraph("")
link(p, "Каталог голосов", "https://aistudio.yandex.ru/ru/docs/speechkit/tts/voices")
p.add_run("   ·   ")
link(p, "Голосовая проба в Playground", "https://console.yandex.cloud/link/speechkit/playground?tab=text-to-speech")
paragraph("Реализуемость", "API позволяет собрать 22 дорожки после авторизации. По тарифу на 26 ноября 2026 года один запрос модели general до 250 символов и 24 секунд стоит 0,1626 ₽. Итог зависит от длины реплик и количества дублей. Реальный тембр, темп и интонацию проверяем на голосовой пробе после авторизации. Если облачная озвучка недоступна, подойдёт запись одного взрослого диктора.")
p = paragraph("")
link(p, "Синтез через API", "https://aistudio.yandex.ru/ru/docs/speechkit/tts/api/tts-examples-v3")
p.add_run("   ·   ")
link(p, "Тариф SpeechKit", "https://aistudio.yandex.ru/ru/docs/speechkit/pricing")
doc.add_heading("Сборка после согласования", 2)
paragraph("Сначала собрать выпуски на 1 и 9 декабря. На первом проверить книгу, карточку, голос и паузу для ответа, на втором — скольжение, переход к среднему плану и паузу на загадку. Затем использовать те же фоны и анимации для оставшихся выпусков. Предлагаемый формат — MP4, 1920 × 1080, 16:9. Для заставки записать короткую оригинальную мелодию с колокольчиками. Под речью приглушить музыку и треск камина. Перед выдачей сверить даты, текст и звук, проверить мелкие буквы на телефоне и карточки на школьном экране. Ссылки на мультфильмы идут рядом с роликами.")

for week in weeks:
    top(f"{week[0]}–{week[-1]} декабря")
    for number in week:
        title, location, duration, greeting, screen, action, note = scenes[number]
        card = cards[number]
        kind = card.get("class").split()[-1]
        if kind in {"activity", "craft", "movie"}:
            title = card.xpath("./h3/text()")[0]
        related_link = None
        if kind == "riddle":
            verse = card.xpath("./p[@class='verse']/text()")
            screen = "  ∕  ".join(verse)
            assignment = screen
            solution = card.xpath(".//details//strong/text()")[0]
            assert solution.casefold() in note.casefold()
            related_link = ("Источник загадки", card.xpath(".//details//a/@href")[0])
        elif kind == "movie":
            duration = card.xpath(".//div[@class='movie-meta']/span/text()")[0]
            screen = f"Посмотрите мультфильм  ∕  «{title}»."
            assignment = f"Посмотрите мультфильм «{title}». Ссылка рядом с роликом."
            if number == 30:
                assignment += " Спасибо, что открывали книгу вместе со мной. С Новым годом!"
            related_link = ("Смотреть на YouTube", card.xpath(".//a[@class='button']/@href")[0])
        elif kind == "rebus":
            assignment = rebus_replies[number]
            solution = card.xpath(".//details//strong/text()")[0]
            assert solution in note
            related_link = ("Карточка с рисунком", f"https://pavor84.github.io/advent/#date-{number}")
        else:
            assignment = card.xpath("./p[not(@class='note')]/text()")[0]
            if number == 2:
                assignment += " Летим… Замри! Летим… Замри!"
            elif number == 21:
                assignment += " Ёлочки… Пенёчки… Ёлочки… Пенёчки!"
        heading = doc.add_heading(f"{number} декабря  ·  {title}", 2)
        heading.paragraph_format.space_before = Pt(3 if number == week[0] else 8)
        heading.paragraph_format.space_after = Pt(2)
        meta = paragraph(f"{locations[location]}  ·  {kinds[kind]}  ·  {duration}", compact=True, keep_next=True)
        meta.runs[0].font.color.rgb = RGBColor.from_string("4A474E")
        spoken = paragraph("Кот говорит", greeting + " ", compact=True, keep_next=True)
        spoken.add_run("[книга] ").italic = True
        spoken.add_run(assignment)
        paragraph("На экране", screen, compact=True, keep_next=True)
        paragraph("В кадре", action, compact=True, keep_next=True)
        p = paragraph("Для взрослого", note, compact=True)
        if related_link:
            p.add_run(" ")
            link(p, *related_link)

doc.save("outputs/Адвент-календарь Кота Учёного.docx")
