#!/bin/bash
# crear_app_mac.sh
# Crea la .app SIN comprimir.

set -e

APP_NAME="Vet Suite"
APP_BIN="VetSuite"
APP_PATH="dist/${APP_NAME}.app"

if [ ! -d "dist/${APP_BIN}" ]; then
    echo "❌ No existe dist/${APP_BIN}"
    exit 1
fi

echo "→ Creando estructura..."
mkdir -p "${APP_PATH}/Contents/MacOS"
mkdir -p "${APP_PATH}/Contents/Resources"

echo "→ Moviendo archivos..."
mv "dist/${APP_BIN}/${APP_BIN}" "${APP_PATH}/Contents/Resources/"
mv "dist/${APP_BIN}/_internal" "${APP_PATH}/Contents/Resources/"

echo "→ Creando Info.plist..."
cat > "${APP_PATH}/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Vet Suite</string>
    <key>CFBundleDisplayName</key>
    <string>Vet Suite</string>
    <key>CFBundleIdentifier</key>
    <string>com.vetsuite.app</string>
    <key>CFBundleVersion</key>
    <string>2.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0.0</string>
    <key>CFBundleExecutable</key>
    <string>VetSuite</string>
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
cat > "${APP_PATH}/Contents/MacOS/${APP_BIN}" << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$DIR/../Resources/VetSuite" "$@"
EOF
chmod +x "${APP_PATH}/Contents/MacOS/${APP_BIN}"

echo "→ Limpiando atributos extendidos..."
xattr -cr "${APP_PATH}" 2>/dev/null || true

echo "→ Firmando binarios..."
find "${APP_PATH}" -type f \( -name "*.so" -o -name "*.dylib" -o -name "Python" \) -exec codesign --force --sign - {} \; 2>/dev/null || true
find "${APP_PATH}" -type d -name "*.framework" -exec codesign --force --deep --sign - {} \; 2>/dev/null || true
codesign --force --sign - "${APP_PATH}/Contents/MacOS/${APP_BIN}" 2>/dev/null || true
codesign --force --deep --sign - "${APP_PATH}" 2>/dev/null || true

echo "✅ ${APP_NAME}.app creada"
