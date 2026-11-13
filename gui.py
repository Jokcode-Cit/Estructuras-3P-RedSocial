"""Interfaz gráfica (Tkinter).""" #últimos cambiosbuscarTab, amigosTab, principalFrame.
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from red import RedSocial, MAX_CARACTERES

COLOR_PRIMARIO = "#2563eb"
FONDO = "#f1f5f9"
BORDE = "#e2e8f0"
GRIS = "#6b7280"
VERDE = "#059669"
ROJO = "#dc2626"
FUENTE = ("Segoe UI", 10)
FUENTE_NEGRITA = ("Segoe UI", 10, "bold")
FUENTE_PEQUENA = ("Segoe UI", 9)

ETIQUETA_ESTADO = {
    "amigo": "✔ Amigo",
    "enviada": "Solicitud enviada",
    "recibida": "Te envió solicitud",
    "ninguna": "",
}


def formatear_fecha(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return iso


def id_seleccionado(tabla: ttk.Treeview, mensaje: str):
    """Devuelve el id de la fila seleccionada o avisa si no hay ninguna."""
    sel = tabla.selection()
    if not sel:
        messagebox.showinfo("Selecciona una fila", mensaje)
        return None
    return int(sel[0])


def enviar_solicitud(principal: "PrincipalFrame", uid: int) -> None:
    """Acción compartida por Buscar, Sugerencias y Perfil."""
    red = principal.red
    try:
        resultado = red.enviar_solicitud(principal.yo.id, uid)
    except ValueError as e:
        messagebox.showinfo("Solicitud de amistad", str(e))
        return
    nombre = red.usuario_por_id(uid).nombre
    if resultado == "aceptada":
        messagebox.showinfo("Solicitud de amistad",
                            f"{nombre} ya te había enviado una solicitud: ¡ahora son amigos!")
    else:
        messagebox.showinfo("Solicitud de amistad", f"Solicitud enviada a {nombre}.")
    principal.refrescar_todo()


def crear_tabla(master, columnas, **kw) -> ttk.Treeview:
    """columnas: lista de (clave, título, ancho)."""
    tabla = ttk.Treeview(master, columns=[c[0] for c in columnas],
                         show="headings", selectmode="browse", **kw)
    for clave, titulo, ancho in columnas:
        tabla.heading(clave, text=titulo)
        tabla.column(clave, width=ancho)
    return tabla


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UniConecta - Red Social Estudiantil")
        self.geometry("920x680")
        self.minsize(780, 560)
        self.option_add("*Font", FUENTE)
        ttk.Style(self).configure("Treeview", rowheight=26)
        self.red = RedSocial()
        self.usuario_actual = None
        self._frame = None
        self.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.mostrar_login()

    def _cambiar(self, frame):
        if self._frame is not None:
            self._frame.destroy()
        self._frame = frame
        frame.pack(fill="both", expand=True)

    def mostrar_login(self, usuario_prellenado: str = ""):
        self.usuario_actual = None
        self._cambiar(LoginFrame(self, usuario_prellenado))

    def mostrar_principal(self):
        self._cambiar(PrincipalFrame(self))

    def cerrar(self):
        self.red.guardar_todo()
        self.destroy()


# ============================================================ LOGIN / REGISTRO
class LoginFrame(ttk.Frame):
    def __init__(self, app: App, usuario_prellenado: str = ""):
        super().__init__(app)
        self.app = app
        centro = ttk.Frame(self)
        centro.place(relx=0.5, rely=0.45, anchor="center")

        tk.Label(centro, text="UniConecta", font=("Segoe UI", 26, "bold"),
                 fg=COLOR_PRIMARIO).grid(row=0, column=0, columnspan=2, pady=(0, 4))
        ttk.Label(centro, text="La red social de tu comunidad estudiantil").grid(
            row=1, column=0, columnspan=2, pady=(0, 24))

        ttk.Label(centro, text="Usuario:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.e_user = ttk.Entry(centro, width=28)
        self.e_user.grid(row=2, column=1, pady=6)
        self.e_user.insert(0, usuario_prellenado)

        ttk.Label(centro, text="Contraseña:").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        self.e_pass = ttk.Entry(centro, width=28, show="•")
        self.e_pass.grid(row=3, column=1, pady=6)

        ttk.Button(centro, text="Iniciar sesión", command=self.iniciar).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(16, 6))
        ttk.Button(centro, text="Crear cuenta nueva", command=self.abrir_registro).grid(
            row=5, column=0, columnspan=2, sticky="ew")

        self.app.bind("<Return>", lambda e: self.iniciar())
        (self.e_pass if usuario_prellenado else self.e_user).focus_set()

    def destroy(self):
        self.app.unbind("<Return>")
        super().destroy()

    def iniciar(self):
        try:
            u = self.app.red.login(self.e_user.get(), self.e_pass.get())
        except ValueError as e:
            messagebox.showwarning("No se pudo iniciar sesión", str(e))
            self.e_pass.delete(0, "end")
            return
        self.app.usuario_actual = u
        self.app.mostrar_principal()

    def abrir_registro(self):
        VentanaRegistro(self.app, self)


class VentanaRegistro(tk.Toplevel):
    def __init__(self, app: App, login: LoginFrame):
        super().__init__(app)
        self.app, self.login = app, login
        self.title("Crear cuenta")
        self.resizable(False, False)
        self.transient(app)
        self.grab_set()

        marco = ttk.Frame(self, padding=24)
        marco.pack()
        self.campos = {}
        for i, (clave, etiqueta, oculto) in enumerate([
            ("nombre", "Nombre completo:", False),
            ("usuario", "Usuario:", False),
            ("password", "Contraseña:", True),
            ("confirmar", "Confirmar contraseña:", True),
        ]):
            ttk.Label(marco, text=etiqueta).grid(row=i, column=0, sticky="e", padx=6, pady=6)
            e = ttk.Entry(marco, width=28, show="•" if oculto else "")
            e.grid(row=i, column=1, pady=6)
            self.campos[clave] = e
        self.campos["nombre"].focus_set()

        botones = ttk.Frame(marco)
        botones.grid(row=4, column=0, columnspan=2, pady=(16, 0))
        ttk.Button(botones, text="Registrarme", command=self.registrar).pack(side="left", padx=6)
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="left", padx=6)
        self.bind("<Return>", lambda e: self.registrar())
        self.bind("<Escape>", lambda e: self.destroy())

    def registrar(self):
        v = {k: e.get() for k, e in self.campos.items()}
        if v["password"] != v["confirmar"]:
            messagebox.showwarning("Registro", "Las contraseñas no coinciden.", parent=self)
            return
        try:
            u = self.app.red.registrar(v["nombre"], v["usuario"], v["password"])
        except ValueError as e:
            messagebox.showwarning("Registro", str(e), parent=self)
            return
        messagebox.showinfo("Registro", f"¡Cuenta creada! Ya puedes iniciar sesión, {u.nombre}.", parent=self)
        self.destroy()
        self.app.mostrar_login(u.usuario)


