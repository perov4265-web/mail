// Temple interior for the АБК-2 hall: painted walls and ceiling, iconostasis, solea carpet, stasidia, lecterns,
// candle stands, Golgotha cross, cabinets. Geometry is parametric; textures are generated on canvas from the photo survey.
import * as THREE from 'three';

const L = (x, y, h = 0) => new THREE.Vector3(x, h, -y);
function tex(w, h, draw, repeat) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d'); draw(x, w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat[0], repeat[1]); }
  return t;
}
function box(w, h, d, mat, x, y, z, shadow = true) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); m.castShadow = shadow; m.receiveShadow = true; return m;
}
const rnd = (seed => () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; })(12345);

// ---------- textures ----------
function leaf(x, cx, cy, s, col) { x.save(); x.translate(cx, cy); x.rotate(rnd() * 6.3); x.fillStyle = col; x.beginPath(); x.moveTo(0, 0); x.quadraticCurveTo(s * 0.6, -s * 0.5, s * 1.6, 0); x.quadraticCurveTo(s * 0.6, s * 0.5, 0, 0); x.fill(); x.restore(); }
const PAL = ['#c9a86a', '#8aa7c8', '#d08c8c', '#b8c48e', '#e0b87a'];
function wallTexture(lengthM, heightM) {
  const PX = 120; const w = Math.round(lengthM * PX), h = Math.round(heightM * PX);
  return tex(w, h, (x) => {
    const band = 1.15 * PX;
    x.fillStyle = '#f4f1ea'; x.fillRect(0, 0, w, h);
    // lower band: white with blue medallions, ornamental border on top
    x.fillStyle = '#f8f7f3'; x.fillRect(0, h - band, w, band);
    for (let cx = PX * 1.0; cx < w; cx += PX * 2.0) {
      x.strokeStyle = '#4e73b0'; x.lineWidth = 6; x.beginPath(); x.arc(cx, h - band * 0.5, PX * 0.32, 0, 7); x.stroke();
      x.lineWidth = 3; x.beginPath(); x.arc(cx, h - band * 0.5, PX * 0.22, 0, 7); x.stroke();
      for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4; x.beginPath(); x.moveTo(cx + Math.cos(a) * PX * 0.1, h - band * 0.5 + Math.sin(a) * PX * 0.1); x.lineTo(cx + Math.cos(a) * PX * 0.22, h - band * 0.5 + Math.sin(a) * PX * 0.22); x.stroke(); }
    }
    x.fillStyle = '#4e73b0'; x.fillRect(0, h - band - 8, w, 8); x.fillStyle = '#c23b3b'; x.fillRect(0, h - band - 22, w, 10); x.fillStyle = '#d9b45a'; x.fillRect(0, h - band - 30, w, 6);
    for (let cx = 0; cx < w; cx += 28) { x.fillStyle = (cx / 28) % 2 ? '#4e73b0' : '#f4f1ea'; x.fillRect(cx, h - band - 22, 14, 10); }
    // arches above the band: alternating pink / blue panels with gold leaves, painted pilasters between
    const arcW = 2.6 * PX, top = 0.15 * PX, base = h - band - 34;
    for (let i = 0, cx = 0; cx < w + arcW; cx += arcW, i++) {
      const pink = i % 2 === 0; const r = arcW / 2 - 18;
      x.fillStyle = pink ? '#e8c9c2' : '#bcd0e6'; x.fillRect(cx, top, arcW, base - top);
      x.fillStyle = '#f6f3ec'; x.beginPath(); x.moveTo(cx + 18, base); x.lineTo(cx + 18, top + r + 40); x.arc(cx + arcW / 2, top + r + 40, r, Math.PI, 0); x.lineTo(cx + arcW - 18, base); x.closePath(); x.fill();
      x.strokeStyle = '#d9b45a'; x.lineWidth = 5; x.stroke();
      for (let k = 0; k < 26; k++) leaf(x, cx + 30 + rnd() * (arcW - 60), top + 60 + rnd() * (base - top - 90), 10 + rnd() * 16, PAL[Math.floor(rnd() * PAL.length)] + 'aa');
      // pilaster
      x.fillStyle = '#c23b3b'; x.fillRect(cx - 7, top + 50, 14, base - top - 50); x.fillStyle = '#d9b45a'; x.fillRect(cx - 12, top + 40, 24, 16); x.fillRect(cx - 12, base - 16, 24, 16);
    }
    x.fillStyle = '#4e73b0'; x.fillRect(0, 0, w, top); x.fillStyle = '#d9b45a'; x.fillRect(0, top, w, 5);
  });
}
function ceilingTexture() {
  return tex(1024, 1024, (x, w, h) => {
    x.fillStyle = '#f3efe4'; x.fillRect(0, 0, w, h);
    for (let k = 0; k < 160; k++) leaf(x, rnd() * w, rnd() * h, 14 + rnd() * 26, PAL[Math.floor(rnd() * PAL.length)] + '99');
    x.strokeStyle = '#8aa7c8'; x.lineWidth = 10; x.beginPath(); x.arc(w / 2, h / 2, 170, 0, 7); x.stroke();
    x.strokeStyle = '#d9b45a'; x.lineWidth = 4; x.beginPath(); x.arc(w / 2, h / 2, 150, 0, 7); x.stroke();
    for (let k = 0; k < 12; k++) { const a = k * Math.PI / 6; leaf(x, w / 2 + Math.cos(a) * 100, h / 2 + Math.sin(a) * 100, 40, '#c9a86acc'); }
  }, [1, 1]);
}
function floorTexture() {
  return tex(512, 512, (x, w, h) => { x.fillStyle = '#efe9dc'; x.fillRect(0, 0, w, h);
    for (let i = 0; i < 2; i++) for (let j = 0; j < 2; j++) { x.fillStyle = `rgb(${236 + rnd() * 10},${230 + rnd() * 10},${216 + rnd() * 10})`; x.fillRect(i * 256 + 2, j * 256 + 2, 252, 252); }
    x.strokeStyle = '#d9d2c3'; x.lineWidth = 3; x.strokeRect(0, 0, 256, 256); x.strokeRect(256, 0, 256, 256); x.strokeRect(0, 256, 256, 256); x.strokeRect(256, 256, 256, 256); }, [1, 1]);
}
function carpetTexture() { // runner: long axis along v, gold border
  return tex(256, 1024, (x, w, h) => { x.fillStyle = '#7a1f2b'; x.fillRect(0, 0, w, h);
    x.strokeStyle = '#d9b45a'; x.lineWidth = 10; x.strokeRect(14, 14, w - 28, h - 28); x.lineWidth = 3; x.strokeRect(34, 34, w - 68, h - 68);
    for (let cy = 60; cy < h; cy += 90) { x.fillStyle = '#d9b45a'; x.beginPath(); x.arc(24, cy, 6, 0, 7); x.fill(); x.beginPath(); x.arc(w - 24, cy, 6, 0, 7); x.fill(); } }, [1, 1]);
}
function iconTexture(i) {
  const robes = ['#8b1e2d', '#2f4f7f', '#5a3d2b', '#3f6b4f', '#7a2d6b'];
  return tex(256, 512, (x, w, h) => {
    const g = x.createLinearGradient(0, 0, 0, h); g.addColorStop(0, '#e2c06a'); g.addColorStop(1, '#c9a24a'); x.fillStyle = g; x.fillRect(0, 0, w, h);
    x.strokeStyle = '#8a6a2a'; x.lineWidth = 8; x.strokeRect(10, 10, w - 20, h - 20);
    x.fillStyle = '#f0d88a'; x.beginPath(); x.arc(w / 2, 150, 70, 0, 7); x.fill(); x.strokeStyle = '#b08a3a'; x.lineWidth = 5; x.stroke();
    x.fillStyle = robes[i % robes.length]; x.beginPath(); x.moveTo(40, h - 20); x.lineTo(60, 240); x.quadraticCurveTo(w / 2, 180, w - 60, 240); x.lineTo(w - 40, h - 20); x.closePath(); x.fill();
    x.fillStyle = '#e8c9a8'; x.beginPath(); x.arc(w / 2, 150, 42, 0, 7); x.fill();
    x.fillStyle = '#4a3326'; x.beginPath(); x.arc(w / 2, 120, 44, Math.PI, 0); x.fill();
    x.fillStyle = '#8a1e1e'; x.font = 'bold 22px serif'; x.textAlign = 'center'; x.fillText(i % 2 ? 'IC XC' : 'ΜΡ ΘΥ', w / 2, 60);
  });
}
const VERSES = [
  ['Ἐν ἀρχῇ ἦν ὁ Λόγος, καὶ ὁ Λόγος ἦν πρὸς τὸν Θεόν', 'Ин. 1:1'], ['בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָרֶץ', 'Быт. 1:1'],
  ['Въ нача́лѣ бѣ̀ сло́во, и҆ сло́во бѣ̀ къ бг҃ꙋ', 'Ин. 1:1'], ['Ἐγώ εἰμι ἡ ὁδὸς καὶ ἡ ἀλήθεια καὶ ἡ ζωή', 'Ин. 14:6'],
  ['שְׁמַע יִשְׂרָאֵל יְהוָה אֱלֹהֵינוּ יְהוָה אֶחָד', 'Втор. 6:4'], ['А҆́зъ є҆́смь свѣ́тъ мі́рꙋ', 'Ин. 8:12'],
  ['Μακάριοι οἱ καθαροὶ τῇ καρδίᾳ, ὅτι αὐτοὶ τὸν Θεὸν ὄψονται', 'Мф. 5:8'], ['יְהוָה רֹעִי לֹא אֶחְסָר', 'Пс. 22:1'],
  ['Бг҃ъ любы̀ є҆́сть', '1 Ин. 4:16'], ['Χριστὸς ἀνέστη ἐκ νεκρῶν, θανάτῳ θάνατον πατήσας', 'тропарь'],
];
function sceneTexture(i) {   // painted biblical scene on a truss casing: landscape, haloed figures, gilded verse band below
  const robes = ['#8b1e2d', '#2f4f7f', '#5a3d2b', '#3f6b4f', '#7a2d6b', '#b8742a'];
  return tex(1024, 320, (x, w, h) => {
    const sky = x.createLinearGradient(0, 0, 0, h * 0.7); sky.addColorStop(0, '#c9b36a'); sky.addColorStop(1, '#efe3bd'); x.fillStyle = sky; x.fillRect(0, 0, w, h);
    x.fillStyle = '#9fae7a'; x.beginPath(); x.moveTo(0, h * 0.62); for (let k = 0; k <= 8; k++) x.lineTo(w * k / 8, h * (0.5 + 0.12 * Math.sin(k * 1.7 + i))); x.lineTo(w, h * 0.72); x.lineTo(0, h * 0.72); x.closePath(); x.fill();
    x.fillStyle = '#b89a6a'; x.fillRect(0, h * 0.7, w, h * 0.1);
    const n = 3 + (i % 3); for (let k = 0; k < n; k++) { const cx = w * (k + 1) / (n + 1), base = h * 0.76, fh = h * 0.5;
      x.fillStyle = '#f0d88a'; x.beginPath(); x.arc(cx, base - fh + 22, 26, 0, 7); x.fill(); x.strokeStyle = '#b08a3a'; x.lineWidth = 3; x.stroke();
      x.fillStyle = robes[(i + k) % robes.length]; x.beginPath(); x.moveTo(cx - 22, base); x.lineTo(cx - 16, base - fh + 50); x.quadraticCurveTo(cx, base - fh + 30, cx + 16, base - fh + 50); x.lineTo(cx + 22, base); x.closePath(); x.fill();
      x.fillStyle = '#e8c9a8'; x.beginPath(); x.arc(cx, base - fh + 22, 15, 0, 7); x.fill(); }
    const band = x.createLinearGradient(0, h * 0.8, 0, h); band.addColorStop(0, '#e6c86a'); band.addColorStop(0.5, '#f6e2a0'); band.addColorStop(1, '#c9a24a'); x.fillStyle = band; x.fillRect(0, h * 0.8, w, h * 0.2);
    x.strokeStyle = '#8a6a2a'; x.lineWidth = 3; x.strokeRect(6, 6, w - 12, h - 12); x.beginPath(); x.moveTo(6, h * 0.8); x.lineTo(w - 6, h * 0.8); x.stroke();
    const [t, ref] = VERSES[i % VERSES.length]; x.fillStyle = '#5a3a0a'; x.textAlign = 'center'; x.textBaseline = 'middle';
    x.font = 'bold 34px "FreeSerif", "Times New Roman", serif'; x.fillText(t, w / 2, h * 0.9); x.font = '18px serif'; x.fillStyle = '#7a5a1a'; x.textAlign = 'right'; x.fillText(ref, w - 16, h * 0.86);
  });
}
function stainedGlassTexture() { // leaded glass: coloured cells with dark leading, warm palette
  return tex(512, 256, (x, w, h) => {
    const cols = ['#c8403a', '#2c6fb3', '#e0b43a', '#3d8a4f', '#8b3f9c', '#e07a2e', '#4bb0c9'];
    for (let i = 0; i < 12; i++) for (let j = 0; j < 6; j++) { x.fillStyle = cols[(i * 7 + j * 3) % cols.length]; x.fillRect(i * 43, j * 43, 43, 43); }
    x.strokeStyle = '#2a2320'; x.lineWidth = 5;
    for (let i = 0; i <= 12; i++) { x.beginPath(); x.moveTo(i * 43, 0); x.lineTo(i * 43, h); x.stroke(); }
    for (let j = 0; j <= 6; j++) { x.beginPath(); x.moveTo(0, j * 43); x.lineTo(w, j * 43); x.stroke(); }
    for (let k = 0; k < 10; k++) { x.beginPath(); x.arc(40 + k * 48, 128, 60, 0, 7); x.stroke(); }
    x.fillStyle = 'rgba(255,255,255,0.18)'; for (let k = 0; k < 40; k++) x.fillRect(rnd() * w, rnd() * h, 20, 8);
  }, [1, 1]);
}
function latticeTexture() {
  return tex(256, 512, (x, w, h) => { x.fillStyle = '#7a1f2b'; x.fillRect(0, 0, w, h); x.strokeStyle = '#d9b45a'; x.lineWidth = 6;
    for (let k = -h; k < w + h; k += 40) { x.beginPath(); x.moveTo(k, 0); x.lineTo(k + h, h); x.stroke(); x.beginPath(); x.moveTo(k + h, 0); x.lineTo(k, h); x.stroke(); } });
}

