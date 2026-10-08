# -*- coding: utf-8 -*-
"""
generar_icono.py
Genera un ícono .icns para la app macOS.
Se ejecuta durante el build en GitHub Actions.
"""
import sys
from pathlib import Path


def generar_icono_png(ruta_salida="icono.png", tamaño=1024):
    """Genera un ícono PNG simple con las letras 'VS' (Vet Suite)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("⚠️ Pillow no está instalado. Instalando...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "pillow"], check=True)
        from PIL import Image, ImageDraw, ImageFont

    # Crear imagen con fondo transparente
    img = Image.new('RGBA', (tamaño, tamaño), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fondo circular con gradiente simulado
    margen = int(tamaño * 0.05)
    draw.ellipse(
        [margen, margen, tamaño - margen, tamaño - margen],
        fill=(30, 90, 150, 255)   # Azul
    )

    # Círculo interior más claro (efecto)
    margen2 = int(tamaño * 0.15)
    draw.ellipse(
        [margen2, margen2, tamaño - margen2, tamaño - margen2],
        fill=(50, 120, 200, 255)   # Azul claro
    )

    # Texto "VS" en el centro
    texto = "VS"
    tamaño_fuente = int(tamaño * 0.45)

    # Intentar cargar una fuente del sistema
    fuente = None
    fuentes_posibles = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for ruta in fuentes_posibles:
        try:
            fuente = ImageFont.truetype(ruta, tamaño_fuente)
            break
        except Exception:
            continue

    if fuente is None:
        fuente = ImageFont.load_default()

    # Calcular posición centrada
    bbox = draw.textbbox((0, 0), texto, font=fuente)
    ancho_texto = bbox[2] - bbox[0]
    alto_texto = bbox[3] - bbox[1]
    x = (tamaño - ancho_texto) // 2 - bbox[0]
    y = (tamaño - alto_texto) // 2 - bbox[1]

    # Dibujar texto con sombra
    draw.text((x + 5, y + 5), texto, fill=(0, 0, 0, 100), font=fuente)
    draw.text((x, y), texto, fill=(255, 255, 255, 255), font=fuente)

    # Guardar
    img.save(ruta_salida, "PNG")
    print(f"✅ PNG generado: {ruta_salida}")
    return ruta_salida


def png_a_icns(ruta_png, ruta_icns="icono.icns"):
    """Convierte un PNG a ICNS usando sips e iconutil (solo macOS)."""
    import subprocess
    import shutil
    from pathlib import Path

    carpeta_iconset = Path("icono.iconset")
    if carpeta_iconset.exists():
        shutil.rmtree(carpeta_iconset)
    carpeta_iconset.mkdir()

    # Tamaños requeridos por macOS
    tamaños = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]

    for tamaño, nombre in tamaños:
        ruta_destino = carpeta_iconset / nombre
        subprocess.run(
            ["sips", "-z", str(tamaño), str(tamaño), ruta_png, "--out", str(ruta_destino)],
            check=True, capture_output=True
        )

    # Convertir a .icns
    subprocess.run(
        ["iconutil", "-c", "icns", str(carpeta_iconset)],
        check=True, capture_output=True
    )

    # Limpiar
    shutil.rmtree(carpeta_iconset)

    if Path("icono.icns").exists():
        print(f"✅ ICNS generado: icono.icns")
        return "icono.icns"
    return None


if __name__ == "__main__":
    import sys

    # 1. Generar PNG
    png = generar_icono_png("icono.png", tamaño=1024)

    # 2. Convertir a ICNS (solo si estamos en macOS)
    if sys.platform == "darwin":
        png_a_icns(png, "icono.icns")
    else:
        print("⚠️ No estamos en macOS, saltando conversión a ICNS")