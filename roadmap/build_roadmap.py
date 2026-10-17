# -*- coding: utf-8 -*-
"""Generate the A3 roadmap infographic (HTML) from the delivery schedule figures."""
import sys, html

OUT = sys.argv[1]

# ---------- data (from "График поставки", Дополнение 1.2) ----------
TOTAL = 1884766.26
LOTS = [  # order on the macro timeline = shipment order
    dict(key="3", name="Часть 3 — ПАК", color="#D97A1A", light="#FBE7CF", mid="#F4C58C",
         comp="ПАК 90CZS02 (осн.) и 90CZS03 (рез.): серверы, АРМ, коммутаторы, ПО",
         sets=2, cost=615158.76, term="Поставка = T0 + 1 мес", S=24, pre_note="подготовка · 1 мес"),
    dict(key="1", name="Часть 1 — Радиостанции", color="#2F6FDE", light="#DCE7FB", mid="#A9C3F2",
         comp="Носимые HP709C / HP789C, возимые HM789C, батареи, лицензии, ЗУ",
         sets=27, cost=306350.00, term="Каир (CIF, авиа) = A + 3 мес", S=95, pre_note=None),
    dict(key="2", name="Часть 2 — Базовые станции и инфраструктура", color="#1C9C8A", light="#D6F0EC", mid="#97D9CF",
         comp="БС DS-6250 с антеннами, БП, антенны VHF, волноводы, настольные компл.",
         sets=27, cost=953047.50, term="Каир (CIF, авиа) = A + 5 мес", S=154, pre_note=None),
]
SERVICES = dict(name="Комплекс услуг", comp="анализатор спектра, FAT, сборы NTRA", cost=10210.00)
ADV_DAY = 10           # A = T0 + 10 дн (п. 23.1)
TRANSIT_CAIRO = 7      # авиа до Каира
SITE = 30              # прибытие на Площадку = S + 30
DP = 40                # Акт входного контроля = S + 40
PAY_LAG = 10           # платёж в течение 10 календарных дней

def usd(x):
    s = f"{round(x):,}".replace(",", " ")
    return s

def pct(x): return f"{x:.0f} %"

# ---------- geometry ----------
W, H = 1587, 1123
M = 26

css = """
@page { size: 420mm 297mm; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #fff; }
body { width: 1587px; height: 1123px; overflow: hidden; font-family: 'Inter', 'Liberation Sans', Arial, sans-serif; color: #1B2333;
       font-feature-settings: 'tnum' 1, 'cv11' 1; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.page { position: relative; width: 1587px; height: 1123px; padding: 0; }
.abs { position: absolute; }
.hdr { position: absolute; left: 0; top: 0; width: 1587px; height: 104px; background: #152238; color: #fff; }
.hdr .title { position: absolute; left: 26px; top: 22px; font-size: 22px; font-weight: 800; letter-spacing: -0.3px; line-height: 1.1; }
.hdr .sub { position: absolute; left: 26px; top: 56px; font-size: 11.5px; color: #B9C4D8; line-height: 1.35; width: 760px; }
.kpi { position: absolute; top: 16px; height: 72px; width: 178px; border-radius: 10px; background: #1F3150; border: 1px solid #2E4368; padding: 10px 12px; }
.kpi .v { font-size: 14.5px; white-space: nowrap; font-weight: 800; color: #fff; line-height: 1.1; letter-spacing: -0.3px; }
.kpi .l { font-size: 10.5px; color: #B9C4D8; margin-top: 4px; line-height: 1.25; }
.sec { position: absolute; border: 1px solid #DCE1EA; border-radius: 12px; background: #fff; }
.sec > .st { position: absolute; left: 14px; top: -11px; background: #fff; padding: 0 8px; font-size: 13.5px; font-weight: 800; color: #152238; letter-spacing: -0.1px; }
.sec > .st .n { display: inline-block; width: 20px; height: 20px; border-radius: 50%; background: #152238; color: #fff; text-align: center; line-height: 20px; font-size: 11.5px; margin-right: 6px; }
.sec > .st .hint { font-weight: 500; color: #5C6B85; font-size: 12px; margin-left: 8px; }
svg text { font-family: 'Inter', 'Liberation Sans', Arial, sans-serif; }
.chip { display: inline-block; font-size: 9.5px; font-weight: 700; padding: 1px 6px; border-radius: 999px; line-height: 14px; }
.c-contr { background: #DCE7FB; color: #1F4FB0; }
.c-cust { background: #FBE0DD; color: #B8321F; }
.c-both { background: #E9E2FB; color: #5B3FB5; }
.c-pay { background: #DDF3E3; color: #1E7A3A; }
.card { position: absolute; border-radius: 10px; border: 1px solid #E3E7EF; background: #FAFBFD; padding: 8px 10px; }
.card .nm { font-size: 12.5px; font-weight: 800; line-height: 1.15; }
.card .cp { font-size: 10px; white-space: nowrap; overflow: hidden; color: #4A5670; line-height: 1.3; margin-top: 3px; }
.card .row { display: flex; gap: 8px; margin-top: 3px; white-space: nowrap; font-size: 10.5px; color: #4A5670; }
.card .row b { color: #1B2333; font-size: 12px; }
.sw { position: absolute; left: 0; top: 0; bottom: 0; width: 6px; border-radius: 10px 0 0 10px; }
.note { font-size: 10px; color: #3A4458; line-height: 1.35; }
.note li { margin: 0 0 4px 0; }
.note ul { margin: 0; padding-left: 14px; }
.foot { position: absolute; left: 26px; right: 26px; bottom: 8px; font-size: 9.5px; color: #6B778C; line-height: 1.3; }
.legend { display: inline-block; margin-right: 14px; }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; vertical-align: -1px; margin-right: 4px; }
"""