// ---------- furniture builders ----------
const WOOD = new THREE.MeshLambertMaterial({color: 0xcfa66c});
const WOOD2 = new THREE.MeshLambertMaterial({color: 0xb98c52});
const GOLD = new THREE.MeshStandardMaterial({color: 0xd4a843, metalness: 0.7, roughness: 0.35});
const RED = new THREE.MeshLambertMaterial({color: 0x7a1f2b});
const WHITE = new THREE.MeshLambertMaterial({color: 0xf2f1ec});
const DARK = new THREE.MeshLambertMaterial({color: 0x3b2a1e});
const BRASS = new THREE.MeshStandardMaterial({color: 0xc9a227, metalness: 0.8, roughness: 0.3});

function stasidion() { // wooden choir chair with high arched back, 0.62 wide
  const g = new THREE.Group();
  g.add(box(0.62, 0.05, 0.5, WOOD, 0, 0.47, 0));
  [-0.28, 0.28].forEach(dx => [-0.2, 0.2].forEach(dz => g.add(box(0.05, 0.47, 0.05, WOOD, dx, 0.235, dz))));
  const back = new THREE.Mesh(new THREE.ExtrudeGeometry((() => { const s = new THREE.Shape(); s.moveTo(-0.31, 0); s.lineTo(-0.31, 0.9); s.absarc(0, 0.9, 0.31, Math.PI, 0, true); s.lineTo(0.31, 0); s.closePath(); return s; })(), {depth: 0.04, bevelEnabled: false}), WOOD2);
  back.position.set(0, 0.45, -0.25); back.castShadow = true; g.add(back);
  g.add(box(0.05, 0.25, 0.45, WOOD, -0.3, 0.6, 0)); g.add(box(0.05, 0.25, 0.45, WOOD, 0.3, 0.6, 0));
  return g;
}
function lectern() { // analoy: sloped top with an icon, 0.5 × 0.5, 1.15 high
  const g = new THREE.Group();
  [-0.2, 0.2].forEach(dx => [-0.2, 0.2].forEach(dz => g.add(box(0.04, 0.95, 0.04, WOOD, dx, 0.475, dz))));
  g.add(box(0.5, 0.03, 0.5, WOOD, 0, 0.3, 0));
  const top = box(0.56, 0.05, 0.56, WOOD, 0, 1.0, 0); top.rotation.x = -0.45; g.add(top);
  const icon = new THREE.Mesh(new THREE.PlaneGeometry(0.4, 0.44), new THREE.MeshLambertMaterial({map: iconTexture(3)})); icon.position.set(0, 1.03, 0.02); icon.rotation.x = -0.45 - Math.PI / 2 + Math.PI / 2; icon.rotateX(-Math.PI / 2 + 0.0); g.add(icon);
  icon.rotation.set(-Math.PI / 2 - 0.45 + Math.PI / 2, 0, 0); icon.position.y = 1.04;
  return g;
}
function candleStand() { // round brass stand, 0.6 dia, 0.95 high
  const g = new THREE.Group();
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.3, 0.02, 10, 40), BRASS); ring.rotation.x = Math.PI / 2; ring.position.y = 0.95; g.add(ring);
  const top = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.03, 40), BRASS); top.position.y = 0.94; g.add(top);
  for (let k = 0; k < 3; k++) { const a = k * 2 * Math.PI / 3; const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.95, 8), BRASS); leg.position.set(Math.cos(a) * 0.25, 0.475, Math.sin(a) * 0.25); g.add(leg); }
  const lamp = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.03, 0.08, 12), new THREE.MeshLambertMaterial({color: 0xc0282f})); lamp.position.y = 1.0; g.add(lamp);
  return g;
}
function golgotha() { // tall wooden cross with gilded corpus on a stepped base, 2.4 high
  const g = new THREE.Group();
  g.add(box(0.7, 0.2, 0.5, WOOD2, 0, 0.1, 0)); g.add(box(0.45, 0.25, 0.35, WOOD2, 0, 0.32, 0));
  g.add(box(0.1, 2.0, 0.06, GOLD, 0, 1.45, 0)); g.add(box(0.9, 0.1, 0.06, GOLD, 0, 1.9, 0)); g.add(box(0.5, 0.08, 0.06, GOLD, 0, 2.25, 0)); const t = box(0.5, 0.08, 0.06, GOLD, 0, 1.0, 0); t.rotation.z = 0.3; g.add(t);
  return g;
}
function cabinet(w = 1.2) { const g = new THREE.Group(); g.add(box(w, 0.9, 0.45, WHITE, 0, 0.45, 0)); g.add(box(w - 0.1, 0.02, 0.4, new THREE.MeshLambertMaterial({color: 0xd9d4c8}), 0, 0.91, 0)); return g; }
function bench() { const g = new THREE.Group(); g.add(box(1.6, 0.04, 0.35, WOOD, 0, 0.45, 0)); [-0.7, 0.7].forEach(dx => g.add(box(0.05, 0.45, 0.3, WOOD, dx, 0.225, 0))); return g; }
function stool() { return box(0.5, 0.45, 0.5, DARK, 0, 0.225, 0); }

