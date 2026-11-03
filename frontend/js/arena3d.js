import * as THREE from "three";

const Arena3D = (() => {
  const COLORS = [0xc24b4b, 0x7b5ea7, 0x769656, 0xd4a017, 0x6a9fbf, 0xe8c547];
  const QUEUE_TYPES = new Set(["ataque", "magia", "morte", "cura", "onda"]);

  let renderer;
  let scene;
  let camera;
  let canvasRef;
  let floor;
  let figures = new Map();
  let animating = false;
  let dragging = false;
  let lastX = 0;
  let theta = 0.4;
  let phi = 0.9;
  let visible = false;
  let lastSeenId = 0;
  let primed = false;
  let matchKey = "";
  let raf = 0;
  const queue = [];
  const radius = 9;

  function colorFor(player, index) {
    if (player.npc) return 0x5a1a1a;
    if ((player.hp || 0) <= 0) return 0x3a3632;
    return COLORS[index % COLORS.length];
  }

  function fingerprint(room) {
    const names = (room.players || []).map((player) => player.name).join(",");
    return `${room.code || ""}|${room.status || ""}|${names}`;
  }

  function resetMatch(room) {
    const key = fingerprint(room);
    const ids = (room.eventos || []).map((ev) => ev.id).filter((id) => id != null);
    const maxId = ids.length ? Math.max(...ids) : 0;
    if (key !== matchKey || (maxId && maxId < lastSeenId)) {
      matchKey = key;
      primed = false;
      lastSeenId = 0;
      queue.length = 0;
      animating = false;
    }
  }

  function disposeObject(object) {
    if (!object) return;
    object.traverse((child) => {
      if (child.geometry) child.geometry.dispose();
      const material = child.material;
      if (!material) return;
      const list = Array.isArray(material) ? material : [material];
      list.forEach((item) => {
        if (item.map) item.map.dispose();
        item.dispose();
      });
    });
  }

  function makeLabelTexture(player, active) {
    const canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 64;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, 256, 64);
    ctx.fillStyle = active ? "rgba(232, 197, 71, 0.92)" : "rgba(22, 21, 18, 0.82)";
    ctx.fillRect(0, 0, 256, 64);
    ctx.fillStyle = "#f0d9b5";
    ctx.font = "bold 22px Georgia, serif";
    ctx.textAlign = "center";
    const suffix = (player.hp || 0) <= 0 ? " (morto)" : "";
    ctx.fillText(`${player.name || "?"}${suffix}`, 128, 26);
    ctx.fillStyle = "#3d3a36";
    ctx.fillRect(24, 38, 208, 14);
    const pct = player.max_hp ? Math.max(0, Math.min(1, player.hp / player.max_hp)) : 0;
    ctx.fillStyle = pct > 0.45 ? "#769656" : "#c24b4b";
    ctx.fillRect(24, 38, 208 * pct, 14);
    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    return texture;
  }

  function makeFigure(player, index) {
    const group = new THREE.Group();
    const geometry = player.npc
      ? new THREE.BoxGeometry(1.1, 1.6, 1.1)
      : new THREE.BoxGeometry(0.7, 1.3, 0.55);
    const material = new THREE.MeshStandardMaterial({
      color: colorFor(player, index),
      roughness: 0.45,
      emissive: 0x000000,
    });
    const body = new THREE.Mesh(geometry, material);
    body.position.y = 0.7;
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: makeLabelTexture(player, false) }));
    sprite.position.y = 2.05;
    sprite.scale.set(2.2, 0.55, 1);
    group.add(body, sprite);
    group.userData = { name: player.name, body, sprite, home: new THREE.Vector3(), labelKey: "" };
    return group;
  }

  function updateFigure(group, player, index, total, currentTurn) {
    const angle = (index / Math.max(total, 1)) * Math.PI * 2 - Math.PI / 2;
    const x = Math.cos(angle) * 3.4;
    const z = Math.sin(angle) * 3.4;
    group.userData.home.set(x, 0, z);
    if (!animating) group.position.set(x, 0, z);
    const dead = (player.hp || 0) <= 0;
    const body = group.userData.body;
    if (!animating) body.scale.set(1, dead ? 0.45 : 1, 1);
    body.material.color.setHex(colorFor(player, index));
    const active = player.name === currentTurn && !dead;
    if (!animating) {
      body.material.emissive.setHex(active ? 0xe8c547 : 0x000000);
      body.material.emissiveIntensity = active ? 0.35 : 0;
    }
    const sprite = group.userData.sprite;
    const labelKey = `${player.name}|${player.hp}|${player.max_hp}|${active}|${dead}`;
    if (group.userData.labelKey === labelKey) return;
    group.userData.labelKey = labelKey;
    const old = sprite.material.map;
    sprite.material.map = makeLabelTexture(player, active);
    sprite.material.needsUpdate = true;
    if (old) old.dispose();
  }

  function flash(group, hex, ms = 280) {
    if (!group) return;
    const body = group.userData.body;
    const prev = body.material.emissive.getHex();
    const prevI = body.material.emissiveIntensity;
    body.material.emissive.setHex(hex);
    body.material.emissiveIntensity = 0.9;
    setTimeout(() => {
      body.material.emissive.setHex(prev);
      body.material.emissiveIntensity = prevI;
    }, ms);
  }

  function flashFloor(color = 0xd4a017) {
    if (!floor) return;
    const orig = floor.material.color.getHex();
    floor.material.color.setHex(color);
    setTimeout(() => {
      floor.material.color.setHex(orig);
    }, 520);
  }

  function showWaveBanner(onda) {
    const el = document.getElementById("ondaBanner");
    if (!el) return;
    el.hidden = false;
    el.textContent = `Onda ${onda || "?"} chegando`;
    clearTimeout(el._hide);
    el._hide = setTimeout(() => {
      el.hidden = true;
    }, 2200);
  }

  function mount(canvas) {
    if (!canvas) return;
    canvasRef = canvas;
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x161512);
    camera = new THREE.PerspectiveCamera(50, canvas.clientWidth / Math.max(canvas.clientHeight, 1), 0.1, 80);
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    resize(canvas);
    scene.add(new THREE.AmbientLight(0xf0d9b5, 0.55));
    const key = new THREE.DirectionalLight(0xffffff, 0.85);
    key.position.set(4, 8, 6);
    scene.add(key);
    floor = new THREE.Mesh(
      new THREE.CylinderGeometry(5.2, 5.2, 0.25, 48),
      new THREE.MeshStandardMaterial({ color: 0x3d3a36, roughness: 0.85 })
    );
    floor.position.y = -0.2;
    scene.add(floor);
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(5.15, 0.06, 8, 48),
      new THREE.MeshStandardMaterial({ color: 0xd4a017 })
    );
    ring.rotation.x = Math.PI / 2;
    scene.add(ring);
    canvas.addEventListener("pointerdown", (event) => {
      dragging = true;
      lastX = event.clientX;
    });
    window.addEventListener("pointerup", () => {
      dragging = false;
    });
    window.addEventListener("pointermove", (event) => {
      if (!dragging) return;
      theta += (event.clientX - lastX) * 0.01;
      lastX = event.clientX;
    });
    window.addEventListener("resize", () => {
      if (canvasRef) resize(canvasRef);
    });
    loop();
  }

  function resize(canvas) {
    if (!renderer || !camera) return;
    const width = canvas.clientWidth || 640;
    const height = canvas.clientHeight || 360;
    renderer.setSize(width, height, false);
    camera.aspect = width / Math.max(height, 1);
    camera.updateProjectionMatrix();
  }

  function place(players, currentTurn) {
    const alive = players || [];
    const seen = new Set();
    const total = Math.max(alive.length, 1);
    alive.forEach((player, index) => {
      seen.add(player.name);
      let group = figures.get(player.name);
      if (!group) {
        group = makeFigure(player, index);
        scene.add(group);
        figures.set(player.name, group);
      }
      updateFigure(group, player, index, total, currentTurn);
    });
    Array.from(figures.keys()).forEach((name) => {
      if (seen.has(name)) return;
      const group = figures.get(name);
      scene.remove(group);
      disposeObject(group);
      figures.delete(name);
    });
  }

  function playDeath(who) {
    animating = true;
    const body = who.userData.body;
    const start = performance.now();
    flash(who, 0x3a3632, 500);
    function tick(now) {
      const t = Math.min(1, (now - start) / 480);
      body.scale.set(1, 1 - 0.55 * t, 1);
      if (t < 1) {
        requestAnimationFrame(tick);
        return;
      }
      body.scale.set(1, 0.45, 1);
      animating = false;
      playNext();
    }
    requestAnimationFrame(tick);
  }

  function playPunch(from, to, ev) {
    animating = true;
    const start = performance.now();
    const home = from.userData.home.clone();
    const toHome = to.userData.home.clone();
    if (ev.tipo === "magia") flash(from, 0x6a9fbf, 420);
    if (ev.critico) flash(to, 0xffffff, 360);
    function tick(now) {
      const t = Math.min(1, (now - start) / 420);
      const punch = t < 0.5 ? t * 2 : (1 - t) * 2;
      from.position.lerpVectors(home, toHome, punch * 0.45);
      to.position.y = ev.acertou || ev.dano || ev.cura ? Math.sin(t * Math.PI) * 0.25 : 0;
      if (t < 1) {
        requestAnimationFrame(tick);
        return;
      }
      from.position.copy(home);
      to.position.y = 0;
      animating = false;
      playNext();
    }
    requestAnimationFrame(tick);
  }

  function playNext() {
    if (animating || !queue.length) return;
    const ev = queue.shift();
    if (ev.tipo === "onda") {
      showWaveBanner(ev.onda);
      flashFloor(0xd4a017);
      playNext();
      return;
    }
    const from = figures.get(ev.de);
    const to = figures.get(ev.para);
    if (ev.tipo === "morte") {
      const who = from || to;
      if (!who) {
        playNext();
        return;
      }
      playDeath(who);
      return;
    }
    if (ev.tipo === "cura" || ev.cura) {
      flash(to || from, 0x769656, 420);
      if (ev.tipo === "cura") {
        playNext();
        return;
      }
    }
    if (!from || !to) {
      playNext();
      return;
    }
    playPunch(from, to, ev);
  }

  function playEvents(eventos) {
    let maxId = lastSeenId;
    const fresh = [];
    for (const ev of eventos || []) {
      const id = ev.id;
      if (id != null) maxId = Math.max(maxId, id);
      if (id != null && id <= lastSeenId) continue;
      if (QUEUE_TYPES.has(ev.tipo) || ev.critico) fresh.push(ev);
    }
    if (!primed) {
      lastSeenId = maxId;
      primed = true;
      return;
    }
    lastSeenId = maxId;
    for (const ev of fresh) queue.push(ev);
    playNext();
  }

  function loop() {
    if (!renderer) return;
    if (visible) {
      camera.position.set(
        Math.cos(theta) * Math.sin(phi) * radius,
        Math.cos(phi) * radius + 2,
        Math.sin(theta) * Math.sin(phi) * radius
      );
      camera.lookAt(0, 0.4, 0);
      renderer.render(scene, camera);
      raf = requestAnimationFrame(loop);
    }
  }

  function render(room) {
    if (!renderer || !visible || !room) return;
    resetMatch(room);
    place(room.players || [], room.current_turn);
    playEvents(room.eventos || []);
  }

  function show(canvas, on) {
    visible = on;
    canvas.hidden = !on;
    canvasRef = canvas;
    if (on && !renderer) mount(canvas);
    if (on) {
      resize(canvas);
      cancelAnimationFrame(raf);
      loop();
    }
  }

  return { mount, render, show };
})();

window.Arena3D = Arena3D;
export default Arena3D;