parts = []
A = parts.append
A("<!doctype html><html lang='ru'><head><meta charset='utf-8'><title>Дорожная карта поставки</title><style>" + css + "</style></head><body><div class='page'>")

# ---------- header ----------
A("<div class='hdr'>")
A("<div class='title'>Дорожная карта поставки оборудования оперативной радиосвязи</div>")
A("<div class='sub'>Упрощённая схема по Графику изготовления и поставки (Дополнение 1.2 к Приложению № 1). Все сроки — относительные: "
  "<b style='color:#fff'>T0</b> вступление Договора в силу · <b style='color:#fff'>A</b> получение аванса · <b style='color:#fff'>S</b> Дата отгрузки · <b style='color:#fff'>ДП</b> Дата поставки (Акт входного контроля). Суммы — USD по Спецификации.</div>")
kpis = [
    (usd(TOTAL) + " USD", "Цена по Спецификации<br>(к пересчёту в EGP)"),
    ("3 партии · 56 компл.", "+ комплекс услуг<br>(FAT, сборы NTRA)"),
    ("90 + 30 + 10 дн", "изготовление · доставка<br>до Площадки · входной контроль"),
    ("35 / 30 / 30 / 5 %", "аванс · после отгрузки ·<br>после Акта ВК · окончательный"),
]
x = W - M - len(kpis) * 186 + 8
for v, l in kpis:
    A(f"<div class='kpi' style='left:{x}px'><div class='v'>{v}</div><div class='l'>{l}</div></div>")
    x += 186
A("</div>")

# =====================================================================
# Section 1 : macro timeline (all lots relative to T0)
# =====================================================================
S1_top, S1_h = 126, 378
A(f"<div class='sec' style='left:{M}px;top:{S1_top}px;width:{W-2*M}px;height:{S1_h}px'>"
  "<div class='st'><span class='n'>1</span>Сводная карта: все партии и платежи относительно T0"
  "<span class='hint'>масштаб — календарные дни от вступления Договора в силу; месяц ≈ 30 дн</span></div>")

sw, sh = W - 2*M - 2, S1_h - 2
A(f"<svg class='abs' style='left:0;top:0' width='{sw}' height='{sh}' viewBox='0 0 {sw} {sh}'>")
x0, x1 = 232, sw - 150
DMAX = 215
def X(d): return x0 + (x1 - x0) * d / DMAX
axis_y = 34
# month grid
for m in range(0, 8):
    d = m * 30
    if d > DMAX: break
    xx = X(d)
    A(f"<line x1='{xx:.1f}' y1='{axis_y}' x2='{xx:.1f}' y2='{sh-16}' stroke='#E6EAF2' stroke-width='1'/>")
    lab = "T0" if m == 0 else f"+{m} мес"
    A(f"<text x='{xx:.1f}' y='{axis_y-8}' font-size='11' font-weight='700' fill='#5C6B85' text-anchor='middle'>{lab}</text>")
A(f"<line x1='{x0}' y1='{axis_y}' x2='{X(DMAX):.1f}' y2='{axis_y}' stroke='#152238' stroke-width='1.5'/>")
A(f"<polygon points='{X(DMAX):.1f},{axis_y-4} {X(DMAX)+8:.1f},{axis_y} {X(DMAX):.1f},{axis_y+4}' fill='#152238'/>")
# T0 and A markers
A(f"<line x1='{X(0):.1f}' y1='{axis_y}' x2='{X(0):.1f}' y2='{sh-16}' stroke='#152238' stroke-width='1.5'/>")
A(f"<line x1='{X(ADV_DAY):.1f}' y1='{axis_y}' x2='{X(ADV_DAY):.1f}' y2='{sh-16}' stroke='#1E7A3A' stroke-width='1.2' stroke-dasharray='4 3'/>")
ADV_LABEL = True

