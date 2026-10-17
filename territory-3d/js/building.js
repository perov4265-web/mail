// Detailed building renderer: walls with openings, windows, doors, furniture, roof (flat+parapet or gable with trusses).
// Input: building JSON (local metres, origin at the SW corner, X along the length) and the site footprint polygon to place it on.
import * as THREE from 'three';

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

function buildWall(g, r, H, openings) {
  const axis = wallAxis(r);
  const t = axis === 'x' ? r[3] - r[1] : r[2] - r[0];
  const a0 = axis === 'x' ? r[0] : r[1], a1 = axis === 'x' ? r[2] : r[3];
  const c = axis === 'x' ? (r[1] + r[3]) / 2 : (r[0] + r[2]) / 2;
  const piece = (from, to, z0, z1) => {
    if (to - from < 0.005 || z1 - z0 < 0.005) return;
    const len = to - from, mid = (from + to) / 2, h = z1 - z0;
    const m = axis === 'x' ? box(len, h, t, MAT.wall, mid, z0 + h / 2, -c) : box(t, h, len, MAT.wall, c, z0 + h / 2, -mid);
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
  const byWall = new Map();
  const addOp = (i, op) => { if (!byWall.has(i)) byWall.set(i, []); byWall.get(i).push(op); };
  (abk.windows || []).forEach(w => addOp(w.wall, {from: w.from, to: w.to, z0: w.sill, z1: w.head}));
  (abk.doors || []).forEach(d => addOp(d.wall, {from: d.from, to: d.to, z0: 0, z1: d.height}));
  const info = walls.map((w, i) => buildWall(g, w.rect, H, byWall.get(i) || []));

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
    const wi = info[d.wall]; if (!wi) return;
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
    g.add(box(w, f.h, d, f.h < 0.6 ? MAT.chair : MAT.furn, (r[0] + r[2]) / 2, f.h / 2, -(r[1] + r[3]) / 2));
  });
  // floor slab
  const [Lx, Ly] = abk.size_m;
  g.add(box(Lx + 0.2, 0.15, Ly + 0.2, MAT.slab, Lx / 2, -0.075, -Ly / 2));
  // porches
  (abk.porches || []).forEach(p => {
    const r = p.rect; g.add(box(r[2] - r[0], 0.12, r[3] - r[1], MAT.porch, (r[0] + r[2]) / 2, -0.06, -(r[1] + r[3]) / 2));
    if (p.canopy) { const ch = p.canopy_h || 2.4; g.add(box(r[2] - r[0] + 0.3, 0.08, r[3] - r[1] + 0.2, MAT.roof, (r[0] + r[2]) / 2, ch, -(r[1] + r[3]) / 2));
      const px = [r[0] + 0.1, r[2] - 0.1], py = p.canopy_posts_y !== undefined ? p.canopy_posts_y : r[1] + 0.1;
      px.forEach(x => g.add(box(0.08, ch, 0.08, MAT.steel, x, ch / 2, -py))); }
  });
  // roof
  const roof = abk.roof || {type: 'flat_parapet', parapet_top: H + 1.2};
  if (roof.type === 'flat_parapet') {
    const top = roof.parapet_top;
    g.add(box(Lx, 0.2, Ly, MAT.roof, Lx / 2, H + 0.1, -Ly / 2));
    const pt = abk.wall_thickness_m || 0.11, ph = top - H;
    g.add(box(Lx, ph, pt, MAT.parapet, Lx / 2, H + ph / 2, -pt / 2));
    g.add(box(Lx, ph, pt, MAT.parapet, Lx / 2, H + ph / 2, -(Ly - pt / 2)));
    g.add(box(pt, ph, Ly, MAT.parapet, pt / 2, H + ph / 2, -Ly / 2));
    g.add(box(pt, ph, Ly, MAT.parapet, Lx - pt / 2, H + ph / 2, -Ly / 2));
  } else if (roof.type === 'gable') {
    const eave = roof.eave, ridge = roof.ridge, ov = roof.overhang || 0.3, chord = roof.bottom_chord || H;
    const half = Ly / 2, slopeLen = Math.hypot(half + ov, ridge - eave);
    const ang = Math.atan2(ridge - eave, half + ov);
    [[-1, half], [1, half]].forEach(([s, _]) => {
      const sheet = new THREE.Mesh(new THREE.BoxGeometry(Lx + 2 * ov, 0.06, slopeLen), MAT.roof);
      // centre of each slope
      const cz = -(half + s * (half + ov) / 2);
      sheet.position.set(Lx / 2, (eave + ridge) / 2 + 0.03, cz);
      sheet.rotation.x = s * ang; sheet.castShadow = sheet.receiveShadow = true; g.add(sheet);
    });
    // gable end triangles (wall above the chord)
    const tri = new THREE.Shape(); tri.moveTo(0, 0); tri.lineTo(Ly, 0); tri.lineTo(Ly / 2, ridge - eave); tri.closePath();
    [0, Lx].forEach(x => { const m = new THREE.Mesh(new THREE.ShapeGeometry(tri), new THREE.MeshLambertMaterial({color: 0xe8e4d8, side: THREE.DoubleSide}));
      m.rotation.y = -Math.PI / 2; m.position.set(x, eave, 0); m.castShadow = true; g.add(m); });
    // trusses: bottom chord at `chord`, top chord along the slope, verticals + diagonals
    const t = roof.truss || {}; const pitch = t.pitch || 3.1, mem = t.member || 0.08;
    const member = (p, q) => { const a = L(...p), b = L(...q); const len = a.distanceTo(b); const m = new THREE.Mesh(new THREE.BoxGeometry(mem, mem, len), MAT.steel);
      m.position.copy(a.clone().lerp(b, 0.5)); m.lookAt(b); m.castShadow = true; return m; };
    const n = Math.round(Lx / pitch);
    for (let i = 0; i <= n; i++) {
      const x = Math.min(i * pitch, Lx); if (i > 0 && x - (i - 1) * pitch < pitch * 0.5) continue;
      g.add(member([x, 0, chord], [x, Ly, chord]));
      g.add(member([x, 0, eave], [x, Ly / 2, ridge])); g.add(member([x, Ly / 2, ridge], [x, Ly, eave]));
      const panels = t.panels || 6; for (let k = 0; k <= panels; k++) {
        const y = Ly * k / panels; const top = eave + (ridge - eave) * (1 - Math.abs(y - Ly / 2) / (Ly / 2));
        if (top - chord > 0.1) g.add(member([x, y, chord], [x, y, top]));
        if (k < panels) { const y2 = Ly * (k + 1) / panels; const top2 = eave + (ridge - eave) * (1 - Math.abs(y2 - Ly / 2) / (Ly / 2));
          g.add(k % 2 === 0 ? member([x, y, chord], [x, y2, top2]) : member([x, y, top], [x, y2, chord])); }
      }
    }
    // purlins along the length on each slope
    const pur = t.purlins || 5;
    for (let k = 0; k <= pur; k++) { [1, -1].forEach(s => { const y = Ly / 2 + s * (Ly / 2) * k / pur; const z = eave + (ridge - eave) * (1 - k / pur); g.add(member([0, y, z - 0.04], [Lx, y, z - 0.04])); }); }
    // eave band (fascia)
    [0, Ly].forEach(y => g.add(box(Lx + 2 * ov, 0.25, 0.05, MAT.parapet, Lx / 2, eave - 0.1, -(y === 0 ? -ov : Ly + ov))));
  }
  // labels (room names) as small sprites
  if (opts.label && abk.labels) abk.labels.forEach(l => { const s = opts.label(l.s, [l.p[0], l.p[1]], 0x334455, 0.9, H + 0.3); s.position.copy(L(l.p[0], l.p[1], 0.9)); g.add(s); });

  // ---- placement on the site footprint: centre on the footprint, long axis along the footprint's long axis
  if (footprint) {
    const xs = footprint.map(p => p[0]), ys = footprint.map(p => p[1]);
    const bx0 = Math.min(...xs), bx1 = Math.max(...xs), by0 = Math.min(...ys), by1 = Math.max(...ys);
    const cx = (bx0 + bx1) / 2, cy = (by0 + by1) / 2;
    const rot = (abk.placement && abk.placement.rotation_deg !== undefined) ? abk.placement.rotation_deg : ((bx1 - bx0) >= (by1 - by0) ? 0 : 90);
    const wrap = new THREE.Group();
    g.position.set(-Lx / 2, 0, Ly / 2);          // centre the local model
    wrap.add(g); wrap.rotation.y = THREE.MathUtils.degToRad(rot); wrap.position.set(cx, 0.02, -cy);
    wrap.userData = {id: abk.id, name: abk.name, size_m: abk.size_m, note: (abk.notes || []).join(' ')};
    return wrap;
  }
  return g;
}
