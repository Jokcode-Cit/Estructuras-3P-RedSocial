"""Lectura y escritura de archivos JSON (sin bases de datos)."""
import json
import os


class Persistencia:
    def __init__(self, carpeta: str = "datos"):
        self.carpeta = carpeta
        os.makedirs(self.carpeta, exist_ok=True)

    def _ruta(self, archivo: str) -> str:
        return os.path.join(self.carpeta, archivo)

    def cargar(self, archivo: str, por_defecto):
        """Devuelve el contenido del archivo o `por_defecto` si no existe o está dañado."""
        ruta = self._ruta(archivo)
        if not os.path.exists(ruta):
            return por_defecto
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return por_defecto

    def guardar(self, archivo: str, datos) -> None:
        """Escritura atómica: se escribe a un temporal y luego se reemplaza,
        así un cierre inesperado no corrompe el archivo."""
        ruta = self._ruta(archivo)
        tmp = ruta + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        os.replace(tmp, ruta)