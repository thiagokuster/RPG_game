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

  els.seats.innerHTML = players.map((player) => {
    const dead = player.hp <= 0;
    const classes = ["seat"];
    if (player.name === room.current_turn) classes.push("active");
    if (player.name === playerName) classes.push("you");
    if (dead) classes.push("dead");
    if (selectedTarget === player.name) classes.push("selected");
    return `
      <article class="${classes.join(" ")}" data-name="${player.name}">
        <h3>${player.name}</h3>
        <div class="meta">${player.classe} · CA ${player.armor_class || "-"} · Nv ${player.nivel || 1}</div>
        <div class="bar"><span class="hp" style="width:${percent(player.hp, player.max_hp)}%"></span></div>
        <div class="meta">HP ${player.hp}/${player.max_hp} · Mana ${player.mana || 0}/${player.max_mana || 0} · ${player.moedas || 0} moedas</div>
      </article>
    `;
  }).join("");

  els.seats.querySelectorAll(".seat").forEach((seat) => {
    seat.addEventListener("click", () => {
      selectedTarget = seat.dataset.name;
      els.target.value = selectedTarget;
      render(room);
    });
  });

  els.target.innerHTML = players
    .filter((player) => player.hp > 0)
    .map((player) => `<option value="${player.name}">${player.name}</option>`)
    .join("");
  if (!selectedTarget || selectedTarget === playerName) {
    const enemy = players.find((player) => player.name !== playerName && player.hp > 0);
    selectedTarget = enemy ? enemy.name : selectedTarget;
  }
  if (selectedTarget) els.target.value = selectedTarget;

  els.magic.innerHTML = (me?.magias || [])
    .map((magic) => `<option value="${magic.nome}">${magic.nome} (${magic.custo})</option>`)
    .join("");
  els.item.innerHTML = (me?.inventory || [])
    .map((item, index) => `<option value="${index}">${item.nome}</option>`)
    .join("");
  els.shop.innerHTML = (room.shop || [])
    .map((item, index) => {
      const extras = [];
      if (item.raridade) extras.push(item.raridade);
      if (item.tipo === "armadura" && item.reducao) extras.push(`red ${item.reducao}`);
      if (item.tipo === "arma" && item.dano) extras.push(`dano ${item.dano}`);
      return `<option value="${index}">${item.nome} ${extras.join(" ")} (${item.valor})</option>`;
    })
    .join("");

  const ended = room.status === "finished";
  [els.attack, els.magicBtn, els.shopBtn, els.buyBtn, els.equipBtn].forEach((button) => {
    button.disabled = !myTurn || ended;
  });

  const lines = (room.log || []).map((entry) => entry.text || entry).join("\n");
  els.log.textContent = lines || "Aguardando lances...";
  els.log.scrollTop = els.log.scrollHeight;
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
