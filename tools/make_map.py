"""Gera o mapa do jogo (grid de tiles) como texto em assets/map.txt."""
import random, os

W, H = 60, 44
# legenda: . grama  , flores  # caminho  ~ agua  T arvore  O pedra
#          R telhado  W parede  S areia  H cerca  D porta  L madeira
g = [["." for _ in range(W)] for _ in range(H)]
rnd = random.Random(11)

def rect(x0, y0, x1, y1, ch):
    for y in range(y0, y1):
        for x in range(x0, x1):
            if 0 <= x < W and 0 <= y < H: g[y][x] = ch

def hline(y, x0, x1, ch): rect(x0, y, x1, y + 1, ch)
def vline(x, y0, y1, ch): rect(x, y0, x + 1, y1, ch)

# flores espalhadas
for _ in range(90):
    g[rnd.randrange(H)][rnd.randrange(W)] = ","

# borda de arvores (limite do mapa)
rect(0, 0, W, 2, "T"); rect(0, H - 2, W, H, "T")
rect(0, 0, 2, H, "T"); rect(W - 2, 0, W, H, "T")

# lago
for y in range(6, 15):
    for x in range(38, 54):
        dx, dy = (x - 46) / 8.0, (y - 10) / 4.2
        if dx * dx + dy * dy <= 1.0: g[y][x] = "~"
for y in range(5, 16):
    for x in range(37, 55):
        if g[y][x] == "~": continue
        if any(0 <= y+dy < H and 0 <= x+dx < W and g[y+dy][x+dx] == "~"
               for dy in (-1,0,1) for dx in (-1,0,1)):
            g[y][x] = "S"

# caminhos principais
hline(22, 2, W - 2, "#"); hline(23, 2, W - 2, "#")
vline(14, 2, H - 2, "#"); vline(15, 2, H - 2, "#")
vline(44, 16, H - 2, "#"); vline(45, 16, H - 2, "#")
hline(16, 14, 46, "#"); hline(17, 14, 46, "#")
hline(34, 14, 46, "#"); hline(35, 14, 46, "#")

def casa(x, y, w, h):
    rect(x, y, x + w, y + h, "W")          # corpo
    rect(x, y, x + w, y + 2, "R")          # telhado
    g[y + h - 1][x + w // 2] = "D"         # porta

casa(5, 6, 8, 7)
casa(21, 5, 9, 8)
casa(50, 25, 8, 7)
casa(20, 27, 10, 8)
casa(5, 30, 7, 6)

# praca central de madeira
rect(30, 19, 38, 27, "L")
for x in range(29, 39): 
    if g[18][x] == ".": g[18][x] = "S"

# cerca viva decorativa
hline(19, 4, 12, "H"); hline(28, 48, 56, "H")

# pedras e arvores decorativas
for _ in range(70):
    x, y = rnd.randrange(3, W - 3), rnd.randrange(3, H - 3)
    if g[y][x] in ".,":
        g[y][x] = "T" if rnd.random() < 0.65 else "O"

# garante spawn limpo
for y in range(20, 26):
    for x in range(12, 18):
        if g[y][x] in "TO": g[y][x] = "#"

os.makedirs("app/src/main/assets", exist_ok=True)
with open("app/src/main/assets/map.txt", "w") as f:
    f.write("\n".join("".join(r) for r in g) + "\n")
print("map ok", W, "x", H)
