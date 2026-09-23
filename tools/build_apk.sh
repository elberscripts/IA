#!/usr/bin/env bash
# Compila e assina o APK do JoJo Quest sem depender do Gradle.
# Pipeline: aapt2 compile/link -> ecj (javac) -> d8 (dex) -> zip -> zipalign -> apksigner
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# shellcheck source=/dev/null
source tools/env.sh

APP=app
OUT=build
MIN_SDK=34
TARGET_SDK=34
PKG=com.elber.jojoquest
APK_NAME=JoJoQuest

KEYSTORE="${KEYSTORE:-$ROOT/keystore/jojoquest.jks}"
KEY_ALIAS="${KEY_ALIAS:-jojoquest}"
KEY_PASS="${KEY_PASS:-jojoquest123}"
STORE_PASS="${STORE_PASS:-jojoquest123}"

echo ">> limpando"
rm -rf "$OUT"
mkdir -p "$OUT"/{res,gen,classes,dex,apk}

echo ">> (re)gerando assets"
python3 tools/make_sprites.py  >/dev/null
python3 tools/make_tiles.py    >/dev/null
python3 tools/make_map.py      >/dev/null
python3 tools/make_ui.py       >/dev/null
python3 tools/make_icon.py     >/dev/null

echo ">> aapt2 compile (recursos)"
"$AAPT2" compile --dir "$APP/src/main/res" -o "$OUT/res/resources.zip"

echo ">> aapt2 link"
"$AAPT2" link \
  -I "$ANDROID_JAR" \
  --manifest "$APP/src/main/AndroidManifest.xml" \
  --java "$OUT/gen" \
  --min-sdk-version "$MIN_SDK" \
  --target-sdk-version "$TARGET_SDK" \
  --version-code 1 --version-name 1.0 \
  -A "$APP/src/main/assets" \
  -o "$OUT/apk/base.apk" \
  "$OUT/res/resources.zip"

echo ">> compilando Java (ecj, bytecode 8 + desugar via d8)"
find "$APP/src/main/java" "$OUT/gen" -name '*.java' > "$OUT/sources.txt"
"$JAVA" -jar "$ECJ" \
  -source 1.8 -target 1.8 -encoding UTF-8 -nowarn -proc:none \
  -bootclasspath "$ANDROID_JAR" \
  -d "$OUT/classes" \
  @"$OUT/sources.txt"

echo ">> d8 (dex)"
find "$OUT/classes" -name '*.class' > "$OUT/classes.txt"
"$JAVA" -cp "$D8" com.android.tools.r8.D8 \
  --release \
  --min-api "$MIN_SDK" \
  --lib "$ANDROID_JAR" \
  --output "$OUT/dex" \
  @"$OUT/classes.txt"

echo ">> empacotando"
cd "$OUT/dex"
zip -q -X "$ROOT/$OUT/apk/base.apk" classes*.dex
cd "$ROOT"

echo ">> keystore"
if [ ! -f "$KEYSTORE" ]; then
  mkdir -p "$(dirname "$KEYSTORE")"
  "$JAVA_HOME/bin/keytool" -genkeypair -v \
    -keystore "$KEYSTORE" -storetype PKCS12 \
    -alias "$KEY_ALIAS" -keyalg RSA -keysize 2048 -validity 10950 \
    -storepass "$STORE_PASS" -keypass "$KEY_PASS" \
    -dname "CN=JoJo Quest, OU=Games, O=elberscripts, L=Ipora, ST=Goias, C=BR" \
    >/dev/null 2>&1
  echo "   keystore criada em $KEYSTORE"
else
  echo "   usando keystore existente $KEYSTORE"
fi

echo ">> alinhando + assinando (v1+v2+v3)"
ALIGNED="$OUT/apk/aligned.apk"
python3 tools/zipalign.py "$OUT/apk/base.apk" "$ALIGNED"

FINAL="$OUT/${APK_NAME}-release.apk"
"$JAVA" -cp "$APKSIGNER" com.android.apksigner.ApkSignerTool sign \
  --ks "$KEYSTORE" \
  --ks-key-alias "$KEY_ALIAS" \
  --ks-pass "pass:$STORE_PASS" \
  --key-pass "pass:$KEY_PASS" \
  --min-sdk-version "$MIN_SDK" \
  --v1-signing-enabled true \
  --v2-signing-enabled true \
  --v3-signing-enabled true \
  --out "$FINAL" \
  "$ALIGNED"

"$JAVA" -cp "$APKSIGNER" com.android.apksigner.ApkSignerTool verify --print-certs -v "$FINAL"

echo
echo "APK pronto: $FINAL"
ls -lh "$FINAL"
