"""Modelos de datos de la red social."""
from dataclasses import dataclass, field, asdict
import hashlib


def hash_password(password: str) -> str:
    """Las contraseñas nunca se guardan en texto plano."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@dataclass
class Usuario:
    id: int
    nombre: str
    usuario: str
    password_hash: str

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Usuario":
        return Usuario(int(d["id"]), d["nombre"], d["usuario"], d["password_hash"])


@dataclass
class Publicacion:
    id: int
    autor_id: int
    texto: str
    timestamp: str  # formato ISO: 2026-11-11T14:30:00
    likes: list[int] = field(default_factory=list)  # ids de quienes dieron "me gusta"

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Publicacion":
        return Publicacion(int(d["id"]), int(d["autor_id"]), d["texto"], d["timestamp"],
                           [int(x) for x in d.get("likes", [])])