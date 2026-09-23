"""Gera os mipmaps do launcher a partir do icone pixel-art."""
from PIL import Image
import numpy as np, os

src = Image.open("assets_src/icon_raw.png").convert("RGBA")
# remove a moldura branca externa gerada pelo modelo
a = np.array(src)
w, h = src.size
m = int(min(w, h) * 0.055)
src = src.crop((m, m, w - m, h - m))

DENS = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
for d, s in DENS.items():
    outdir = f"app/src/main/res/mipmap-{d}"
    os.makedirs(outdir, exist_ok=True)
    legacy = src.resize((s, s), Image.LANCZOS)
    legacy.convert("RGB").save(f"{outdir}/ic_launcher.png")
    # round: mascara circular
    mask = Image.new("L", (s * 4, s * 4), 0)
    from PIL import ImageDraw
    ImageDraw.Draw(mask).ellipse((0, 0, s * 4 - 1, s * 4 - 1), fill=255)
    mask = mask.resize((s, s), Image.LANCZOS)
    rnd = legacy.convert("RGBA"); rnd.putalpha(mask)
    rnd.save(f"{outdir}/ic_launcher_round.png")
    # foreground adaptativo: conteudo em ~66% do canvas (safe zone)
    fs = int(s * 108 / 48)
    fg = Image.new("RGBA", (fs, fs), (0, 0, 0, 0))
    inner = src.resize((int(fs * 0.68), int(fs * 0.68)), Image.LANCZOS).convert("RGBA")
    # recorta cantos do inner para nao virar quadrado duro
    fg.paste(inner, ((fs - inner.width) // 2, (fs - inner.height) // 2), inner)
    fg.save(f"{outdir}/ic_launcher_fg.png")
    print(d, s, "->", fs)

# Play Store 512
src.resize((512, 512), Image.LANCZOS).convert("RGB").save("assets_src/playstore_icon_512.png")
print("ok")