lane_y = 54
lane_h = 58
def lot_lane(lot, y):
    c, lt, md, S = lot["color"], lot["light"], lot["mid"], lot["S"]
    by, bh = y + 14, 24
    # label
    A(f"<text x='14' y='{y+22}' font-size='12.5' font-weight='800' fill='#1B2333'>{html.escape(lot['name'])}</text>")
    A(f"<text x='14' y='{y+37}' font-size='10' fill='#5C6B85'>{lot['sets']} компл. · <tspan font-weight='700' fill='#1B2333'>{usd(lot['cost'])} USD</tspan></text>")
    A(f"<text x='14' y='{y+50}' font-size='9.5' fill='#5C6B85'>{html.escape(lot['term'])}</text>")
    # segments
    def seg(d0, d1, fill, label, dark=False, dash=False):
        xa, xb = X(max(d0, 0)), X(d1)
        extra = " stroke-dasharray='3 2'" if dash else ""
        A(f"<rect x='{xa:.1f}' y='{by}' width='{xb-xa:.1f}' height='{bh}' fill='{fill}' stroke='{c}' stroke-width='1'{extra}/>")
        if label:
            col = '#fff' if dark else '#1B2333'
            A(f"<text x='{(xa+xb)/2:.1f}' y='{by+15.5}' font-size='9.5' font-weight='600' fill='{col}' text-anchor='middle'>{html.escape(label)}</text>")
    if lot["pre_note"]:
        seg(0, S, lt, lot["pre_note"], dash=True)
    else:
        seg(S-90, S-30, lt, "изготовление · 60 дн")
        seg(S-30, S, md, "FAT, разрешения · 30 дн")
    seg(S, S+SITE, c, "перевозка до Площадки · 30 дн", dark=True)
    seg(S+SITE, S+DP, "#152238", "ВК 10 дн", dark=True)
    # S diamond
    xs = X(S); cy = by - 7
    A(f"<polygon points='{xs:.1f},{cy-7} {xs+7:.1f},{cy} {xs:.1f},{cy+7} {xs-7:.1f},{cy}' fill='{c}' stroke='#fff' stroke-width='1.5'/>")
    A(f"<text x='{xs+11:.1f}' y='{cy+4}' font-size='10' font-weight='800' fill='{c}'>S{lot['key']} = T0 + {S} дн</text>")
    # DP flag
    xd = X(S+DP)
    A(f"<line x1='{xd:.1f}' y1='{by-3}' x2='{xd:.1f}' y2='{by+bh+14}' stroke='#152238' stroke-width='1.5'/>")
    A(f"<polygon points='{xd:.1f},{by+bh+2} {xd+9:.1f},{by+bh+7} {xd:.1f},{by+bh+12}' fill='#152238'/>")
    A(f"<text x='{xd+12:.1f}' y='{by+bh+13}' font-size='10' font-weight='800' fill='#152238'>ДП{lot['key']} = T0 + {S+DP} дн</text>")
    # Cairo tick
    xc = X(S+TRANSIT_CAIRO)
    A(f"<line x1='{xc:.1f}' y1='{by}' x2='{xc:.1f}' y2='{by+bh}' stroke='#fff' stroke-width='1' stroke-dasharray='2 2'/>")

for i, lot in enumerate(LOTS):
    lot_lane(lot, lane_y + i * lane_h)

# payments lane
py = lane_y + 3 * lane_h + 2
A(f"<line x1='8' y1='{py-6}' x2='{sw-8}' y2='{py-6}' stroke='#DCE1EA' stroke-width='1'/>")
A(f"<text x='14' y='{py+16}' font-size='12.5' font-weight='800' fill='#1E7A3A'>Платежи (ст. 23)</text>")
A(f"<text x='14' y='{py+31}' font-size='10' fill='#5C6B85'>в течение 10 дн после условия;</text>")
A(f"<text x='14' y='{py+44}' font-size='10' fill='#5C6B85'>2-й и 3-й — по каждой партии</text>")
pay_axis = py + 30
A(f"<text x='{X(ADV_DAY)+4:.1f}' y='{py-12}' font-size='10' font-weight='700' fill='#1E7A3A'>A = T0 + 10 дн · получение аванса</text>")
A(f"<line x1='{x0}' y1='{pay_axis}' x2='{X(DMAX):.1f}' y2='{pay_axis}' stroke='#1E7A3A' stroke-width='1.2'/>")

