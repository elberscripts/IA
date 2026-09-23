"""zipalign 4 bytes em Python puro (substitui o zipalign do SDK).

Recria o zip garantindo que o offset dos dados de cada entrada STORED
seja multiplo de 4, usando o campo extra do cabecalho local como padding.
"""
import struct
import sys
import zipfile

ALIGN = 4
SO_ALIGN = 4096  # libs nativas precisam de alinhamento de pagina


def align_of(name, method):
    if method != zipfile.ZIP_STORED:
        return 1
    if name.endswith(".so"):
        return SO_ALIGN
    return ALIGN


def main(src, dst):
    zin = zipfile.ZipFile(src, "r")
    out = open(dst, "wb")
    central = []

    for info in zin.infolist():
        data = zin.read(info.filename)
        name = info.filename.encode("utf-8")
        method = info.compress_type
        if method == zipfile.ZIP_DEFLATED:
            import zlib
            co = zlib.compressobj(9, zlib.DEFLATED, -15)
            blob = co.compress(data) + co.flush()
        else:
            blob = data

        crc = zipfile.crc32(data) & 0xFFFFFFFF
        dostime = ((info.date_time[3] << 11) | (info.date_time[4] << 5)
                   | (info.date_time[5] // 2))
        dosdate = (((info.date_time[0] - 1980) << 9) | (info.date_time[1] << 5)
                   | info.date_time[2])

        offset = out.tell()
        header_len = 30 + len(name)
        a = align_of(info.filename, method)
        pad = (a - ((offset + header_len) % a)) % a
        extra = b"\0" * pad

        out.write(struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, 0, method,
                              dostime, dosdate, crc, len(blob), len(data),
                              len(name), len(extra)))
        out.write(name)
        out.write(extra)
        out.write(blob)

        central.append((name, method, dostime, dosdate, crc, len(blob),
                        len(data), offset, info.external_attr))

    cd_start = out.tell()
    for (name, method, dostime, dosdate, crc, csize, usize,
         offset, attr) in central:
        out.write(struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50, 20, 20, 0,
                              method, dostime, dosdate, crc, csize, usize,
                              len(name), 0, 0, 0, 0, attr, offset))
        out.write(name)
    cd_size = out.tell() - cd_start

    out.write(struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, len(central),
                          len(central), cd_size, cd_start, 0))
    out.close()
    zin.close()
    print("zipalign ok ->", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
