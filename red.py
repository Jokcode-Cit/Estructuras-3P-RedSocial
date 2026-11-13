"""Lógica de negocio: estructuras en memoria + persistencia.."""
from datetime import datetime
from modelos import Usuario, Publicacion, hash_password
from persistencia import Persistencia

MAX_CARACTERES = 280


class RedSocial:
    def __init__(self, carpeta: str = "datos"):
        self.persistencia = Persistencia(carpeta)
        # --- Estructuras de datos en memoria ---
        self.usuarios: list[Usuario] = []             # lista dinámica de usuarios
        self.publicaciones: list[Publicacion] = []    # historial de publicaciones
        self.amistades: dict[int, set[int]] = {}      # grafo: lista de adyacencia
        self.solicitudes: dict[int, set[int]] = {}    # {receptor_id: {emisor_ids}} pendientes
        self._por_id: dict[int, Usuario] = {}         # índice para búsquedas O(1)
        self.cargar_todo()

    # ------------------------------------------------------------ persistencia
    def cargar_todo(self) -> None:
        p = self.persistencia
        self.usuarios = [Usuario.from_dict(d) for d in p.cargar("usuarios.json", [])]
        self.publicaciones = [Publicacion.from_dict(d) for d in p.cargar("publicaciones.json", [])]
        raw = p.cargar("amistades.json", {})
        self.amistades = {int(k): {int(x) for x in v} for k, v in raw.items()}
        raw = p.cargar("solicitudes.json", {})
        self.solicitudes = {int(k): {int(x) for x in v} for k, v in raw.items()}
        self._por_id = {u.id: u for u in self.usuarios}

    def guardar_todo(self) -> None:
        p = self.persistencia
        p.guardar("usuarios.json", [u.to_dict() for u in self.usuarios])
        p.guardar("publicaciones.json", [x.to_dict() for x in self.publicaciones])
        p.guardar("amistades.json", {str(k): sorted(v) for k, v in self.amistades.items()})
        p.guardar("solicitudes.json", {str(k): sorted(v) for k, v in self.solicitudes.items() if v})

    # ---------------------------------------------------------- autenticación
    def registrar(self, nombre: str, usuario: str, password: str) -> Usuario:
        nombre, usuario = nombre.strip(), usuario.strip()
        if not nombre or not usuario or not password:
            raise ValueError("Todos los campos son obligatorios.")
        if " " in usuario:
            raise ValueError("El usuario no puede contener espacios.")
        if len(password) < 4:
            raise ValueError("La contraseña debe tener al menos 4 caracteres.")
        if any(u.usuario.lower() == usuario.lower() for u in self.usuarios):
            raise ValueError("Ese nombre de usuario ya existe.")
        nuevo_id = max((u.id for u in self.usuarios), default=0) + 1
        nuevo = Usuario(nuevo_id, nombre, usuario, hash_password(password))
        self.usuarios.append(nuevo)
        self._por_id[nuevo.id] = nuevo
        self.amistades.setdefault(nuevo.id, set())
        self.guardar_todo()
        return nuevo

    def login(self, usuario: str, password: str) -> Usuario:
        usuario = usuario.strip()
        if not usuario or not password:
            raise ValueError("Ingresa usuario y contraseña.")
        h = hash_password(password)
        for u in self.usuarios:
            if u.usuario.lower() == usuario.lower() and u.password_hash == h:
                return u
        raise ValueError("Usuario o contraseña incorrectos.")

    def usuario_por_id(self, uid: int):
        return self._por_id.get(uid)

    # ------------------------------------------------------------- búsqueda
    def buscar(self, texto: str, excluir_id: int) -> list[Usuario]:
        t = texto.strip().lower()
        return [u for u in self.usuarios
                if u.id != excluir_id and (t in u.nombre.lower() or t in u.usuario.lower())]

    # --------------------------------------------------------------- amistades
    def son_amigos(self, a: int, b: int) -> bool:
        return b in self.amistades.get(a, set())

    def estado_relacion(self, a: int, b: int) -> str:
        """Relación de `a` hacia `b`: 'amigo', 'enviada', 'recibida' o 'ninguna'."""
        if self.son_amigos(a, b):
            return "amigo"
        if a in self.solicitudes.get(b, set()):
            return "enviada"      # a le envió solicitud a b
        if b in self.solicitudes.get(a, set()):
            return "recibida"     # b le envió solicitud a a
        return "ninguna"

    def _crear_amistad(self, a: int, b: int) -> None:
        # Amistad mutua: arista en ambos sentidos del grafo
        self.amistades.setdefault(a, set()).add(b)
        self.amistades.setdefault(b, set()).add(a)

    def eliminar_amigo(self, a: int, b: int) -> None:
        self.amistades.get(a, set()).discard(b)
        self.amistades.get(b, set()).discard(a)
        self.guardar_todo()

    def amigos_de(self, uid: int) -> list[Usuario]:
        amigos = [self._por_id[i] for i in self.amistades.get(uid, set()) if i in self._por_id]
        return sorted(amigos, key=lambda u: u.nombre.lower())

    # ------------------------------------------------------ solicitudes de amistad
    def enviar_solicitud(self, emisor: int, receptor: int) -> str:
        """Devuelve 'enviada' o 'aceptada' (si la otra persona ya te había escrito)."""
        if emisor == receptor:
            raise ValueError("No puedes enviarte una solicitud a ti mismo.")
        if receptor not in self._por_id:
            raise ValueError("El usuario no existe.")
        estado = self.estado_relacion(emisor, receptor)
        if estado == "amigo":
            raise ValueError("Ya son amigos.")
        if estado == "enviada":
            raise ValueError("Ya enviaste una solicitud a esta persona.")
        if estado == "recibida":          # solicitudes cruzadas: se acepta sola
            self.aceptar_solicitud(emisor, receptor)
            return "aceptada"
        self.solicitudes.setdefault(receptor, set()).add(emisor)
        self.guardar_todo()
        return "enviada"

    def aceptar_solicitud(self, receptor: int, emisor: int) -> None:
        if emisor not in self.solicitudes.get(receptor, set()):
            raise ValueError("Esa solicitud ya no existe.")
        self.solicitudes[receptor].discard(emisor)
        self.solicitudes.get(emisor, set()).discard(receptor)
        self._crear_amistad(receptor, emisor)
        self.guardar_todo()

    def rechazar_solicitud(self, receptor: int, emisor: int) -> None:
        self.solicitudes.get(receptor, set()).discard(emisor)
        self.guardar_todo()

    def cancelar_solicitud(self, emisor: int, receptor: int) -> None:
        self.solicitudes.get(receptor, set()).discard(emisor)
        self.guardar_todo()

    def solicitudes_recibidas(self, uid: int) -> list[Usuario]:
        us = [self._por_id[i] for i in self.solicitudes.get(uid, set()) if i in self._por_id]
        return sorted(us, key=lambda u: u.nombre.lower())

    def solicitudes_enviadas(self, uid: int) -> list[Usuario]:
        us = [self._por_id[r] for r, emisores in self.solicitudes.items()
              if uid in emisores and r in self._por_id]
        return sorted(us, key=lambda u: u.nombre.lower())

    # ----------------------------------------------------- sugerencias (grafo)
    def sugerencias(self, uid: int) -> list[tuple[Usuario, list[Usuario]]]:
        """'Amigos de tus amigos': recorre los vecinos de los vecinos en el grafo.
        Devuelve [(persona, [amigos en común])] ordenado por más amigos en común."""
        mis_amigos = self.amistades.get(uid, set())
        comunes: dict[int, list[Usuario]] = {}
        for amigo_id in mis_amigos:
            for candidato in self.amistades.get(amigo_id, set()):
                if (candidato == uid or candidato in mis_amigos
                        or candidato not in self._por_id
                        or self.estado_relacion(uid, candidato) != "ninguna"):
                    continue
                comunes.setdefault(candidato, []).append(self._por_id[amigo_id])
        orden = sorted(comunes.items(),
                       key=lambda kv: (-len(kv[1]), self._por_id[kv[0]].nombre.lower()))
        return [(self._por_id[i], sorted(c, key=lambda u: u.nombre.lower())) for i, c in orden]

    # --------------------------------------------------------- publicaciones
    def publicar(self, autor_id: int, texto: str) -> Publicacion:
        texto = texto.strip()
        if not texto:
            raise ValueError("Escribe algo antes de publicar.")
        if len(texto) > MAX_CARACTERES:
            raise ValueError(f"Máximo {MAX_CARACTERES} caracteres (llevas {len(texto)}).")
        nuevo_id = max((p.id for p in self.publicaciones), default=0) + 1
        pub = Publicacion(nuevo_id, autor_id, texto, datetime.now().isoformat(timespec="seconds"))
        self.publicaciones.append(pub)
        self.guardar_todo()
        return pub

    def _pub_por_id(self, pub_id: int):
        return next((p for p in self.publicaciones if p.id == pub_id), None)

    def eliminar_publicacion(self, uid: int, pub_id: int) -> None:
        pub = self._pub_por_id(pub_id)
        if pub is None:
            raise ValueError("La publicación ya no existe.")
        if pub.autor_id != uid:
            raise ValueError("Solo puedes eliminar tus propias publicaciones.")
        self.publicaciones.remove(pub)
        self.guardar_todo()

    def alternar_like(self, uid: int, pub_id: int) -> bool:
        """Da o quita 'me gusta'. Devuelve True si quedó con me gusta."""
        pub = self._pub_por_id(pub_id)
        if pub is None:
            raise ValueError("La publicación ya no existe.")
        if pub.autor_id != uid and not self.son_amigos(uid, pub.autor_id):
            raise ValueError("Solo puedes dar me gusta a publicaciones tuyas o de tus amigos.")
        if uid in pub.likes:
            pub.likes.remove(uid)
        else:
            pub.likes.append(uid)
        self.guardar_todo()
        return uid in pub.likes

    def publicaciones_de(self, uid: int) -> list[Publicacion]:
        """Perfil: solo las publicaciones de esa persona, de la más reciente a la más antigua."""
        pubs = [p for p in self.publicaciones if p.autor_id == uid]
        return sorted(pubs, key=lambda p: (p.timestamp, p.id), reverse=True)

    def muro(self, uid: int) -> list[Publicacion]:
        """Publicaciones propias + de amigos, de la más reciente a la más antigua."""
        visibles = {uid} | self.amistades.get(uid, set())
        pubs = [p for p in self.publicaciones if p.autor_id in visibles]
        return sorted(pubs, key=lambda p: (p.timestamp, p.id), reverse=True)

    # ------------------------------------------------------------ estadísticas
    def estadisticas(self, uid: int) -> dict:
        return {
            "amigos": len(self.amigos_de(uid)),
            "publicaciones": len(self.publicaciones_de(uid)),
            "solicitudes": len(self.solicitudes_recibidas(uid)),
        }
