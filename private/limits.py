import secrets
import time
from threading import Lock

MAX_NAME = 24
MAX_ROOM = 8
MAX_PASSWORD = 16
MAX_BODY = 4096
MAX_MAGIC = 40
ALLOWED_ACTIONS = {"attack", "shop", "equip", "use_magic"}
ALLOWED_CLASSES = {"Guerreiro", "Mago", "Arqueiro", "Paladino", "Clerigo"}


def sanitize_name(name):
    name = " ".join(str(name or "").split())
    if not name or len(name) > MAX_NAME:
        raise ValueError("Informe um nome válido.")
    if any(caractere in name for caractere in "<>\"'\\/;{}()[]"):
        raise ValueError("O nome contém caracteres inválidos.")
    return name


def sanitize_room(code):
    code = str(code or "").strip().upper()
    if not code or len(code) > MAX_ROOM or not code.isalnum():
        raise ValueError("Código de sala inválido.")
    return code


def sanitize_password(password, required=False):
    password = str(password or "").strip()
    if not password:
        if required:
            raise ValueError("Informe a senha da sala.")
        return ""
    if not 4 <= len(password) <= MAX_PASSWORD:
        raise ValueError("A senha da sala deve ter entre 4 e 16 caracteres.")
    if any(caractere in password for caractere in "<>\"'\\/;{}()[]"):
        raise ValueError("A senha contém caracteres inválidos.")
    return password


def sanitize_magic(name):
    name = " ".join(str(name or "").split())
    if len(name) > MAX_MAGIC:
        raise ValueError("Nome de magia inválido.")
    return name


def issue_token():
    return secrets.token_urlsafe(24)


def token_matches(stored, given):
    stored = str(stored or "")
    given = str(given or "")
    return bool(stored) and len(stored) == len(given) and secrets.compare_digest(stored, given)


class RateLimiter:
    def __init__(self, limit=20, window=10):
        self.limit = limit
        self.window = window
        self._hits = {}
        self._lock = Lock()

    def check(self, key):
        agora = time.monotonic()
        with self._lock:
            marcas = [marca for marca in self._hits.get(key, []) if agora - marca < self.window]
            if len(marcas) >= self.limit:
                return False
            marcas.append(agora)
            self._hits[key] = marcas
            return True
