"""Prepara o fundo da tela de titulo em 480x270 (pixel art, escala inteira)."""
from PIL import Image
import os

W, H = 480, 270
src = Image.open("assets_src/title_raw.png").convert("RGB")

# corta para 16:9 exato e reduz para o tamanho logico do jogo
sw, sh = src.size
target = W / float(H)
if sw / float(sh) > target:
    nw = int(sh * target)
    src = src.crop(((sw - nw) // 2, 0, (sw - nw) // 2 + nw, sh))
else:
    nh = int(sw / target)
    src = src.crop((0, (sh - nh) // 2, sw, (sh - nh) // 2 + nh))

bg = src.resize((W, H), Image.LANCZOS)
# quantiza a paleta para reforcar o visual retro
bg = bg.quantize(colors=64, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")

os.makedirs("app/src/main/assets", exist_ok=True)
bg.save("app/src/main/assets/title_bg.png")
print("title ok", bg.size)
