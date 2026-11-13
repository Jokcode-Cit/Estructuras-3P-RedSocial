"""Interfaz gráfica (Tkinter)."""
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from datetime import datetime

from red import RedSocial, MAX_CARACTERES

COLOR_PRIMARIO = "#2563eb"
FUENTE = ("Segoe UI", 10)


def formatear_fecha(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return iso


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UniConecta - Red Social Estudiantil")
        self.geometry("860x620")
        self.minsize(720, 520)
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
        ttk.Button(barra, text="Cerrar sesión", command=self.cerrar_sesion).pack(
            side="right", padx=14, pady=8)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_muro = MuroTab(self.notebook, self)
        self.tab_buscar = BuscarTab(self.notebook, self)
        self.tab_amigos = AmigosTab(self.notebook, self)
        self.notebook.add(self.tab_muro, text="  Muro  ")
        self.notebook.add(self.tab_buscar, text="  Buscar personas  ")
        self.notebook.add(self.tab_amigos, text="  Mis amigos  ")
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refrescar_todo())
        self.refrescar_todo()

    def refrescar_todo(self):
        self.tab_muro.refrescar()
        self.tab_buscar.refrescar()
        self.tab_amigos.refrescar()

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
        self.feed = ScrolledText(self, wrap="word", state="disabled", relief="flat",
                                 background="#f8fafc", padx=10, pady=10)
        self.feed.pack(fill="both", expand=True)
        self.feed.tag_configure("autor", font=("Segoe UI", 10, "bold"), foreground=COLOR_PRIMARIO)
        self.feed.tag_configure("yo", font=("Segoe UI", 10, "bold"), foreground="#059669")
        self.feed.tag_configure("fecha", foreground="#6b7280", font=("Segoe UI", 9))
        self.feed.tag_configure("vacio", foreground="#6b7280", justify="center")

    def _contador(self):
        n = len(self.entrada.get("1.0", "end-1c"))
        self.lbl_contador.config(text=f"{n}/{MAX_CARACTERES}",
                                 foreground="#dc2626" if n > MAX_CARACTERES else "")

    def publicar(self):
        try:
            self.p.red.publicar(self.p.yo.id, self.entrada.get("1.0", "end-1c"))
        except ValueError as e:
            messagebox.showwarning("Publicar", str(e))
            return
        self.entrada.delete("1.0", "end")
        self._contador()
        self.refrescar()

    def refrescar(self):
        red, yo = self.p.red, self.p.yo
        self.feed.config(state="normal")
        self.feed.delete("1.0", "end")
        pubs = red.muro(yo.id)
        if not pubs:
            self.feed.insert("end", "\nAún no hay publicaciones.\nEscribe algo o agrega amigos para ver las suyas.", "vacio")
        for pub in pubs:
            autor = red.usuario_por_id(pub.autor_id)
            if autor is None:
                continue
            if autor.id == yo.id:
                self.feed.insert("end", "Tú", "yo")
            else:
                self.feed.insert("end", f"{autor.nombre} (@{autor.usuario})", "autor")
            self.feed.insert("end", f"   {formatear_fecha(pub.timestamp)}\n", "fecha")
            self.feed.insert("end", pub.texto + "\n\n")
        self.feed.config(state="disabled")


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

        self.tabla = ttk.Treeview(self, columns=("nombre", "usuario", "estado"),
                                  show="headings", selectmode="browse")
        for col, texto, ancho in [("nombre", "Nombre", 280), ("usuario", "Usuario", 180), ("estado", "Estado", 120)]:
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho)
        self.tabla.pack(fill="both", expand=True, pady=10)
        self.tabla.bind("<Double-1>", lambda e: self.agregar())

        ttk.Button(self, text="Agregar como amigo", command=self.agregar).pack(anchor="e")

    def refrescar(self):
        self.tabla.delete(*self.tabla.get_children())
        for u in self.p.red.buscar(self.e_busqueda.get(), self.p.yo.id):
            estado = "✔ Amigo" if self.p.red.son_amigos(self.p.yo.id, u.id) else ""
            self.tabla.insert("", "end", iid=str(u.id), values=(u.nombre, u.usuario, estado))

    def agregar(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showinfo("Agregar amigo", "Selecciona una persona de la lista.")
            return
        uid = int(sel[0])
        try:
            self.p.red.agregar_amigo(self.p.yo.id, uid)
        except ValueError as e:
            messagebox.showinfo("Agregar amigo", str(e))
            return
        nombre = self.p.red.usuario_por_id(uid).nombre
        messagebox.showinfo("Agregar amigo", f"Ahora eres amigo de {nombre}.")
        self.p.refrescar_todo()


class AmigosTab(ttk.Frame):
    def __init__(self, master, principal: PrincipalFrame):
        super().__init__(master, padding=10)
        self.p = principal
        self.lbl = ttk.Label(self, text="")
        self.lbl.pack(anchor="w")
        self.tabla = ttk.Treeview(self, columns=("nombre", "usuario"), show="headings", selectmode="browse")
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("usuario", text="Usuario")
        self.tabla.column("nombre", width=320)
        self.tabla.column("usuario", width=200)
        self.tabla.pack(fill="both", expand=True, pady=10)
        ttk.Button(self, text="Eliminar amigo", command=self.eliminar).pack(anchor="e")

    def refrescar(self):
        self.tabla.delete(*self.tabla.get_children())
        amigos = self.p.red.amigos_de(self.p.yo.id)
        self.lbl.config(text=f"Tienes {len(amigos)} amigo(s)")
        for u in amigos:
            self.tabla.insert("", "end", iid=str(u.id), values=(u.nombre, u.usuario))

    def eliminar(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showinfo("Eliminar amigo", "Selecciona un amigo de la lista.")
            return
        uid = int(sel[0])
        nombre = self.p.red.usuario_por_id(uid).nombre
        if messagebox.askyesno("Eliminar amigo", f"¿Eliminar a {nombre} de tus amigos?"):
            self.p.red.eliminar_amigo(self.p.yo.id, uid)
            self.p.refrescar_todo()