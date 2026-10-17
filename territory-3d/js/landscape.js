// Озеленение у мечети: клумба-орнамент (каменный бортик по контуру розетки, рисунок орнамента цветами) и цветущие кусты.
import * as THREE from 'three';

const STONE = new THREE.MeshStandardMaterial({color: 0x9a948a, roughness: 0.95, metalness: 0.02});
const SOIL = new THREE.MeshLambertMaterial({color: 0x4a3a2a});
const LEAF = new THREE.MeshLambertMaterial({color: 0x3f7a3a});
const LEAF2 = new THREE.MeshLambertMaterial({color: 0x5a9a4a});

function stoneTexture() {   // сухая кладка: неровные камни с тёмными швами
  const c = document.createElement('canvas'); c.width = 512; c.height = 128; const x = c.getContext('2d');
  x.fillStyle = '#6f6a62'; x.fillRect(0, 0, 512, 128);
  let seed = 7; const rnd = () => (seed = (seed * 9301 + 49297) % 233280) / 233280;
  for (let row = 0; row < 3; row++) for (let px = -20; px < 512; px += 40 + rnd() * 30) {
    const w = 36 + rnd() * 30, h = 30 + rnd() * 10, g = 150 + rnd() * 60;
    x.fillStyle = `rgb(${g},${g - 6},${g - 14})`; x.beginPath(); x.ellipse(px + w / 2, row * 42 + 22, w / 2, h / 2, 0, 0, 7); x.fill();
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; return t;
}

export function buildLandscape(data, loadTexture) {
  const g = new THREE.Group(); g.name = 'landscape';
  const stoneMat = new THREE.MeshStandardMaterial({map: stoneTexture(), roughness: 0.95, metalness: 0.02});
  (data.flowerbeds || []).forEach(fb => {
    const R = fb.radius_m, [cx, cy] = fb.center, rot = THREE.MathUtils.degToRad(fb.rotation_deg || 0);
    const pts = fb.outline.map(([u, v]) => new THREE.Vector2(u * R, v * R));
    // бортик: кольцо между контуром и контуром, стянутым к центру на ширину бортика
    const kw = fb.kerb.w, inner = fb.outline.map(([u, v]) => { const l = Math.hypot(u, v) || 1; const s = Math.max(0.05, (l * R - kw) / (l * R)); return new THREE.Vector2(u * R * s, v * R * s); });
    const ring = new THREE.Shape(pts); const hole = new THREE.Path(inner.slice().reverse()); ring.holes.push(hole);
    const kerb = new THREE.Mesh(new THREE.ExtrudeGeometry(ring, {depth: fb.kerb.h, bevelEnabled: true, bevelThickness: 0.02, bevelSize: 0.02, bevelSegments: 1}), stoneMat);
    stoneMat.map.repeat.set(1 / 2.5, 1 / 0.6);
    // заполнение: рисунок орнамента — текстура по координатам контура (u,v ∈ −1..1 ↔ центр текстуры ± tex_half_px)
    const tex = loadTexture(fb.texture); tex.colorSpace = THREE.SRGBColorSpace; tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping;
    const k = fb.tex_half_px / fb.tex_px; tex.repeat.set(k / R, k / R); tex.offset.set(0.5, 0.5); tex.center.set(0, 0);
    const fillShape = new THREE.Shape(inner);
    const fill = new THREE.Mesh(new THREE.ExtrudeGeometry(fillShape, {depth: fb.fill_h, bevelEnabled: false}), [new THREE.MeshLambertMaterial({map: tex, transparent: true}), SOIL]);
    // цветы: мелкие полусферы над бордовым рисунком читаются как кустики цветов — упрощённо: лёгкий рельеф из точек по кольцу
    [kerb, fill].forEach(m => { m.rotation.x = -Math.PI / 2; m.rotation.z = rot; m.position.set(cx, 0.01, -cy); m.castShadow = m.receiveShadow = true; m.userData = {id: fb.id, name: fb.name, note: fb.planting}; g.add(m); });
    // подушки цветов: кольцо низких полусфер по внутреннему краю бортика
    const petal = new THREE.SphereGeometry(0.11, 10, 8); const flowerMat = new THREE.MeshLambertMaterial({color: 0xeae4d8});
    for (let i = 0; i < inner.length; i += 2) { const p = inner[i]; const m = new THREE.Mesh(petal, flowerMat); m.position.set(cx + p.x * 0.94, fb.fill_h + 0.06, -(cy + p.y * 0.94)); m.scale.set(1, 0.6, 1); g.add(m); }
  });
  // кусты: три кроны и цветы-точки
  const crown = new THREE.SphereGeometry(1, 12, 10), dot = new THREE.SphereGeometry(0.06, 6, 5);
  (data.bushes || []).forEach(b => {
    const [x, y] = b.pos, r = b.r, h = b.h; const fm = new THREE.MeshLambertMaterial({color: b.flower});
    [[0, 0, 0, 1], [0.45, 0.1, 0.2, 0.7], [-0.4, 0.05, -0.25, 0.65], [0.1, 0.35, -0.3, 0.6]].forEach(([dx, dy, dz, s], i) => {
      const m = new THREE.Mesh(crown, i % 2 ? LEAF2 : LEAF); m.scale.set(r * s, h * 0.55 * s, r * s); m.position.set(x + dx * r, h * 0.5 + dy * h, -(y + dz * r)); m.castShadow = true; m.userData = {id: 'куст', name: b.kind}; g.add(m);
    });
    let seed = Math.round(x * 13 + y * 7); const rnd = () => (seed = (seed * 9301 + 49297) % 233280) / 233280;
    for (let i = 0; i < 26; i++) { const a = rnd() * Math.PI * 2, t = Math.acos(1 - rnd()); const d = new THREE.Mesh(dot, fm);
      d.position.set(x + Math.sin(t) * Math.cos(a) * r * 1.02, h * 0.5 + Math.cos(t) * h * 0.56, -(y + Math.sin(t) * Math.sin(a) * r * 1.02)); g.add(d); }
  });
  return g;
}