# ===================================================== COMPONENTES DE PUBLICACIONES
class ListaDesplazable(ttk.Frame):
    """Contenedor con scroll vertical donde se apilan tarjetas."""

    def __init__(self, master):
        super().__init__(master)
        self.canvas = tk.Canvas(self, highlightthickness=0, background=FONDO)
        barra = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.interior = tk.Frame(self.canvas, background=FONDO)
        self._ventana = self.canvas.create_window((0, 0), window=self.interior, anchor="nw")
        self.interior.bind("<Configure>",
                           lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._ajustar_ancho)
        self._etiquetas = []   # etiquetas cuyo salto de línea depende del ancho

        # Rueda del mouse (Windows/Mac: MouseWheel, Linux: Button-4/5)
        top = self.winfo_toplevel()
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            top.bind(ev, self._rueda, add="+")

    def _ajustar_ancho(self, e):
        self.canvas.itemconfigure(self._ventana, width=e.width)
        for lbl in self._etiquetas:
            lbl.configure(wraplength=max(e.width - 70, 100))

    def _rueda(self, e):
        try:
            w = self.winfo_containing(e.x_root, e.y_root)
        except tk.TclError:
            return
        while w is not None and w is not self:
            w = w.master
        if w is None:      # el mouse no está sobre esta lista
            return
        if e.num == 4:
            paso = -1
        elif e.num == 5:
            paso = 1
        else:
            paso = -1 if e.delta > 0 else 1
        self.canvas.yview_scroll(paso, "units")

    def limpiar(self):
        for w in self.interior.winfo_children():
            w.destroy()
        self._etiquetas = []
        self.canvas.yview_moveto(0)

    def registrar_etiqueta(self, lbl):
        self._etiquetas.append(lbl)
        lbl.configure(wraplength=max(self.canvas.winfo_width() - 70, 100))

    def mensaje_vacio(self, texto: str):
        lbl = tk.Label(self.interior, text=texto, bg=FONDO, fg=GRIS, justify="center")
        lbl.pack(pady=40)


