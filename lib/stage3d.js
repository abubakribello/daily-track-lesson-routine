// Shared 3D stage for lesson animations: renderer, lights, ground, overlay (title, labels, captions, progress),
// camera keyframes keyed to narration scenes, particle families, and primitive helpers.
//
// In a scene page (see examples/separator_3d/scene.html):
//   <script type="importmap">{"imports":{"three":"/node_modules/three/build/three.module.js"}}</script>
//   <script type="module">
//     import * as THREE from "three";
//     import { createStage } from "/lib/stage3d.js";
//     const S = createStage({ title: "Three-phase separator in 3D", tag: "Cut-away view · schematic" });
//     ... add meshes to S.scene, S.label(...), S.camera keys in S.cams ...
//     S.start();   // defines window.setup / window.renderAt / window.ready
//   </script>
import * as THREE from "three";

export const C = {
  bg: 0xEDEAE2, steel: 0x7D8790, dark: 0x4F5B66, light: 0xC9CED3, water: 0x2F6FC4, oil: 0xD0892C,
  gas: 0x9AA6B2, hot: 0xC0392B, cold: 0x2E86C1, accent: 0xE4572E, ground: 0xDCD6C8,
};

const CSS = `
html,body{margin:0;width:1280px;height:720px;overflow:hidden;background:#EDEAE2;font-family:"DejaVu Sans",Arial,sans-serif}
#c{position:absolute;inset:0}
.lab{position:absolute;transform:translate(-50%,-100%);font-size:15px;font-weight:bold;color:#1F2328;background:rgba(255,255,255,.88);
 padding:3px 8px;border-radius:4px;border:1px solid #9AA3AB;white-space:nowrap}
.lab.on{background:#E4572E;color:#fff;border-color:#E4572E}
.lab::after{content:"";position:absolute;left:50%;top:100%;width:1px;height:14px;background:#5B6670}
#title{position:absolute;left:34px;top:22px;font-size:26px;font-weight:bold;color:#12332F}
#tag{position:absolute;right:34px;top:30px;font-size:14px;color:#5B6670}
#cap{position:absolute;left:0;right:0;bottom:0;height:78px;background:#12332F;color:#fff;font-size:20px;display:flex;align-items:center;
 justify-content:center;text-align:center;padding:0 60px;box-sizing:border-box}
#bar{position:absolute;left:0;bottom:78px;height:5px;background:#E4572E;width:0}`;