def pay_marker(d, title, amount, color, up):
    xx = X(d)
    A(f"<circle cx='{xx:.1f}' cy='{pay_axis}' r='6' fill='{color}' stroke='#fff' stroke-width='1.5'/>")
    if up:
        ty = pay_axis - 14
        A(f"<text x='{xx:.1f}' y='{ty-11}' font-size='10' font-weight='800' fill='{color}' text-anchor='middle'>{html.escape(title)}</text>")
        A(f"<text x='{xx:.1f}' y='{ty+1}' font-size='10.5' font-weight='800' fill='#1B2333' text-anchor='middle'>{amount}</text>")
    else:
        ty = pay_axis + 20
        A(f"<text x='{xx:.1f}' y='{ty}' font-size='10' font-weight='800' fill='{color}' text-anchor='middle'>{html.escape(title)}</text>")
        A(f"<text x='{xx:.1f}' y='{ty+12}' font-size='10.5' font-weight='800' fill='#1B2333' text-anchor='middle'>{amount}</text>")

pay_marker(ADV_DAY, "35 % аванс · A", usd(TOTAL*0.35) + " USD", "#1E7A3A", True)
for lot in LOTS:
    amt = usd(lot["cost"]*0.30)
    pay_marker(lot["S"] + PAY_LAG, f"30 % Ч.{lot['key']} · S{lot['key']}+10", amt, lot["color"], False)
    pay_marker(lot["S"] + DP + PAY_LAG, f"30 % Ч.{lot['key']} · ДП{lot['key']}+10", amt, lot["color"], True)
# final payment (off-axis)
xf = X(DMAX) + 10
A(f"<rect x='{xf}' y='{pay_axis-26}' width='128' height='52' rx='8' fill='#F3F5F9' stroke='#DCE1EA'/>")
A(f"<text x='{xf+64}' y='{pay_axis-10}' font-size='10' font-weight='800' fill='#1E7A3A' text-anchor='middle'>5 % окончательный</text>")
A(f"<text x='{xf+64}' y='{pay_axis+3}' font-size='10.5' font-weight='800' fill='#1B2333' text-anchor='middle'>{usd(TOTAL*0.05)} USD</text>")
A(f"<text x='{xf+64}' y='{pay_axis+16}' font-size='9' fill='#5C6B85' text-anchor='middle'>по факту: Акт сдачи-приёмки</text>")
A(f"<text x='{xf+64}' y='{pay_axis+26}' font-size='9' fill='#5C6B85' text-anchor='middle'>по Блоку + 30 дн</text>")
# problems lane
pz = pay_axis + 44
A(f"<line x1='8' y1='{pz-6}' x2='{sw-8}' y2='{pz-6}' stroke='#DCE1EA' stroke-width='1'/>")
A(f"<text x='14' y='{pz+16}' font-size='12.5' font-weight='800' fill='#B8321F'>Проблемы</text>")
A(f"<text x='14' y='{pz+31}' font-size='10' fill='#5C6B85'>сроки — от текущей даты (≈ T0)</text>")
prob_axis = pz + 26
A(f"<line x1='{x0}' y1='{prob_axis}' x2='{X(DMAX):.1f}' y2='{prob_axis}' stroke='#B8321F' stroke-width='1' stroke-dasharray='4 3'/>")
# ASE supplementary agreement: open-ended bar
A(f"<rect x='{X(0):.1f}' y='{prob_axis-9}' width='{X(28)-X(0):.1f}' height='18' rx='4' fill='#FBE0DD' stroke='#B8321F' stroke-dasharray='3 2'/>")
A(f"<text x='{X(0)+5:.1f}' y='{prob_axis+4}' font-size='9.5' font-weight='700' fill='#B8321F'>Допсоглашение с АСЭ</text>")
A(f"<text x='{X(0)+5:.1f}' y='{prob_axis+22}' font-size='9' fill='#5C6B85'>срок не определён</text>")
# encryption -> customs release, 1 month
xe = X(30)
A(f"<line x1='{xe:.1f}' y1='{prob_axis}' x2='{xe:.1f}' y2='{lane_y+14}' stroke='#B8321F' stroke-width='1.2' stroke-dasharray='3 2'/>")
A(f"<polygon points='{xe:.1f},{prob_axis-8} {xe+8:.1f},{prob_axis} {xe:.1f},{prob_axis+8} {xe-8:.1f},{prob_axis}' fill='#B8321F' stroke='#fff' stroke-width='1.5'/>")
A(f"<text x='{xe+12:.1f}' y='{prob_axis-2}' font-size='10' font-weight='800' fill='#B8321F'>Шифрование → таможня · решение: 1 мес</text>")
A(f"<text x='{xe+12:.1f}' y='{prob_axis+11}' font-size='9' fill='#5C6B85'>риск задержки выпуска Части 3 (Каир = S3 + 7 дн)</text>")
# working documentation before New Year
xr = X(77)
A(f"<polygon points='{xr:.1f},{prob_axis-8} {xr+8:.1f},{prob_axis} {xr:.1f},{prob_axis+8} {xr-8:.1f},{prob_axis}' fill='#B8321F' stroke='#fff' stroke-width='1.5'/>")
A(f"<text x='{xr+12:.1f}' y='{prob_axis-2}' font-size='10' font-weight='800' fill='#B8321F'>РД: разработка 16 компл. + согласование 27 компл. · до Нового года (≈ T0 + 2,5 мес)</text>")
A(f"<text x='{xr+12:.1f}' y='{prob_axis+11}' font-size='9' fill='#5C6B85'>до отгрузки Части 1 (S1 = T0 + 95 дн)</text>")
# services note
A(f"<text x='{x0}' y='{sh-5}' font-size='9' fill='#6B778C'>Комплекс услуг {usd(SERVICES['cost'])} USD оплачивается в тех же долях (30 % = {usd(SERVICES['cost']*0.3)} USD) и на маркерах не показан. Пунктирная засечка внутри перевозки — прибытие в Каир (S + 7 дн, авиа).</text>")
A("</svg></div>")