def crear_tarjeta(lista: ListaDesplazable, red: RedSocial, yo, pub, al_cambiar,
                  interactivo: bool = True) -> None:
    """Dibuja una publicación como tarjeta con 'me gusta' y 'eliminar' (si es tuya)."""
    autor = red.usuario_por_id(pub.autor_id)
    if autor is None:
        return
    es_mia = autor.id == yo.id

    tarjeta = tk.Frame(lista.interior, background="white",
                       highlightbackground=BORDE, highlightthickness=1)
    tarjeta.pack(fill="x", padx=8, pady=5)

    cab = tk.Frame(tarjeta, bg="white")
    cab.pack(fill="x", padx=12, pady=(10, 0))
    tk.Label(cab, text="Tú" if es_mia else f"{autor.nombre} (@{autor.usuario})",
             bg="white", fg=VERDE if es_mia else COLOR_PRIMARIO,
             font=FUENTE_NEGRITA).pack(side="left")
    tk.Label(cab, text=formatear_fecha(pub.timestamp), bg="white", fg=GRIS,
             font=FUENTE_PEQUENA).pack(side="right")

    cuerpo = tk.Label(tarjeta, text=pub.texto, bg="white", justify="left", anchor="w")
    cuerpo.pack(fill="x", padx=12, pady=8)
    lista.registrar_etiqueta(cuerpo)

    pie = tk.Frame(tarjeta, bg="white")
    pie.pack(fill="x", padx=12, pady=(0, 10))

    n = len(pub.likes)
    me_gusta = yo.id in pub.likes

    def alternar():
        try:
            red.alternar_like(yo.id, pub.id)
        except ValueError as e:
            messagebox.showwarning("Me gusta", str(e))
            return
        al_cambiar()

    def eliminar():
        if messagebox.askyesno("Eliminar publicación", "¿Seguro que quieres eliminar esta publicación?"):
            try:
                red.eliminar_publicacion(yo.id, pub.id)
            except ValueError as e:
                messagebox.showwarning("Eliminar", str(e))
                return
            al_cambiar()

    if interactivo:
        tk.Button(pie, text=f"♥ {'Te gusta' if me_gusta else 'Me gusta'} ({n})",
                  command=alternar, relief="flat", cursor="hand2", bg="white",
                  activebackground=BORDE, fg=ROJO if me_gusta else GRIS,
                  font=FUENTE_NEGRITA if me_gusta else FUENTE).pack(side="left")
    else:
        tk.Label(pie, text=f"♥ {n}", bg="white", fg=GRIS).pack(side="left")

    if es_mia:
        tk.Button(pie, text="✕ Eliminar", command=eliminar, relief="flat", cursor="hand2",
                  bg="white", activebackground=BORDE, fg=GRIS).pack(side="right")


