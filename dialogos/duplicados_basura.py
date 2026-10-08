# dialogos/duplicados_basura.py
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui.utils import configurar_ventana

from core.rutas_estetica import (
    CLIENTES_MAESTRO, MASCOTAS_FILE, TRANSPORTES_CLIENTE,
)
from modulos.estetica_transportes import (
    _cargar_json, _guardar_json, clave_busqueda, normalizar_nombre,
)


PALABRAS_BASURA = [
    "eliminar", "prueba", "test", "xxx", "exterreno", "externo",
    "hospital", "pendiente agregar", "solicitar",
]


def es_basura(nombre: str) -> bool:
    n = clave_busqueda(nombre)
    if not n:
        return True
    for p in PALABRAS_BASURA:
        if p in n:
            return True
    return False


# ============================================================
# Diálogo para elegir cuál duplicado se queda
# ============================================================
class DialogoResolverDuplicado(ttk.Toplevel):
    def __init__(self, master, grupo, on_resolver):
        """
        grupo: lista de clientes con la misma clave
        on_resolver: callback(cliente_elegido, ids_a_eliminar)
        """
        super().__init__(master)
        self.title("Resolver duplicado")
        configurar_ventana(master, self, ancho=780, alto=480, centrar_en_padre=True)

        self.grupo = grupo
        self.on_resolver = on_resolver
        self.elegido_id = None

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(
            frame,
            text=f"Hay {len(grupo)} registros con el mismo nombre. "
                 f"Elige con cuál te quedas (los demás se eliminan):",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        cols = ("elegido", "id", "cliente", "poblacion", "direccion")
        self.tabla = ttk.Treeview(frame, columns=cols, show="headings",
                                  bootstyle="primary")
        for c, t, w in [("elegido", "✔", 40), ("id", "ID", 60),
                        ("cliente", "Cliente", 220),
                        ("poblacion", "Población", 160),
                        ("direccion", "Dirección", 260)]:
            self.tabla.heading(c, text=t)
            self.tabla.column(c, width=w)
        self.tabla.pack(fill=BOTH, expand=True)

        for c in grupo:
            self.tabla.insert("", END, iid=str(c["id"]), values=(
                "", c["id"], c.get("cliente", ""),
                c.get("poblacion", ""), c.get("direccion", ""),
            ))

        self.tabla.bind("<Double-1>", self._marcar_elegido)

        ttk.Label(frame, text="(doble clic para marcar cuál se queda)",
                  foreground="gray").pack(anchor="w", pady=(6, 0))

        barra = ttk.Frame(frame)
        barra.pack(fill=X, pady=(10, 0))
        ttk.Button(barra, text="✔ Aplicar", command=self._aplicar,
                   bootstyle="success").pack(side=RIGHT)

    def _marcar_elegido(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        self.elegido_id = int(sel[0])
        for iid in self.tabla.get_children():
            self.tabla.set(iid, "elegido", "")
        self.tabla.set(sel[0], "elegido", "✔")

    def _aplicar(self):
        if not self.elegido_id:
            messagebox.showinfo("Sin selección",
                                "Doble clic en el registro que quieres conservar.",
                                parent=self)
            return
        elegido = next(c for c in self.grupo if c["id"] == self.elegido_id)
        ids_borrar = [c["id"] for c in self.grupo if c["id"] != self.elegido_id]
        self.on_resolver(elegido, ids_borrar)
        self.destroy()


# ============================================================
# Diálogo de edición de un registro basura
# ============================================================
class DialogoBasuraAccion(ttk.Toplevel):
    def __init__(self, master, cliente, on_guardar, on_eliminar, on_restaurar):
        super().__init__(master)
        self.title("Registro basura")
        configurar_ventana(master, self, ancho=560, alto=200, centrar_en_padre=True)

        self.cliente = dict(cliente)
        self.on_guardar = on_guardar
        self.on_eliminar = on_eliminar
        self.on_restaurar = on_restaurar

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text="Nombre:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.var_nombre = tk.StringVar(value=self.cliente.get("cliente", ""))
        ttk.Entry(frame, textvariable=self.var_nombre, width=45).grid(row=0, column=1, sticky="w")

        ttk.Label(frame, text="Población:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.var_pob = tk.StringVar(value=self.cliente.get("poblacion", ""))
        ttk.Entry(frame, textvariable=self.var_pob, width=45).grid(row=1, column=1, sticky="w")

        ttk.Label(frame, text="Dirección:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.var_dir = tk.StringVar(value=self.cliente.get("direccion", ""))
        ttk.Entry(frame, textvariable=self.var_dir, width=45).grid(row=2, column=1, sticky="w")

        barra = ttk.Frame(frame)
        barra.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        ttk.Button(barra, text="🗑️ Eliminar", command=self._eliminar,
                   bootstyle="danger-outline").pack(side=LEFT, padx=2)
        ttk.Button(barra, text="♻️ Restaurar", command=self._restaurar,
                   bootstyle="warning").pack(side=LEFT, padx=2)
        ttk.Button(barra, text="💾 Guardar cambios", command=self._guardar,
                   bootstyle="success").pack(side=RIGHT)

        self.protocol("WM_DELETE_WINDOW", self._guardar_y_cerrar)

    def _aplicar_campos(self):
        self.cliente["cliente"] = normalizar_nombre(self.var_nombre.get())
        self.cliente["poblacion"] = self.var_pob.get().strip()
        self.cliente["direccion"] = self.var_dir.get().strip()

    def _guardar(self):
        if not self.var_nombre.get().strip():
            messagebox.showwarning("Falta nombre", "El nombre no puede estar vacío.",
                                   parent=self)
            return False
        self._aplicar_campos()
        self.on_guardar(self.cliente)
        return True

    def _guardar_y_cerrar(self):
        if self._guardar():
            self.destroy()

    def _eliminar(self):
        if not messagebox.askyesno("Confirmar", "¿Eliminar definitivamente?",
                                   parent=self):
            return
        self.on_eliminar(self.cliente)
        self.destroy()

    def _restaurar(self):
        self._aplicar_campos()
        self.on_restaurar(self.cliente)
        self.destroy()


# ============================================================
# Ventana principal: duplicados + basura
# ============================================================
class DialogoDuplicadosBasura(ttk.Toplevel):
    def __init__(self, master, on_guardar):
        super().__init__(master)
        self.title("Duplicados y registros basura")
        configurar_ventana(master, self, ancho=920, alto=620,
                           min_ancho=800, min_alto=500, centrar_en_padre=True)

        self.on_guardar = on_guardar
        self.clientes = _cargar_json(CLIENTES_MAESTRO, [])
        self.mascotas = _cargar_json(MASCOTAS_FILE, {})
        self.transportes = _cargar_json(TRANSPORTES_CLIENTE, {})

        self._analizar()

        nb = ttk.Notebook(self)
        nb.pack(fill=BOTH, expand=True, padx=8, pady=8)

        self.tab_dup = ttk.Frame(nb, padding=8)
        self.tab_bas = ttk.Frame(nb, padding=8)
        nb.add(self.tab_dup, text=f"Duplicados ({len(self.grupos_dup)})")
        nb.add(self.tab_bas, text=f"Basura ({len(self.bas)})")

        self._construir_duplicados()
        self._construir_basura()

    # ---------- Análisis ----------

    def _analizar(self):
        por_clave = {}
        self.bas = []
        for c in self.clientes:
            nombre = c.get("cliente", "")
            if es_basura(nombre):
                self.bas.append(c)
                continue
            clave = clave_busqueda(nombre)
            por_clave.setdefault(clave, []).append(c)

        self.grupos_dup = [grupo for grupo in por_clave.values() if len(grupo) > 1]

    # ---------- Duplicados ----------

    def _construir_duplicados(self):
        f = self.tab_dup
        cols = ("id", "cliente", "poblacion", "direccion")
        self.tabla_dup = ttk.Treeview(f, columns=cols, show="headings",
                                      bootstyle="warning")
        for c, t, w in [("id", "ID", 60), ("cliente", "Cliente", 260),
                        ("poblacion", "Población", 180),
                        ("direccion", "Dirección", 350)]:
            self.tabla_dup.heading(c, text=t)
            self.tabla_dup.column(c, width=w)
        self.tabla_dup.pack(fill=BOTH, expand=True)

        # Mostramos un representante de cada grupo (el primero)
        self._repr_por_iid = {}
        for idx, grupo in enumerate(self.grupos_dup):
            primero = grupo[0]
            iid = f"g{idx}"
            self._repr_por_iid[iid] = grupo
            self.tabla_dup.insert("", END, iid=iid, values=(
                f"{len(grupo)} registros",
                primero.get("cliente", ""),
                primero.get("poblacion", ""),
                primero.get("direccion", ""),
            ))

        self.tabla_dup.bind("<Double-1>", self._abrir_grupo)
        ttk.Label(f, text="(doble clic para resolver el grupo)",
                  foreground="gray").pack(anchor="w", pady=(6, 0))

    def _abrir_grupo(self, event=None):
        sel = self.tabla_dup.selection()
        if not sel:
            return
        grupo = self._repr_por_iid.get(sel[0])
        if not grupo:
            return

        def _resolver(elegido, ids_borrar):
            # Migrar mascotas y transporte al elegido si no las tiene
            nombre_elegido = elegido.get("cliente", "")

            mascotas_elegido = self.mascotas.get(nombre_elegido, [])
            for c in grupo:
                if c["id"] == elegido["id"]:
                    continue
                nombre_otro = c.get("cliente", "")
                # Mascotas
                for m in self.mascotas.get(nombre_otro, []):
                    if m not in mascotas_elegido:
                        mascotas_elegido.append(m)
                # Transporte
                if nombre_otro not in self.transportes and nombre_elegido not in self.transportes:
                    self.transportes[nombre_elegido] = self.transportes.get(nombre_otro, {})
                # Borrar del maestro
                self.clientes = [x for x in self.clientes if x["id"] != c["id"]]
                self.mascotas.pop(nombre_otro, None)

            self.mascotas[nombre_elegido] = mascotas_elegido

            # Persistir
            _guardar_json(CLIENTES_MAESTRO, self.clientes)
            _guardar_json(MASCOTAS_FILE, self.mascotas)
            _guardar_json(TRANSPORTES_CLIENTE, self.transportes)

            # Reanalizar y refrescar
            self._analizar()
            self._refrescar_duplicados()
            if self.on_guardar:
                self.on_guardar()

        DialogoResolverDuplicado(self, grupo, _resolver)

    def _refrescar_duplicados(self):
        for i in self.tabla_dup.get_children():
            self.tabla_dup.delete(i)
        self._repr_por_iid = {}
        for idx, grupo in enumerate(self.grupos_dup):
            primero = grupo[0]
            iid = f"g{idx}"
            self._repr_por_iid[iid] = grupo
            self.tabla_dup.insert("", END, iid=iid, values=(
                f"{len(grupo)} registros",
                primero.get("cliente", ""),
                primero.get("poblacion", ""),
                primero.get("direccion", ""),
            ))

    # ---------- Basura ----------

    def _construir_basura(self):
        f = self.tab_bas
        cols = ("id", "cliente", "poblacion", "direccion")
        self.tabla_bas = ttk.Treeview(f, columns=cols, show="headings",
                                      bootstyle="danger")
        for c, t, w in [("id", "ID", 60), ("cliente", "Cliente", 260),
                        ("poblacion", "Población", 180),
                        ("direccion", "Dirección", 350)]:
            self.tabla_bas.heading(c, text=t)
            self.tabla_bas.column(c, width=w)
        self.tabla_bas.pack(fill=BOTH, expand=True)
        self._refrescar_basura()
        self.tabla_bas.bind("<Double-1>", self._abrir_basura)

    def _refrescar_basura(self):
        for i in self.tabla_bas.get_children():
            self.tabla_bas.delete(i)
        for c in self.bas:
            self.tabla_bas.insert("", END, iid=str(c["id"]), values=(
                c["id"], c.get("cliente", ""), c.get("poblacion", ""),
                c.get("direccion", "")))

    def _abrir_basura(self, event=None):
        sel = self.tabla_bas.selection()
        if not sel:
            return
        cid = int(sel[0])
        cliente = next((c for c in self.bas if c["id"] == cid), None)
        if not cliente:
            return

        def _guardar(c):
            for i, x in enumerate(self.clientes):
                if x["id"] == c["id"]:
                    self.clientes[i] = c
                    break
            _guardar_json(CLIENTES_MAESTRO, self.clientes)
            self._analizar()
            self._refrescar_basura()
            if self.on_guardar:
                self.on_guardar()

        def _eliminar(c):
            self.clientes = [x for x in self.clientes if x["id"] != c["id"]]
            _guardar_json(CLIENTES_MAESTRO, self.clientes)
            self._analizar()
            self._refrescar_basura()
            if self.on_guardar:
                self.on_guardar()

        def _restaurar(c):
            # Lo saca de basura → vuelve a clientes normales
            for i, x in enumerate(self.clientes):
                if x["id"] == c["id"]:
                    self.clientes[i] = c
                    break
            _guardar_json(CLIENTES_MAESTRO, self.clientes)
            self._analizar()
            self._refrescar_basura()
            if self.on_guardar:
                self.on_guardar()

        DialogoBasuraAccion(self, cliente, _guardar, _eliminar, _restaurar)