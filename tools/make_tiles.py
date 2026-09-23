"""Gera o tileset pixel-art 32x32 do mapa (estilo GBA retro)."""
from PIL import Image
import random, os

T = 32
NAMES = ["grass", "grass_flower", "path", "water", "tree", "rock",
         "roof", "wall", "sand", "hedge", "wood", "door"]
sheet = Image.new("RGBA", (T * len(NAMES), T), (0, 0, 0, 0))


def px(img, x, y, c):
    if 0 <= x < T and 0 <= y < T:
        img.putpixel((x, y), c)


def base(color):
    return Image.new("RGBA", (T, T), color)


def noise(img, colors, rnd, density=0.18):
    for y in range(T):
        for x in range(T):
            if rnd.random() < density:
                px(img, x, y, rnd.choice(colors))


def rect(img, x0, y0, x1, y1, c):
    for y in range(y0, y1):
        for x in range(x0, x1):
            px(img, x, y, c)


tiles = {}
rnd = random.Random(7)

# --- grama
g = base((88, 168, 72, 255))
noise(g, [(104, 184, 88, 255), (72, 148, 64, 255), (120, 200, 96, 255)], rnd, 0.22)
for i in range(26):
    x, y = rnd.randrange(T), rnd.randrange(T - 2)
    px(g, x, y, (64, 136, 56, 255)); px(g, x, y + 1, (64, 136, 56, 255))
tiles["grass"] = g

# --- grama com flores
gf = g.copy()
for (fx, fy, c) in [(6, 8, (248, 216, 96, 255)), (20, 5, (240, 120, 160, 255)),
                    (13, 22, (248, 248, 248, 255)), (25, 18, (240, 120, 160, 255))]:
    px(gf, fx, fy, c); px(gf, fx + 1, fy, c); px(gf, fx, fy + 1, c); px(gf, fx + 1, fy + 1, c)
    px(gf, fx, fy + 2, (64, 136, 56, 255))
tiles["grass_flower"] = gf

# --- caminho de terra
p = base((208, 176, 120, 255))
noise(p, [(224, 196, 144, 255), (192, 160, 104, 255), (176, 144, 96, 255)], rnd, 0.3)
for i in range(12):
    x, y = rnd.randrange(T), rnd.randrange(T)
    px(p, x, y, (160, 128, 88, 255))
tiles["path"] = p

# --- agua
w = base((56, 120, 208, 255))
for y in range(T):
    for x in range(T):
        if (x + y * 2) % 11 == 0:
            px(w, x, y, (88, 152, 232, 255))
        if (x * 3 - y) % 17 == 0:
            px(w, x, y, (40, 96, 176, 255))
for (wx, wy) in [(5, 7), (18, 14), (24, 25), (9, 21)]:
    for k in range(5):
        px(w, wx + k, wy, (168, 216, 248, 255))
    for k in range(3):
        px(w, wx + 1 + k, wy + 1, (120, 184, 240, 255))
tiles["water"] = w

# --- arvore (colisao)
t = g.copy()
trunk = (112, 76, 44, 255)
rect(t, 13, 20, 19, 31, trunk)
rect(t, 13, 20, 15, 31, (88, 56, 32, 255))
leaf_d, leaf_m, leaf_l = (32, 96, 48, 255), (48, 132, 64, 255), (80, 176, 88, 255)
for y in range(0, 22):
    for x in range(0, T):
        dx, dy = x - 15.5, y - 11.0
        d = (dx * dx) / 156.0 + (dy * dy) / 118.0
        if d <= 1.0:
            c = leaf_m
            if d > 0.82: c = leaf_d
            elif dx + dy < -6: c = leaf_l
            px(t, x, y, c)
rnd2 = random.Random(3)
for y in range(0, 22):
    for x in range(T):
        if t.getpixel((x, y))[:3] in (leaf_m[:3], leaf_l[:3]) and rnd2.random() < 0.12:
            px(t, x, y, leaf_d)
tiles["tree"] = t

# --- pedra
rk = g.copy()
body, hi, sh = (152, 152, 160, 255), (196, 196, 204, 255), (104, 104, 116, 255)
for y in range(10, 28):
    for x in range(4, 28):
        dx, dy = x - 16, y - 20
        if (dx * dx) / 130.0 + (dy * dy) / 72.0 <= 1.0:
            px(rk, x, y, body)
            if dy < -3 and dx < 2: px(rk, x, y, hi)
            if dy > 4: px(rk, x, y, sh)
tiles["rock"] = rk

# --- telhado
rf = base((188, 64, 64, 255))
for y in range(T):
    for x in range(T):
        if y % 8 in (6, 7): px(rf, x, y, (140, 40, 44, 255))
        if (x + (y // 8) * 4) % 8 == 0: px(rf, x, y, (156, 52, 52, 255))
        if y % 8 == 0: px(rf, x, y, (220, 96, 92, 255))
tiles["roof"] = rf

# --- parede
wl = base((228, 208, 176, 255))
for y in range(T):
    for x in range(T):
        if y % 10 == 9 or (x + (y // 10) * 5) % 10 == 0:
            px(wl, x, y, (196, 172, 140, 255))
tiles["wall"] = wl

# --- areia
sd = base((236, 216, 160, 255))
noise(sd, [(248, 232, 184, 255), (216, 196, 140, 255)], rnd, 0.25)
tiles["sand"] = sd

# --- cerca viva
hd = base((40, 108, 52, 255))
noise(hd, [(56, 132, 64, 255), (28, 84, 40, 255), (72, 156, 80, 255)], rnd, 0.35)
rect(hd, 0, 0, T, 2, (72, 156, 80, 255))
rect(hd, 0, 30, T, T, (24, 72, 36, 255))
tiles["hedge"] = hd

# --- piso de madeira
wd = base((176, 132, 84, 255))
for y in range(T):
    for x in range(T):
        if y % 8 == 7: px(wd, x, y, (128, 92, 56, 255))
        if (x + (y // 8) * 11) % 16 == 0: px(wd, x, y, (148, 108, 68, 255))
tiles["wood"] = wd

# --- porta
dr = wl.copy()
rect(dr, 8, 6, 24, 32, (120, 80, 44, 255))
rect(dr, 9, 7, 23, 31, (152, 104, 56, 255))
rect(dr, 15, 7, 17, 31, (120, 80, 44, 255))
rect(dr, 19, 18, 21, 20, (248, 208, 96, 255))
tiles["door"] = dr

for i, n in enumerate(NAMES):
    sheet.paste(tiles[n], (i * T, 0))

os.makedirs("app/src/main/assets", exist_ok=True)
sheet.save("app/src/main/assets/tiles.png")
print("tiles ok", sheet.size, NAMES)