function iconostasis(width, gaps = []) { // full-width screen: panel base, icon row, cornice, royal doors + two deacon doors with curtains; `gaps` = [[from,to]] left open
  const g = new THREE.Group(); const H = 2.7;
  const inGap = (a, b) => gaps.some(([f, t]) => b > f + 0.02 && a < t - 0.02);
  // continuous members are split around the gaps
  let segs = [[0, width]]; gaps.forEach(([f, t]) => { const n = []; segs.forEach(([a, b]) => { if (t <= a || f >= b) n.push([a, b]); else { if (f > a) n.push([a, f]); if (t < b) n.push([t, b]); } }); segs = n; });
  segs.forEach(([a, b]) => { const w = b - a, c = (a + b) / 2; g.add(box(w, 0.95, 0.12, WOOD, c, 0.475, 0)); g.add(box(w, 0.12, 0.2, WOOD2, c, H - 0.06, 0)); g.add(box(w, 0.06, 0.16, WOOD2, c, 1.0, 0)); });
  const lat = new THREE.MeshLambertMaterial({map: latticeTexture()});
  const n = Math.max(6, Math.round(width / 1.0)); const pw = width / n;
  const mid = Math.floor(n / 2), d1 = Math.max(1, mid - 3), d2 = Math.min(n - 2, mid + 3);
  for (let i = 0; i < n; i++) {
    const cx = (i + 0.5) * pw;
    if (inGap(i * pw, (i + 1) * pw)) continue;
    if (i === mid || i === mid - 1) { // royal doors (two leaves) with curtain behind
      const leaf = box(pw * 0.95, 1.6, 0.06, lat, cx, 1.8, 0.02); g.add(leaf);
      g.add(box(pw, 1.65, 0.03, RED, cx, 1.85, -0.06));
      continue;
    }
    if (i === d1 || i === d2) { g.add(box(pw * 0.95, 1.6, 0.03, RED, cx, 1.8, 0)); g.add(box(pw * 0.95, 0.5, 0.05, WOOD, cx, 2.3, 0.01)); continue; } // deacon doors: curtains
    const icon = new THREE.Mesh(new THREE.PlaneGeometry(pw * 0.8, 1.45), new THREE.MeshLambertMaterial({map: iconTexture(i)})); icon.position.set(cx, 1.78, 0.07); g.add(icon);
    g.add(box(pw * 0.1, 1.6, 0.14, WOOD, cx - pw * 0.45, 1.8, 0)); g.add(box(pw * 0.1, 1.6, 0.14, WOOD, cx + pw * 0.45, 1.8, 0));
    g.add(box(pw * 0.8, 0.2, 0.1, WOOD2, cx, 0.6, 0.02));
  }
  // crosses on top
  [width / 2, width / 2 - 2.2, width / 2 + 2.2].forEach((cx, k) => { const s = k ? 0.25 : 0.4; g.add(box(0.04, s * 2, 0.04, GOLD, cx, H + s, 0)); g.add(box(s * 1.2, 0.04, 0.04, GOLD, cx, H + s * 1.2, 0)); });
  return g;
}

