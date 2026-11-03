export const QUEUE_TYPES = ["ataque", "magia", "morte", "cura", "onda"];

export function fingerprint(room) {
  const names = (room.players || [])
    .filter((player) => !player.npc)
    .map((player) => player.name)
    .join(",");
  return `${room.code || ""}|${names}`;
}

export function shouldResetMatch(room, matchKey, lastSeenId) {
  const key = fingerprint(room);
  const ids = (room.eventos || []).map((ev) => ev.id).filter((id) => id != null);
  const maxId = ids.length ? Math.max(...ids) : 0;
  return {
    key,
    maxId,
    reset: key !== matchKey || Boolean(maxId && maxId < lastSeenId),
  };
}

export function collectFreshEvents(eventos, lastSeenId, primed, types = QUEUE_TYPES) {
  const allowed = types instanceof Set ? types : new Set(types);
  let maxId = lastSeenId;
  const fresh = [];
  for (const ev of eventos || []) {
    const id = ev.id;
    if (id != null) maxId = Math.max(maxId, id);
    if (id != null && id <= lastSeenId) continue;
    if (allowed.has(ev.tipo) || ev.critico) fresh.push(ev);
  }
  if (!primed) {
    return { lastSeenId: maxId, primed: true, fresh: [] };
  }
  return { lastSeenId: maxId, primed: true, fresh };
}