# =====================================================================
# Section 2 : typical lot cycle relative to S
# =====================================================================
S2_top, S2_h = S1_top + S1_h + 18, 288
A(f"<div class='sec' style='left:{M}px;top:{S2_top}px;width:{W-2*M}px;height:{S2_h}px'>"
  "<div class='st'><span class='n'>2</span>Типовой цикл одной партии: все события относительно Даты отгрузки S"
  "<span class='hint'>S — приём грузовых мест первым перевозчиком; одинаков для Части 1, 2 и 3</span></div>")
sw2, sh2 = W - 2*M - 2, S2_h - 2
A(f"<svg class='abs' style='left:0;top:0' width='{sw2}' height='{sh2}' viewBox='0 0 {sw2} {sh2}'>")
d0, d1 = -95, 46
xa0, xa1 = 40, sw2 - 40
def X2(d): return xa0 + (xa1 - xa0) * (d - d0) / (d1 - d0)
ay = sh2 / 2 + 4   # axis y
# phase bands
phases = [(-90, -30, "#EEF2F8", "#5C6B85", "ИЗГОТОВЛЕНИЕ · 60 дн"),
          (-30, 0, "#E9E2FB", "#5B3FB5", "ИСПЫТАНИЯ · FAT · РАЗРЕШЕНИЯ NTRA · 30 дн"),
          (0, 30, "#DCE7FB", "#1F4FB0", "ПЕРЕВОЗКА (авиа → Каир → Площадка) · 30 дн"),
          (30, 40, "#152238", "#fff", "ВК · 10 дн")]
bh2 = 34
for a, b, f, tc, lab in phases:
    xa, xb = X2(a), X2(b)
    A(f"<rect x='{xa:.1f}' y='{ay-bh2/2}' width='{xb-xa:.1f}' height='{bh2}' fill='{f}' stroke='#fff' stroke-width='2'/>")
    A(f"<text x='{(xa+xb)/2:.1f}' y='{ay+12}' font-size='10' font-weight='800' fill='{tc}' text-anchor='middle' letter-spacing='0.3'>{lab}</text>")
# ticks
for d in [-90, -60, -30, -20, -15, -1, 0, 1, 7, 30, 40]:
    xx = X2(d)
    lab = "S" if d == 0 else (f"S{d:+d}".replace("+", "+").replace("-", "−"))
    A(f"<line x1='{xx:.1f}' y1='{ay+bh2/2}' x2='{xx:.1f}' y2='{ay+bh2/2+5}' stroke='#152238' stroke-width='1'/>")
# milestones: (day, slot_x_center, above?, title, lines, chips)
RESP = {"contr": ("Подрядчик", "#DCE7FB", "#1F4FB0"), "cust": ("Заказчик", "#FBE0DD", "#B8321F"),
        "both": ("Стороны", "#E9E2FB", "#5B3FB5"), "pay": ("платёж", "#DDF3E3", "#1E7A3A")}
