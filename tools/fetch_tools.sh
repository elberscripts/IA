#!/usr/bin/env bash
# Baixa as ferramentas de build para .build-tools/ (aapt2, android.jar, d8, ecj, apksigner).
# Usa pacotes npm que reempacotam os binários do Android SDK — funciona sem
# o sdkmanager do Google. Rode uma vez após clonar o repositório.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/.build-tools"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$DEST/bin"
cd "$TMP"
npm init -y >/dev/null 2>&1
echo ">> baixando pacotes"
npm pack aaptjs3@2.0.2 @drxiaozhi/minapk@0.4.0 >/dev/null

for f in *.tgz; do mkdir -p "x/${f%.tgz}"; tar xzf "$f" -C "x/${f%.tgz}"; done

case "$(uname -s)" in
  Linux)  OSDIR=linux ;;
  Darwin) OSDIR=darwin ;;
  *) echo "SO não suportado"; exit 1 ;;
esac

cp "x/aaptjs3-2.0.2/package/bin/x64/$OSDIR/aapt2" "$DEST/bin/aapt2"
chmod +x "$DEST/bin/aapt2"
cp x/drxiaozhi-minapk-0.4.0/package/tools/{android.jar,apksigner.jar,d8.jar,ecj-3.45.0.jar} "$DEST/"

echo ">> pronto:"
ls -lh "$DEST" "$DEST/bin"

if ! command -v java >/dev/null 2>&1; then
  echo
  echo "AVISO: Java não encontrado. Instale um JDK 17+ ou rode:"
  echo "  pip install jdk4py   # o build_apk.sh detecta automaticamente"
fi
