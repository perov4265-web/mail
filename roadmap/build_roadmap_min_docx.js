const fs = require('fs');
const D = require('docx');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
        BorderStyle, AlignmentType, VerticalAlign, HeightRule, PageOrientation, TabStopType } = D;

const OUT = process.argv[2];
const FONT = 'Arial';
const INK = '111111', MUTE = '8A8F99', LINE = 'D9DCE2', ACC = 'D63B2F', BAR = '111111';

const usd = x => Math.round(x).toLocaleString('ru-RU').replace(/ /g, ' ');
const TOTAL = 1884766.26, ADV = 10, DP = 40, LAG = 10;
const LOTS = [
  { key: '3', name: 'Часть 3 · ПАК', sub: 'программно-аппаратные комплексы · T0 + 1 мес', cost: 615158.76, S: 24 },
  { key: '1', name: 'Часть 1 · Радиостанции', sub: 'носимые и возимые · Каир = A + 3 мес', cost: 306350, S: 95 },
  { key: '2', name: 'Часть 2 · Базовые станции', sub: 'антенны, БП, инфраструктура · Каир = A + 5 мес', cost: 953047.5, S: 154 },
];

// ---------- page: A3 landscape ----------
const PAGE_W = 23811, PAGE_H = 16838, MARG = 680;  // DXA, A3 landscape
const USABLE = PAGE_W - 2 * MARG;                           // 15478
const NCELL = 21;                                           // 10-day cells, 7 months
const LABEL_W = 4700;
const CELL_W = Math.floor((USABLE - LABEL_W) / NCELL);      // 575
const TABLE_W = LABEL_W + CELL_W * NCELL;

const none = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const thin = (c = LINE) => ({ style: BorderStyle.SINGLE, size: 4, color: c });
const NOB = { top: none, bottom: none, left: none, right: none, insideHorizontal: none, insideVertical: none };

const FS = 1.35;
const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: Math.round((o.size || 18) * FS), bold: !!o.bold, color: o.color || INK });
const par = (runs, o = {}) => new Paragraph({ children: Array.isArray(runs) ? runs : [runs], alignment: o.align || AlignmentType.LEFT,
  spacing: { before: o.before || 0, after: o.after || 0, line: o.line || 240 }, tabStops: o.tabs,
  indent: o.hang ? { left: o.hang, hanging: o.hang } : undefined });

function cell(children, o = {}) {
  return new TableCell({
    children: children.length ? children : [par(run(''))],
    width: { size: o.w || CELL_W, type: WidthType.DXA },
    columnSpan: o.span, rowSpan: o.rowSpan,
    shading: o.fill ? { type: ShadingType.CLEAR, fill: o.fill, color: 'auto' } : undefined,
    borders: { top: o.top || none, bottom: o.bottom || none, left: o.left || none, right: o.right || none },
    verticalAlign: o.valign || VerticalAlign.CENTER,
    margins: { top: 20, bottom: 20, left: o.ml ?? 60, right: 60 },
  });
}
const idx = d => Math.min(NCELL - 1, Math.floor(d / 10));   // day -> cell index
const monthLeft = i => (i % 3 === 0 ? thin() : none);         // light vertical line at month boundaries

// build a grid row: segments = [{from, to(excl), children, fill, ...}], others empty
function gridRow(labelCell, segments, h) {
  h = Math.round(h * 1.85);
  const cells = [];
  if (labelCell) cells.push(labelCell);
  let i = 0;
  const segs = [...segments].sort((a, b) => a.from - b.from);
  for (const s of segs) {
    while (i < s.from) { cells.push(cell([], { left: monthLeft(i) })); i++; }
    const span = s.to - s.from;
    cells.push(cell(s.children || [], { span: span > 1 ? span : undefined, w: CELL_W * span, fill: s.fill, left: s.left ?? monthLeft(i), ml: s.ml }));
    i = s.to;
  }
  while (i < NCELL) { cells.push(cell([], { left: monthLeft(i) })); i++; }
  return new TableRow({ children: cells, height: { value: h, rule: HeightRule.ATLEAST }, cantSplit: true });
}