ms = [
    (-90, True,  "S − 90 дн", ["Уведомление об отгрузке (Прил. № 11)", "Старт изготовления на заводе", "Подтверждение стоимости перевозки"], ["contr"]),
    (-60, False, "S − 60 дн", ["Уведомление о тяжеловесных /", "крупногабаритных грузах (п. 8.14)"], ["contr"]),
    (-30, True,  "S − 30 дн", ["Завершение изготовления, заводские испытания", "Копии Type Approval NTRA (п. 8.6)", "Заявление в NTRA на разрешение на ввоз"], ["contr"]),
    (-20, False, "S − 20 дн", ["Приёмочная инспекция (FAT) на заводе,", "г. Шэньчжэнь, с участием Заказчика", "Данные для страхования груза (п. 8.1)"], ["contr", "cust"]),
    (-15, True,  "S − 15 … 14 дн", ["Удостоверение о приёмочной инспекции (EN-004)", "Документы для лицензии NTRA на частоты", "Сканы отгрузочных документов, заявка на проформу"], ["both"]),
    (-1,  False, "S − 1 дн · стоп-точка", ["ACID-номер для транспортных документов", "Письменное разрешение на отгрузку", "+ копия страхового полиса"], ["cust"]),
    (0,   True,  "S · ДАТА ОТГРУЗКИ", ["Приём грузовых мест первым перевозчиком", "S+1: копия транспортного документа,", "Акт о переходе права собственности"], ["contr", "pay"]),
    (7,   False, "S + 7 дн", ["Прибытие в аэропорт Каира", "(CIF Каир, авиа; оценочный срок)"], ["contr"]),
    (30,  True,  "S + 30 дн", ["Прибытие на Строительную площадку", "Передача разрешения NTRA на ввоз", "(не позднее прибытия)"], ["contr"]),
    (40,  False, "S + 40 дн · ДАТА ПОСТАВКИ", ["Входной контроль, Акт ВК без замечаний", "Передача документации (Прил. № 3)", "Старт гарантийного периода"], ["both", "pay"]),
]
# slots: evenly spread for above and below rows
above = [m for m in ms if m[1]]
below = [m for m in ms if not m[1]]
box_w = 262
def slots(n):
    span = xa1 - xa0
    step = (span - box_w) / (n - 1)
    return [xa0 + box_w/2 + i*step for i in range(n)]
sa, sb = slots(len(above)), slots(len(below))
box_h = 80
for row, sl, up in ((above, sa, True), (below, sb, False)):
    for (d, _, title, lines, chips), cx in zip(row, sl):
        xx = X2(d)
        bx = cx - box_w/2
        by = ay - bh2/2 - 18 - box_h if up else ay + bh2/2 + 18
        # leader
        ly0 = by + box_h if up else by
        ly1 = ay - bh2/2 if up else ay + bh2/2
        A(f"<path d='M{cx:.1f},{ly0} L{cx:.1f},{(ly0+ly1)/2:.1f} L{xx:.1f},{(ly0+ly1)/2:.1f} L{xx:.1f},{ly1}' fill='none' stroke='#9AA6BD' stroke-width='1.2'/>")
        strong = d in (0, 40, -1)
        stroke = "#152238" if d in (0, 40) else ("#B8321F" if d == -1 else "#DCE1EA")
        A(f"<rect x='{bx:.1f}' y='{by}' width='{box_w}' height='{box_h}' rx='8' fill='#fff' stroke='{stroke}' stroke-width='{1.6 if strong else 1}'/>")
        tcol = "#152238" if d in (0, 40) else ("#B8321F" if d == -1 else "#5B3FB5" if -30 <= d < 0 else "#1F4FB0" if d > 0 else "#5C6B85")
        A(f"<text x='{bx+10:.1f}' y='{by+16}' font-size='11' font-weight='800' fill='{tcol}'>{html.escape(title)}</text>")
        for i, ln in enumerate(lines):
            A(f"<text x='{bx+10:.1f}' y='{by+31+i*12.5:.1f}' font-size='9.8' fill='#1B2333'>{html.escape(ln)}</text>")
        # chips
        chx = bx + 10
        chy = by + box_h - 8
        for ch in chips:
            name, bg, fg = RESP[ch]
            wch = 8 + len(name) * 5.6
            A(f"<rect x='{chx:.1f}' y='{chy-11}' width='{wch:.1f}' height='14' rx='7' fill='{bg}'/>")
            A(f"<text x='{chx+wch/2:.1f}' y='{chy-1}' font-size='9' font-weight='700' fill='{fg}' text-anchor='middle'>{name}</text>")
            chx += wch + 5
        # point on axis
        A(f"<circle cx='{xx:.1f}' cy='{ay-8}' r='{6 if strong else 4.5}' fill='{'#152238' if d in (0,40) else ('#B8321F' if d == -1 else '#fff')}' stroke='{'#fff' if d in (0,40,-1) else '#152238'}' stroke-width='1.5'/>")
A("</svg></div>")

# =====================================================================
# Section 3/4/5 : lots, payments, conditions
# =====================================================================
S3_top = S2_top + S2_h + 18
S3_h = H - S3_top - 30
col_gap = 16
c1w, c2w = 462, 540
c3w = W - 2*M - c1w - c2w - 2*col_gap
c1x, c2x, c3x = M, M + c1w + col_gap, M + c1w + col_gap + c2w + col_gap

# --- lots ---
A(f"<div class='sec' style='left:{c1x}px;top:{S3_top}px;width:{c1w}px;height:{S3_h}px'>"
  "<div class='st'><span class='n'>3</span>Партии поставки и суммы<span class='hint'>USD по Спецификации</span></div>")
