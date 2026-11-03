import assert from "node:assert/strict";
import { collectFreshEvents, fingerprint, shouldResetMatch } from "../frontend/js/arena3d_match.js";

const anaBruno = [
  { name: "Ana", npc: false },
  { name: "Bruno", npc: false },
];

const waiting = { code: "SALA1", status: "started", players: [...anaBruno], eventos: [{ id: 3, tipo: "ataque" }] };
const withBoss = {
  ...waiting,
  players: [...anaBruno, { name: "Chefe da onda 1", npc: true }],
  eventos: [{ id: 4, tipo: "onda", onda: 2 }],
};
const finished = { ...withBoss, status: "finished", eventos: [{ id: 5, tipo: "morte", de: "Chefe da onda 1" }] };
const rematch = { code: "SALA1", status: "started", players: [...anaBruno], eventos: [{ id: 1, tipo: "onda", onda: 1 }] };
const otherRoom = { code: "SALA2", status: "started", players: [...anaBruno], eventos: [{ id: 1, tipo: "ataque" }] };

assert.equal(fingerprint(waiting), "SALA1|Ana,Bruno");
assert.equal(fingerprint(withBoss), fingerprint(waiting));
assert.equal(fingerprint(finished), fingerprint(waiting));
assert.notEqual(fingerprint(otherRoom), fingerprint(waiting));

assert.equal(shouldResetMatch(withBoss, fingerprint(waiting), 3).reset, false);
assert.equal(shouldResetMatch(finished, fingerprint(waiting), 4).reset, false);
assert.equal(shouldResetMatch(rematch, fingerprint(waiting), 40).reset, true);
assert.equal(shouldResetMatch(otherRoom, fingerprint(waiting), 3).reset, true);

const first = collectFreshEvents(
  [
    { id: 1, tipo: "onda" },
    { id: 2, tipo: "ataque" },
  ],
  0,
  false
);
assert.deepEqual(first.fresh, []);
assert.equal(first.lastSeenId, 2);
assert.equal(first.primed, true);

const later = collectFreshEvents(
  [
    { id: 1, tipo: "onda" },
    { id: 2, tipo: "ataque" },
    { id: 3, tipo: "morte", de: "Chefe da onda 1" },
    { id: 4, tipo: "onda", onda: 2 },
  ],
  2,
  true
);
assert.deepEqual(
  later.fresh.map((ev) => ev.tipo),
  ["morte", "onda"]
);

console.log("ok");
