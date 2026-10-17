// Detailed building renderer: walls with openings, windows, doors, furniture, roof (flat+parapet or gable with trusses).
// Input: building JSON (local metres, origin at the SW corner, X along the length) and the site footprint polygon to place it on.
import * as THREE from 'three';
import { buildTemple } from './temple.js';

const MAT = {
  wall: new THREE.MeshLambertMaterial({color: 0xe8e4d8}),
  wallIn: new THREE.MeshLambertMaterial({color: 0xf3f1ea}),
  parapet: new THREE.MeshLambertMaterial({color: 0x9aa0a6}),
  roof: new THREE.MeshStandardMaterial({color: 0x6e7378, metalness: 0.4, roughness: 0.6, side: THREE.DoubleSide}),
  glass: new THREE.MeshPhysicalMaterial({color: 0x9ccbe8, transparent: true, opacity: 0.45, roughness: 0.1, metalness: 0.1, side: THREE.DoubleSide}),
  frame: new THREE.MeshLambertMaterial({color: 0xffffff}),
  door: new THREE.MeshLambertMaterial({color: 0x8c6b4a}),
  doorAl: new THREE.MeshLambertMaterial({color: 0x5b6670}),
  furn: new THREE.MeshLambertMaterial({color: 0xb8a98c}),
  chair: new THREE.MeshLambertMaterial({color: 0x6f7f8f}),
  steel: new THREE.MeshStandardMaterial({color: 0x4a5560, metalness: 0.7, roughness: 0.4}),
  slab: new THREE.MeshLambertMaterial({color: 0xcfcac0}),
  porch: new THREE.MeshLambertMaterial({color: 0xbdb7ad}),
};

function box(w, h, d, mat, x, y, z) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; return m;
}
// local (x, y) plan metres -> group space: X = x, Z = -y (north up); Y = height
const L = (x, y, h = 0) => new THREE.Vector3(x, h, -y);

function wallAxis(r) { const w = r[2] - r[0], d = r[3] - r[1]; return w >= d ? 'x' : 'y'; }

function buildWall(g, r, H, openings, material) {
  const axis = wallAxis(r);
  const wm = material === 'glass' ? MAT.glass : MAT.wall;
  const t = axis === 'x' ? r[3] - r[1] : r[2] - r[0];
  const a0 = axis === 'x' ? r[0] : r[1], a1 = axis === 'x' ? r[2] : r[3];
  const c = axis === 'x' ? (r[1] + r[3]) / 2 : (r[0] + r[2]) / 2;
  const piece = (from, to, z0, z1) => {
    if (to - from < 0.005 || z1 - z0 < 0.005) return;
    const len = to - from, mid = (from + to) / 2, h = z1 - z0;
    const m = axis === 'x' ? box(len, h, t, wm, mid, z0 + h / 2, -c) : box(t, h, len, wm, c, z0 + h / 2, -mid);
    if (material === 'glass') m.castShadow = false;
    g.add(m);
  };
  const ops = openings.filter(o => o.to > a0 + 0.01 && o.from < a1 - 0.01).sort((p, q) => p.from - q.from);
  let cur = a0;
  for (const o of ops) {
    const f = Math.max(o.from, a0), tt = Math.min(o.to, a1);
    if (f > cur) piece(cur, f, 0, H);
    if (o.z0 > 0) piece(f, tt, 0, o.z0);
    if (o.z1 < H) piece(f, tt, o.z1, H);
    cur = Math.max(cur, tt);
  }
  if (cur < a1) piece(cur, a1, 0, H);
  return {axis, t, c};
}