const rows = [];
// header: month labels
{
  const cells = [cell([], { w: LABEL_W })];
  for (let m = 0; m < 7; m++) {
    cells.push(cell([par(run(m === 0 ? 'T0' : `+${m} мес`, { size: 16, color: MUTE }))],
      { span: 3, w: CELL_W * 3, left: thin(), bottom: thin(INK) }));
  }
  rows.push(new TableRow({ children: cells, height: { value: 520, rule: HeightRule.ATLEAST } }));
}
// advance row
rows.push(gridRow(cell([], { w: LABEL_W }), [
  { from: idx(ADV), to: idx(ADV) + 7, children: [par([run('● 35 % · ', { size: 17, bold: true }), run(usd(TOTAL * 0.35), { size: 17 }), run('   A = T0 + 10 дн', { size: 16, color: MUTE })])] },
], 380));

for (const lot of LOTS) {
  const S = lot.S, E = S + DP;
  const a = idx(S), b = idx(E) + 1;                         // bar cells [a, b)
  const label = cell([
    par(run(lot.name, { size: 22, bold: true })),
    par(run(lot.sub, { size: 15, color: MUTE })),
    par(run(usd(lot.cost), { size: 20, bold: true }), { before: 60 }),
  ], { w: LABEL_W, rowSpan: 3, ml: 0 });
  // spacer + label row
  rows.push(gridRow(label, [
    { from: a, to: Math.min(NCELL, b + 2), children: [par([run(`S${lot.key} · T0 + ${S}`, { size: 17, bold: true }), run('   →   ', { size: 17, color: MUTE }), run(`ДП${lot.key} · T0 + ${E}`, { size: 17, bold: true })])] },
  ], 420));
  // bar row: dotted pre-shipment (light grey) + solid transit (black)
  const pre = Math.max(idx(S - 90), 0);
  rows.push(gridRow(null, [
    { from: pre, to: a, fill: 'EEEEEE', children: [par(run('изготовление', { size: 14, color: MUTE }))] },
    { from: a, to: b, fill: BAR, children: [par([run('○ отгрузка', { size: 13, bold: true, color: 'FFFFFF' }), run(' · 40 дн · ', { size: 13, color: 'BBBBBB' }), run('■ поставка', { size: 13, bold: true, color: 'FFFFFF' })])] },
  ], 300));
  // payments row
  const p1 = idx(S + LAG), p2 = idx(E + LAG);
  const pay = '30 % · ' + usd(lot.cost * 0.3);
  if (p1 + 3 <= p2 && p2 + 3 <= NCELL) {
    rows.push(gridRow(null, [
      { from: p1, to: p1 + 3, children: [par(run('│ ' + pay, { size: 15 }))] },
      { from: p2, to: p2 + 3, children: [par(run('│ ' + pay, { size: 15 }))] },
    ], 380));
  } else {
    const w = (NCELL - p1) * CELL_W - 140;
    rows.push(gridRow(null, [
      { from: p1, to: NCELL, children: [par(run('│ ' + pay + '\t' + pay + ' │', { size: 15 }), { tabs: [{ type: TabStopType.RIGHT, position: w }] })] },
    ], 380));
  }
  rows.push(gridRow(cell([], { w: LABEL_W }), [], 160));
}
// problems row
rows.push(gridRow(cell([par(run('Проблемы', { size: 22, bold: true, color: ACC })), par(run('срок — от текущей даты', { size: 15, color: MUTE }))], { w: LABEL_W, ml: 0 }), [
  { from: 0, to: 3, children: [par(run('◆ Допсоглашение с АСЭ', { size: 14, bold: true, color: ACC })), par(run('срок не определён', { size: 15, color: MUTE }))] },
  { from: 3, to: 7, children: [par(run('◆ Шифрование → таможня', { size: 14, bold: true, color: ACC })), par(run('решение: 1 мес', { size: 15, color: MUTE }))] },
  { from: 7, to: 12, children: [par(run('◆ РД 16 + 27 компл.', { size: 14, bold: true, color: ACC })), par(run('до Нового года', { size: 15, color: MUTE }))] },
], 520));

const timeline = new Table({
  rows, width: { size: TABLE_W, type: WidthType.DXA },
  columnWidths: [LABEL_W, ...Array(NCELL).fill(CELL_W)],
  borders: NOB, layout: D.TableLayoutType.FIXED,
});

