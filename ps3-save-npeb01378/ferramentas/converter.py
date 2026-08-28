#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversor de regiao/ID de save data de PS3 (muda o TITLE_ID e a pasta).

ATENCAO: este script NAO re-assina o PARAM.PFD (isso exige a chave do seu
console). Ele faz a parte "editavel no PC":
   1. Le o PARAM.SFO do save de origem.
   2. Troca TITLE_ID (e SAVEDATA_DIRECTORY, opcionalmente ACCOUNT_ID).
   3. Opcionalmente remove a protecao de copia (ATTRIBUTE = 0).
   4. Reconstroi o PARAM.SFO e copia tudo para uma pasta nova com o nome certo.

Depois disso, o save fica "pronto para re-assinar" no PS3 (Apollo Save Tool)
ou no PC (Bruteforce Save Data).

Uso:
    python3 converter.py <pasta_save_origem> <TITLE_ID_novo>
        [--savedata-dir DIR] [--account-id XXXXXXXX] [--unlock]
        [--out pasta_saida]

Exemplo (converter para NPEB01378):
    python3 converter.py "BLES01831-SAVEDATA" NPEB01378
        # auto-deriva SAVEDATA_DIRECTORY se a pasta comeca com BLES01831
"""

import os
import shutil
import struct
import sys


def parse_sfo(data: bytes):
    if len(data) < 0x14:
        raise ValueError("Arquivo pequeno demais para ser um SFO.")
    if data[0:4] != b"\x00PSF":
        raise ValueError("Magic invalido: nao e um PARAM.SFO.")
    version = struct.unpack_from("<I", data, 0x04)[0]
    key_start = struct.unpack_from("<I", data, 0x08)[0]
    data_start = struct.unpack_from("<I", data, 0x0C)[0]
    num = struct.unpack_from("<I", data, 0x10)[0]

    entries = []  # lista ordenada de (key, fmt, value_bytes_raw, decoded)
    for i in range(num):
        off = 0x14 + i * 16
        key_off, fmt, data_len, data_max, data_off = struct.unpack_from("<HHIII", data, off)
        raw_key = data[key_start + key_off:]
        key = raw_key.split(b"\x00", 1)[0].decode("ascii", "replace")
        raw = data[data_start + data_off: data_start + data_off + data_len]
        entries.append((key, fmt, raw))
    return entries


def build_sfo(entries):
    """entries: lista de (key, fmt, value_bytes). Reconstroi o SFO do zero."""
    num = len(entries)

    key_offsets = {}
    key_table = b""
    for key, fmt, val in entries:
        key_offsets[key] = len(key_table)
        key_table += key.encode("ascii") + b"\x00"

    # tabela de dados (cada valor alinhado a 4 bytes)
    data_table = b""
    data_meta = {}  # key -> (fmt, data_len, data_max, data_off, blob)
    for key, fmt, val in entries:
        blob = bytearray(val)
        if fmt == 0x0204 and (len(blob) == 0 or blob[-1] != 0):
            blob.append(0)  # utf8 precisa terminar em null
        blob = bytes(blob)
        padded_len = (len(blob) + 3) & ~3
        data_off = len(data_table)
        data_table += blob + b"\x00" * (padded_len - len(blob))
        if fmt == 0x0404:
            data_len = data_max = 4
        else:
            data_len = len(blob)
            data_max = padded_len
        data_meta[key] = (fmt, data_len, data_max, data_off)

    key_start = 0x14 + num * 16
    data_start = key_start + len(key_table)

    out = bytearray()
    out += struct.pack("<IIIII", 0x46535000, 0x00000101, key_start, data_start, num)
    for key, fmt, val in entries:
        fmt2, data_len, data_max, data_off = data_meta[key]
        out += struct.pack("<HHIII", key_offsets[key], fmt2, data_len, data_max, data_off)
    out += key_table
    out += data_table
    return bytes(out)


def set_string(entries, key, value, fmt_hint=None):
    """Substitui (ou adiciona) um campo string no SFO, preservando o fmt."""
    value_b = value.encode("utf-8")
    for i, (k, fmt, raw) in enumerate(entries):
        if k == key:
            new_fmt = fmt if fmt in (0x0204, 0x0004) else (fmt_hint or 0x0204)
            entries[i] = (k, new_fmt, value_b)
            return
    entries.append((key, fmt_hint or 0x0204, value_b))


def set_int32(entries, key, value):
    b = struct.pack("<I", value & 0xFFFFFFFF)
    for i, (k, fmt, raw) in enumerate(entries):
        if k == key:
            entries[i] = (k, 0x0404, b)
            return
    entries.append((key, 0x0404, b))


def get_str(entries, key):
    for k, fmt, raw in entries:
        if k == key:
            return raw.rstrip(b"\x00").decode("utf-8", "replace")
    return None


def get_int(entries, key):
    for k, fmt, raw in entries:
        if k == key and fmt == 0x0404:
            return struct.unpack("<I", raw[:4])[0]
    return None


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)

    src = args[0]
    new_title_id = args[1].strip().upper()

    savedata_dir = None
    account_id = None
    unlock = False
    out = None

    i = 2
    while i < len(args):
        a = args[i]
        if a == "--savedata-dir" and i + 1 < len(args):
            savedata_dir = args[i + 1]
            i += 2
        elif a == "--account-id" and i + 1 < len(args):
            account_id = args[i + 1]
            i += 2
        elif a == "--unlock":
            unlock = True
            i += 1
        elif a == "--out" and i + 1 < len(args):
            out = args[i + 1]
            i += 2
        else:
            print("Argumento desconhecido: %s" % a)
            print(__doc__)
            sys.exit(1)

    if not os.path.isdir(src):
        print("ERRO: pasta de origem nao encontrada: %s" % src)
        sys.exit(1)

    sfo_path = os.path.join(src, "PARAM.SFO")
    if not os.path.exists(sfo_path):
        print("ERRO: PARAM.SFO nao encontrado em %s" % src)
        sys.exit(1)

    with open(sfo_path, "rb") as f:
        entries = parse_sfo(f.read())

    old_title_id = get_str(entries, "TITLE_ID")
    old_dir = get_str(entries, "SAVEDATA_DIRECTORY")
    old_account = get_str(entries, "ACCOUNT_ID")
    old_attr = get_int(entries, "ATTRIBUTE")

    print("Origem: %s" % src)
    print("  TITLE_ID atual      : %s" % old_title_id)
    print("  SAVEDATA_DIRECTORY  : %s" % old_dir)
    print("  ACCOUNT_ID atual    : %s" % old_account)
    print("  ATTRIBUTE           : %s" % (("0x%08X" % old_attr) if old_attr is not None else "n/a"))
    print("  TITLE_ID novo       : %s" % new_title_id)

    if len(new_title_id) != 9:
        print("AVISO: TITLE_ID normalmente tem 9 caracteres. Confira se %s esta certo." % new_title_id)

    if savedata_dir is None:
        # tenta derivar: se a pasta atual comeca com o title id antigo, troca o prefixo
        if old_dir and old_title_id and old_dir.upper().startswith(old_title_id.upper()):
            savedata_dir = new_title_id + old_dir[len(old_title_id):]
            print("  SAVEDATA_DIRECTORY  : %s  (derivado automaticamente)" % savedata_dir)
        else:
            print("\nERRO: nao consegui derivar o SAVEDATA_DIRECTORY.")
            print("Informe o nome correto da pasta com --savedata-dir DIR")
            print("(voce encontra esse nome no save base criado pelo seu NPEB01378).")
            sys.exit(1)
    else:
        print("  SAVEDATA_DIRECTORY  : %s" % savedata_dir)

    # aplica mudancas
    set_string(entries, "TITLE_ID", new_title_id)
    set_string(entries, "SAVEDATA_DIRECTORY", savedata_dir)
    if account_id:
        set_string(entries, "ACCOUNT_ID", account_id.strip().upper())
        print("  ACCOUNT_ID novo     : %s" % account_id.strip().upper())
    if unlock:
        set_int32(entries, "ATTRIBUTE", 0)
        print("  ATTRIBUTE           : 0 (protecao de copia removida)")

    new_sfo = build_sfo(entries)

    # pasta de saida
    if out is None:
        parent = os.path.dirname(os.path.abspath(src))
        out = os.path.join(parent, savedata_dir)
    print("\nGerando pasta de saida: %s" % out)

    if os.path.abspath(out) == os.path.abspath(src):
        print("ERRO: a pasta de saida nao pode ser a mesma de origem.")
        sys.exit(1)

    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out, exist_ok=True)

    for name in sorted(os.listdir(src)):
        p = os.path.join(src, name)
        if os.path.isdir(p):
            continue
        if name.upper() == "PARAM.SFO":
            continue
        shutil.copy2(p, os.path.join(out, name))

    with open(os.path.join(out, "PARAM.SFO"), "wb") as f:
        f.write(new_sfo)

    print("Feito! Arquivos copiados para: %s" % out)
    print("\nPROXIMO PASSO (obrigatorio): re-assinar o PARAM.PFD.")
    print("  - No PS3 (HEN): abra o Apollo Save Tool -> abra este save ->")
    print("    'Apply changes & resign' (ou 'Resign' no menu de patches).")
    print("  - No PC: use o Bruteforce Save Data para re-assinar com o seu perfil.")
    print("  Somente depois disso coloque a pasta no pendrive em PS3/SAVEDATA/.")


if __name__ == "__main__":
    main()
