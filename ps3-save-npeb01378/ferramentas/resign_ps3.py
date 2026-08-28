#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Re-assinador de save de PS3 (PARAM.PFD) + troca de SAVEDATA_DIRECTORY.

O que faz:
  1. Lê a pasta do save (deve conter PARAM.SFO e PARAM.PFD).
  2. Troca o SAVEDATA_DIRECTORY no PARAM.SFO pelo novo nome (mesma largura).
  3. Re-assina o PARAM.PFD usando as chaves "universais" (as mesmas que o
     Bruteforce Save Data usa no destravamento "para qualquer conta"):
       - console_id            = 16 bytes zerados
       - authentication_id     = PSID padrão "1010000001000003"
       - disc_hash_key         = fallback universal
       - savegame_param_sfo_key= chave fixa do formato de save
     Isso torna o save aceito em QUALQUER PS3, sem precisar do IDPS do usuário.

  4. Gera a pasta de saída pronta para copiar/FTP para o PS3.

IMPORTANTE:
  - O arquivo de progresso (ex.: GAME1) NÃO é re-criptografado: ele continua
    usando a chave de jogo (secure_file_id) original. Em jogos onde o
    secure_file_id é o mesmo entre regiões (quase todos, incluindo os LEGO
    da TT Games), o save carrega normalmente na outra região.
  - Uso local/offline apenas.

Uso:
    python3 resign_ps3.py <pasta_origem> <novo_diretorio> [--out <pasta_saida>]

Exemplo:
    python3 resign_ps3.py BLES01831000 NPEB01378000 --out NPEB01378000

