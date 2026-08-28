# Save convertido para **NPEB01378** — LEGO® Marvel™ Super Heroes

> **Status: conversão concluída e validada.** O save está pronto em
> `NPEB01378000.zip`, com a estrutura `PS3/SAVEDATA/NPEB01378000/`.
> Progresso do save: **99,9%** ("Fortschritt: 99,9%" / tempo 46:34:33 — save alemão).

---

## 1. O que eu fiz (análise do save)

O save original é o `BLES01831000.zip` que você colocou no `main` do repositório
(LEGO Marvel, disco EU/DE, ID `BLES01831`). Ao analisar, descobri que ele **já estava
destravado** (passou pelo Bruteforce Save Data antes):

| Campo | Valor no original | O que significa |
|---|---|---|
| `ACCOUNT_ID` | 16 bytes zerados | save "universal" (aceito em qualquer conta) |
| `ATTRIBUTE` | `0` | proteção de cópia já removida |
| `TITLE_ID` | *(ausente)* | não há trava de região no SFO |
| `SAVEDATA_DIRECTORY` | `BLES01831000` | **única coisa que precisava mudar** |
| `PARAM.PFD` | protege `PARAM.SFO` + `GAME1` | precisa re-assinar ao mexer no SFO |

Arquivos do save: `GAME1` (progresso, 88 KB), `ICON0.PNG`, `PARAM.SFO`, `PARAM.PFD`.

## 2. O que eu converti

1. Troquei `SAVEDATA_DIRECTORY` de `BLES01831000` → **`NPEB01378000`** no `PARAM.SFO`.
2. **Re-assinei o `PARAM.PFD`** do zero, usando as mesmas chaves "universais" que o
   Bruteforce usa no destravamento (`console_id` zerado, PSID padrão, chave de disco
   fallback). Isso torna o save aceito em **qualquer PS3, sem precisar do seu IDPS**.
3. **Validei tudo** (o equivalente ao `pfdtool -c`): os 4 hashes do `PARAM.SFO`, os
   hashes de entrada, `top_hash` e `bottom_hash` — **todos batem** ✔.

Resultado — pasta pronta:

```
PS3/SAVEDATA/NPEB01378000/
├── GAME1
├── ICON0.PNG
├── PARAM.SFO
└── PARAM.PFD
```

(Compactado em `NPEB01378000.zip`, ~135 KB, para baixar no celular.)

---

## 3. Como usar **sem pendrive** (FTP pelo celular) ⭐

Como você está no celular, o caminho é enviar o save por **FTP** direto para o PS3
(webMAN MOD / multiMAN criam o servidor FTP).

1. **No celular:** baixe o `NPEB01378000.zip` e extraia (apps: *Material Files*,
   *CX File Explorer*, *ZArchiver*…). Você vai ficar com a pasta `NPEB01378000`.

2. **No PS3 (HEN ativado):**
   - Abra o **webMAN MOD** → `Settings` → ative o **FTP Server**.
   - Ou abra o **multiMAN/IRISMAN** → ative o FTP.
   - Anote o **IP do PS3** (aparece no webMAN no XMB, ex.: `192.168.0.10`).

3. **No celular:** abra um app de FTP e conecte em:
   ```
   Host:  192.168.0.10   (o IP do seu PS3)
   Porta: 21
   Login/senha: em branco (webMAN não exige)
   ```

4. Navegue até:
   ```
   /dev_hdd0/home/00000001/savedata/
   ```
   (o número pode ser outro, ex. `00000002` — escolha a pasta do seu usuário).

5. **Envie a pasta `NPEB01378000` inteira** para dentro de `savedata/`.

6. Abra o jogo **NPEB01378** no PS3 e carregue o save (vai aparecer o slot com 99,9%).

> Se o save não aparecer no XMB de imediato: reinicie o jogo (ele reindexa ao salvar),
> ou faça **Rebuild Database** no menu de recuperação. O jogo em si lê a pasta direto.

---

## 4. Como usar **com pendrive** (alternativa)

- Pendrive **FAT32**.
- Estrutura exata:
  ```
  PENDRIVE:\PS3\SAVEDATA\NPEB01378000\  (os 4 arquivos dentro)
  ```
- No PS3: **Saved Data Utility (PS3)** → copiar do USB para o HDD.
- O save não tem proteção de cópia (já removida), então a cópia via XMB funciona.

---

## 5. Se o jogo disser "dados corrompidos" (plano B)

A única parte que **não** depende de mim é a chave de criptografia do arquivo
`GAME1` (o `secure_file_id` do jogo). Nos jogos LEGO/TT Games essa chave costuma ser
**a mesma entre regiões**, então deve carregar direto. Mas se o NPEB01378 recusar:

1. Instale o **Apollo Save Tool** (`.pkg` → Package Manager do HEN).
2. Coloque o save convertido em `dev_hdd0/home/000000XX/savedata/` (ou no USB).
3. Abra o **Apollo** → selecione o save → **"Apply changes & resign"**.
   - O Apollo detecta seu PS3 e re-assina com o banco de chaves correto do jogo
     (inclusive o `secure_file_id`), finalizando o que não dá para fazer no PC.

---

## 6. Ferramentas incluídas (para refazer/reutilizar)

| Arquivo | Função |
|---|---|
| `ferramentas/analisar_save.py` | Analisa um save (arquivos, PARAM.SFO, PARAM.PFD). |
| `ferramentas/resign_ps3.py` | Troca `SAVEDATA_DIRECTORY` + re-assina o PFD (chaves universais). |
| `ferramentas/converter.py` | Só troca TITLE_ID/pasta no SFO (sem re-assinar o PFD). |

---

## 7. Avisos

- **Uso local/offline apenas.** Não use para troféus/online (risco de ban).
- O `GAME1` continua no formato criptografado original — não foi re-criptografado,
  apenas re-assinado. Funciona se a chave do jogo for a mesma entre regiões (padrão
  dos LEGO).
- Faça backup: o save original continua no `main` do repositório (`BLES01831000.zip`).

### Referências
- Apollo Save Tool: https://github.com/bucanero/apollo-ps3
- pfdtool (flatz): https://github.com/bucanero/pfd_sfo_tools
- PARAM.SFO: https://www.psdevwiki.com/ps3/PARAM.SFO
- PARAM.PFD: https://www.psdevwiki.com/ps3/PARAM.PFD
