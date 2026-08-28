#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analisador de save data de PS3 (PARAM.SFO + PARAM.PFD)
Uso:
    python3 analisar_save.py <pasta_do_save>
    python3 analisar_save.py <arquivo_PARAM.SFO>

Exemplo:
    python3 analisar_save.py "BLES01831-SAVEDATA"

Ele mostra:
  - Lista de arquivos da pasta (tamanho e tipo detectado)
  - Campos do PARAM.SFO (TITLE_ID, SAVEDATA_DIRECTORY, ACCOUNT_ID,
    ATTRIBUTE, CATEGORY, títulos, etc.)
  - Estrutura do PARAM.PFD (arquivos protegidos por assinatura HMAC)
  - Avisos (ex.: save criptografado .EDAT, proteção de cópia, etc.)
"""

import os
import sys
import struct

FMT_NAMES = {0x0004: "binary", 0x0204: "utf8", 0x0404: "int32"}


# ----------------------------------------------------------------------------
# PARAM.SFO
# ----------------------------------------------------------------------------
def parse_sfo(data: bytes):
    """Retorna um dict ordenado key -> (fmt, data_len, valor_decodificado, bytes_raw)."""
    if len(data) < 0x14:
        raise ValueError("Arquivo pequeno demais para ser um SFO (%d bytes)." % len(data))

    magic = data[0:4]
    if magic != b"\x00PSF":
        raise ValueError("Magic invalido (esperado 00 50 53 46, achado %r). Nao parece ser PARAM.SFO." % magic)

    version = struct.unpack_from("<I", data, 0x04)[0]
    key_start = struct.unpack_from("<I", data, 0x08)[0]
    data_start = struct.unpack_from("<I", data, 0x0C)[0]
    num = struct.unpack_from("<I", data, 0x10)[0]

    entries = {}
    for i in range(num):
        off = 0x14 + i * 16
        key_off, fmt, data_len, data_max, data_off = struct.unpack_from("<HHIII", data, off)
        raw_key = data[key_start + key_off:]
        key = raw_key.split(b"\x00", 1)[0].decode("ascii", "replace")
        raw = data[data_start + data_off: data_start + data_off + data_len]
        if fmt == 0x0404:
            value = struct.unpack("<I", raw[:4])[0]
        elif fmt == 0x0204:
            value = raw.rstrip(b"\x00").decode("utf-8", "replace")
        else:
            value = raw
        entries[key] = (fmt, data_len, value, raw)

    return {
        "version": version,
        "entries": entries,
        "num_entries": num,
    }


def attribute_flags(value: int):
    """Decodifica os bits de ATTRIBUTE (info generica, sem assumir bit especifico)."""
    flags = []
    for bit in range(32):
        if value & (1 << bit):
            flags.append("bit%d" % bit)
    return flags


# ----------------------------------------------------------------------------
# PARAM.PFD
# ----------------------------------------------------------------------------
ENTRY_SIZE = 272
TABLE_OFFSET = 0x240
MAX_ENTRIES = 114


def parse_pfd(data: bytes):
    """Lista os arquivos protegidos dentro do PARAM.PFD (campos big-endian)."""
    info = {"size": len(data), "magic": data[4:8] if len(data) >= 8 else b""}
    if len(data) >= 16:
        info["version"] = struct.unpack_from(">Q", data, 8)[0]

    files = []
    if len(data) < 0x60 + 24:
        info["protected_files"] = files
        return info

    capacity = struct.unpack_from(">Q", data, 0x60)[0]
    num_used = struct.unpack_from(">Q", data, 0x60 + 16)[0]
    entry_table_off = 0x60 + 24 + capacity * 8

    for i in range(min(num_used, MAX_ENTRIES)):
        off = entry_table_off + i * ENTRY_SIZE
        if off + ENTRY_SIZE > len(data):
            break
        name_raw = data[off + 8: off + 8 + 65]
        name = name_raw.split(b"\x00", 1)[0].decode("utf-8", "replace")
        if not name:
            continue
        fsize = struct.unpack_from(">Q", data, off + 264)[0]
        files.append((name, fsize))
    info["protected_files"] = files
    return info


# ----------------------------------------------------------------------------
# Utilitários
# ----------------------------------------------------------------------------
def sniff_type(data: bytes) -> str:
    if data[:4] == b"\x89PNG":
        return "PNG (imagem)"
    if data[:3] == b"NPD":
        return "EDAT (possivel criptografia)"
    if data[:4] == b"\x00PSF":
        return "PARAM.SFO"
    if data[:4] == b"PDFB":
        return "PARAM.PFD"
    if data[:4] == b"\x00SDT" or data[:4] == b"SDAT":
        return "SDAT (possivel criptografia)"
    return "desconhecido"


def analyze_folder(folder: str):
    print("=" * 70)
    print("ANALISE DO SAVE: %s" % folder)
    print("=" * 70)

    files = sorted(os.listdir(folder))
    print("\n[1] ARQUIVOS NA PASTA:")
    for name in files:
        p = os.path.join(folder, name)
        if os.path.isdir(p):
            print("  DIR  %s/" % name)
            continue
        with open(p, "rb") as f:
            head = f.read(256)
        size = os.path.getsize(p)
        print("  %-20s %10d bytes   [%s]" % (name, size, sniff_type(head)))

    sfo_path = os.path.join(folder, "PARAM.SFO")
    if not os.path.exists(sfo_path):
        print("\n[!] PARAM.SFO nao encontrado nesta pasta.")
        return
    with open(sfo_path, "rb") as f:
        sfo = parse_sfo(f.read())

    print("\n[2] PARAM.SFO (version 0x%08X, %d campos):" % (sfo["version"], sfo["num_entries"]))
    for key, (fmt, dlen, value, raw) in sfo["entries"].items():
        if key == "ATTRIBUTE":
            flags = attribute_flags(value)
            print("  %-22s (%-6s len=%d) = 0x%08X  bits:%s" % (key, FMT_NAMES.get(fmt, fmt), dlen, value, flags))
            if value != 0:
                print("        ^^^ ATTRIBUTE != 0 -> normalmente indica PROTECAO DE COPIA (copy protected)")
        elif fmt == 0x0404:
            print("  %-22s (%-6s len=%d) = %d" % (key, FMT_NAMES.get(fmt, fmt), dlen, value))
        else:
            print("  %-22s (%-6s len=%d) = %r" % (key, FMT_NAMES.get(fmt, fmt), dlen, value))

    # destaques
    e = sfo["entries"]
    print("\n[3] RESUMO IMPORTANTE:")
    for key, label in [("TITLE_ID", "TITLE_ID (regiao/ID do jogo)"),
                       ("SAVEDATA_DIRECTORY", "SAVEDATA_DIRECTORY (nome da pasta)"),
                       ("ACCOUNT_ID", "ACCOUNT_ID (conta dona do save)"),
                       ("CATEGORY", "CATEGORY"),
                       ("ATTRIBUTE", "ATTRIBUTE")]:
        if key in e:
            fmt, dlen, value, raw = e[key]
            print("  %-26s = %s" % (label, value))

    pfd_path = os.path.join(folder, "PARAM.PFD")
    if os.path.exists(pfd_path):
        with open(pfd_path, "rb") as f:
            pfd = parse_pfd(f.read())
        print("\n[4] PARAM.PFD (%d bytes, magic=%r):" % (pfd["size"], pfd["magic"]))
        if "version" in pfd:
            print("  version: %d" % pfd["version"])
        prot = pfd["protected_files"]
        print("  %d arquivo(s) protegido(s) por assinatura HMAC:" % len(prot))
        sfo_protected = False
        for name, size in prot:
            mark = "  <-- PARAM.SFO esta protegido (precisa re-assinar o PFD ao edita-lo)" if name.upper() == "PARAM.SFO" else ""
            if name.upper() == "PARAM.SFO":
                sfo_protected = True
            print("    - %-24s (%d bytes)%s" % (name, size, mark))
        if not sfo_protected:
            print("  (PARAM.SFO nao esta listado no PFD - menos comum, mas acontece em jogos antigos)")
    else:
        print("\n[4] PARAM.PFD nao encontrado (save nao tem assinaturas).")

    print("\n" + "=" * 70)
    print("DICA: para usar em outro jogo/regiao, voce precisa que TITLE_ID")
    print("bata com o jogo alvo (NPEB01378) e que SAVEDATA_DIRECTORY seja")
    print("o nome de pasta que a versao NPEB01378 espera.")
    print("=" * 70)


def main():
    if len(sys.argv) != 2:
        print("Uso: python3 analisar_save.py <pasta_do_save | PARAM.SFO>")
        sys.exit(1)
    target = sys.argv[1]
    if os.path.isdir(target):
        analyze_folder(target)
    else:
        with open(target, "rb") as f:
            sfo = parse_sfo(f.read())
        print("PARAM.SFO analisado (%s):" % target)
        for key, (fmt, dlen, value, raw) in sfo["entries"].items():
            print("  %-22s (%-6s) = %r" % (key, FMT_NAMES.get(fmt, fmt), value))


if __name__ == "__main__":
    main()