# ================================================================ PANTALLA PRINCIPAL
class PrincipalFrame(ttk.Frame):
    def __init__(self, app: App):
        super().__init__(app)
        self.app = app
        self.red = app.red
        self.yo = app.usuario_actual

        barra = tk.Frame(self, bg=COLOR_PRIMARIO)
        barra.pack(fill="x")
        tk.Label(barra, text=f"Hola, {self.yo.nombre}  (@{self.yo.usuario})",
                 bg=COLOR_PRIMARIO, fg="white", font=("Segoe UI", 11, "bold")).pack(
            side="left", padx=14, pady=10)
        self.lbl_stats = tk.Label(barra, bg=COLOR_PRIMARIO, fg="white", font=FUENTE)
        self.lbl_stats.pack(side="left", padx=20)
        ttk.Button(barra, text="Cerrar sesión", command=self.cerrar_sesion).pack(
            side="right", padx=14, pady=8)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_muro = MuroTab(self.notebook, self)
        self.tab_buscar = BuscarTab(self.notebook, self)
        self.tab_solicitudes = SolicitudesTab(self.notebook, self)
        self.tab_amigos = AmigosTab(self.notebook, self)
        self.tab_sugerencias = SugerenciasTab(self.notebook, self)
        self.notebook.add(self.tab_muro, text="  Muro  ")
        self.notebook.add(self.tab_buscar, text="  Buscar personas  ")
        self.notebook.add(self.tab_solicitudes, text="  Solicitudes  ")
        self.notebook.add(self.tab_amigos, text="  Mis amigos  ")
        self.notebook.add(self.tab_sugerencias, text="  Sugerencias  ")
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refrescar_todo())
        self.refrescar_todo()

    def refrescar_todo(self):
        est = self.red.estadisticas(self.yo.id)
        self.lbl_stats.config(
            text=f"Amigos: {est['amigos']}   |   Publicaciones: {est['publicaciones']}"
                 f"   |   Solicitudes: {est['solicitudes']}")
        pendientes = est["solicitudes"]
        self.notebook.tab(self.tab_solicitudes,
                          text=f"  Solicitudes ({pendientes})  " if pendientes else "  Solicitudes  ")
        self.tab_muro.refrescar()
        self.tab_buscar.refrescar()
        self.tab_solicitudes.refrescar()
        self.tab_amigos.refrescar()
        self.tab_sugerencias.refrescar()

    def cerrar_sesion(self):
        self.red.guardar_todo()
        self.app.mostrar_login()


class MuroTab(ttk.Frame):
    def __init__(self, master, principal: PrincipalFrame):
        super().__init__(master, padding=10)
        self.p = principal

        ttk.Label(self, text="¿Qué estás pensando?").pack(anchor="w")
        self.entrada = tk.Text(self, height=4, wrap="word", relief="solid", borderwidth=1)
        self.entrada.pack(fill="x", pady=(4, 6))
        self.entrada.bind("<KeyRelease>", lambda e: self._contador())

        fila = ttk.Frame(self)
        fila.pack(fill="x")
        self.lbl_contador = ttk.Label(fila, text=f"0/{MAX_CARACTERES}")
        self.lbl_contador.pack(side="left")
        ttk.Button(fila, text="Publicar", command=self.publicar).pack(side="right")

        ttk.Separator(self).pack(fill="x", pady=10)
        self.lista = ListaDesplazable(self)
        self.lista.pack(fill="both", expand=True)

    def _contador(self):
        n = len(self.entrada.get("1.0", "end-1c"))
        self.lbl_contador.config(text=f"{n}/{MAX_CARACTERES}",
                                 foreground=ROJO if n > MAX_CARACTERES else "")

    def publicar(self):
        try:
            self.p.red.publicar(self.p.yo.id, self.entrada.get("1.0", "end-1c"))
        except ValueError as e:
            messagebox.showwarning("Publicar", str(e))
            return
        self.entrada.delete("1.0", "end")
        self._contador()
        self.p.refrescar_todo()

    def refrescar(self):
        red, yo = self.p.red, self.p.yo
        self.lista.limpiar()
        pubs = red.muro(yo.id)
        if not pubs:
            self.lista.mensaje_vacio("Aún no hay publicaciones.\n"
                                     "Escribe algo o agrega amigos para ver las suyas.")
        for pub in pubs:
            crear_tarjeta(self.lista, red, yo, pub, self.p.refrescar_todo)


