const Arena3D = (() => {
  const COLORS = [0xc24b4b, 0x7b5ea7, 0x769656, 0xd4a017, 0x6a9fbf, 0xe8c547];

  let renderer;
  let scene;
  let camera;
  let figures = new Map();
  let lastSignature = "";
  let animating = false;
  let dragging = false;
  let lastX = 0;
  let theta = 0.4;
  let phi = 0.9;
  const radius = 9;

  function colorFor(player, index) {
    if (player.npc) return 0x5a1a1a;
    return COLORS[index % COLORS.length];
  }

  function shapeFor(player) {
    if (player.npc) return new THREE.BoxGeometry(1.1, 1.6, 1.1);
    return new THREE.BoxGeometry(0.7, 1.3, 0.55);
  }

  function mount(canvas) {
    if (!window.THREE || !canvas) return;
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
    const floor = new THREE.Mesh(
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

  function place(players) {
    const alive = players || [];
    const signature = alive.map((player) => `${player.name}:${player.classe}:${player.hp}`).join("|");
    if (signature === lastSignature) return;
    lastSignature = signature;
    figures.forEach((mesh) => scene.remove(mesh));
    figures.clear();
    const total = Math.max(alive.length, 1);
    alive.forEach((player, index) => {
      const mesh = new THREE.Mesh(
        shapeFor(player),
        new THREE.MeshStandardMaterial({ color: colorFor(player, index), roughness: 0.45 })
      );
      const angle = (index / total) * Math.PI * 2 - Math.PI / 2;
      mesh.position.set(Math.cos(angle) * 3.4, 0.7, Math.sin(angle) * 3.4);
      mesh.userData = { name: player.name, home: mesh.position.clone() };
      scene.add(mesh);
      figures.set(player.name, mesh);
    });
  }

  function playEvents(eventos) {
    if (!eventos || !eventos.length || animating) return;
    const ataque = eventos.find((ev) => ev.tipo === "ataque" || ev.tipo === "magia");
    if (!ataque) return;
    const from = figures.get(ataque.de);
    const to = figures.get(ataque.para);
    if (!from || !to) return;
    animating = true;
    const start = performance.now();
    const home = from.userData.home.clone();
    function tick(now) {
      const t = Math.min(1, (now - start) / 420);
      const punch = t < 0.5 ? t * 2 : (1 - t) * 2;
      from.position.lerpVectors(home, to.position, punch * 0.45);
      to.position.y = 0.7 + (ataque.acertou || ataque.dano || ataque.cura ? Math.sin(t * Math.PI) * 0.25 : 0);
      if (t < 1) {
        requestAnimationFrame(tick);
        return;
      }
      from.position.copy(home);
      to.position.y = 0.7;
      animating = false;
    }
    requestAnimationFrame(tick);
  }

  function loop() {
    if (!renderer) return;
    camera.position.set(Math.cos(theta) * Math.sin(phi) * radius, Math.cos(phi) * radius + 2, Math.sin(theta) * Math.sin(phi) * radius);
    camera.lookAt(0, 0.4, 0);
    renderer.render(scene, camera);
    requestAnimationFrame(loop);
  }

  function render(room) {
    if (!renderer) return;
    place(room.players || []);
    playEvents(room.eventos || []);
  }

  function show(canvas, on) {
    canvas.hidden = !on;
    if (on && !renderer) mount(canvas);
    if (on) resize(canvas);
  }

  return { mount, render, show };
})();
