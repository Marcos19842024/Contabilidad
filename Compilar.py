# -*- coding: utf-8 -*-
"""
compilar.py
Compila SistemaIngresos para Windows (o Mac/Linux) incluyendo los
archivos de datos necesarios.

Ejecutar desde la misma carpeta donde están:
  - Ingresos.py
  - lector_facturas.py
  - correo_facturas.py
  - catalogo_qvet.json
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path


# ============================================================
# CONFIGURACIÓN
# ============================================================
NOMBRE_APP = "SistemaIngresos"

# Archivos Python que deben existir antes de compilar
ARCHIVOS_REQUERIDOS = [
    "Ingresos.py",
    "lector_facturas.py",
    "correo_facturas.py",
]

# Archivos de datos que se incluirán DENTRO del ejecutable
# (solo los que son de solo lectura; los editables se crean en
#  ~/Documents/Contabilidad App/)
ARCHIVOS_DATOS = [
    "catalogo_qvet.json",
]

# Archivos de datos que el usuario edita (NO se empaquetan;
# se crean solos en Documents/Contabilidad App/)
ARCHIVOS_USUARIO = [
    "categorias_manuales.json",
    "config_ui.json",
    "historial_autocompletado.json",
    "correos_procesados.json",
    "registros_ingresos_<año>.json",
]


def verificar_requisitos():
    """Verifica que existan los archivos necesarios."""
    print("🔍 Verificando archivos necesarios...")
    faltantes = []

    for archivo in ARCHIVOS_REQUERIDOS:
        if not Path(archivo).exists():
            faltantes.append(archivo)
            print(f"   ❌ Falta: {archivo}")
        else:
            print(f"   ✅ {archivo}")

    for archivo in ARCHIVOS_DATOS:
        if not Path(archivo).exists():
            print(f"   ⚠️  Opcional no encontrado: {archivo}")
        else:
            print(f"   ✅ {archivo}")

    if faltantes:
        print(f"\n❌ Faltan archivos obligatorios: {faltantes}")
        print("   Asegúrate de ejecutar este script desde la carpeta del proyecto.")
        sys.exit(1)


def instalar_dependencias():
    """Instala todas las dependencias necesarias."""
    print("\n📦 Instalando dependencias...")
    paquetes = [
        "openpyxl",
        "pyinstaller",
        "ttkbootstrap",
        "pdfplumber",
        "pillow",
    ]
    for paquete in paquetes:
        print(f"   Instalando {paquete}...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", paquete],
            check=True, capture_output=True
        )
    print("   ✅ Dependencias instaladas")


def limpiar_builds_anteriores():
    """Elimina builds anteriores para evitar conflictos."""
    print("\n🧹 Limpiando builds anteriores...")
    for carpeta in ["build", "dist"]:
        if Path(carpeta).exists():
            shutil.rmtree(carpeta)
            print(f"   Eliminado: {carpeta}/")

    spec = Path(f"{NOMBRE_APP}.spec")
    if spec.exists():
        spec.unlink()
        print(f"   Eliminado: {spec}")


def construir_comando_pyinstaller():
    """Arma el comando de PyInstaller con todos los archivos."""
    # Usamos "python -m PyInstaller" para no depender del PATH
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",                # ✅ más rápido al abrir que --onefile
        "--windowed",              # sin consola
        "--name", NOMBRE_APP,
        "--clean",
        "--noconfirm",
    ]

    # Ícono según plataforma
    if sys.platform.startswith("win") and Path("icono.ico").exists():
        cmd.append("--icon=icono.ico")
        print("   🎨 Ícono: icono.ico")
    elif sys.platform == "darwin" and Path("icono.icns").exists():
        cmd.append("--icon=icono.icns")
        print("   🎨 Ícono: icono.icns")

    # Separador de --add-data según plataforma
    separador = ";" if sys.platform.startswith("win") else ":"

    # Incluir archivos de datos (solo los de solo lectura)
    for archivo in ARCHIVOS_DATOS:
        if Path(archivo).exists():
            cmd.append(f"--add-data={archivo}{separador}.")
            print(f"   📎 Incluir: {archivo}")

    # Hidden imports que PyInstaller no detecta bien
    hidden_imports = [
        "ttkbootstrap",
        "PIL",
        "PIL._tkinter_finder",
        "pdfplumber",
        "pdfminer",
        "pdfminer.high_level",
        "pdfminer.layout",
        "imghdr",
        "openpyxl",
        "openpyxl.styles",
        "openpyxl.utils",
    ]
    for h in hidden_imports:
        cmd.append(f"--hidden-import={h}")

    # Excluir módulos pesados que no se usan
    excluir = [
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "tkinter.test",
        "test",
    ]
    for e in excluir:
        cmd.append(f"--exclude-module={e}")

    # Punto de entrada
    cmd.append("Ingresos.py")

    return cmd


def compilar():
    """Compila la aplicación."""
    print("=" * 60)
    print(f"🔨 Compilando {NOMBRE_APP}")
    print("=" * 60)

    sistema = ("Windows" if sys.platform.startswith("win")
               else "Mac" if sys.platform == "darwin"
               else "Linux")
    print(f"🖥️  Plataforma detectada: {sistema}\n")

    # 1. Verificar archivos
    verificar_requisitos()

    # 2. Instalar dependencias
    instalar_dependencias()

    # 3. Limpiar builds anteriores
    limpiar_builds_anteriores()

    # 4. Armar comando
    print("\n🛠️  Preparando PyInstaller...")
    cmd = construir_comando_pyinstaller()

    print(f"\n▶️  Ejecutando:")
    print(f"   {' '.join(cmd)}\n")

    # 5. Ejecutar
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error al compilar: {e}")
        sys.exit(1)

    # 6. Resultado
    print("\n" + "=" * 60)
    print("✅ ¡Compilación terminada!")
    print("=" * 60)

    if sistema == "Windows":
        exe = Path("dist") / NOMBRE_APP / f"{NOMBRE_APP}.exe"
        if exe.exists():
            size_mb = exe.stat().st_size / (1024 * 1024)
            print(f"\n📁 Carpeta: {exe.parent}")
            print(f"📄 Ejecutable: {exe.name}")
            print(f"   Tamaño: {size_mb:.1f} MB")
            print(f"\n💡 Copia TODA la carpeta '{NOMBRE_APP}' a donde quieras.")
            print(f"   El .exe solo no funciona: necesita los archivos vecinos.")

    elif sistema == "Mac":
        app = Path("dist") / f"{NOMBRE_APP}.app"
        if app.exists():
            print(f"\n📄 Aplicación: {app}")
            print(f"\n💡 Para distribuir:")
            print(f"   1. Comprime: zip -r {NOMBRE_APP}.zip dist/{NOMBRE_APP}.app")
            print(f"   2. Envíala al destinatario")
            print(f"   3. Si macOS la bloquea:")
            print(f"      xattr -cr /ruta/a/{NOMBRE_APP}.app")

    print("\n📌 IMPORTANTE:")
    print("   Al ejecutar la app por primera vez, se crearán los")
    print("   siguientes archivos en ~/Documents/Contabilidad App/:")
    print("   • registros_ingresos_<año>.json   (uno por año)")
    print("   • historial_autocompletado.json")
    print("   • config_ui.json")
    print("   • correos_procesados.json")
    print("   • categorias_manuales.json        (si editas categorías)")
    print("   • catalogo_qvet.json              (copia editable)")
    print("   • backups/                        (respaldos automáticos)")
    print("   • logs/                           (logs de sincronización)")
    print("   • facturas_descargadas/           (temporal del correo)")


if __name__ == "__main__":
    compilar()