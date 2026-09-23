"""Extrai a spritesheet original (fundo verde) para uma sheet RGBA 4x4 uniforme."""
from PIL import Image
import numpy as np, os, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "Max_a_A_complete_2D_pixel_.png"
OUT = sys.argv[2] if len(sys.argv) > 2 else "app/src/main/assets/hero.png"
CELL = 64  # tamanho final de cada frame

im = Image.open(SRC).convert("RGB")
a = np.array(im).astype(int)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
green = (g > 80) & (g > r + 25) & (g > b + 25)
fg = ~green

def bands(mask):
    out, s = [], None
    for i, v in enumerate(mask):
        if v and s is None: s = i
        if not v and s is not None: out.append((s, i - 1)); s = None
    if s is not None: out.append((s, len(mask) - 1))
    return out

rgba = np.dstack([a, np.where(green, 0, 255)]).astype(np.uint8)
# limpa franja verde: pixels semi-verdes viram transparentes tambem
full = Image.fromarray(rgba, "RGBA")

rows = bands(fg.any(1))
assert len(rows) == 4, rows
boxes = []
for (y0, y1) in rows:
    cols = bands(fg[y0:y1 + 1].any(0))
    assert len(cols) == 4, cols
    boxes.append([(c0, y0, c1 + 1, y1 + 1) for (c0, c1) in cols])

# escala unica para todos os frames, baseada na maior altura
maxh = max(y1 - y0 for row in boxes for (x0, y0, x1, y1) in row)
maxw = max(x1 - x0 for row in boxes for (x0, y0, x1, y1) in row)
scale = (CELL - 2) / float(max(maxh, maxw))

sheet = Image.new("RGBA", (CELL * 4, CELL * 4), (0, 0, 0, 0))
for ri, row in enumerate(boxes):
    for ci, (x0, y0, x1, y1) in enumerate(row):
        crop = full.crop((x0, y0, x1, y1))
        w = max(1, int(round((x1 - x0) * scale)))
        h = max(1, int(round((y1 - y0) * scale)))
        crop = crop.resize((w, h), Image.NEAREST)
        # remove franjas de alpha parcial
        arr = np.array(crop).astype(int)
        arr[..., 3] = np.where(arr[..., 3] > 128, 255, 0)
        # despill: remove residuo esverdeado das bordas
        gg = arr[..., 1]
        lim = np.maximum(arr[..., 0], arr[..., 2])
        spill = (gg > lim + 10) & (arr[..., 3] > 0)
        arr[..., 1] = np.where(spill, lim, gg)
        arr = arr.astype(np.uint8)
        crop = Image.fromarray(arr, "RGBA")
        px = ci * CELL + (CELL - w) // 2      # centralizado na horizontal
        py = ri * CELL + (CELL - h) - 1       # ancorado na base (pes)
        sheet.paste(crop, (px, py), crop)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
sheet.save(OUT)
print("ok", OUT, sheet.size, "cell", CELL)
