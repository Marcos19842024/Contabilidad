# -*- coding: utf-8 -*-
"""
ui/widgets.py
Widgets personalizados de tkinter/ttkbootstrap:
  - EntryMoneda: entrada con formato de moneda y evaluación de expresiones.
  - EntryAutoComplete: entrada con autocompletado y debounce.
"""

import tkinter as tk
import ttkbootstrap as ttk

from config.temas import COLORES
from core.utilidades import evaluar_expresion, limpiar_moneda, formatear_moneda


# ============================================================
# ENTRY DE MONEDA
# ============================================================
class EntryMoneda(ttk.Entry):
    """Entry con formato moneda, evaluación de expresiones y colores."""

    def __init__(self, master=None, callback=None, **kw):
        super().__init__(master, justify="right", **kw)
        self.callback = callback
        self._ultimo_valor = 0.0
        self._ultima_expresion = ""
        self.insert(0, "0.00")
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<KeyRelease>", self._on_key_release)
        self._pintar()

    def _tiene_operacion(self, texto):
        if any(op in texto for op in "+*/()"):
            return True
        if texto.count("-") > 0 and not texto.strip().startswith("-"):
            return True
        if texto.strip().startswith("-") and texto.count("-") > 1:
            return True
        return False

    def _on_key_release(self, e):
        self._pintar()

    def _pintar(self):
        texto = self.get()
        try:
            color_fg = (COLORES["texto_operacion"]
                        if self._tiene_operacion(texto)
                        else COLORES["texto_normal"])
            self.configure(foreground=color_fg)
            try:
                self.configure(background=COLORES["fondo_entry"])
            except Exception:
                pass
        except Exception:
            pass

    def _on_focus_in(self, e):
        self.delete(0, tk.END)
        if self._ultima_expresion:
            self.insert(0, self._ultima_expresion)
        elif self._ultimo_valor:
            self.insert(0, f"{self._ultimo_valor:.2f}")
        self._pintar()

    def _on_focus_out(self, e):
        texto = self.get().strip()
        if self._tiene_operacion(texto):
            self._ultima_expresion = texto.replace(",", "").replace("$", "").strip()
            self._ultimo_valor = evaluar_expresion(texto)
        else:
            try:
                valor_actual = limpiar_moneda(texto)
            except Exception:
                valor_actual = None
            if (valor_actual is not None
                    and abs(valor_actual - self._ultimo_valor) < 0.01
                    and self._ultima_expresion):
                pass
            else:
                self._ultima_expresion = ""
                self._ultimo_valor = limpiar_moneda(texto)
        self.delete(0, tk.END)
        self.insert(0, formatear_moneda(self._ultimo_valor))
        self._pintar()
        if self.callback:
            self.callback()

    def get_valor(self):
        texto = self.get().strip()
        if self._tiene_operacion(texto):
            return evaluar_expresion(texto)
        return limpiar_moneda(texto)

    def set_valor(self, v, expresion=None):
        self._ultimo_valor = float(v or 0)
        self._ultima_expresion = expresion or ""
        self.delete(0, tk.END)
        self.insert(0, formatear_moneda(self._ultimo_valor))
        self._pintar()


# ============================================================
# ENTRY CON AUTOCOMPLETADO
# ============================================================
class EntryAutoComplete(ttk.Entry):
    """Entry con autocompletado optimizado con debounce."""

    def __init__(self, master=None, opciones=None, **kw):
        super().__init__(master, **kw)
        self.opciones = opciones or []
        self._lista = None
        self._listbox = None
        self._after_id = None
        self._ultimo_filtro = ""
        self._teclas_ignoradas = {
            "Shift_L", "Shift_R", "Control_L", "Control_R",
            "Alt_L", "Alt_R", "Meta_L", "Meta_R",
            "Caps_Lock", "Num_Lock", "Scroll_Lock",
            "Left", "Right", "Up", "Down", "Home", "End",
            "Page_Up", "Page_Down", "Escape", "Tab",
            "Return", "KP_Enter", "BackSpace", "Delete",
        }
        self.bind("<KeyRelease>", self._on_key)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Escape>", lambda e: self._cerrar_lista())

    def set_opciones(self, ops):
        self.opciones = ops or []

    def _on_key(self, e):
        if e.keysym in self._teclas_ignoradas:
            return
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(150, self._buscar)

    def _on_focus_out(self, e):
        self.after(120, self._cerrar_lista)

    def _buscar(self):
        self._after_id = None
        txt = self.get().strip().lower()
        if not txt:
            self._cerrar_lista()
            return
        if txt == self._ultimo_filtro and self._lista is not None:
            return
        self._ultimo_filtro = txt
        coincidencias = [o for o in self.opciones if txt in o.lower()][:8]
        if not coincidencias:
            self._cerrar_lista()
            return
        self._mostrar_lista(coincidencias)

    def _mostrar_lista(self, items):
        if self._lista is None or not self._lista.winfo_exists():
            self._crear_lista()
        self._listbox.delete(0, tk.END)
        for it in items:
            self._listbox.insert(tk.END, it)
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        w = max(self.winfo_width(), 200)
        h = min(len(items) * 22 + 4, 180)
        try:
            self._lista.wm_geometry(f"{w}x{h}+{x}+{y}")
            self._lista.deiconify()
            self._lista.lift()
        except Exception:
            pass

    def _crear_lista(self):
        self._lista = ttk.Toplevel(self)
        self._lista.wm_overrideredirect(True)
        try:
            self._lista.attributes("-topmost", True)
        except Exception:
            pass
        frame = ttk.Frame(self._lista, borderwidth=1, relief="solid")
        frame.pack(fill="both", expand=True)
        self._listbox = tk.Listbox(
            frame, font=("Segoe UI", 9), activestyle="none",
            highlightthickness=0, borderwidth=0,
        )
        self._listbox.pack(fill="both", expand=True)
        self._listbox.bind("<<ListboxSelect>>", self._seleccionar)
        self._listbox.bind("<Double-Button-1>", self._seleccionar)
        self._listbox.bind("<Return>", self._seleccionar)
        self._listbox.bind("<Escape>", lambda e: self._cerrar_lista())

    def _seleccionar(self, e=None):
        if not self._listbox:
            return
        sel = self._listbox.curselection()
        if sel:
            valor = self._listbox.get(sel[0])
            self.delete(0, tk.END)
            self.insert(0, valor)
            self.icursor(tk.END)
        self._cerrar_lista()
        self.focus_set()

    def _cerrar_lista(self):
        if self._lista is not None and self._lista.winfo_exists():
            try:
                self._lista.withdraw()
            except Exception:
                pass
        self._ultimo_filtro = ""