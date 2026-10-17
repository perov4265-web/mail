# -*- coding: utf-8 -*-
"""Ultra-minimal A3 roadmap (one sheet, relative timeline)."""
import sys, html
OUT = sys.argv[1]

TOTAL = 1884766.26
LOTS = [
    dict(key="3", name="Часть 3 · ПАК", sub="программно-аппаратные комплексы", cost=615158.76, S=24, term="T0 + 1 мес"),
    dict(key="1", name="Часть 1 · Радиостанции", sub="носимые и возимые", cost=306350.00, S=95, term="Каир = A + 3 мес"),
    dict(key="2", name="Часть 2 · Базовые станции", sub="антенны, БП, инфраструктура", cost=953047.50, S=154, term="Каир = A + 5 мес"),
]
SERV = 10210.0
ADV, DP, LAG = 10, 40, 10
def usd(x): return f"{round(x):,}".replace(",", " ")

W, H = 1587, 1123
INK, MUTE, LINE, ACC = "#111", "#8A8F99", "#D9DCE2", "#D63B2F"

css = f"""
@page {{ size: 420mm 297mm; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin:0; padding:0; background:#fff; }}
body {{ width:{W}px; height:{H}px; overflow:hidden; font-family:'Inter','Liberation Sans',Arial,sans-serif; color:{INK};
  font-feature-settings:'tnum' 1; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
.abs {{ position:absolute; }}
svg text {{ font-family:'Inter','Liberation Sans',Arial,sans-serif; }}
h1 {{ position:absolute; left:70px; top:62px; margin:0; font-size:34px; font-weight:300; letter-spacing:-0.5px; }}
h1 b {{ font-weight:700; }}
.cap {{ position:absolute; left:70px; top:112px; font-size:12px; color:{MUTE}; letter-spacing:.2px; }}
.big {{ position:absolute; right:70px; top:58px; text-align:right; }}
.big .v {{ font-size:34px; font-weight:700; letter-spacing:-0.8px; line-height:1; }}
.big .l {{ font-size:12px; color:{MUTE}; margin-top:8px; }}
.col {{ position:absolute; top:748px; }}
.col h2 {{ margin:0 0 14px 0; font-size:11px; font-weight:700; letter-spacing:1.6px; text-transform:uppercase; color:{MUTE}; }}
.col h2.acc {{ color:{ACC}; }}
.row {{ display:flex; gap:14px; font-size:13px; line-height:1.35; margin-bottom:9px; }}
.row .k {{ flex:0 0 112px; font-weight:700; white-space:nowrap; }}
.row .k.acc {{ color:{ACC}; }}
.col {{ top:905px; }}
.row .t {{ color:{INK}; }}
.row .t small {{ color:{MUTE}; }}
.li {{ display:flex; gap:10px; font-size:13px; line-height:1.35; margin-bottom:8px; }}
.li .n {{ flex:0 0 14px; color:{MUTE}; font-weight:700; }}
.foot {{ position:absolute; left:70px; right:70px; bottom:40px; font-size:10.5px; color:{MUTE}; display:flex; justify-content:space-between; }}
"""

P = []
A = P.append
A(f"<!doctype html><html lang='ru'><head><meta charset='utf-8'><title>Дорожная карта — минимум</title><style>{css}</style></head><body>")
A("<h1>Поставка оборудования радиосвязи <b>· дорожная карта</b></h1>")
A("<div class='cap'>T0 — вступление Договора в силу · A — аванс · S — отгрузка · ДП — Дата поставки (Акт входного контроля) · все сроки в днях от T0 · суммы USD</div>")
A(f"<div class='big'><div class='v'>{usd(TOTAL)} USD</div><div class='l'>3 партии · 56 комплектов · последняя поставка T0 + {LOTS[2]['S']+DP} дн</div></div>")

# ---------------- main timeline ----------------
top, h = 175, 690
A(f"<svg class='abs' style='left:0;top:{top}px' width='{W}' height='{h}'>")
x0, x1 = 390, W - 110
DMAX = 215
X = lambda d: x0 + (x1 - x0) * d / DMAX
ay = 36
for m in range(8):
    d = m * 30
    if d > DMAX: break
    xx = X(d)
    A(f"<line x1='{xx:.1f}' y1='{ay}' x2='{xx:.1f}' y2='{h-70}' stroke='{LINE}' stroke-width='1'/>")
    A(f"<text x='{xx:.1f}' y='{ay-12}' font-size='11' fill='{MUTE}' text-anchor='middle'>{'T0' if m==0 else f'+{m} мес'}</text>")
A(f"<line x1='{x0}' y1='{ay}' x2='{x1}' y2='{ay}' stroke='{INK}' stroke-width='1'/>")
# advance marker
xa = X(ADV)
A(f"<line x1='{xa:.1f}' y1='{ay}' x2='{xa:.1f}' y2='{h-70}' stroke='{INK}' stroke-width='1' stroke-dasharray='2 4'/>")
A(f"<text x='{xa+6:.1f}' y='{h-76}' font-size='11' fill='{MUTE}'>A = T0 + 10 дн</text>")

