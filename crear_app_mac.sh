#!/bin/bash
# crear_app_mac.sh
# Convierte el build de PyInstaller en una .app de macOS.
# Se ejecuta durante el build en GitHub Actions.

set -e

echo "=========================================="
echo "Creando SistemaIngresos.app"
echo "=========================================="

# 1. Verificar que existe el build
if [ ! -d "dist/SistemaIngresos" ]; then
    echo "❌ No existe dist/SistemaIngresos"
    exit 1
fi

# 2. Crear estructura de la .app
echo "→ Creando estructura..."
mkdir -p "dist/SistemaIngresos.app/Contents/MacOS"
mkdir -p "dist/SistemaIngresos.app/Contents/Resources"

# 3. Mover el ejecutable y _internal a Resources
echo "→ Moviendo archivos..."
mv dist/SistemaIngresos/SistemaIngresos "dist/SistemaIngresos.app/Contents/Resources/"
mv dist/SistemaIngresos/_internal "dist/SistemaIngresos.app/Contents/Resources/"

# 4. Generar Info.plist
echo "→ Creando Info.plist..."
cat > "dist/SistemaIngresos.app/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>SistemaIngresos</string>
    <key>CFBundleDisplayName</key>
    <string>Sistema de Ingresos</string>
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
    cp icono.icns "dist/SistemaIngresos.app/Contents/Resources/"
fi

# 6. Crear lanzador
echo "→ Creando lanzador..."
cat > "dist/SistemaIngresos.app/Contents/MacOS/SistemaIngresos" << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$DIR/../Resources/SistemaIngresos" "$@"
EOF
chmod +x "dist/SistemaIngresos.app/Contents/MacOS/SistemaIngresos"

# 7. Quitar atributos extendidos
echo "→ Limpiando atributos extendidos..."
xattr -cr "dist/SistemaIngresos.app" 2>/dev/null || true

# 8. Firmar todo con ad-hoc
echo "→ Firmando binarios..."
find "dist/SistemaIngresos.app" -type f \( -name "*.so" -o -name "*.dylib" -o -name "Python" \) -exec codesign --force --sign - {} \; 2>/dev/null || true

find "dist/SistemaIngresos.app" -type d -name "*.framework" -exec codesign --force --deep --sign - {} \; 2>/dev/null || true

codesign --force --sign - "dist/SistemaIngresos.app/Contents/MacOS/SistemaIngresos" 2>/dev/null || true
codesign --force --deep --sign - "dist/SistemaIngresos.app" 2>/dev/null || true

# 9. Verificar
echo "→ Verificando firma..."
codesign -dv "dist/SistemaIngresos.app" 2>&1 | head -5 || true

echo ""
echo "✅ SistemaIngresos.app creada"