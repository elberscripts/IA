#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/Max_a_Crie_uma_spritesheet.png"
MOD="$ROOT/RapperLaranja"
ATLAS="$MOD/images/characters/rapper-laranja.png"
XML="$MOD/images/characters/rapper-laranja.xml"
RELEASE="$ROOT/release/RapperLaranja-v1.0.0.zip"
CELL_SOURCE=181
CELL_OUTPUT=440
COLS=8
ROWS=6

for command in convert identify zip python3; do
  if ! command -v "$command" >/dev/null 2>&1; then
    printf 'Erro: comando obrigatório não encontrado: %s\n' "$command" >&2
    exit 1
  fi
done

if [[ ! -f "$SOURCE" ]]; then
  printf 'Erro: spritesheet de origem não encontrada: %s\n' "$SOURCE" >&2
  exit 1
fi

read -r width height < <(identify -format '%w %h\n' "$SOURCE")
expected_width=$((CELL_SOURCE * COLS))
expected_height=$((CELL_SOURCE * ROWS))
if [[ "$width" -ne "$expected_width" || "$height" -ne "$expected_height" ]]; then
  printf 'Erro: a imagem deve medir %sx%s, mas mede %sx%s.\n' \
    "$expected_width" "$expected_height" "$width" "$height" >&2
  exit 1
fi

mkdir -p "$MOD/images/characters" "$MOD/images/icons" "$ROOT/release"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Cria uma máscara chroma-key baseada na dominância do canal verde. Em seguida,
# reduz o spill verde nos pixels de borda sem apagar laranja, roxo ou tons de pele.
convert "$SOURCE" \
  \( +clone -alpha off -fx '(g > (1.22*max(r,b) + 0.035)) ? 0 : 1' \) \
  -alpha off -compose CopyOpacity -composite \
  -channel G -fx 'min(g,max(r,b)*1.04)' +channel \
  "$tmp/keyed.png"

# Aumenta cada célula de 181x181 para 440x440. O atlas final fica abaixo do
# limite comum de textura de 4096 px e mantém tamanho semelhante ao BF original.
convert "$tmp/keyed.png" \
  -filter Lanczos -resize "$((CELL_OUTPUT * COLS))x$((CELL_OUTPUT * ROWS))!" \
  -strip "$ATLAS"

# Ícone legado da barra de vida: estado normal à esquerda e perdendo à direita.
convert "$tmp/keyed.png" -crop 120x120+30+0 +repage -trim +repage \
  -filter Lanczos -resize 145x145 -gravity center -background none -extent 150x150 \
  "$tmp/icon-normal.png"
convert "$tmp/keyed.png" -crop 120x120+754+905 +repage -trim +repage \
  -filter Lanczos -resize 145x145 -gravity center -background none -extent 150x150 \
  "$tmp/icon-losing.png"
convert "$tmp/icon-normal.png" "$tmp/icon-losing.png" +append -strip \
  "$MOD/images/icons/icon-bf.png"

# Capa exibida pelo menu de mods.
convert -size 362x350 gradient:'#2A1047-#F47B20' \
  -fill 'rgba(255,255,255,0.10)' -draw 'circle 181,174 329,174' \
  "$tmp/mod-background.png"
convert "$tmp/keyed.png" -crop 181x181+0+0 +repage \
  -filter Lanczos -resize 330x330 "$tmp/mod-character.png"
convert "$tmp/mod-background.png" "$tmp/mod-character.png" \
  -gravity south -geometry +0-4 -composite -depth 8 -strip "$MOD/_polymod_icon.png"

# Gera o TextureAtlas/Sparrow com a ordem exata das seis linhas da imagem.
python3 - "$XML" "$CELL_OUTPUT" <<'PY'
from pathlib import Path
from xml.sax.saxutils import quoteattr
import sys

output = Path(sys.argv[1])
cell = int(sys.argv[2])
rows = [
    [("Rapper idle", 8)],
    [("Rapper singLEFT", 4), ("Rapper singLEFTmiss", 4)],
    [("Rapper singDOWN", 4), ("Rapper singDOWNmiss", 4)],
    [("Rapper singUP", 4), ("Rapper singUPmiss", 4)],
    [("Rapper singRIGHT", 4), ("Rapper singRIGHTmiss", 4)],
    [("Rapper hey", 4), ("Rapper scared", 4)],
]

lines = ['<?xml version="1.0" encoding="utf-8"?>',
         '<TextureAtlas imagePath="rapper-laranja.png">']
for row_index, groups in enumerate(rows):
    column = 0
    for prefix, count in groups:
        for frame in range(count):
            name = f'{prefix}{frame:04d}'
            attrs = {
                'name': name,
                'x': str(column * cell),
                'y': str(row_index * cell),
                'width': str(cell),
                'height': str(cell),
            }
            rendered = ' '.join(f'{key}={quoteattr(value)}' for key, value in attrs.items())
            lines.append(f'  <SubTexture {rendered} />')
            column += 1
    if column != 8:
        raise SystemExit(f'Linha {row_index + 1} tem {column} frames; esperado: 8')
lines.append('</TextureAtlas>')
output.write_text('\n'.join(lines) + '\n', encoding='utf-8')
PY

# O ZIP contém a pasta externa correta para ser extraído diretamente em mods/.
rm -f "$RELEASE"
(
  cd "$ROOT"
  zip -q -r "$RELEASE" RapperLaranja
)

printf 'Mod criado com sucesso:\n  %s\n' "$RELEASE"