// ---------- header table ----------
const header = new Table({
  width: { size: USABLE, type: WidthType.DXA }, columnWidths: [USABLE - 5200, 5200], borders: NOB, layout: D.TableLayoutType.FIXED,
  rows: [new TableRow({ children: [
    cell([
      par([run('Поставка оборудования радиосвязи ', { size: 44 }), run('· дорожная карта', { size: 44, bold: true })]),
      par(run('T0 — вступление Договора в силу · A — аванс · S — отгрузка · ДП — Дата поставки (Акт входного контроля) · все сроки в днях от T0 · суммы USD', { size: 16, color: MUTE }), { before: 120 }),
    ], { w: USABLE - 5200, ml: 0, valign: VerticalAlign.TOP }),
    cell([
      par(run(`${usd(TOTAL)} USD`, { size: 44, bold: true }), { align: AlignmentType.RIGHT }),
      par(run('3 партии · 56 комплектов · последняя поставка T0 + 194 дн', { size: 16, color: MUTE }), { align: AlignmentType.RIGHT, before: 120 }),
    ], { w: 5200, valign: VerticalAlign.TOP }),
  ] })],
});

// ---------- bottom blocks ----------
const kv = (k, v, o = {}) => par([run(k, { size: 18, bold: true, color: o.kcolor || INK }), run('\t' + v, { size: 18 })], { tabs: [{ type: TabStopType.LEFT, position: o.tab || 1500 }], hang: o.tab || 1500, after: 100, line: 260 });
const h2 = (t, c = MUTE) => par(run(t.toUpperCase(), { size: 15, bold: true, color: c }), { after: 160 });
const col = (children, w) => cell(children, { w, ml: 0, valign: VerticalAlign.TOP });
const W1 = 6600, W2 = 9200, W3 = USABLE - W1 - W2;
const bottom = new Table({
  width: { size: USABLE, type: WidthType.DXA }, columnWidths: [W1, W2, W3], borders: NOB, layout: D.TableLayoutType.FIXED,
  rows: [new TableRow({ children: [
    col([h2('Проблемы', ACC),
      kv('1 мес', 'шифрование радиооборудования влияет на таможенный выпуск', { kcolor: ACC, tab: 1500 }),
      kv('до НГ', 'разработка 16 и согласование 27 комплектов РД', { kcolor: ACC, tab: 1500 }),
      kv('—', 'допсоглашение с АСЭ: подготовка и согласование', { kcolor: ACC, tab: 1500 }),
    ], W1),
    col([h2('Шифрование · хронология'),
      kv('08.02.2026', 'совещание, вопрос поднят', { tab: 2300 }),
      kv('09.05.2026', 'материалы по шифрованию подготовлены и переданы', { tab: 2300 }),
      kv('22.06.2026', 'NPPA официально принял материалы', { tab: 2300 }),
      kv('сентябрь', 'по нашим сведениям NPPA передал запрос только в сентябре', { kcolor: ACC, tab: 2300 }),
      par([run('Проблема', { size: 18, bold: true, color: ACC }), run('\tна вопросы и попытки уточнить информацию по шифрованию NPPA не отвечает, ссылаясь на секретность', { size: 18 })], { tabs: [{ type: TabStopType.LEFT, position: 2300 }], hang: 2300, before: 120, line: 260 }),
    ], W2),
    col([h2('Командировка в Китай · Hytera'),
      ...['Окончательное согласование технического решения', 'Решение по АФУ по параметрам NTRA, вместе с инженерами Hytera', 'Сертификат проектировщика от Hytera', 'Проверка избыточности или дефицита лицензий']
        .map((t, i) => kv(String(i + 1), t, { kcolor: MUTE, tab: 500 })),
    ], W3),
  ] })],
});

const foot = par([run('Источник: График изготовления и поставки, Дополнение 1.2 к Приложению № 1 · суммы по Спецификации, к пересчёту в EGP', { size: 14, color: MUTE }),
                  run('\tмесяц на шкале = 30 дн · ○ отгрузка · ■ Дата поставки · ◆ проблема', { size: 14, color: MUTE })],
                 { tabs: [{ type: TabStopType.RIGHT, position: USABLE }], before: 700 });

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 18, color: INK } } } },
  sections: [{
    properties: { page: { size: { width: PAGE_H, height: PAGE_W, orientation: PageOrientation.LANDSCAPE }, margin: { top: MARG, bottom: MARG, left: MARG, right: MARG } } },
    children: [header, par(run(''), { before: 500 }), timeline, par(run(''), { before: 700 }), bottom, foot],
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(OUT, b); console.log('ok', OUT); });
