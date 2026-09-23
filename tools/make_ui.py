"""Processa o D-pad gerado (fundo magenta) em 5 botoes recortados com alpha."""
from PIL import Image
import numpy as np, os

src = Image.open("assets_src/joystick_raw.png").convert("RGB")
a = np.array(src).astype(int)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
mag = (r > 140) & (b > 140) & (g < r - 50) & (g < b - 50)
alpha = np.where(mag, 0, 255)
rgba = np.dstack([a, alpha]).astype(np.uint8)
img = Image.fromarray(rgba, "RGBA")

# pixeliza para um grid limpo de 96x96 e volta
S = 96
img = img.resize((S, S), Image.NEAREST)
arr = np.array(img)
arr[..., 3] = np.where(arr[..., 3] > 120, 255, 0)
img = Image.fromarray(arr, "RGBA")
os.makedirs("app/src/main/assets", exist_ok=True)
img = img.resize((192, 192), Image.NEAREST)
img.save("app/src/main/assets/dpad.png")
print("dpad ok", img.size)