export function buildDetailedBuilding(abk, footprint, opts = {}) {
  const g = new THREE.Group();
  const H = abk.levels.wall_h;
  const walls = abk.walls;
  if (abk.colors && abk.colors.wall) MAT.wall = new THREE.MeshLambertMaterial({color: new THREE.Color(abk.colors.wall)}); else MAT.wall = new THREE.MeshLambertMaterial({color: 0xe8e4d8});
  const bandMat = abk.colors && abk.colors.band ? new THREE.MeshLambertMaterial({color: new THREE.Color(abk.colors.band)}) : MAT.parapet;
  const byWall = new Map();
  const addOp = (i, op) => { if (!byWall.has(i)) byWall.set(i, []); byWall.get(i).push(op); };
  (abk.windows || []).forEach(w => addOp(w.wall, {from: w.from, to: w.to, z0: w.sill, z1: w.head}));
  (abk.doors || []).forEach(d => addOp(d.wall, {from: d.from, to: d.to, z0: 0, z1: d.height}));
  const info = walls.map((w, i) => buildWall(g, w.rect, H, byWall.get(i) || [], w.material));
  const roofG = new THREE.Group(); roofG.name = 'roof'; g.add(roofG);
  const trussG = new THREE.Group(); trussG.name = 'trusses'; g.add(trussG);

  // windows: glass pane + frame
  (abk.windows || []).forEach(w => {
    const wi = info[w.wall]; if (!wi) return;
    const len = w.to - w.from, mid = (w.from + w.to) / 2, h = w.head - w.sill, zc = (w.sill + w.head) / 2;
    const glass = wi.axis === 'x' ? box(len - 0.08, h - 0.08, 0.02, MAT.glass, mid, zc, -wi.c) : box(0.02, h - 0.08, len - 0.08, MAT.glass, wi.c, zc, -mid);
    glass.castShadow = false; g.add(glass);
    const fr = wi.axis === 'x' ? box(len, h, 0.06, MAT.frame, mid, zc, -wi.c) : box(0.06, h, len, MAT.frame, wi.c, zc, -mid);
    g.add(fr);
    // hollow the frame look by adding an inner dark outline (edges)
    fr.add(new THREE.LineSegments(new THREE.EdgesGeometry(fr.geometry), new THREE.LineBasicMaterial({color: 0x667})));
  });
  // doors: leaf in the opening, shown ajar
  (abk.doors || []).forEach(d => {
    const wi = info[d.wall]; if (!wi || d.opening) return;
    const len = d.to - d.from, h = d.height; const mat = len > 1.2 ? MAT.doorAl : MAT.door;
    const leaf = new THREE.Mesh(new THREE.BoxGeometry(len * 0.98, h - 0.02, 0.045), mat);
    leaf.geometry.translate(len * 0.49, 0, 0); // hinge at local origin
    leaf.castShadow = true;
    const hx = d.hinge ? d.hinge[0] : (wi.axis === 'x' ? d.from : wi.c), hy = d.hinge ? d.hinge[1] : (wi.axis === 'x' ? wi.c : d.from);
    leaf.position.copy(L(hx, hy, h / 2));
    // direction along the wall from the hinge, opened 25° into the swing side
    let ang = wi.axis === 'x' ? (d.hinge && d.hinge[0] > (d.from + d.to) / 2 ? Math.PI : 0) : (d.hinge && d.hinge[1] > (d.from + d.to) / 2 ? Math.PI / 2 : -Math.PI / 2);
    if (wi.axis === 'y') ang = (d.hinge && d.hinge[1] > (d.from + d.to) / 2) ? Math.PI / 2 : -Math.PI / 2;
    let sw = 0.45;
    if (d.swing_to) { const sx = d.swing_to[0] - hx, sy = d.swing_to[1] - hy; const target = Math.atan2(-sy, sx); // in XZ plane (z=-y)
      // rotate from wall direction towards the swing direction by 25°
      const wallDir = ang; let delta = target - wallDir; while (delta > Math.PI) delta -= 2 * Math.PI; while (delta < -Math.PI) delta += 2 * Math.PI; sw = Math.sign(delta) * 0.45; }
    leaf.rotation.y = -(ang) + (-sw);
    leaf.rotation.y = -ang - sw;
    g.add(leaf);
  });
  // furniture
  (abk.furniture || []).forEach(f => {
    const r = f.rect; const w = r[2] - r[0], d = r[3] - r[1];
    let fm = f.color ? new THREE.MeshLambertMaterial({color: new THREE.Color(f.color)}) : (f.h < 0.6 ? MAT.chair : MAT.furn);
    if (f.tex === 'green_carpet') {
      const c = document.createElement('canvas'); c.width = 1024; c.height = 1024; const x = c.getContext('2d');
      x.fillStyle = '#1f6b3a'; x.fillRect(0, 0, 1024, 1024);
      x.strokeStyle = '#d4a843'; x.lineWidth = 18; x.strokeRect(24, 24, 976, 976); x.lineWidth = 5; x.strokeRect(54, 54, 916, 916);
      const rows = Math.round(w / 1.2), cols = Math.round(d / 1.0);
      for (let i = 0; i < rows; i++) for (let j = 0; j < cols; j++) { const cx = 70 + (i + 0.5) * (884 / rows), cy = 70 + (j + 0.5) * (884 / cols), rw = 884 / rows * 0.36, rh = 884 / cols * 0.4;
        x.strokeStyle = '#c9b25a'; x.lineWidth = 4; x.beginPath(); x.moveTo(cx - rw, cy + rh); x.lineTo(cx - rw, cy - rh * 0.3); x.quadraticCurveTo(cx - rw, cy - rh, cx, cy - rh); x.quadraticCurveTo(cx + rw, cy - rh, cx + rw, cy - rh * 0.3); x.lineTo(cx + rw, cy + rh); x.stroke();
        x.fillStyle = '#2a7d47'; x.fillRect(cx - rw + 6, cy - rh * 0.3, rw * 2 - 12, rh * 1.3 - 6); }
      const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
      fm = new THREE.MeshLambertMaterial({map: t});
    }
    g.add(box(w, f.h, d, fm, (r[0] + r[2]) / 2, f.h / 2, -(r[1] + r[3]) / 2));
  });
  // floor slab
  const [Lx, Ly] = abk.size_m;
  g.add(box(Lx + 0.2, 0.15, Ly + 0.2, MAT.slab, Lx / 2, -0.075, -Ly / 2));
  // porches
  (abk.porches || []).forEach(p => {
    const r = p.rect; g.add(box(r[2] - r[0], 0.12, r[3] - r[1], MAT.porch, (r[0] + r[2]) / 2, -0.06, -(r[1] + r[3]) / 2));
    if (p.canopy) { const ch = p.canopy_h || 2.4; g.add(box(r[2] - r[0] + 0.3, 0.08, r[3] - r[1] + 0.2, MAT.roof, (r[0] + r[2]) / 2, ch, -(r[1] + r[3]) / 2));
      if (p.posts) p.posts.forEach(([x, y]) => g.add(box(0.1, ch, 0.1, MAT.steel, x, ch / 2, -y)));
      else { const px = [r[0] + 0.1, r[2] - 0.1], py = p.canopy_posts_y !== undefined ? p.canopy_posts_y : r[1] + 0.1; px.forEach(x => g.add(box(0.08, ch, 0.08, MAT.steel, x, ch / 2, -py))); } }
  });
  // roof
  const roof = abk.roof || {type: 'flat_parapet', parapet_top: H + 1.2};
  if (roof.type === 'flat_parapet') {
    const top = roof.parapet_top;
    roofG.add(box(Lx, 0.2, Ly, MAT.roof, Lx / 2, H + 0.1, -Ly / 2));
    const pt = abk.wall_thickness_m || 0.11, ph = top - H;
    roofG.add(box(Lx, ph, pt, MAT.parapet, Lx / 2, H + ph / 2, -pt / 2));
    roofG.add(box(Lx, ph, pt, MAT.parapet, Lx / 2, H + ph / 2, -(Ly - pt / 2)));
    roofG.add(box(pt, ph, Ly, MAT.parapet, pt / 2, H + ph / 2, -Ly / 2));
    roofG.add(box(pt, ph, Ly, MAT.parapet, Lx - pt / 2, H + ph / 2, -Ly / 2));
  } else if (roof.type === 'gable') {
    const eave = roof.eave, ridge = roof.ridge, ov = roof.overhang || 0.3, chord = roof.bottom_chord || H;
    const half = Ly / 2, slopeLen = Math.hypot(half + ov, ridge - eave);
    const ang = Math.atan2(ridge - eave, half + ov);
    [[-1, half], [1, half]].forEach(([s, _]) => {
      const sheet = new THREE.Mesh(new THREE.BoxGeometry(Lx + 2 * ov, 0.06, slopeLen), MAT.roof);
      // centre of each slope
      const cz = -(half + s * (half + ov) / 2);
      sheet.position.set(Lx / 2, (eave + ridge) / 2 + 0.03, cz);
      sheet.rotation.x = -s * ang; sheet.castShadow = sheet.receiveShadow = true; roofG.add(sheet);
    });
    // gable end triangles (wall above the chord)
    const tri = new THREE.Shape(); tri.moveTo(0, 0); tri.lineTo(Ly, 0); tri.lineTo(Ly / 2, ridge - eave); tri.closePath();
    [0, Lx].forEach(x => { const m = new THREE.Mesh(new THREE.ShapeGeometry(tri), new THREE.MeshLambertMaterial({color: 0xe8e4d8, side: THREE.DoubleSide}));
      m.rotation.y = -Math.PI / 2; m.position.set(x, eave, 0); m.castShadow = true; roofG.add(m); });
    // trusses at a uniform pitch along the length: bottom chord at `chord`, top chord 0.12 m under the sheet, verticals + diagonals
    const t = roof.truss || {}; const pitch = t.pitch || 3.1, mem = t.member || 0.08, off = 0.12;
    const trussMat = t.color ? new THREE.MeshLambertMaterial({color: new THREE.Color(t.color)}) : MAT.steel; g.userData.trussMat = trussMat;
    const member = (p, q, mat = trussMat) => { const a = L(...p), b = L(...q); const len = a.distanceTo(b); const m = new THREE.Mesh(new THREE.BoxGeometry(mem, mem, len), mat);
      m.position.copy(a.clone().lerp(b, 0.5)); m.lookAt(b); m.castShadow = true; return m; };
    const topAt = y => eave - off + (ridge - eave) * (1 - Math.abs(y - Ly / 2) / (Ly / 2));
    const x0 = t.first !== undefined ? t.first : 0;
    for (let x = x0; roof.trusses !== false && x <= Lx + 0.01; x += pitch) {
      const xx = Math.min(x, Lx);
      trussG.add(member([xx, 0, chord], [xx, Ly, chord]));
      trussG.add(member([xx, 0, topAt(0)], [xx, Ly / 2, topAt(Ly / 2)])); trussG.add(member([xx, Ly / 2, topAt(Ly / 2)], [xx, Ly, topAt(Ly)]));
      const panels = t.panels || 6; for (let k = 0; k <= panels; k++) {
        const y = Ly * k / panels; const top = topAt(y);
        if (top - chord > 0.1) trussG.add(member([xx, y, chord], [xx, y, top]));
        if (k < panels) { const y2 = Ly * (k + 1) / panels; const top2 = topAt(y2);
          g.add(k % 2 === 0 ? member([xx, y, chord], [xx, y2, top2]) : member([xx, y, top], [xx, y2, chord])); }
      }
    }
    // purlins along the length on each slope
    const pur = roof.trusses === false ? -1 : (t.purlins || 5);
    for (let k = 0; k <= pur; k++) { [1, -1].forEach(s => { const y = Ly / 2 + s * (Ly / 2) * k / pur; const z = topAt(y) + 0.02; trussG.add(member([0, y, z], [Lx, y, z])); }); }
    if (roof.band) {
      // perimeter band like АБК-1's parapet: vertical sheet from the eave up to the ridge on all four sides, hiding the slopes
      const b0 = roof.band.from !== undefined ? roof.band.from : eave, b1 = roof.band.to !== undefined ? roof.band.to : ridge;
      const bh = b1 - b0, bc = (b0 + b1) / 2, bt = 0.06;
      roofG.add(box(Lx + 2 * ov + bt, bh, bt, bandMat, Lx / 2, bc, ov));
      roofG.add(box(Lx + 2 * ov + bt, bh, bt, bandMat, Lx / 2, bc, -(Ly + ov)));
      roofG.add(box(bt, bh, Ly + 2 * ov + bt, bandMat, -ov, bc, -Ly / 2));
      roofG.add(box(bt, bh, Ly + 2 * ov + bt, bandMat, Lx + ov, bc, -Ly / 2));
      // flat cap between the band and the slopes along the eaves so the box reads closed from above
      [[ov, 0], [Ly + ov, Ly]].forEach(([yo, yi]) => { const d = Math.abs(yo - yi); roofG.add(box(Lx + 2 * ov, 0.05, d, MAT.roof, Lx / 2, eave, -(yo + yi) / 2)); });
    } else {
      // eave band (fascia)
      [0, Ly].forEach(y => roofG.add(box(Lx + 2 * ov, 0.25, 0.05, MAT.parapet, Lx / 2, eave - 0.1, -(y === 0 ? -ov : Ly + ov))));
    }
  }
  // temple interior (АБК-2 hall): painted walls/ceiling, iconostasis, furniture
  if (abk.temple) {
    const T = Object.assign({wall_h: H}, abk.temple);
    // openings (doors/passages) in the wall that carries the iconostasis -> the screen is broken there
    const side = T.altar_side || 'x1'; const wallAt = side === 'x0' ? T.x0 : side === 'x1' ? T.x1 : side === 'y0' ? T.y0 : T.y1; const alongX = side === 'y0' || side === 'y1';
    T.openings = (abk.doors || []).filter(d => { const r = walls[d.wall].rect; const c = alongX ? (r[1] + r[3]) / 2 : (r[0] + r[2]) / 2; return d.axis === (alongX ? 'x' : 'y') && Math.abs(c - wallAt) < 0.3; }).map(d => [d.from, d.to]);
    if (roof.type === 'gable') { const e = roof.eave, r = roof.ridge; T.topAt = y => e - 0.12 + (r - e) * (1 - Math.abs(y - Ly / 2) / (Ly / 2)); T.chord = roof.bottom_chord || H; T.truss_pitch = (roof.truss && roof.truss.pitch) || 3.1; T.trussMat = g.userData.trussMat; }
    g.add(buildTemple(T));
  }
  // extras
  (abk.extras || []).forEach(e => {
    if (e.type === 'finial') { const gold = new THREE.MeshStandardMaterial({color: 0xd4a843, metalness: 0.8, roughness: 0.3}); const b = e.base_h, h = e.h;
      const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.04, h, 12), gold); rod.position.copy(L(e.pos[0], e.pos[1], b + h / 2)); roofG.add(rod);
      [0.3, 0.6].forEach((f, k) => { const s = new THREE.Mesh(new THREE.SphereGeometry(0.16 - k * 0.05, 16, 12), gold); s.position.copy(L(e.pos[0], e.pos[1], b + h * f)); roofG.add(s); });
      const cres = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.03, 8, 24, Math.PI * 1.3), gold); cres.position.copy(L(e.pos[0], e.pos[1], b + h - 0.1)); cres.rotation.z = Math.PI * 0.35; roofG.add(cres); }
  });
  // labels (room names) as small sprites
  if (opts.label && abk.labels) abk.labels.forEach(l => { const s = opts.label(l.s, [l.p[0], l.p[1]], 0x334455, 0.9, H + 0.3); s.position.copy(L(l.p[0], l.p[1], 0.9)); g.add(s); });

  // ---- placement on the site footprint: centre on the footprint, long axis along the footprint's long axis
  if (footprint || (abk.placement && abk.placement.center)) {
    const fp = footprint || [[abk.placement.center[0] - Lx / 2, abk.placement.center[1]], [abk.placement.center[0] + Lx / 2, abk.placement.center[1]]];
    const xs = fp.map(p => p[0]), ys = fp.map(p => p[1]);
    const bx0 = Math.min(...xs), bx1 = Math.max(...xs), by0 = Math.min(...ys), by1 = Math.max(...ys);
    const cx = abk.placement && abk.placement.center ? abk.placement.center[0] : (bx0 + bx1) / 2, cy = abk.placement && abk.placement.center ? abk.placement.center[1] : (by0 + by1) / 2;
    const rot = (abk.placement && abk.placement.rotation_deg !== undefined) ? abk.placement.rotation_deg : ((bx1 - bx0) >= (by1 - by0) ? 0 : 90);
    const wrap = new THREE.Group();
    g.position.set(-Lx / 2, 0, Ly / 2);          // centre the local model
    wrap.add(g); wrap.rotation.y = THREE.MathUtils.degToRad(rot); wrap.position.set(cx, 0.02, -cy);
    wrap.userData = {id: abk.id, name: abk.name, size_m: abk.size_m, note: (abk.notes || []).join(' ')};
    return wrap;
  }
  return g;
}