class BuscarTab(ttk.Frame):
    def __init__(self, master, principal: PrincipalFrame):
        super().__init__(master, padding=10)
        self.p = principal

        fila = ttk.Frame(self)
        fila.pack(fill="x")
        ttk.Label(fila, text="Buscar por nombre o usuario:").pack(side="left")
        self.e_busqueda = ttk.Entry(fila)
        self.e_busqueda.pack(side="left", fill="x", expand=True, padx=8)
        self.e_busqueda.bind("<Return>", lambda e: self.refrescar())
        ttk.Button(fila, text="Buscar", command=self.refrescar).pack(side="left")

        self.tabla = crear_tabla(self, [("nombre", "Nombre", 280),
                                        ("usuario", "Usuario", 180),
                                        ("estado", "Estado", 160)])
        self.tabla.pack(fill="both", expand=True, pady=10)
        self.tabla.bind("<Double-1>", lambda e: self.ver_perfil())

        botones = ttk.Frame(self)
        botones.pack(fill="x")
        ttk.Button(botones, text="Enviar solicitud", command=self.enviar).pack(side="right")
        ttk.Button(botones, text="Ver perfil", command=self.ver_perfil).pack(side="right", padx=6)

    def refrescar(self):
        self.tabla.delete(*self.tabla.get_children())
        red, yo = self.p.red, self.p.yo
        for u in red.buscar(self.e_busqueda.get(), yo.id):
            estado = ETIQUETA_ESTADO[red.estado_relacion(yo.id, u.id)]
            self.tabla.insert("", "end", iid=str(u.id), values=(u.nombre, u.usuario, estado))

    def enviar(self):
        uid = id_seleccionado(self.tabla, "Selecciona una persona de la lista.")
        if uid is not None:
            enviar_solicitud(self.p, uid)

    def ver_perfil(self):
        uid = id_seleccionado(self.tabla, "Selecciona una persona de la lista.")
        if uid is not None:
            VentanaPerfil(self.p, uid)


class SolicitudesTab(ttk.Frame):
    def __init__(self, master, principal: PrincipalFrame):
        super().__init__(master, padding=10)
        self.p = principal

        ttk.Label(self, text="Solicitudes recibidas", font=FUENTE_NEGRITA).pack(anchor="w")
        self.t_recibidas = crear_tabla(self, [("nombre", "Nombre", 320), ("usuario", "Usuario", 200)])
        self.t_recibidas.pack(fill="both", expand=True, pady=(4, 6))
        f1 = ttk.Frame(self)
        f1.pack(fill="x")
        ttk.Button(f1, text="Aceptar", command=self.aceptar).pack(side="right")
        ttk.Button(f1, text="Rechazar", command=self.rechazar).pack(side="right", padx=6)
        ttk.Button(f1, text="Ver perfil", command=lambda: self._perfil(self.t_recibidas)).pack(side="right")

        ttk.Separator(self).pack(fill="x", pady=12)

        ttk.Label(self, text="Solicitudes enviadas (pendientes)", font=FUENTE_NEGRITA).pack(anchor="w")
        self.t_enviadas = crear_tabla(self, [("nombre", "Nombre", 320), ("usuario", "Usuario", 200)])
        self.t_enviadas.pack(fill="both", expand=True, pady=(4, 6))
        f2 = ttk.Frame(self)
        f2.pack(fill="x")
        ttk.Button(f2, text="Cancelar solicitud", command=self.cancelar).pack(side="right")

    def refrescar(self):
        red, yo = self.p.red, self.p.yo
        self.t_recibidas.delete(*self.t_recibidas.get_children())
        for u in red.solicitudes_recibidas(yo.id):
            self.t_recibidas.insert("", "end", iid=str(u.id), values=(u.nombre, u.usuario))
        self.t_enviadas.delete(*self.t_enviadas.get_children())
        for u in red.solicitudes_enviadas(yo.id):
            self.t_enviadas.insert("", "end", iid=str(u.id), values=(u.nombre, u.usuario))

    def _perfil(self, tabla):
        uid = id_seleccionado(tabla, "Selecciona una persona de la lista.")
        if uid is not None:
            VentanaPerfil(self.p, uid)

    def aceptar(self):
        uid = id_seleccionado(self.t_recibidas, "Selecciona una solicitud de la lista.")
        if uid is None:
            return
        try:
            self.p.red.aceptar_solicitud(self.p.yo.id, uid)
        except ValueError as e:
            messagebox.showinfo("Solicitudes", str(e))
        else:
            messagebox.showinfo("Solicitudes", f"Ahora eres amigo de {self.p.red.usuario_por_id(uid).nombre}.")
        self.p.refrescar_todo()

    def rechazar(self):
        uid = id_seleccionado(self.t_recibidas, "Selecciona una solicitud de la lista.")
        if uid is None:
            return
        self.p.red.rechazar_solicitud(self.p.yo.id, uid)
        self.p.refrescar_todo()

    def cancelar(self):
        uid = id_seleccionado(self.t_enviadas, "Selecciona una solicitud enviada.")
        if uid is None:
            return
        self.p.red.cancelar_solicitud(self.p.yo.id, uid)
        self.p.refrescar_todo()