y = 16
order = sorted(LOTS, key=lambda l: l["key"])
for lot in order:
    A(f"<div class='card' style='left:12px;top:{y}px;width:{c1w-24}px;height:58px;padding-left:16px'>"
      f"<div class='sw' style='background:{lot['color']}'></div>"
      f"<div style='display:flex;justify-content:space-between;align-items:baseline'><div class='nm'>{html.escape(lot['name'])}</div>"
      f"<div style='font-size:15px;font-weight:800;color:{lot['color']}'>{usd(lot['cost'])} USD</div></div>"
      f"<div class='cp'>{html.escape(lot['comp'])}</div>"
      f"<div class='row'><span><b>{lot['sets']}</b> компл.</span><span>{html.escape(lot['term'].replace(' (условия поставщика)','').replace(' (CIF, авиа)',''))}</span><span>S{lot['key']} = T0+{lot['S']} · ДП{lot['key']} = T0+{lot['S']+DP} дн</span></div></div>")
    y += 62
A(f"<div class='card' style='left:12px;top:{y}px;width:{c1w-24}px;height:30px;padding-left:16px;padding-top:6px'>"
  f"<div class='sw' style='background:#8A94A8'></div>"
  f"<div style='display:flex;justify-content:space-between;align-items:baseline'><div class='nm'>{SERVICES['name']} <span style='font-weight:500;font-size:10.5px;color:#4A5670'>— {html.escape(SERVICES['comp'])}</span></div>"
  f"<div style='font-size:13px;font-weight:800;color:#5C6B85;white-space:nowrap'>{usd(SERVICES['cost'])} USD</div></div></div>")
y += 34
A(f"<div class='abs' style='left:12px;top:{y}px;width:{c1w-24}px;display:flex;justify-content:space-between;align-items:baseline;border-top:2px solid #152238;padding-top:6px'>"
  f"<div style='font-size:13px;font-weight:800'>ИТОГО по Спецификации</div><div style='font-size:17px;font-weight:800'>{usd(TOTAL)} USD</div></div>")
A("</div>")

# --- payments ---
A(f"<div class='sec' style='left:{c2x}px;top:{S3_top}px;width:{c2w}px;height:{S3_h}px'>"
  "<div class='st'><span class='n'>4</span>Платежи по ст. 23 Договора<span class='hint'>доля от Цены · условие · срок</span></div>")
# stacked bar
bx, by, bw, bhh = 12, 16, c2w - 24, 22
A(f"<svg class='abs' style='left:0;top:0' width='{c2w}' height='{by+bhh+30}'>")
segs = [(35, "#1E7A3A", "35 % аванс"), (30, "#2F6FDE", "30 % после отгрузки"), (30, "#5B3FB5", "30 % после Акта ВК"), (5, "#D97A1A", "5 %")]
xx = bx
for p, col, lab in segs:
    w = bw * p / 100
    A(f"<rect x='{xx:.1f}' y='{by}' width='{w:.1f}' height='{bhh}' fill='{col}' stroke='#fff' stroke-width='2'/>")
    A(f"<text x='{xx+w/2:.1f}' y='{by+15}' font-size='10' font-weight='800' fill='#fff' text-anchor='middle'>{lab}</text>")
    A(f"<text x='{xx+w/2:.1f}' y='{by+bhh+14}' font-size='10' font-weight='700' fill='#1B2333' text-anchor='middle'>{usd(TOTAL*p/100)}</text>")
    xx += w
A("</svg>")
pays = [
    ("1", "#1E7A3A", "Аванс · 35 %", usd(TOTAL*0.35), "Обеспечения возврата аванса и исполнения Договора (≥ 5 раб. дн до платежа); счёт", "10 кал. дн от вступления в силу → A = T0 + 10 дн"),
    ("2", "#2F6FDE", "Второй · 30 %", usd(TOTAL*0.30), "Удостоверение о приёмочной инспекции; разрешение на отгрузку; копия транспортного документа", "10 кал. дн · по каждой партии (первая — Часть 3) → S + 10 дн"),
    ("3", "#5B3FB5", "Третий · 30 %", usd(TOTAL*0.30), "Акт ВК без замечаний + документы по п. 23.3; не ранее 10 раб. дн после оплаты Ген. заказчиком", "10 кал. дн, не позднее 75 дн от Акта · по партии → ДП + 10 дн"),
    ("4", "#D97A1A", "Окончательный · 5 %", usd(TOTAL*0.05), "Акт сдачи-приёмки Оборудования по Блоку; действующее Обеспечение исполнения Договора", "30 кал. дн · по каждому Блоку после Акта Собственника об Этапе СФЗ"),
]
y = by + bhh + 24
for n, col, nm, amt, cond, term in pays:
    A(f"<div class='abs' style='left:12px;top:{y}px;width:{c2w-24}px;height:42px;border-left:4px solid {col};padding-left:8px'>"
      f"<div style='display:flex;justify-content:space-between'><div style='font-size:12px;font-weight:800;color:{col}'>{nm}</div><div style='font-size:12px;font-weight:800'>{amt} USD</div></div>"
      f"<div style='font-size:9.4px;color:#4A5670;line-height:1.25;white-space:nowrap'>{html.escape(cond)}</div>"
      f"<div style='font-size:9.6px;font-weight:700;color:#1B2333;line-height:1.25;white-space:nowrap'>{html.escape(term)}</div></div>")
    y += 43
