const CLASSES = ["Guerreiro", "Mago", "Arqueiro", "Paladino", "Clerigo"];

const els = {
  playerName: document.getElementById("playerName"),
  joinName: document.getElementById("joinName"),
  roomCode: document.getElementById("roomCode"),
  createStatus: document.getElementById("createStatus"),
  joinStatus: document.getElementById("joinStatus"),
  roomsList: document.getElementById("roomsList"),
  waiting: document.getElementById("waiting"),
  classBox: document.getElementById("classBox"),
  waitingPlayers: document.getElementById("waitingPlayers"),
  createRoomBtn: document.getElementById("createRoomBtn"),
  createPassword: document.getElementById("createPassword"),
  joinPassword: document.getElementById("joinPassword"),
};

let activeRoom = null;
let goingToBoard = false;
let creating = false;
let lobbyStream = null;

function saveSession(player, code, token) {
  localStorage.setItem("rpg_player", player);
  localStorage.setItem("rpg_room", code);
  if (token) {
    localStorage.setItem("rpg_token", token);
  }
}

function setStatus(node, message, ok) {
  node.textContent = message;
  node.style.color = ok ? "var(--you)" : "var(--danger)";
}

function goToBoard(code) {
  if (goingToBoard || !code) return;
  goingToBoard = true;
  const player = localStorage.getItem("rpg_player") || els.playerName.value.trim() || els.joinName.value.trim();
  window.location.replace(`/jogo.html?code=${encodeURIComponent(code)}&player=${encodeURIComponent(player)}`);
}

function renderClasses(players) {
  const previous = selectedClasses();
  els.classBox.innerHTML = players.map((player) => {
    const name = player.name || player;
    const options = CLASSES.map((classe) => `<option value="${classe}">${classe}</option>`).join("");
    return `<label>${name}<select data-player="${name}">${options}</select></label>`;
  }).join("");
  els.classBox.querySelectorAll("select").forEach((select) => {
    if (previous[select.dataset.player]) {
      select.value = previous[select.dataset.player];
    }
  });
}

function selectedClasses() {
  const selected = {};
  els.classBox.querySelectorAll("select").forEach((select) => {
    selected[select.dataset.player] = select.value;
  });
  return selected;
}

function watchRoom(code) {
  if (!code || (lobbyStream && lobbyStream.roomCode === code)) {
    return;
  }
  if (lobbyStream) {
    lobbyStream.close();
  }
  lobbyStream = api.stream(code, (room) => {
    if (!room) return;
    if (room.status === "started" || room.status === "finished") {
      goToBoard(room.code || code);
      return;
    }
    showWaiting(room, false);
  });
  lobbyStream.roomCode = code;
}

function showWaiting(room, subscribe = true) {
  if (!room || goingToBoard) return;
  activeRoom = room.code;
  els.waiting.hidden = false;
  els.waitingPlayers.textContent = `${(room.players || []).length} jogador(es) na sala`;
  if ((room.status || "waiting") === "waiting") {
    renderClasses(room.players || []);
  }
  if (room.status === "started" || room.status === "finished") {
    goToBoard(room.code);
    return;
  }
  if (subscribe) {
    watchRoom(room.code);
  }
}

async function createRoom() {
  if (creating) return;
  if (activeRoom) {
    setStatus(els.createStatus, `Voce ja esta na sala ${activeRoom}.`, true);
    return;
  }
  const player = els.playerName.value.trim();
  if (!player) {
    setStatus(els.createStatus, "Informe seu nome.", false);
    return;
  }
  creating = true;
  els.createRoomBtn.disabled = true;
  try {
    const room = await api.createRoom(player, els.createPassword.value.trim());
    saveSession(player, room.code, room.token);
    els.roomCode.value = room.code;
    els.joinName.value = player;
    setStatus(els.createStatus, `Sala ${room.code} criada. Compartilhe o codigo.`, true);
    showWaiting(room);
    await loadRooms();
  } catch (error) {
    setStatus(els.createStatus, error.message, false);
  } finally {
    creating = false;
    els.createRoomBtn.disabled = false;
  }
}

async function joinRoom() {
  const player = els.joinName.value.trim();
  const room = els.roomCode.value.trim().toUpperCase();
  if (!player || !room) {
    setStatus(els.joinStatus, "Informe nome e codigo.", false);
    return;
  }
  try {
    const data = await api.joinRoom(player, room, els.joinPassword.value.trim());
    saveSession(player, data.code, data.token);
    setStatus(els.joinStatus, `Entrou na sala ${data.code}.`, true);
    showWaiting(data);
    await loadRooms();
  } catch (error) {
    setStatus(els.joinStatus, error.message, false);
  }
}

async function startMatch() {
  if (!activeRoom || goingToBoard) return;
  const player = localStorage.getItem("rpg_player") || els.playerName.value.trim();
  try {
    const room = (await api.room(activeRoom)).room;
    if ((room.players || []).length < 2) {
      setStatus(els.createStatus, "E preciso pelo menos dois jogadores.", false);
      return;
    }
    await api.startMatch(activeRoom, selectedClasses(), localStorage.getItem("rpg_token"));
    saveSession(player, activeRoom, localStorage.getItem("rpg_token"));
    goToBoard(activeRoom);
  } catch (error) {
    setStatus(els.createStatus, error.message, false);
  }
}

async function loadRooms() {
  try {
    const data = await api.rooms();
    const rooms = data.rooms || [];
    if (!rooms.length) {
      els.roomsList.innerHTML = "<div class='room-item'>Nenhuma sala ativa.</div>";
      return;
    }
    els.roomsList.innerHTML = "";
    rooms.forEach((room) => {
      const item = document.createElement("div");
      item.className = "room-item";
      item.innerHTML = `<div><div class="code">${room.code}</div><div>${(room.players || []).map((p) => p.name || p).join(", ")}</div></div><div>${room.status}${room.protected ? " · senha" : ""}</div>`;
      item.addEventListener("click", () => {
        els.roomCode.value = room.code;
        api.room(room.code).then((data) => showWaiting(data.room));
      });
      els.roomsList.appendChild(item);
    });
  } catch (error) {
    console.error(error);
  }
}

document.getElementById("createRoomBtn").addEventListener("click", (event) => {
  event.preventDefault();
  createRoom();
});
document.getElementById("joinRoomBtn").addEventListener("click", (event) => {
  event.preventDefault();
  joinRoom();
});
document.getElementById("startMatchBtn").addEventListener("click", (event) => {
  event.preventDefault();
  startMatch();
});
document.getElementById("refreshRoomsBtn").addEventListener("click", (event) => {
  event.preventDefault();
  loadRooms();
});

loadRooms();
setInterval(loadRooms, 5000);

const savedPlayer = localStorage.getItem("rpg_player");
const savedRoom = localStorage.getItem("rpg_room");
if (savedPlayer) {
  els.playerName.value = savedPlayer;
  els.joinName.value = savedPlayer;
}
if (savedRoom) {
  els.roomCode.value = savedRoom;
  api.room(savedRoom).then((data) => {
    if (data.room && data.room.status === "waiting") {
      showWaiting(data.room);
    } else if (data.room && data.room.status === "started") {
      goToBoard(data.room.code);
    }
  }).catch(() => {
    localStorage.removeItem("rpg_room");
  });
}