class AmigosTab(ttk.Frame):
    def __init__(self, master, principal: PrincipalFrame):
        super().__init__(master, padding=10)
        self.p = principal
        self.lbl = ttk.Label(self, text="")
        self.lbl.pack(anchor="w")
        self.tabla = crear_tabla(self, [("nombre", "Nombre", 320), ("usuario", "Usuario", 200)])
        self.tabla.pack(fill="both", expand=True, pady=10)
        self.tabla.bind("<Double-1>", lambda e: self.ver_perfil())
        botones = ttk.Frame(self)
        botones.pack(fill="x")
        ttk.Button(botones, text="Eliminar amigo", command=self.eliminar).pack(side="right")
        ttk.Button(botones, text="Ver perfil", command=self.ver_perfil).pack(side="right", padx=6)

    def refrescar(self):
        self.tabla.delete(*self.tabla.get_children())
        amigos = self.p.red.amigos_de(self.p.yo.id)
        self.lbl.config(text=f"Tienes {len(amigos)} amigo(s)")
        for u in amigos:
            self.tabla.insert("", "end", iid=str(u.id), values=(u.nombre, u.usuario))

    def ver_perfil(self):
        uid = id_seleccionado(self.tabla, "Selecciona un amigo de la lista.")
        if uid is not None:
            VentanaPerfil(self.p, uid)

    def eliminar(self):
        uid = id_seleccionado(self.tabla, "Selecciona un amigo de la lista.")
        if uid is None:
            return
        nombre = self.p.red.usuario_por_id(uid).nombre
        if messagebox.askyesno("Eliminar amigo", f"¿Eliminar a {nombre} de tus amigos?"):
            self.p.red.eliminar_amigo(self.p.yo.id, uid)
            self.p.refrescar_todo()