# lot rows
ry, rh = 100, 150
for i, lot in enumerate(LOTS):
    y = ry + i * rh
    S, D = lot["S"], lot["S"] + DP
    A(f"<text x='70' y='{y-4}' font-size='16' font-weight='700' fill='{INK}'>{html.escape(lot['name'])}</text>")
    A(f"<text x='70' y='{y+16}' font-size='12' fill='{MUTE}'>{html.escape(lot['sub'])} · {html.escape(lot['term'])}</text>")
    A(f"<text x='70' y='{y+38}' font-size='15' font-weight='700' fill='{INK}'>{usd(lot['cost'])}</text>")
    # pre-shipment thin line
    pre = max(S - 90, 0)
    A(f"<line x1='{X(pre):.1f}' y1='{y}' x2='{X(S):.1f}' y2='{y}' stroke='{INK}' stroke-width='1' stroke-dasharray='1 4'/>")
    # transit thick line
    A(f"<line x1='{X(S):.1f}' y1='{y}' x2='{X(D):.1f}' y2='{y}' stroke='{INK}' stroke-width='6' stroke-linecap='butt'/>")
    A(f"<circle cx='{X(S):.1f}' cy='{y}' r='7' fill='#fff' stroke='{INK}' stroke-width='2'/>")
    A(f"<rect x='{X(D)-7:.1f}' y='{y-7}' width='14' height='14' fill='{INK}'/>")
    A(f"<text x='{X(S):.1f}' y='{y-16}' font-size='12' font-weight='700' fill='{INK}' text-anchor='middle'>S{lot['key']} · T0 + {S}</text>")
    A(f"<text x='{X(D):.1f}' y='{y-16}' font-size='12' font-weight='700' fill='{INK}' text-anchor='middle'>ДП{lot['key']} · T0 + {D}</text>")
    # payments under row
    for d, lab in ((S + LAG, "30 %"), (D + LAG, "30 %")):
        A(f"<line x1='{X(d):.1f}' y1='{y+10}' x2='{X(d):.1f}' y2='{y+26}' stroke='{INK}' stroke-width='1'/>")
        A(f"<text x='{X(d):.1f}' y='{y+40}' font-size='11' fill='{INK}' text-anchor='middle'>{lab} · {usd(lot['cost']*0.3)}</text>")
# advance payment amount
A(f"<text x='{xa:.1f}' y='{ry-44}' font-size='11' fill='{INK}' text-anchor='middle'>35 % · {usd(TOTAL*0.35)}</text>")
A(f"<circle cx='{xa:.1f}' cy='{ry-30}' r='3.5' fill='{INK}'/>")

# problems row
py = ry + 3 * rh - 4
A(f"<text x='70' y='{py+4}' font-size='16' font-weight='700' fill='{ACC}'>Проблемы</text>")
A(f"<text x='70' y='{py+24}' font-size='12' fill='{MUTE}'>срок — от текущей даты</text>")
A(f"<line x1='{x0}' y1='{py}' x2='{x1}' y2='{py}' stroke='{ACC}' stroke-width='1' stroke-dasharray='2 4'/>")
for d, t, s in ((0, "Допсоглашение с АСЭ", "срок не определён"), (30, "Шифрование → таможня", "решение: 1 мес"), (77, "РД 16 + 27 компл.", "до Нового года")):
    xx = X(d)
    A(f"<polygon points='{xx:.1f},{py-7} {xx+7:.1f},{py} {xx:.1f},{py+7} {xx-7:.1f},{py}' fill='{ACC}'/>")
    if d == 0:
        A(f"<text x='{xx-12:.1f}' y='{py-4}' font-size='12' font-weight='700' fill='{ACC}' text-anchor='end'>{t}</text>")
        A(f"<text x='{xx-12:.1f}' y='{py+12}' font-size='11' fill='{MUTE}' text-anchor='end'>{s}</text>")
    else:
        A(f"<text x='{xx+12:.1f}' y='{py-4}' font-size='12' font-weight='700' fill='{ACC}'>{t}</text>")
        A(f"<text x='{xx+12:.1f}' y='{py+12}' font-size='11' fill='{MUTE}'>{s}</text>")
A("</svg>")

# ---------------- columns ----------------
c1, c2, c3 = 70, 600, 1120
A(f"<div class='col' style='left:{c1}px;width:470px'><h2 class='acc'>Проблемы</h2>")
for k, t in [("1 мес", "шифрование радиооборудования влияет на таможенный выпуск"),
             ("до НГ", "разработка 16 и согласование 27 комплектов РД"),
             ("—", "допсоглашение с АСЭ: подготовка и согласование")]:
    A(f"<div class='row'><div class='k acc' style='flex-basis:60px'>{k}</div><div class='t'>{t}</div></div>")
A("</div>")
A(f"<div class='col' style='left:{c2}px;width:470px'><h2>Командировка в Китай · Hytera</h2>")
for i, t in enumerate(["Окончательное согласование технического решения",
                       "Решение по АФУ по параметрам NTRA, вместе с инженерами Hytera",
                       "Сертификат проектировщика от Hytera",
                       "Проверка избыточности или дефицита лицензий"], 1):
    A(f"<div class='li'><div class='n'>{i}</div><div>{t}</div></div>")
A("</div>")

A("<div class='foot'><span>Источник: График изготовления и поставки, Дополнение 1.2 к Приложению № 1 · суммы по Спецификации, к пересчёту в EGP</span><span>месяц на шкале = 30 дн · ○ отгрузка · ■ Дата поставки · ◆ проблема</span></div>")
A("</body></html>")
open(OUT, "w", encoding="utf-8").write("".join(P))
print("written", OUT)
