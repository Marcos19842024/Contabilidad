#!/bin/bash
# crear_app_mac.sh
# Convierte el build de PyInstaller en una .app de macOS.
# Comprime la .app en un .zip que preserva symlinks.

set -e

echo "=========================================="
echo "Creando Sistema Ingresos.app"
echo "=========================================="

APP_NAME="Sistema Ingresos"
APP_PATH="dist/${APP_NAME}.app"

# 1. Verificar que existe el build
if [ ! -d "dist/SistemaIngresos" ]; then
    echo "❌ No existe dist/SistemaIngresos"
    exit 1
fi

# 2. Crear estructura de la .app
echo "→ Creando estructura..."
mkdir -p "${APP_PATH}/Contents/MacOS"
mkdir -p "${APP_PATH}/Contents/Resources"

# 3. Mover el ejecutable y _internal a Resources
echo "→ Moviendo archivos..."
mv dist/SistemaIngresos/SistemaIngresos "${APP_PATH}/Contents/Resources/"
mv dist/SistemaIngresos/_internal "${APP_PATH}/Contents/Resources/"

# 4. Generar Info.plist
echo "→ Creando Info.plist..."
cat > "${APP_PATH}/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Sistema Ingresos</string>
    <key>CFBundleDisplayName</key>
    <string>Sistema Ingresos</string>
    <key>CFBundleIdentifier</key>
    <string>com.qvet.sistemaingresos</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleExecutable</key>
    <string>SistemaIngresos</string>
    <key>CFBundleIconFile</key>
    <string>icono.icns</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
EOF

# 5. Copiar el ícono si existe
if [ -f "icono.icns" ]; then
    echo "→ Copiando ícono..."
    cp icono.icns "${APP_PATH}/Contents/Resources/"
fi

# 6. Crear lanzador
echo "→ Creando lanzador..."
cat > "${APP_PATH}/Contents/MacOS/SistemaIngresos" << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$DIR/../Resources/SistemaIngresos" "$@"
EOF
chmod +x "${APP_PATH}/Contents/MacOS/SistemaIngresos"

# 7. Quitar atributos extendidos
echo "→ Limpiando atributos extendidos..."
xattr -cr "${APP_PATH}" 2>/dev/null || true

# 8. Firmar todo con ad-hoc
echo "→ Firmando binarios..."
find "${APP_PATH}" -type f \( -name "*.so" -o -name "*.dylib" -o -name "Python" \) -exec codesign --force --sign - {} \; 2>/dev/null || true

find "${APP_PATH}" -type d -name "*.framework" -exec codesign --force --deep --sign - {} \; 2>/dev/null || true

codesign --force --sign - "${APP_PATH}/Contents/MacOS/SistemaIngresos" 2>/dev/null || true
codesign --force --deep --sign - "${APP_PATH}" 2>/dev/null || true

# 9. Verificar
echo "→ Verificando firma..."
codesign -dv "${APP_PATH}" 2>&1 | head -5 || true

# 10. Comprimir la .app en un .zip preservando symlinks
echo "→ Comprimiendo .app en .zip..."
cd dist
zip -r -y "Sistema Ingresos.zip" "${APP_NAME}.app" > /dev/null
cd ..

echo ""
echo "✅ ${APP_NAME}.app creada y comprimida"
echo "   Archivo: dist/Sistema Ingresos.zip"