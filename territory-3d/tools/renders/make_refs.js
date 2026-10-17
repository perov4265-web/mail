// Референсные скриншоты для фотореалистичного рендера (без подписей, стрелок, сетки и бордюрных линий).
// Запуск: node tools/renders/make_refs.js [имя ...]   (нужен статический сервер на :8765 и three@0.160.0 в node_modules)
const { chromium } = require(process.env.PW || 'playwright');
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');
const THREE_DIR = process.env.THREE_DIR || path.join(ROOT, 'node_modules', 'three');
const FRONT = 'cam=113.3,1.6,-258.6&at=120.4,1.8,-258.6';            // из зала напротив иконостаса
const VIEWS = {
  park_aerial: 'cam=120,45,-280&at=70,0,-322', park_aisle: 'cam=104,1.7,-323&at=60,2.5,-323',
  park_gate: 'cam=28,1.7,-335&at=60,2.5,-323', park_gabion: 'cam=90,2.5,-308&at=76,1.5,-324',
  mosque_ne: 'view=mosque', mosque_canopy: 'cam=46,2.2,-112&at=35,1.5,-118.6',
  mosque_entrance: 'cam=34,1.8,-131&at=33,1.5,-120', mosque_aerial: 'cam=22,24,-100&at=32,0,-118.6',
  mosque_interior: 'roof=0&cam=38,2.6,-123.5&at=29,1.0,-117', mosque_hall: 'cam=30.9,1.6,-116.0&at=26.7,0.7,-121.3',
  temple_nave: 'finish=wood&' + FRONT, temple_trusses: 'cam=124.5,1.6,-266&at=114,2.9,-254',
  temple_stasidia: 'cam=121,1.6,-258&at=113,1.6,-262',
};
for (const f of ['white', 'wood', 'wood_open', 'wood_glass', 'stucco', 'icons', 'ceiling']) VIEWS['temple_finish_' + f] = 'finish=' + f + '&' + FRONT;
(async () => {
  const names = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(VIEWS);
  const b = await chromium.launch({ executablePath: process.env.CHROME || undefined, args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  for (const n of names) {
    const p = await b.newPage({ viewport: { width: 1600, height: 900 } });
    p.on('pageerror', e => console.error(n, 'pageerror', e.message.slice(0, 200)));
    await p.route('https://cdn.jsdelivr.net/npm/three@0.160.0/**', r => { const rel = r.request().url().replace('https://cdn.jsdelivr.net/npm/three@0.160.0/', ''); r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(path.join(THREE_DIR, rel)) }); });
    await p.route('**/textures/plan.jpg', r => r.fulfill({ status: 200, contentType: 'image/jpeg', body: fs.readFileSync(path.join(ROOT, 'textures', 'plan_render.jpg')) }));
    await p.route('**/index.html**', async r => { const res = await r.fetch(); const t = (await res.text()).replace('function templeBox(){', 'window.__scene = scene; function templeBox(){'); r.fulfill({ response: res, body: t, headers: { 'content-type': 'text/html' } }); });
    await p.goto('http://localhost:8765/index.html?ui=0&' + VIEWS[n], { waitUntil: 'networkidle', timeout: 90000 });
    await p.waitForTimeout(1500);
    await p.evaluate((outdoor) => {
      const cb = document.getElementById('cbCurbs'); if (cb && cb.checked) cb.click();           // красные линии бордюров
      const cv = document.getElementById('cbVol'); if (outdoor && cv && !cv.checked) cv.click();     // объёмы остальных зданий
      __scene.children.forEach(o => { if (o.type === 'GridHelper') o.visible = false; });         // сетка
      __scene.children.forEach(o => { if (o.type === 'Group' && o.children.some(c => c.isSprite) && o.children.some(c => c.isMesh)) o.visible = false; }); // стрелка севера
      __scene.children.forEach(o => { if (o.type === 'Line' || o.type === 'LineSegments' || o.type === 'Line2') o.visible = false; }); // граница участка
    }, /^(park_|mosque_(ne|canopy|entrance|aerial))/.test(n));
    await p.waitForTimeout(4000);
    await p.screenshot({ path: path.join(ROOT, 'renders', n + '.jpg'), type: 'jpeg', quality: 92 });
    await p.close(); console.log('ok', n);
  }
  await b.close();
})();