# per-lot 30% table
A(f"<div class='abs' style='left:12px;top:{y+2}px;width:{c2w-24}px;border-top:1px solid #DCE1EA;padding-top:5px;font-size:10px;color:#4A5670'>"
  "<b style='color:#1B2333'>30 % по партиям</b> (2-й и 3-й платёж, каждый): "
  + " · ".join(f"<span style='color:{l['color']};font-weight:800'>Ч.{l['key']}</span> {usd(l['cost']*0.3)}" for l in order)
  + f" · услуги {usd(SERVICES['cost']*0.3)}</div>")
A("</div>")

# --- problems & open questions ---
A(f"<div class='sec' style='left:{c3x}px;top:{S3_top}px;width:{c3w}px;height:{S3_h}px;border-color:#E8B4AE'>"
  "<div class='st'><span class='n' style='background:#B8321F'>5</span>Проблемы и открытые вопросы<span class='hint'>сроки — от текущей даты</span></div>")
probs = [
    ("Шифрование радиооборудования", "влияет на выпуск из таможни Египта", "решение: 1 мес"),
    ("Рабочая документация (РД)", "разработка 16 комплектов + согласование 27 комплектов", "до Нового года"),
    ("Дополнительное соглашение с АСЭ", "подготовка и согласование", "срок не определён"),
]
y = 16
A(f"<div class='abs' style='left:14px;top:{y}px;font-size:10px;font-weight:800;color:#B8321F;letter-spacing:.4px'>ПРОБЛЕМЫ</div>")
y += 16
for t, d, term in probs:
    A(f"<div class='abs' style='left:14px;top:{y}px;width:{c3w-28}px;height:34px;border-left:4px solid #B8321F;padding-left:8px;background:#FFF6F5;border-radius:0 6px 6px 0'>"
      f"<div style='display:flex;justify-content:space-between;align-items:baseline'><div style='font-size:11.5px;font-weight:800;padding-top:3px'>{html.escape(t)}</div>"
      f"<div style='font-size:10px;font-weight:800;color:#B8321F;white-space:nowrap;padding-top:3px'>{html.escape(term)}</div></div>"
      f"<div style='font-size:10px;color:#4A5670;line-height:1.2'>{html.escape(d)}</div></div>")
    y += 39
y += 6
A(f"<div class='abs' style='left:14px;top:{y}px;font-size:10px;font-weight:800;color:#5B3FB5;letter-spacing:.4px'>ВОПРОСЫ К РЕШЕНИЮ В КОМАНДИРОВКЕ В КИТАЙ (HYTERA)</div>")
y += 16
qs = [
    "Окончательное согласование всего технического решения",
    "Разработка с инженерами Hytera решения по АФУ по параметрам NTRA",
    "Получение сертификата проектировщика от Hytera",
    "Проверка избыточности или дефицита лицензий",
]
for i, q in enumerate(qs, 1):
    A(f"<div class='abs' style='left:14px;top:{y}px;width:{c3w-28}px;display:flex;gap:7px;align-items:flex-start'>"
      f"<div style='flex:0 0 17px;height:17px;border-radius:50%;background:#E9E2FB;color:#5B3FB5;font-size:10px;font-weight:800;text-align:center;line-height:17px'>{i}</div>"
      f"<div style='font-size:10.5px;line-height:1.25;padding-top:1px'>{html.escape(q)}</div></div>")
    y += 24
A("</div>")

# footer
A("<div class='foot'>"
  "<span class='legend'><i style='background:#EEF2F8;border:1px solid #9AA6BD'></i>изготовление</span>"
  "<span class='legend'><i style='background:#E9E2FB'></i>испытания и разрешения</span>"
  "<span class='legend'><i style='background:#2F6FDE'></i>перевозка</span>"
  "<span class='legend'><i style='background:#152238'></i>входной контроль</span>"
  "<span class='legend'><i style='background:#1E7A3A;border-radius:50%'></i>платёж</span>"
  "&nbsp;&nbsp;Источник: График изготовления и поставки (Дополнение 1.2 к Приложению № 1), Modified_Nept_list_13-10-2026. Суммы USD по Спецификации (к пересчёту в EGP). Сроки — календарные дни; месяц на шкале = 30 дн."
  "</div>")
A("</div></body></html>")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("".join(parts))
print("written", OUT)
