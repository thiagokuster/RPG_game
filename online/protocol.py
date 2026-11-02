import json
import socket

HEADER_SIZE = 4
MAX_MESSAGE = 4096


def encode_message(payload):
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def decode_message(raw):
    if isinstance(raw, str):
        raw = raw.encode("utf-8")

    if len(raw) >= HEADER_SIZE and raw[:HEADER_SIZE] != b'\x00' * HEADER_SIZE:
        try:
            length = int.from_bytes(raw[:HEADER_SIZE], byteorder="big")
            if length == len(raw) - HEADER_SIZE:
                raw = raw[HEADER_SIZE:]
        except ValueError:
            pass

    return json.loads(raw.decode("utf-8"))


def send_message(conn, payload):
    raw = encode_message(payload)
    if len(raw) > MAX_MESSAGE:
        raise ValueError("Mensagem grande demais.")
    conn.sendall(len(raw).to_bytes(HEADER_SIZE, byteorder="big") + raw)


def _recv_exact(conn, size):
    body = bytearray()
    while len(body) < size:
        chunk = conn.recv(size - len(body))
        if not chunk:
            return None
        body.extend(chunk)
    return bytes(body)


def receive_message(conn):
    try:
        header = _recv_exact(conn, HEADER_SIZE)
    except (socket.timeout, OSError):
        return None

    if not header:
        return None

    length = int.from_bytes(header, byteorder="big")
    if length <= 0 or length > MAX_MESSAGE:
        return None

    try:
        body = _recv_exact(conn, length)
    except (socket.timeout, OSError):
        return None
    if body is None:
        return None

    return decode_message(body)
