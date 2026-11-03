const api = {
  async request(url, options = {}) {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Falha na comunicacao com o servidor.");
    }
    return data;
  },

  rooms() {
    return this.request("/api/rooms");
  },

  room(code) {
    return this.request(`/api/room?code=${encodeURIComponent(code)}`);
  },

  createRoom(player, password) {
    return this.request("/api/create-room", {
      method: "POST",
      body: JSON.stringify({ player, password }),
    });
  },

  joinRoom(player, room, password) {
    return this.request("/api/join-room", {
      method: "POST",
      body: JSON.stringify({ player, room, password }),
    });
  },

  startMatch(room, classes, token, modo) {
    return this.request("/api/start-match", {
      method: "POST",
      body: JSON.stringify({ room, classes, token, modo: modo || "pvp" }),
    });
  },

  action(payload) {
    return this.request("/api/action", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  stream(code, onEvent) {
    const source = new EventSource(`/api/stream?code=${encodeURIComponent(code)}`);
    source.onmessage = (event) => {
      try {
        onEvent(JSON.parse(event.data));
      } catch (error) {
        console.error(error);
      }
    };
    return source;
  },
};
