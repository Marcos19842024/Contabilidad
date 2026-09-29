#!/bin/bash
# crear_app_mac.sh
# Crea la .app SIN comprimir.

set -e

APP_NAME="Sistema Ingresos"
APP_PATH="dist/${APP_NAME}.app"

if [ ! -d "dist/SistemaIngresos" ]; then
    echo "❌ No existe dist/SistemaIngresos"
    exit 1
fi

echo "→ Creando estructura..."
mkdir -p "${APP_PATH}/Contents/MacOS"
mkdir -p "${APP_PATH}/Contents/Resources"

echo "→ Moviendo archivos..."
mv dist/SistemaIngresos/SistemaIngresos "${APP_PATH}/Contents/Resources/"
mv dist/SistemaIngresos/_internal "${APP_PATH}/Contents/Resources/"

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

if [ -f "icono.icns" ]; then
    echo "→ Copiando ícono..."
    cp icono.icns "${APP_PATH}/Contents/Resources/"
fi

echo "→ Creando lanzador..."
cat > "${APP_PATH}/Contents/MacOS/SistemaIngresos" << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$DIR/../Resources/SistemaIngresos" "$@"
EOF
chmod +x "${APP_PATH}/Contents/MacOS/SistemaIngresos"

echo "→ Limpiando atributos extendidos..."
xattr -cr "${APP_PATH}" 2>/dev/null || true

echo "→ Firmando binarios..."
find "${APP_PATH}" -type f \( -name "*.so" -o -name "*.dylib" -o -name "Python" \) -exec codesign --force --sign - {} \; 2>/dev/null || true
find "${APP_PATH}" -type d -name "*.framework" -exec codesign --force --deep --sign - {} \; 2>/dev/null || true
codesign --force --sign - "${APP_PATH}/Contents/MacOS/SistemaIngresos" 2>/dev/null || true
codesign --force --deep --sign - "${APP_PATH}" 2>/dev/null || true

echo "✅ ${APP_NAME}.app creada"