// ---------- assembly ----------
// T = {x0,x1,y0,y1 (hall rect, local m), sanctuary_depth, altar_side:'x1'|'x0', wall_h, topAt(y) (ceiling slope fn), columns:[[x,y]...]}
export function buildTemple(T) {
  const g = new THREE.Group(); g.name = 'temple';
  const {x0, x1, y0, y1, wall_h: H} = T; const Lx = x1 - x0, Ly = y1 - y0;
  const altarAtX1 = (T.altar_side || 'x1') === 'x1';
  const icX = altarAtX1 ? x1 - T.sanctuary_depth : x0 + T.sanctuary_depth;
  // floor
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(Lx, Ly), new THREE.MeshStandardMaterial({map: floorTexture(), roughness: 0.25, metalness: 0.05}));
  floor.material.map.repeat.set(Lx / 1.2, Ly / 1.2); floor.rotation.x = -Math.PI / 2; floor.position.set(x0 + Lx / 2, 0.012, -(y0 + Ly / 2)); floor.receiveShadow = true; g.add(floor);
  // painted walls: inner faces of the four walls (0.02 m inside), long walls up to the ceiling slope, end walls up to the gable line
  const wmLong = new THREE.MeshLambertMaterial({map: wallTexture(Lx, H)}), wmEnd = new THREE.MeshLambertMaterial({map: wallTexture(Ly, H)});
  const topLine = y => (T.topAt ? T.topAt(y - y0) + 0.08 : H);
  const Hend = Math.max(topLine(y0), topLine(y0 + Ly / 2), topLine(y1));
  const wmLongFull = new THREE.MeshLambertMaterial({map: wallTexture(Lx, topLine(y0))}), wmEndFull = new THREE.MeshLambertMaterial({map: wallTexture(Ly, Hend)});
  // long walls: painted from the floor to the roof line (constant height along the hall)
  const long = (y, flip) => { const h = topLine(y); const m = new THREE.Mesh(new THREE.PlaneGeometry(Lx, h), wmLongFull); m.position.set(x0 + Lx / 2, h / 2, -y); if (flip) m.rotation.y = Math.PI; m.receiveShadow = true; g.add(m); };
  long(y0 + 0.02, true); long(y1 - 0.02, false);
  // end walls: one painted shape from the floor up to the gable, so the cladding reads continuous with the wall
  const endShape = new THREE.Shape(); endShape.moveTo(0, 0); endShape.lineTo(Ly, 0); endShape.lineTo(Ly, topLine(y1));
  for (let k = 10; k >= 0; k--) { const yy = y0 + Ly * k / 10; endShape.lineTo(yy - y0, topLine(yy)); } endShape.closePath();
  wmEndFull.map.repeat.set(1 / Ly, 1 / Hend); wmEndFull.map.wrapS = wmEndFull.map.wrapT = THREE.ClampToEdgeWrapping;
  const end = (x, flip) => { const m = new THREE.Mesh(new THREE.ShapeGeometry(endShape), wmEndFull); m.rotation.y = flip ? -Math.PI / 2 : Math.PI / 2; m.position.set(x, 0, flip ? -y0 : -y1); m.receiveShadow = true; g.add(m); };
  end(x0 + 0.02, false); end(x1 - 0.02, true);
  const ceil = new THREE.Group(); ceil.name = 'roof'; g.add(ceil);   // toggled together with the building roof
  if (T.topAt) { // painted ceiling under the roof
    const top = y => T.topAt(y - y0) + 0.08;
    const cm = new THREE.MeshLambertMaterial({map: ceilingTexture(), side: THREE.DoubleSide}); cm.map.repeat.set(Lx / 6, Ly / 2 / 6);
    [[y0, y0 + Ly / 2], [y0 + Ly / 2, y1]].forEach(([ya, yb]) => {
      const za = top(ya), zb = top(yb); const len = Math.hypot(yb - ya, zb - za);
      const m = new THREE.Mesh(new THREE.PlaneGeometry(Lx, len), cm); m.position.set(x0 + Lx / 2, (za + zb) / 2, -(ya + yb) / 2);
      m.rotation.x = Math.PI / 2 + Math.atan2(zb - za, yb - ya); ceil.add(m);
    });
  }
  // columns and trusses: finish variants (T.finish): white | wood | wood_open | wood_glass | stucco | icons | icons_painted | ceiling
  const F = T.finish || 'white'; const chord = T.chord || H;
  const colH = y => (T.topAt ? T.topAt(y - y0) : H) + 0.1;
  const fluted = new THREE.MeshLambertMaterial({map: tex(256, 64, (x, w, h) => { x.fillStyle = '#efe9dc'; x.fillRect(0, 0, w, h); for (let i = 0; i < w; i += 32) { x.fillStyle = '#d8d0bf'; x.fillRect(i, 0, 8, h); x.fillStyle = '#f8f5ee'; x.fillRect(i + 8, 0, 6, h); } }, [6, 1])});
  const marble = new THREE.MeshStandardMaterial({color: 0xcfc6b8, roughness: 0.3, metalness: 0.05});
  // carved oak brackets (косынки) under the truss on both sides of the column, in the plane of the truss
  const CARVED = new THREE.MeshLambertMaterial({map: tex(256, 256, (c, w, h) => {
    c.fillStyle = '#b98c52'; c.fillRect(0, 0, w, h);
    for (let i = 0; i < 6; i++) { c.strokeStyle = i % 2 ? '#8a6238' : '#d8b074'; c.lineWidth = 7 - i % 2 * 3; c.beginPath();
      c.arc(w * 0.5 + (i % 2 ? 4 : 0), h * 0.5, 30 + i * 16, 0.3 + i * 0.4, 3.6 + i * 0.4); c.stroke(); }
    for (let k = 0; k < 10; k++) { const ax = (k * 97) % w, ay = (k * 61) % h; c.fillStyle = '#8a6238'; c.beginPath(); c.ellipse(ax, ay, 12, 5, k, 0, 7); c.fill(); c.fillStyle = '#d8b074'; c.beginPath(); c.ellipse(ax + 3, ay - 2, 7, 2.5, k, 0, 7); c.fill(); }
  }, [3, 3])});
  const bracket = (x, y, colW) => {   // 40 mm openwork (ажурные) brackets: ogee outline pierced with round and slot openings
    const top = chord - 0.12, hb = 0.75, lb = 0.6;
    [1, -1].forEach(sgn => {
      const sh = new THREE.Shape(); sh.moveTo(0, 0); sh.lineTo(lb, 0); sh.lineTo(lb, -0.06);
      sh.bezierCurveTo(lb * 0.7, -0.08, lb * 0.5, -hb * 0.15, lb * 0.42, -hb * 0.3);   // ogee: convex shoulder
      sh.bezierCurveTo(lb * 0.3, -hb * 0.55, lb * 0.12, -hb * 0.7, 0.07, -hb);          // then concave sweep to the column
      sh.lineTo(0, -hb); sh.closePath();
      [[0.09, -0.09, 0.045], [0.2, -0.07, 0.033], [0.31, -0.05, 0.022], [0.08, -0.22, 0.04], [0.17, -0.17, 0.028], [0.06, -0.36, 0.03], [0.055, -0.5, 0.024], [0.045, -0.62, 0.018]]
        .forEach(([hx, hy, r]) => { const hole = new THREE.Path(); hole.absellipse(hx, hy, r, r * 1.25, 0, Math.PI * 2, true); sh.holes.push(hole); });
      const geo = new THREE.ExtrudeGeometry(sh, {depth: 0.04, bevelEnabled: true, bevelThickness: 0.004, bevelSize: 0.004, bevelSegments: 1, curveSegments: 10});
      geo.rotateY(sgn * Math.PI / 2);   // shape X -> outward along the truss, extrusion along world x
      const m = new THREE.Mesh(geo, CARVED); m.position.set(x - sgn * 0.02, top, -y - sgn * colW / 2); m.castShadow = true; g.add(m);
    });
  };
  (T.columns || []).forEach(([x, y]) => {
    const h = colH(y);
    bracket(x, y, {wood:0.32, wood_open:0.32, wood_glass:0.32, icons:0.36, icons_painted:0.36, stucco:0.34, ceiling:0.34}[F] || 0.22);   // carved brackets in every finish, width = column width
    if (F === 'wood' || F === 'wood_open' || F === 'wood_glass') {            // oak casing with plinth and capital
      g.add(box(0.32, h, 0.32, WOOD2, x, h / 2, -y)); g.add(box(0.46, 0.3, 0.46, WOOD, x, 0.15, -y)); g.add(box(0.46, 0.18, 0.46, WOOD, x, h - 0.09, -y)); g.add(box(0.4, 0.04, 0.4, GOLD, x, h - 0.2, -y));
    } else if (F === 'icons' || F === 'icons_painted') {    // oak casing carrying icons on four sides, gilded cornice
      g.add(box(0.36, h, 0.36, WOOD2, x, h / 2, -y)); g.add(box(0.5, 0.25, 0.5, WOOD, x, 0.125, -y)); g.add(box(0.5, 0.12, 0.5, GOLD, x, 2.55, -y));
      [[0, 0.185, 0], [0, -0.185, Math.PI], [0.185, 0, Math.PI / 2], [-0.185, 0, -Math.PI / 2]].forEach(([dx, dz, ry], k) => { const ic = new THREE.Mesh(new THREE.PlaneGeometry(0.26, 0.5), new THREE.MeshLambertMaterial({map: iconTexture(k + 5)})); ic.position.set(x + dx, 1.9, -y - dz); ic.rotation.y = ry; g.add(ic); });
    } else if (F === 'stucco' || F === 'ceiling') {   // fluted plaster column, marble base, gilded capital
      const c = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, h, 24), fluted); c.position.set(x, h / 2, -y); c.castShadow = true; g.add(c);
      const b = new THREE.Mesh(new THREE.CylinderGeometry(0.27, 0.3, 0.25, 24), marble); b.position.set(x, 0.125, -y); g.add(b);
      const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.17, 0.3, 24), GOLD); cap.position.set(x, h - 0.15 - (F === 'ceiling' ? h - chord : 0), -y); g.add(cap);
    } else {                        // as built: white painted steel tube
      const c = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, h, 20), WHITE); c.position.set(x, h / 2, -y); c.castShadow = true; g.add(c);
    }
  });
  // trusses: positions along the hall at the truss pitch (building grid), bottom chord at `chord`
  const trussX = []; if (T.truss_pitch) { for (let x = 0; x <= x1 + 0.01; x += T.truss_pitch) if (x >= x0 - 0.05 && x <= x1 + 0.05) trussX.push(x); }
  if (T.trussMat) T.trussMat.color.set(F === 'stucco' ? '#e8dcc0' : (F === 'wood' || F === 'wood_open' || F === 'wood_glass' || F === 'icons_painted') ? '#eee8dc' : '#f2f1ec');
  if (F === 'wood_open' || F === 'wood_glass') {   // cladding follows the members exactly (same geometry as the steel truss): oak boxes around chords, verticals and diagonals
    const topY = y => (T.topAt ? T.topAt(y - y0) : chord + 0.3);           // = top chord axis of the building truss
    const L = (x, y, h) => new THREE.Vector3(x, h, -y);
    const mem = (p, q, sz = 0.2) => { const a = L(...p), b = L(...q); const len = a.distanceTo(b) + sz * 0.6; const m = new THREE.Mesh(new THREE.BoxGeometry(sz, sz, len), WOOD2); m.position.copy(a.clone().lerp(b, 0.5)); m.lookAt(b); m.castShadow = true; g.add(m); return m; };
    const glassMat = F === 'wood_glass' ? new THREE.MeshBasicMaterial({map: stainedGlassTexture(), transparent: true, opacity: 0.92, side: THREE.DoubleSide}) : null;
    const panels = 6;
    trussX.forEach(x => {
      mem([x, y0, chord], [x, y1, chord], 0.28); g.add(box(0.34, 0.05, Ly, GOLD, x, chord - 0.165, -(y0 + Ly / 2)));
      mem([x, y0, topY(y0)], [x, y0 + Ly / 2, topY(y0 + Ly / 2)], 0.24); mem([x, y0 + Ly / 2, topY(y0 + Ly / 2)], [x, y1, topY(y1)], 0.24);
      for (let k = 0; k <= panels; k++) { const y = y0 + Ly * k / panels; if (topY(y) - chord > 0.2) mem([x, y, chord], [x, y, topY(y)], 0.18);
        if (k < panels) { const y2 = y0 + Ly * (k + 1) / panels; k % 2 === 0 ? mem([x, y, chord], [x, y2, topY(y2)], 0.16) : mem([x, y, topY(y)], [x, y2, chord], 0.16);
          if (glassMat && Math.min(topY(y), topY(y2)) - chord > 0.3) {   // stained glass filling the panel (quad between chords), lit from behind by the ceiling lights
            const sh = new THREE.Shape(); sh.moveTo(y - y0, chord + 0.1); sh.lineTo(y2 - y0, chord + 0.1); sh.lineTo(y2 - y0, topY(y2) - 0.08); sh.lineTo(y - y0, topY(y) - 0.08); sh.closePath();
            const gm = new THREE.Mesh(new THREE.ShapeGeometry(sh), glassMat); gm.rotation.y = Math.PI / 2; gm.position.set(x, 0, -y0); g.add(gm);
            const gl = new THREE.PointLight(0xffe9c4, 3, 6, 1.5); gl.position.set(x, chord + 0.6, -(y + y2) / 2); g.add(gl);
          } } }
    });
  }
  if (F === 'wood' || F === 'stucco' || F === 'icons_painted') {   // full truss casing: a solid profile from the bottom chord up to the roof, 0.3 m thick, gilded moulding along the bottom edge
    const topY = y => (T.topAt ? T.topAt(y - y0) : chord + 0.3) - 0.02;
    trussX.forEach(x => {
      const sh = new THREE.Shape(); sh.moveTo(y0, chord - 0.12); sh.lineTo(y1, chord - 0.12); sh.lineTo(y1, topY(y1));
      for (let k = 10; k >= 0; k--) { const y = y0 + (y1 - y0) * k / 10; sh.lineTo(y, topY(y)); } sh.closePath();
      const geo = new THREE.ExtrudeGeometry(sh, {depth: 0.3, bevelEnabled: false}); geo.rotateY(Math.PI / 2);   // shape (y->X, z->Y) extruded along -Z... -> after rotation: extrude along +X, shape y along -Z
      const m = new THREE.Mesh(geo, F !== 'stucco' ? WOOD2 : new THREE.MeshLambertMaterial({color: 0xe8dcc0})); m.position.set(x - 0.15, 0, 0); m.castShadow = true; g.add(m);
      g.add(box(0.36, 0.06, Ly, GOLD, x, chord - 0.13, -(y0 + Ly / 2)));
      g.add(box(0.34, 0.1, Ly, F !== 'stucco' ? WOOD : new THREE.MeshLambertMaterial({color: 0xd8ccae}), x, chord - 0.05, -(y0 + Ly / 2)));
      // carved panels: on both faces, one recessed panel per bay between column lines, framed by gilded strips
      const lines = [y0, ...(T.columns || []).map(c => c[1]).filter((v, i, a) => a.indexOf(v) === i).sort((p, q) => p - q), y1];
      const panelMat = F === 'wood' ? WOOD : new THREE.MeshLambertMaterial({color: 0xf0e6cf});
      for (let i = 0; i < lines.length - 1; i++) {
        const painted = F === 'icons_painted' ? new THREE.MeshBasicMaterial({map: sceneTexture(trussX.indexOf(x) * 3 + i)}) : null;   // painted scene with gilded verse band
        const a = lines[i] + 0.25, b = lines[i + 1] - 0.25; if (b - a < 0.8) continue;
        const ya = a, yb = b, hA = topY(a) - chord, hB = topY(b) - chord; const hMin = Math.min(hA, hB) - 0.14;
        if (hMin < 0.25) continue;
        [x - 0.16, x + 0.16].forEach(fx => {
          g.add(box(0.02, hMin, b - a, painted || panelMat, fx, chord + 0.07 + hMin / 2, -(a + b) / 2));           // lighter field / painted scene
          g.add(box(0.03, 0.04, b - a, GOLD, fx, chord + 0.07, -(a + b) / 2)); g.add(box(0.03, 0.04, b - a, GOLD, fx, chord + 0.07 + hMin, -(a + b) / 2));
          g.add(box(0.03, hMin, 0.04, GOLD, fx, chord + 0.07 + hMin / 2, -a)); g.add(box(0.03, hMin, 0.04, GOLD, fx, chord + 0.07 + hMin / 2, -b));
          if (!painted) { const ros = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.03, 16), GOLD); ros.rotation.z = Math.PI / 2; ros.position.set(fx, chord + 0.07 + hMin / 2, -(a + b) / 2); g.add(ros); }
        });
      }
    });
  }
  if (F === 'ceiling') {                                                                                                // suspended painted ceiling below the trusses
    const cm = new THREE.MeshLambertMaterial({map: tex(1024, 1024, (x, w, h) => { x.fillStyle = '#f3efe4'; x.fillRect(0, 0, w, h); x.strokeStyle = '#d9b45a'; x.lineWidth = 14; x.strokeRect(40, 40, w - 80, h - 80); x.strokeStyle = '#8aa7c8'; x.lineWidth = 6; x.strokeRect(80, 80, w - 160, h - 160); for (let k = 0; k < 60; k++) leaf(x, 120 + rnd() * (w - 240), 120 + rnd() * (h - 240), 16 + rnd() * 24, PAL[Math.floor(rnd() * PAL.length)] + 'aa'); x.strokeStyle = '#d9b45a'; x.lineWidth = 8; x.beginPath(); x.arc(w / 2, h / 2, 170, 0, 7); x.stroke(); }, [Lx / 3.1, Ly / 3.1]), side: THREE.DoubleSide});
    const m = new THREE.Mesh(new THREE.PlaneGeometry(Lx, Ly), cm); m.rotation.x = Math.PI / 2; m.position.set(x0 + Lx / 2, chord - 0.06, -(y0 + Ly / 2)); g.add(m);
    for (let x = x0 + 3.1; x < x1 - 0.1; x += 3.1) g.add(box(0.12, 0.12, Ly, GOLD, x, chord - 0.1, -(y0 + Ly / 2)));    // gilded coffer ribs
  }
  // furniture layout is built in a (u, v) frame with the altar at u = U1 and then mapped onto the hall:
  //   altar on an x-wall: u = x, v = y (no rotation); altar on a y-wall: u runs across the hall (y), v along it (x)
  const side = T.altar_side || 'x1';
  const onY = side === 'y0' || side === 'y1';
  const U0 = onY ? -y1 : x0, U1 = onY ? -y0 : x1, V0 = onY ? x0 : y0, V1 = onY ? x1 : y1;
  const altarAtU1 = onY ? side === 'y0' : side === 'x1';
  const fg = new THREE.Group(); g.add(fg);
  if (onY) fg.rotation.y = -Math.PI / 2;   // (u, h, -v) -> (v, h, u): with u = -y this gives x = v, z = -y
  const place = (obj, u, v, ry = 0) => { obj.position.set(u, 0, -v); obj.rotation.y = ry; fg.add(obj); return obj; };
  const Lu = U1 - U0, Lv = V1 - V0;
  const icU = altarAtU1 ? U1 - T.sanctuary_depth : U0 + T.sanctuary_depth;
  const dir = altarAtU1 ? -1 : 1; // towards the nave along u
  const cv = V0 + Lv / 2;
  // iconostasis along the full v-width of the sanctuary wall, facing the nave; broken at wall openings; solea carpet and step in front
  const gapsV = (T.openings || []).map(([f, t]) => altarAtU1 ? [f - V0, t - V0] : [V1 - t, V1 - f]);
  const ic = iconostasis(Lv, gapsV); place(ic, icU, altarAtU1 ? V1 : V0, altarAtU1 ? -Math.PI / 2 : Math.PI / 2);
  const carpet = new THREE.Mesh(new THREE.PlaneGeometry(1.6, Lv - 0.4), new THREE.MeshLambertMaterial({map: carpetTexture()})); carpet.material.map.repeat.set(1, (Lv - 0.4) / 2.5);
  carpet.rotation.x = -Math.PI / 2; carpet.position.set(icU + dir * 0.95, 0.12, -cv); carpet.receiveShadow = true; fg.add(carpet);
  fg.add(box(1.0, 0.1, Lv - 0.4, WOOD2, icU + dir * 0.6, 0.05, -cv));
  fg.add(box(1.0, 1.0, 1.0, RED, icU - dir * T.sanctuary_depth / 2, 0.5, -cv));
  // stasidia along the wall opposite the iconostasis (full length, stools between groups of four) and around the corners onto the end walls
  const farU = altarAtU1 ? U0 + 0.35 : U1 - 0.35, farRy = altarAtU1 ? Math.PI / 2 : -Math.PI / 2;
  { let v = V0 + 0.5, k = 0; while (v + 0.35 < V1 - 0.5) { if (k % 5 === 4) { place(stool(), farU, v); v += 0.75; k++; continue; } place(stasidion(), farU, v, farRy); v += 0.7; k++; } }
  const endRun = altarAtU1 ? [U0 + 1.2, U0 + 3.6] : [U1 - 3.6, U1 - 1.2];
  [[V0 + 0.35, 0], [V1 - 0.35, Math.PI]].forEach(([v, ry]) => { for (let u = endRun[0]; u < endRun[1]; u += 0.7) place(stasidion(), u, v, ry); });
  // end walls, nave part: white cabinets with a bench between, exit to the corridor is next to the iconostasis end; Golgotha cross by the cabinet on one side
  const nearU = altarAtU1 ? icU - 2.0 : icU + 2.0;   // just outside the solea
  [[V0 + 0.3, Math.PI / 2], [V1 - 0.3, -Math.PI / 2]].forEach(([v, ry], k) => {
    place(cabinet(1.2), altarAtU1 ? U0 + 4.6 : U1 - 4.6, v, ry); place(cabinet(1.2), altarAtU1 ? U0 + 6.4 : U1 - 6.4, v, ry);
    place(bench(), altarAtU1 ? U0 + 5.5 : U1 - 5.5, v + (k ? -0.15 : 0.15), 0);
  });
  place(golgotha(), nearU - dir * 1.2, V0 + 0.9, altarAtU1 ? Math.PI / 2 : -Math.PI / 2);
  // lecterns (analoy) and candle stands in the nave in front of the solea
  [[icU + dir * 3.0, cv - 2.5], [icU + dir * 3.0, cv + 2.5], [icU + dir * 5.0, cv]].forEach(([u, v]) => place(lectern(), u, v, altarAtU1 ? Math.PI / 2 : -Math.PI / 2));
  // candle stands at the solea edge, 1.5 m from the iconostasis: clear of the column row that stands 2.25 m from it
  [[icU + dir * 1.5, cv - 1.0], [icU + dir * 1.5, cv + 1.0], [icU + dir * 4.0, V0 + 2.6]].forEach(([u, v]) => place(candleStand(), u, v));
  // interior lighting (no shadows) so the painted room reads under the roof
  for (let i = 1; i <= 3; i++) { const p = new THREE.PointLight(0xfff2dc, 14, 14, 1.4); p.position.set(x0 + Lx * i / 4, 2.9, -(y0 + Ly / 2)); g.add(p); }
  g.userData = {id: 'Храм', name: 'Храм (оси 12–17): иконостас, солея, стасидии, аналои, подсвечники, Голгофа', note: 'Мебель и роспись восстановлены по фотосъёмке; размеры мебели типовые, расстановка — по фото'};
  g.traverse(o => { if (o.isMesh) o.userData = g.userData; });
  return g;
}
