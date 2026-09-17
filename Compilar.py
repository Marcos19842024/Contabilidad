import subprocess
import sys
import os

def compilar():
    print("🔨 Compilando SistemaIngresos...")
    sistema = "Windows" if sys.platform.startswith("win") else "Mac" if sys.platform == "darwin" else "Linux"
    print(f"   Plataforma detectada: {sistema}")

    # Instalar dependencias
    subprocess.run([sys.executable, "-m", "pip", "install", "openpyxl", "pyinstaller"], check=True)

    # Ícono según plataforma
    icono = ""
    if sistema == "Windows" and os.path.exists("icono.ico"):
        icono = "--icon=icono.ico"
    elif sistema == "Mac" and os.path.exists("icono.icns"):
        icono = "--icon=icono.icns"

    cmd = [
        "pyinstaller", "--onefile", "--windowed",
        "--name", "SistemaIngresos",
        "--clean",
    ]
    if icono:
        cmd.append(icono)
    cmd.append("ingresos.py")

    subprocess.run(cmd, check=True)
    print("\n✅ Listo. Busca el ejecutable en la carpeta 'dist/'")
    if sistema == "Windows":
        print("   📄 dist/SistemaIngresos.exe")
    elif sistema == "Mac":
        print("   📄 dist/SistemaIngresos.app")
        print("   ℹ️  Si macOS lo bloquea: clic derecho → Abrir, o ejecuta:")
        print("      xattr -cr dist/SistemaIngresos.app")

if __name__ == "__main__":
    compilar()