"""Genera datos/ con 5 usuarios, amistades, solicitudes, publicaciones y likes de prueba.
Uso: python generar_datos_prueba.py   (sobrescribe la carpeta datos/)"""
from datetime import datetime, timedelta
from modelos import Usuario, Publicacion, hash_password
from persistencia import Persistencia

ahora = datetime.now().replace(microsecond=0)
def hace(**kw): return (ahora - timedelta(**kw)).isoformat()

usuarios = [
    Usuario(1, "Ana Martínez", "ana", hash_password("1234")),
    Usuario(2, "Carlos Rojas", "carlos", hash_password("1234")),
    Usuario(3, "Lucía Fernández", "lucia", hash_password("1234")),
    Usuario(4, "Diego Vargas", "diego", hash_password("1234")),
    Usuario(5, "Valeria Soto", "valeria", hash_password("1234")),
]
publicaciones = [
    Publicacion(1, 1, "¡Hola a todos! Estrenando UniConecta.", hace(days=3), [2, 3]),
    Publicacion(2, 2, "¿Alguien tiene los apuntes de Estructuras de Datos?", hace(days=2, hours=5), [1]),
    Publicacion(3, 3, "Hoy hay estudio grupal en la biblioteca a las 3pm.", hace(days=2), [1, 2]),
    Publicacion(4, 1, "Ya terminé el proyecto de listas enlazadas.", hace(days=1, hours=4), [2]),
    Publicacion(5, 4, "Busco equipo para el hackathon del viernes.", hace(days=1), [2]),
    Publicacion(6, 2, "Gracias por la ayuda con grafos, Ana.", hace(hours=6), [1, 4]),
    Publicacion(7, 3, "Recuerden: examen parcial el lunes.", hace(hours=2), []),
    Publicacion(8, 5, "Soy nueva por aquí, ¡hola a todos!", hace(hours=1), []),
]
# Grafo de amistades (no dirigido): ana-carlos, ana-lucia, carlos-diego
amistades = {1: {2, 3}, 2: {1, 4}, 3: {1}, 4: {2}, 5: set()}
# Solicitudes pendientes {receptor: {emisores}}: valeria -> ana, diego -> lucia
solicitudes = {1: {5}, 3: {4}}

p = Persistencia("datos")
p.guardar("usuarios.json", [u.to_dict() for u in usuarios])
p.guardar("publicaciones.json", [x.to_dict() for x in publicaciones])
p.guardar("amistades.json", {str(k): sorted(v) for k, v in amistades.items()})
p.guardar("solicitudes.json", {str(k): sorted(v) for k, v in solicitudes.items()})
print("Datos de prueba generados en datos/")