class SugerenciasTab(ttk.Frame):
    def __init__(self, master, principal: PrincipalFrame):
        super().__init__(master, padding=10)
        self.p = principal
        self.lbl = ttk.Label(self, text="")
        self.lbl.pack(anchor="w")
        self.tabla = crear_tabla(self, [("nombre", "Nombre", 220),
                                        ("usuario", "Usuario", 130),
                                        ("comun", "Amigos en común", 320)])
        self.tabla.pack(fill="both", expand=True, pady=10)
        self.tabla.bind("<Double-1>", lambda e: self.ver_perfil())
        botones = ttk.Frame(self)
        botones.pack(fill="x")
        ttk.Button(botones, text="Enviar solicitud", command=self.enviar).pack(side="right")
        ttk.Button(botones, text="Ver perfil", command=self.ver_perfil).pack(side="right", padx=6)

    def refrescar(self):
        self.tabla.delete(*self.tabla.get_children())
        sugerencias = self.p.red.sugerencias(self.p.yo.id)
        if sugerencias:
            self.lbl.config(text="Personas que podrías conocer (amigos de tus amigos):")
        else:
            self.lbl.config(text="Aún no hay sugerencias. Agrega amigos para descubrir a los amigos de tus amigos.")
        for u, comunes in sugerencias:
            texto = f"{len(comunes)}: " + ", ".join(c.nombre for c in comunes)
            self.tabla.insert("", "end", iid=str(u.id), values=(u.nombre, u.usuario, texto))

    def enviar(self):
        uid = id_seleccionado(self.tabla, "Selecciona una persona de la lista.")
        if uid is not None:
            enviar_solicitud(self.p, uid)

    def ver_perfil(self):
        uid = id_seleccionado(self.tabla, "Selecciona una persona de la lista.")
        if uid is not None:
            VentanaPerfil(self.p, uid)


# ===================================================================== PERFIL
class VentanaPerfil(tk.Toplevel):
    """Perfil de otra persona (o el propio): solo sus publicaciones."""

    def __init__(self, principal: PrincipalFrame, uid: int):
        super().__init__(principal.app)
        self.p = principal
        self.uid = uid
        usuario = principal.red.usuario_por_id(uid)
        self.title(f"Perfil de {usuario.nombre}")
        self.geometry("580x620")
        self.minsize(440, 420)
        self.transient(principal.app)

        cab = tk.Frame(self, bg=COLOR_PRIMARIO)
        cab.pack(fill="x")
        tk.Label(cab, text=usuario.nombre, bg=COLOR_PRIMARIO, fg="white",
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=16, pady=(12, 0))
        tk.Label(cab, text=f"@{usuario.usuario}", bg=COLOR_PRIMARIO, fg="white").pack(anchor="w", padx=16)
        self.lbl_info = tk.Label(cab, bg=COLOR_PRIMARIO, fg="white")
        self.lbl_info.pack(anchor="w", padx=16, pady=(4, 12))

        self.fila = ttk.Frame(self, padding=(10, 8))
        self.fila.pack(fill="x")
        self.btn = ttk.Button(self.fila, command=self.accion)

        self.lista = ListaDesplazable(self)
        self.lista.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.refrescar()

    def accion(self):
        red, yo = self.p.red, self.p.yo
        if red.estado_relacion(yo.id, self.uid) == "recibida":
            try:
                red.aceptar_solicitud(yo.id, self.uid)
            except ValueError as e:
                messagebox.showinfo("Solicitud", str(e), parent=self)
            else:
                messagebox.showinfo("Solicitud", f"Ahora eres amigo de {red.usuario_por_id(self.uid).nombre}.", parent=self)
            self._cambio()
        else:
            enviar_solicitud(self.p, self.uid)
            self.refrescar()

    def _cambio(self):
        self.refrescar()
        self.p.refrescar_todo()

    def refrescar(self):
        red, yo = self.p.red, self.p.yo
        pubs = red.publicaciones_de(self.uid)
        es_yo = self.uid == yo.id
        estado = "amigo" if es_yo else red.estado_relacion(yo.id, self.uid)
        etiqueta = "Este es tu perfil" if es_yo else (ETIQUETA_ESTADO[estado] or "No son amigos")
        self.lbl_info.config(
            text=f"Amigos: {len(red.amigos_de(self.uid))}   |   Publicaciones: {len(pubs)}   |   {etiqueta}")

        if estado == "ninguna":
            self.btn.config(text="Enviar solicitud")
            self.btn.pack(side="right")
        elif estado == "recibida":
            self.btn.config(text="Aceptar solicitud")
            self.btn.pack(side="right")
        else:
            self.btn.pack_forget()

        self.lista.limpiar()
        if not pubs:
            self.lista.mensaje_vacio("Aún no ha publicado nada.")
        for pub in pubs:
            crear_tarjeta(self.lista, red, yo, pub, self._cambio, interactivo=(estado == "amigo"))