export function createStage({ title = "", tag = "", ground = true, groundY = -3.27, bg = C.bg } = {}) {
  const st = document.createElement("style"); st.textContent = CSS; document.head.appendChild(st);
  document.body.innerHTML = `<canvas id="c" width="1280" height="720"></canvas><div id="title"></div><div id="tag"></div>
    <div id="labels"></div><div id="bar"></div><div id="cap"></div>`;
  document.getElementById("title").textContent = title;
  document.getElementById("tag").textContent = tag;

  const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById("c"), antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(1280, 720, false); renderer.setPixelRatio(1);
  renderer.localClippingEnabled = true; renderer.toneMapping = THREE.ACESFilmicToneMapping;
  const scene = new THREE.Scene(); scene.background = new THREE.Color(bg);
  const camera = new THREE.PerspectiveCamera(38, 1280 / 720, 0.1, 300);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8170, 1.6));
  const sun = new THREE.DirectionalLight(0xffffff, 2.2); sun.position.set(6, 12, 9); scene.add(sun);
  const fill = new THREE.DirectionalLight(0xffffff, 0.7); fill.position.set(-8, 4, -6); scene.add(fill);
  if (ground) {
    const g = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshStandardMaterial({ color: C.ground, roughness: 1 }));
    g.rotation.x = -Math.PI / 2; g.position.y = groundY; scene.add(g);
    const grid = new THREE.GridHelper(80, 80, 0xC4BDAD, 0xCDC7B8); grid.position.y = groundY + 0.01; scene.add(grid);
  }

  const S = { THREE, renderer, scene, camera, cams: {}, labels: [], particles: [], onFrame: null, drift: 0.6, TL: null };

  // ---- helpers ----
  S.plane = (nx, ny, nz, c) => new THREE.Plane(new THREE.Vector3(nx, ny, nz), c);
  S.mat = (color, o = {}) => new THREE.MeshStandardMaterial(Object.assign({ color, metalness: 0.35, roughness: 0.5 }, o));
  S.ghost = (color, opacity = 0.15, o = {}) => S.mat(color, Object.assign({ transparent: true, opacity, depthWrite: false, side: THREE.DoubleSide }, o));
  S.add = (...m) => { m.forEach(x => scene.add(x)); return m[0]; };
  // horizontal capsule shell along x (rounded ends), length = straight length
  S.hCapsule = (r, length) => { const g = new THREE.CapsuleGeometry(r, length, 24, 64); g.rotateZ(Math.PI / 2); return g; };
  S.pipe = (a, b, r = 0.17, material = S.mat(C.steel, { metalness: 0.5, roughness: 0.45 })) => {
    const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b), d = B.clone().sub(A);
    const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, d.length(), 24), material);
    m.position.copy(A.clone().add(B).multiplyScalar(0.5)); m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize());
    scene.add(m); return m;
  };
  S.flange = (p, axis = "y", r = 0.32) => {
    const f = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 0.08, 32), S.mat(C.steel, { metalness: 0.5 }));
    f.position.set(...p); if (axis === "x") f.rotation.z = Math.PI / 2; if (axis === "z") f.rotation.x = Math.PI / 2;
    scene.add(f); return f;
  };
  S.box = (size, pos, color = C.dark, o = {}) => { const m = new THREE.Mesh(new THREE.BoxGeometry(...size), S.mat(color, o)); m.position.set(...pos); scene.add(m); return m; };
  // camera keyframe for a narration scene key: S.cam("inlet", [x,y,z], [tx,ty,tz])
  S.cam = (key, pos, target) => { S.cams[key] = [pos, target]; };
  // label pinned to a 3D point; highlighted while any of `keys` is the active scene
  S.label = (text, p, keys = []) => {
    const el = document.createElement("div"); el.className = "lab"; el.textContent = text;
    document.getElementById("labels").appendChild(el); S.labels.push({ el, v: new THREE.Vector3(...p), keys });
  };
  // particles moving along polylines (unlit spheres so they stay readable inside translucent volumes)
  let seed = 42; S.rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  S.poly = (pts) => { const v = pts.map(p => new THREE.Vector3(...p)); const L = [0];
    for (let i = 1; i < v.length; i++) L.push(L[i - 1] + v[i].distanceTo(v[i - 1]));
    return (u) => { const d = (u % 1) * L[L.length - 1]; let i = 1; while (i < L.length - 1 && L[i] < d) i++;
      return v[i - 1].clone().lerp(v[i], (d - L[i - 1]) / ((L[i] - L[i - 1]) || 1)); }; };
  S.flow = (n, color, size, speed, makePath, { onTop = false } = {}) => {
    const mat = new THREE.MeshBasicMaterial({ color, depthTest: !onTop });
    const im = new THREE.InstancedMesh(new THREE.SphereGeometry(size, 10, 8), mat, n);
    if (onTop) im.renderOrder = 10;
    scene.add(im);
    const items = []; for (let i = 0; i < n; i++) items.push({ path: makePath(i), ph: S.rnd(), sp: speed * (0.85 + 0.3 * S.rnd()) });
    S.particles.push({ im, items }); return im;
  };

  // ---- timeline-driven rendering ----
  const ease = (x) => x < 0 ? 0 : x > 1 ? 1 : x * x * (3 - 2 * x);
  const dummy = new THREE.Object3D();
  function lineAt(t) { const L = S.TL.lines; let i = 0; while (i < L.length - 1 && t >= L[i + 1].start - 0.6) i++; return i; }
  function camFor(key) { return S.cams[key] || S.cams.default || Object.values(S.cams)[0]; }
  function camAt(t, i) {
    const L = S.TL.lines; let j = i; while (j > 0 && L[j - 1].scene === L[i].scene) j--;   // first line of current scene
    const cur = camFor(L[j].scene), prev = j > 0 ? camFor(L[j - 1].scene) : cur;
    const k = ease((t - (L[j].start - 0.6)) / 1.8);
    const pos = new THREE.Vector3(...prev[0]).lerp(new THREE.Vector3(...cur[0]), k);
    const tgt = new THREE.Vector3(...prev[1]).lerp(new THREE.Vector3(...cur[1]), k);
    pos.x += Math.sin(t * 0.35) * S.drift; pos.y += Math.cos(t * 0.3) * S.drift * 0.33;
    return [pos, tgt];
  }
  S.start = () => {
    window.setup = (tl) => { S.TL = tl; };
    window.renderAt = (t) => {
      const i = lineAt(t), line = S.TL.lines[i];
      const [pos, tgt] = camAt(t, i);
      camera.position.copy(pos); camera.lookAt(tgt); camera.updateMatrixWorld();
      for (const f of S.particles) {
        f.items.forEach((it, k) => { dummy.position.copy(it.path(it.ph + it.sp * t)); dummy.updateMatrix(); f.im.setMatrixAt(k, dummy.matrix); });
        f.im.instanceMatrix.needsUpdate = true;
      }
      if (S.onFrame) S.onFrame(t, line);
      renderer.render(scene, camera);
      S.labels.forEach(l => { const v = l.v.clone().project(camera); const sx = (v.x + 1) / 2 * 1280, sy = (1 - v.y) / 2 * 720;
        const vis = v.z < 1 && sx > 70 && sx < 1210 && sy > 95 && sy < 620;
        l.el.style.display = vis ? "block" : "none"; l.el.style.left = sx + "px"; l.el.style.top = (sy - 14) + "px";
        l.el.classList.toggle("on", l.keys.includes(line.scene)); });
      const active = t >= line.start - 0.4 && t <= line.end + 0.9;
      document.getElementById("cap").textContent = active ? line.caption : "";
      if (line.title) document.getElementById("title").textContent = line.title;
      document.getElementById("bar").style.width = (t / S.TL.total * 1280) + "px";
      return true;
    };
    window.ready = true;
  };
  return S;
}
