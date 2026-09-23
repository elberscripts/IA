"""Gera a spritesheet animada da moeda (6 frames de rotacao) a partir de coin_raw.png."""
from PIL import Image
import numpy as np, os

CELL = 32
FRAMES = 6

src = Image.open("assets_src/coin_raw.png").convert("RGB")
a = np.array(src).astype(int)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
mag = (r > 140) & (b > 140) & (g < r - 45) & (g < b - 45)
rgba = np.dstack([a, np.where(mag, 0, 255)]).astype(np.uint8)
img = Image.fromarray(rgba, "RGBA")

# recorta na bounding box da moeda
al = np.array(img)[..., 3]
ys, xs = np.where(al > 0)
img = img.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))

# quantiza para pixel art limpa
base = img.resize((CELL - 4, CELL - 4), Image.LANCZOS)
arr = np.array(base).astype(int)
arr[..., 3] = np.where(arr[..., 3] > 110, 255, 0)
# reforca a paleta dourada (evita cinza das bordas antialiased)
opaque = arr[..., 3] > 0
lum = (arr[..., 0] * 0.3 + arr[..., 1] * 0.59 + arr[..., 2] * 0.11)
PAL = [(58, 38, 8), (140, 96, 16), (206, 156, 28), (246, 208, 60), (255, 244, 170)]
idx = np.clip((lum / 255.0 * len(PAL)).astype(int), 0, len(PAL) - 1)
for i, c in enumerate(PAL):
    m = opaque & (idx == i)
    for ch in range(3):
        arr[..., ch] = np.where(m, c[ch], arr[..., ch])
base = Image.fromarray(arr.astype(np.uint8), "RGBA")

W, H = base.size
sheet = Image.new("RGBA", (CELL * FRAMES, CELL), (0, 0, 0, 0))

EDGE_DARK = (150, 110, 22, 255)
EDGE_LIGHT = (214, 170, 40, 255)

for f in range(FRAMES):
    # largura segue um cosseno: frente -> perfil -> frente
    t = f / float(FRAMES)
    w = max(2, int(round(abs(np.cos(np.pi * t)) * W)))
    if w >= 3:
        fr = base.resize((w, H), Image.NEAREST)
    else:
        # frame de perfil: barra vertical fina (a "borda" da moeda)
        fr = Image.new("RGBA", (max(2, w), H), (0, 0, 0, 0))
        d = np.zeros((H, fr.width, 4), dtype=np.uint8)
        pad = int(H * 0.12)
        d[pad:H - pad, :] = EDGE_LIGHT
        if fr.width > 1:
            d[pad:H - pad, 0] = EDGE_DARK
        fr = Image.fromarray(d, "RGBA")
    px = f * CELL + (CELL - fr.width) // 2
    py = (CELL - H) // 2
    sheet.paste(fr, (px, py), fr)

os.makedirs("app/src/main/assets", exist_ok=True)
sheet.save("app/src/main/assets/coin.png")

# icone estatico para o HUD (frame frontal)
hud = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
hud.paste(base, ((CELL - W) // 2, (CELL - H) // 2), base)
hud.save("app/src/main/assets/coin_hud.png")
print("coin ok", sheet.size, "frames", FRAMES)
