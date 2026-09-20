# -*- coding: utf-8 -*-
"""
compilar.py
Compila SistemaIngresos incluyendo los archivos de datos necesarios.
Ejecutar desde la misma carpeta donde están ingresos.py y lector_facturas.py.
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

# Archivos que deben existir antes de compilar
ARCHIVOS_REQUERIDOS = [
    "ingresos.py",
    "lector_facturas.py",
]

# Archivos de datos que se incluirán en el ejecutable
ARCHIVOS_DATOS = [
    "catalogo_qvet.json",
    "categorias_manuales.json",
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
    ]
    for paquete in paquetes:
        print(f"   Instalando {paquete}...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", paquete],
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
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
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

    # Incluir archivos de datos
    # Formato: --add-data "origen:destino" (Mac/Linux) o "origen;destino" (Windows)
    separador = ";" if sys.platform.startswith("win") else ":"

    for archivo in ARCHIVOS_DATOS:
        if Path(archivo).exists():
            cmd.append(f"--add-data={archivo}{separador}.")
            print(f"   📎 Incluir: {archivo}")

    # Punto de entrada
    cmd.append("ingresos.py")

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
        exe = Path("dist") / f"{NOMBRE_APP}.exe"
        if exe.exists():
            size_mb = exe.stat().st_size / (1024 * 1024)
            print(f"\n📄 Ejecutable: {exe}")
            print(f"   Tamaño: {size_mb:.1f} MB")
            print(f"\n💡 Copia este archivo a donde quieras.")
    elif sistema == "Mac":
        app = Path("dist") / f"{NOMBRE_APP}.app"
        if app.exists():
            print(f"\n📄 Aplicación: {app}")
            print(f"\n💡 Para distribuir:")
            print(f"   1. Comprime la app: zip -r {NOMBRE_APP}.zip dist/{NOMBRE_APP}.app")
            print(f"   2. Envíala al destinatario")
            print(f"   3. Si macOS la bloquea, ejecuta:")
            print(f"      xattr -cr /ruta/a/{NOMBRE_APP}.app")

    print("\n📌 IMPORTANTE:")
    print("   Al ejecutar la app por primera vez, se crearán los")
    print("   siguientes archivos en la misma carpeta del ejecutable:")
    print("   • registros_ingresos.json")
    print("   • historial_autocompletado.json")
    print("   • config_ui.json")
    print("   • categorias_manuales.json (si editas categorías)")
    print("   • backups/ (carpeta con respaldos)")


if __name__ == "__main__":
    compilar()