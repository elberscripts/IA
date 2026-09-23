# JoJo Quest 🎩

Jogo Android 2D top-down em pixel art retrô (estilo Pokémon GBA) com o Jotaro chibi.
Você anda livremente por um mapa de vila usando um D-pad de setas na tela,
coletando moedas de ouro que ficam guardadas no **Dex**.

**APK assinado:** [`build/JoJoQuest-release.apk`](build/JoJoQuest-release.apk)

| | |
|---|---|
| Pacote | `com.elber.jojoquest` |
| minSdk | **34 (Android 14)** |
| targetSdk | 34 |
| Assinatura | APK Signature Scheme **v2 + v3** |
| Tamanho | ~731 KB |
| Orientação | Paisagem |

---

## Como instalar no celular

1. Baixe `build/JoJoQuest-release.apk` para o telefone.
2. Abra o arquivo e permita **"Instalar apps desconhecidos"** para o app que estiver abrindo o APK (Arquivos / Chrome).
3. Instale e abra **JoJo Quest**.

> Precisa de Android 14 ou superior — em versões mais antigas o sistema recusa a instalação (é o `minSdk 34` que você pediu).

Via ADB:

```bash
adb install -r build/JoJoQuest-release.apk
```

---

## Como jogar

- **D-pad na esquerda da tela**: arraste ou toque nas setas para andar (8 direções, inclusive diagonais).
- O personagem anima o ciclo de caminhada e vira para a direção do movimento.
- Árvores, pedras, água, casas e cercas **bloqueiam** a passagem; caminhos, grama, areia e piso de madeira são andáveis.
- A câmera segue o herói e trava nas bordas do mapa.
- **Moedas de ouro** giram pelo mapa — encoste nelas para coletar. São 40 espalhadas.
- O HUD mostra a carteira de moedas, quantas faltam no mapa e a coordenada atual.
- **Tela de título**: "Novo Jogo" zera o progresso, "Continuar" retoma de onde parou.
- Botão voltar do Android retorna à tela de título (o progresso fica salvo).

---

## Estrutura do projeto

```
app/src/main/
├── AndroidManifest.xml          minSdk 34, fullscreen, landscape
├── assets/
│   ├── hero.png                 spritesheet 4x4 (64px) — baixo/cima/esq/dir
│   ├── tiles.png                tileset 12 tiles de 32px
│   ├── dpad.png                 botão direcional
│   ├── coin.png                 moeda animada (6 frames de rotação)
│   ├── coin_hud.png             ícone da moeda para o HUD
│   ├── title_bg.png             fundo da tela de título
│   └── map.txt                  mapa 60x44 em texto
├── java/com/elber/jojoquest/
│   ├── MainActivity.java        tela cheia imersiva (WindowInsetsController)
│   ├── GameView.java            SurfaceView + game loop + render
│   ├── GameMap.java             grid de tiles e colisão
│   ├── Player.java              movimento, animação, colisão por eixo
│   ├── Dpad.java                D-pad multitouch com 8 setores
│   ├── Dex.java                 catálogo + carteira de moedas (persistido)
│   ├── Coin.java                moeda coletável do mapa
│   ├── TitleScreen.java         tela inicial
│   └── FloatingText.java        efeito "+1" ao coletar
└── res/
    ├── mipmap-*/                ícone do launcher (legacy + adaptativo)
    └── values/                  strings, cores, tema

tools/
├── build_apk.sh                 build completo + assinatura
├── make_sprites.py              recorta a spritesheet original (chroma key verde)
├── make_tiles.py                gera o tileset
├── make_map.py                  gera o mapa
├── make_ui.py                   processa o D-pad
├── make_coin.py                 gera a moeda animada
├── make_title.py                prepara o fundo do título
├── make_icon.py                 gera os mipmaps do ícone
└── zipalign.py                  zipalign 4 bytes em Python

preview/                         versão web jogável (mesmos assets)
```

### O mapa

`assets/map.txt` é texto puro — dá pra editar à mão. Legenda:

| Char | Tile | Sólido |
|---|---|---|
| `.` | grama | não |
| `,` | grama com flores | não |
| `#` | caminho de terra | não |
| `~` | água | **sim** |
| `T` | árvore | **sim** |
| `O` | pedra | **sim** |
| `R` | telhado | **sim** |
| `W` | parede | **sim** |
| `S` | areia | não |
| `H` | cerca viva | **sim** |
| `L` | piso de madeira | não |
| `D` | porta | não |

Editou o mapa? É só rodar `bash tools/build_apk.sh` de novo.

---

## O Dex

`Dex.java` é o catálogo do jogo e, ao mesmo tempo, a carteira do jogador.
Tudo é persistido em `SharedPreferences`, então o progresso sobrevive a fechar o app.

**Carteira:** `coins()`, `addCoins(n)`, `spendCoins(n)`, `canAfford(n)`,
`totalEarned()`, `totalSpent()`.

**Catálogo:** 8 entradas, sendo 4 descobríveis e 4 compráveis com moedas.

| Entrada | Preço | Efeito |
|---|---|---|
| Jotaro, Moeda, A Vila, O Lago | — | só descoberta |
| Botas Velozes | 25 | +40% de velocidade *(já ativo no jogo)* |
| Lanterna | 40 | reservado |
| Amuleto Dourado | 80 | moedas valem o dobro *(já ativo)* |
| Boné Extra | 120 | cosmético |

`buy(id)` retorna `OK`, `ALREADY_OWNED`, `NOT_ENOUGH_COINS` ou `UNKNOWN_ENTRY`.
Um `Dex.Listener` avisa a HUD sempre que o saldo muda (é o que dispara o brilho
no contador). As moedas já pegas ficam marcadas por id (`markPicked`), então não
reaparecem ao reabrir o jogo — e `resetPickups()` devolve todas ao mapa.

---

## Como rebuildar o APK

```bash
bash tools/build_apk.sh
```

O script regenera todos os assets, compila e assina. Pipeline (sem Gradle,
funciona offline): `aapt2 compile` → `aapt2 link` → `ecj` → `d8` → `zip` →
`zipalign` → `apksigner`.

### Preview web

```bash
python3 -m http.server 3000 --directory preview
```

Abre em `http://localhost:3000` — jogável com teclado (WASD/setas) ou toque.

---

## ⚠️ Sobre a assinatura

O APK aqui está assinado com a keystore **de desenvolvimento** em
`keystore/jojoquest.jks` (senha `jojoquest123`), que **não está no Git**.
Serve pra instalar e testar no seu celular.

**Para publicar na Play Store**, gere a sua própria keystore de release e
guarde-a em local seguro — se perder, não dá para atualizar o app:

```bash
keytool -genkeypair -v \
  -keystore minha-release.jks -storetype PKCS12 \
  -alias jojoquest -keyalg RSA -keysize 2048 -validity 10950 \
  -dname "CN=Seu Nome, O=Sua Empresa, C=BR"
```

Depois rebuilde apontando para ela:

```bash
KEYSTORE=/caminho/minha-release.jks KEY_ALIAS=jojoquest \
STORE_PASS=suasenha KEY_PASS=suasenha \
bash tools/build_apk.sh
```

> Nota de direitos: Jotaro Kujo e JoJo's Bizarre Adventure são propriedade de
> Hirohiko Araki / Shueisha. Este projeto é um fan game sem fins comerciais —
> não publique na Play Store com esses assets.