A pasta de saída fica pronta no formato PS3/SAVEDATA/<novo_diretorio>/.
"""

import hashlib
import hmac
import os
import shutil
import struct
import subprocess
import sys

# ---------------------------------------------------------------------------
# Constantes fixas do formato de save (PS3). Os valores "obfuscados" vêm do
# código do Apollo (xor_key aplicado por setup_key()).
# ---------------------------------------------------------------------------
XOR_KEY = bytes([0xD4, 0xD1, 0x6B, 0x0C, 0x5D, 0xB0, 0x87, 0x91])


def deobfuscate(hexstr: bytes) -> bytes:
    return bytes(b ^ XOR_KEY[i % 8] for i, b in enumerate(hexstr))


SYSCON_MANAGER_KEY = deobfuscate(bytes.fromhex("00C2D39A3E51790EA1C55637E9E6D5E5"))
KEYGEN_KEY = deobfuscate(bytes.fromhex("BFCBA5AE1B07C26C5B421D37CFB5135C8799508E"))
SAVEGAME_PARAM_SFO_KEY = deobfuscate(bytes.fromhex("D8D96B0254B58395D9D0640C59B68593DDD7660F"))
FALLBACK_DISC_HASH_KEY = deobfuscate(bytes.fromhex("05108A07C1E4F9F94F5136C1CAA0491C"))
DEFAULT_PSID = bytes.fromhex("1010000001000003")  # authentication_id padrão
ZERO_CONSOLE_ID = b"\x00" * 16  # console_id "universal"

# Layout do PARAM.PFD
PFD_SIGNATURE_OFFSET = 0x20
PFD_SIGNATURE_SIZE = 64
PFD_HASH_TABLE_OFFSET = 0x60
PFD_HASH_TABLE_HEADER_SIZE = 24
PFD_ENTRY_SIZE = 272


def aes_128_cbc(key: bytes, iv: bytes, data: bytes, decrypt: bool) -> bytes:
    mode = "-d" if decrypt else "-e"
    p = subprocess.run(
        ["openssl", "enc", "-aes-128-cbc", mode, "-K", key.hex(), "-iv", iv.hex(), "-nopad"],
        input=data,
        capture_output=True,
    )
    if p.returncode != 0:
        raise RuntimeError("openssl falhou: " + p.stderr.decode())
    return p.stdout


def hmac_sha1(key: bytes, *parts: bytes) -> bytes:
    h = hmac.new(key, digestmod=hashlib.sha1)
    for part in parts:
        h.update(part)
    return h.digest()


def patch_sfo_directory(sfo: bytes, old_dir: str, new_dir: str) -> bytes:
    """Troca o valor de SAVEDATA_DIRECTORY no SFO (substituição direta)."""
    if len(old_dir) != len(new_dir):
        raise ValueError(
            "Os nomes precisam ter o mesmo tamanho (%d != %d). "
            "O diretório alvo deve ser derivado do ID alvo (ex.: BLES01831000 -> NPEB01378000)."
            % (len(old_dir), len(new_dir))
        )
    old_b = old_dir.encode("utf-8")
    new_b = new_dir.encode("utf-8")
    count = sfo.count(old_b)
    if count == 0:
        raise ValueError("String %r não encontrada no PARAM.SFO." % old_dir)
    if count != 1:
        raise ValueError("String %r aparece %d vezes (esperava 1)." % (old_dir, count))
    return sfo.replace(old_b, new_b)


def resign_pfd(pfd: bytes, new_sfo: bytes) -> bytes:
    """Re-assina o PARAM.PFD para o novo PARAM.SFO, com chaves universais."""
    out = bytearray(pfd)

    header_key = pfd[0x10:0x20]  # IV
    sig = aes_128_cbc(SYSCON_MANAGER_KEY, header_key, pfd[PFD_SIGNATURE_OFFSET:PFD_SIGNATURE_OFFSET + PFD_SIGNATURE_SIZE], decrypt=True)
    bottom_hash = sig[0:20]
    top_hash = sig[20:40]
    hash_key = sig[40:60]

    real_hash_key = hmac_sha1(KEYGEN_KEY, hash_key)

    cap, num_reserved, num_used = struct.unpack_from(">QQQ", out, PFD_HASH_TABLE_OFFSET)
    entry_table_off = PFD_HASH_TABLE_OFFSET + PFD_HASH_TABLE_HEADER_SIZE + cap * 8
    sig_table_off = entry_table_off + num_reserved * PFD_ENTRY_SIZE

    def get_entry(i):
        off = entry_table_off + i * PFD_ENTRY_SIZE
        return out[off:off + PFD_ENTRY_SIZE]

    # 1) Atualiza file_hashes do PARAM.SFO (todos os 4, com chaves universais)
    sfo_keys = [SAVEGAME_PARAM_SFO_KEY, ZERO_CONSOLE_ID, FALLBACK_DISC_HASH_KEY, DEFAULT_PSID]
    for i in range(num_used):
        off = entry_table_off + i * PFD_ENTRY_SIZE
        name = bytes(out[off + 8:off + 8 + 65]).split(b"\x00", 1)[0].decode()
        if name.upper() == "PARAM.SFO":
            for j in range(4):
                h = hmac_sha1(sfo_keys[j], new_sfo)
                out[off + 144 + j * 20: off + 144 + j * 20 + 20] = h
            print("  [PARAM.SFO] file_hashes[0..3] atualizados")

    # 2) Recalcula os hashes de entrada (Y-table) de todas as entradas usadas
    def hash_index(name: str) -> int:
        h = 0
        for c in name.encode():
            h = (h << 5) - h + c
        h &= (1 << 64) - 1
        return h % cap

    for i in range(num_used):
        off = entry_table_off + i * PFD_ENTRY_SIZE
        entry = out[off:off + PFD_ENTRY_SIZE]
        name = bytes(entry[8:8 + 65]).split(b"\x00", 1)[0].decode()
        idx = hash_index(name)
        eh = hmac_sha1(real_hash_key, name.encode().ljust(65, b"\x00"), entry[80:272])
        out[sig_table_off + idx * 20: sig_table_off + idx * 20 + 20] = eh

    # 3) bottom_hash = HMAC(real_hash_key, tabela Y)
    sig_table_buf = bytes(out[sig_table_off: sig_table_off + cap * 20])
    new_bottom = hmac_sha1(real_hash_key, sig_table_buf)

    # 4) top_hash = HMAC(real_hash_key, hash table)  (não muda, mas recalcula)
    hash_table_buf = bytes(out[PFD_HASH_TABLE_OFFSET: PFD_HASH_TABLE_OFFSET + 24 + cap * 8])
    new_top = hmac_sha1(real_hash_key, hash_table_buf)

    # 5) Monta a assinatura e re-encripta
    new_sig = new_bottom + new_top + hash_key + sig[60:64]
    enc_sig = aes_128_cbc(SYSCON_MANAGER_KEY, header_key, new_sig, decrypt=False)
    out[PFD_SIGNATURE_OFFSET:PFD_SIGNATURE_OFFSET + PFD_SIGNATURE_SIZE] = enc_sig

    return bytes(out)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    src = sys.argv[1]
    new_dir = sys.argv[2].strip().upper()
    out = None
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]

    if not os.path.isdir(src):
        print("ERRO: pasta de origem não encontrada: %s" % src)
        sys.exit(1)

    sfo_path = os.path.join(src, "PARAM.SFO")
    pfd_path = os.path.join(src, "PARAM.PFD")
    if not os.path.exists(sfo_path) or not os.path.exists(pfd_path):
        print("ERRO: a pasta precisa conter PARAM.SFO e PARAM.PFD.")
        sys.exit(1)

    with open(sfo_path, "rb") as f:
        old_sfo = f.read()
    with open(pfd_path, "rb") as f:
        old_pfd = f.read()

    # descobre o diretório atual dentro do SFO (lê o campo SAVEDATA_DIRECTORY)
    old_dir = None
    # parse simples do SFO
    if old_sfo[:4] == b"\x00PSF":
        key_start = struct.unpack_from("<I", old_sfo, 0x08)[0]
        data_start = struct.unpack_from("<I", old_sfo, 0x0C)[0]
        num = struct.unpack_from("<I", old_sfo, 0x10)[0]
        for i in range(num):
            ko, fmt, dl, dm, do = struct.unpack_from("<HHIII", old_sfo, 0x14 + i * 16)
            key = old_sfo[key_start + ko:].split(b"\x00", 1)[0].decode()
            if key == "SAVEDATA_DIRECTORY":
                old_dir = old_sfo[data_start + do: data_start + do + dl].rstrip(b"\x00").decode()
                break
    if not old_dir:
        print("ERRO: não consegui ler SAVEDATA_DIRECTORY do PARAM.SFO.")
        sys.exit(1)

    print("Save origem          : %s" % src)
    print("SAVEDATA_DIRECTORY   : %s -> %s" % (old_dir, new_dir))

    new_sfo = patch_sfo_directory(old_sfo, old_dir, new_dir)
    new_pfd = resign_pfd(old_pfd, new_sfo)

    if out is None:
        parent = os.path.dirname(os.path.abspath(src))
        out = os.path.join(parent, new_dir)
    print("Pasta de saída       : %s" % out)

    if os.path.abspath(out) == os.path.abspath(src):
        print("ERRO: saída não pode ser igual à origem.")
        sys.exit(1)
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out, exist_ok=True)

    for name in sorted(os.listdir(src)):
        p = os.path.join(src, name)
        if os.path.isdir(p):
            continue
        upper = name.upper()
        if upper in ("PARAM.SFO", "PARAM.PFD", "PARAM.SFO_ORIGINAL"):
            continue
        shutil.copy2(p, os.path.join(out, name))

    with open(os.path.join(out, "PARAM.SFO"), "wb") as f:
        f.write(new_sfo)
    with open(os.path.join(out, "PARAM.PFD"), "wb") as f:
        f.write(new_pfd)

    print("\nConcluído!")
    print("  Arquivos na pasta de saída:")
    for name in sorted(os.listdir(out)):
        print("    - %s (%d bytes)" % (name, os.path.getsize(os.path.join(out, name))))
    print("\n  A pasta está pronta para ser copiada para o PS3 em:")
    print("  PS3/SAVEDATA/" + new_dir + "/  (via pendrive)  OU")
    print("  /dev_hdd0/home/000000XX/savedata/" + new_dir + "/  (via FTP, sem pendrive)")


if __name__ == "__main__":
    main()
