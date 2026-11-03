const params = new URLSearchParams(window.location.search);
const roomCode = (params.get("code") || localStorage.getItem("rpg_room") || "").toUpperCase();
const playerName = params.get("player") || localStorage.getItem("rpg_player") || "";
const playerToken = localStorage.getItem("rpg_token") || "";

const els = {
  roomLabel: document.getElementById("roomLabel"),
  turnBanner: document.getElementById("turnBanner"),
  seats: document.getElementById("seats"),
  log: document.getElementById("log"),
  status: document.getElementById("status"),
  target: document.getElementById("targetSelect"),
  magic: document.getElementById("magicSelect"),
  shop: document.getElementById("shopSelect"),
  item: document.getElementById("itemSelect"),
  attack: document.getElementById("attackBtn"),
  magicBtn: document.getElementById("magicBtn"),
  shopBtn: document.getElementById("shopBtn"),
  buyBtn: document.getElementById("buyBtn"),
  equipBtn: document.getElementById("equipBtn"),
};

let selectedTarget = "";
let source = null;

function percent(current, max) {
  if (!max) return 0;
  return Math.max(0, Math.min(100, Math.round((current / max) * 100)));
}

function setStatus(message, ok = true) {
  els.status.textContent = message;
  els.status.style.color = ok ? "var(--muted)" : "var(--danger)";
}

function render(room) {
  if (!room) return;
  const players = room.players || [];
  const me = players.find((player) => player.name === playerName);
  const myTurn = room.current_turn === playerName && room.status === "started";

  els.roomLabel.textContent = `Sala ${room.code || roomCode}`;
  if (room.status === "finished") {
    els.turnBanner.textContent = room.winner && room.winner !== "nenhum"
      ? `${room.winner} venceu a partida.`
      : "Partida encerrada sem vencedor.";
  } else if (room.status !== "started") {
    els.turnBanner.textContent = "Aguardando o inicio da partida.";
  } else {
    els.turnBanner.textContent = myTurn ? "Sua vez." : `Vez de ${room.current_turn || "—"}.`;
  }

  els.seats.replaceChildren();
  players.forEach((player) => {
    const dead = player.hp <= 0;
    const article = document.createElement("article");
    article.className = "seat";
    if (player.name === room.current_turn) article.classList.add("active");
    if (player.name === playerName) article.classList.add("you");
    if (dead) article.classList.add("dead");
    if (selectedTarget === player.name) article.classList.add("selected");
    article.dataset.name = player.name;
    const title = document.createElement("h3");
    title.textContent = player.name;
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `CA ${player.armor_class || "-"} · Nv ${player.nivel || 1}`;
    const bar = document.createElement("div");
    bar.className = "bar";
    const hp = document.createElement("span");
    hp.className = "hp";
    hp.style.width = `${percent(player.hp, player.max_hp)}%`;
    bar.append(hp);
    const stats = document.createElement("div");
    stats.className = "meta";
    stats.textContent = `HP ${player.hp}/${player.max_hp} · Mana ${player.mana || 0}/${player.max_mana || 0} · ${player.moedas || 0} moedas`;
    article.append(title, meta, bar, stats);
    article.addEventListener("click", () => {
      selectedTarget = player.name;
      els.target.value = selectedTarget;
      render(room);
    });
    els.seats.append(article);
  });

  els.target.replaceChildren();
  players.filter((player) => player.hp > 0).forEach((player) => {
    const option = document.createElement("option");
    option.value = player.name;
    option.textContent = player.name;
    els.target.append(option);
  });
  if (!selectedTarget || selectedTarget === playerName) {
    const enemy = players.find((player) => player.name !== playerName && player.hp > 0);
    selectedTarget = enemy ? enemy.name : selectedTarget;
  }
  if (selectedTarget) els.target.value = selectedTarget;

  els.magic.replaceChildren();
  (me?.magias || []).forEach((magic) => {
    const option = document.createElement("option");
    option.value = magic.nome;
    option.textContent = `${magic.nome} (${magic.custo})`;
    els.magic.append(option);
  });
  els.item.replaceChildren();
  (me?.inventory || []).forEach((item, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = item.nome;
    els.item.append(option);
  });
  els.shop.replaceChildren();
  (room.shop || []).forEach((item, index) => {
    const extras = [];
    if (item.raridade) extras.push(item.raridade);
    if (item.tipo === "armadura" && item.reducao) extras.push(`red ${item.reducao}`);
    if (item.tipo === "arma" && item.dano) extras.push(`dano ${item.dano}`);
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = `${item.nome} ${extras.join(" ")} (${item.valor})`;
    els.shop.append(option);
  });

  const ended = room.status === "finished";
  [els.attack, els.magicBtn, els.shopBtn, els.buyBtn, els.equipBtn].forEach((button) => {
    button.disabled = !myTurn || ended;
  });

  const lines = (room.log || []).map((entry) => entry.text || entry).join("\n");
  els.log.textContent = lines || "Aguardando lances...";
  els.log.scrollTop = els.log.scrollHeight;
  if (window.Arena3D && !document.getElementById("arena3d").hidden) {
    window.Arena3D.render(room);
  }
}

async function act(payload) {
  try {
    const data = await api.action({
      room: roomCode,
      token: playerToken,
      ...payload,
    });
    if (data.error || data.type === "error") {
      setStatus(data.error || data.message, false);
      return;
    }
    setStatus("Lance enviado.");
    render(data.room_state || (await api.room(roomCode)).room);
  } catch (error) {
    setStatus(error.message, false);
  }
}

els.attack.addEventListener("click", () => act({ action: "attack", target: els.target.value }));
els.magicBtn.addEventListener("click", () => act({ action: "use_magic", target: els.target.value, magic: els.magic.value }));
els.shopBtn.addEventListener("click", () => act({ action: "shop", action_type: "refresh" }));
els.buyBtn.addEventListener("click", () => act({ action: "shop", item_index: Number(els.shop.value) }));
els.equipBtn.addEventListener("click", () => act({ action: "equip", item_index: Number(els.item.value) }));
els.target.addEventListener("change", () => {
  selectedTarget = els.target.value;
});

const toggle3d = document.getElementById("toggle3d");
const canvas3d = document.getElementById("arena3d");
if (toggle3d && canvas3d) {
  toggle3d.addEventListener("click", () => {
    const on = canvas3d.hidden;
    if (window.Arena3D) {
      window.Arena3D.show(canvas3d, on);
    } else {
      canvas3d.hidden = !on;
    }
    toggle3d.textContent = on ? "Tabuleiro 2D" : "Arena 3D";
  });
}

async function boot() {
  if (!roomCode || !playerName || !playerToken) {
    window.location.href = "/";
    return;
  }
  localStorage.setItem("rpg_player", playerName);
  localStorage.setItem("rpg_room", roomCode);
  const data = await api.room(roomCode);
  render(data.room);
  source = api.stream(roomCode, render);
}

boot().catch((error) => setStatus(error.message, false));
