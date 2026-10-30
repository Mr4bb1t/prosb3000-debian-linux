import os
import sys
import struct
import shutil

HEADER_MAGIC = b"IMAGEWTY"
MAIN_HEADER_SIZE = 1024
FILE_HEADERS_START = 0x400
ALIGNMENT = 1024

def compute_checksum(filepath):
    """Calcula a soma de palavras de 32 bits (little-endian) modulo 2^32."""
    total = 0
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            # alinha caso chunk nao seja multiplo de 4
            rem = len(chunk) % 4
            if rem != 0:
                chunk += b"\x00" * (4 - rem)
            words = struct.unpack(f"<{len(chunk)//4}I", chunk)
            total = (total + sum(words)) & 0xFFFFFFFF
    return total

def is_checksum_file(name):
    return len(name) > 5 and name.startswith("V") and name.endswith(".fex")

def unpack_image(img_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(img_path, "rb") as f:
        hdr = f.read(1024)
        if not hdr.startswith(HEADER_MAGIC):
            raise ValueError("Arquivo nao e uma imagem valida Allwinner IMAGEWTY")

        magic = hdr[:8].decode("latin1")
        header_version, header_size, base_ram, format_version, total_image_size, header_size_aligned, file_header_length = struct.unpack("<7I", hdr[8:36])
        usb_product_id, usb_vendor_id, hardware_id, firmware_id, unknown1, unknown2, num_files, unknown3 = struct.unpack("<8I", hdr[36:68])

        print(f"[*] IMAGEWTY detectado: {num_files} arquivos internos.")
        files = []
        for i in range(num_files):
            f.seek(FILE_HEADERS_START + i * file_header_length)
            fhdr = f.read(file_header_length)
            fn_len, fh_size = struct.unpack("<II", fhdr[:8])
            maintype = fhdr[8:16].decode("latin1", "ignore").strip("\x00")
            subtype = fhdr[16:32].decode("latin1", "ignore").strip("\x00")
            unknown0 = struct.unpack("<I", fhdr[32:36])[0]
            filename = fhdr[36:292].decode("latin1", "ignore").split("\x00")[0]
            stored_len, pad1, orig_len, pad2, offset = struct.unpack("<IIIIQ", fhdr[0x124:0x13C])

            files.append({
                "index": i + 1,
                "filename_length": fn_len,
                "file_header_size": fh_size,
                "maintype": maintype,
                "subtype": subtype,
                "unknown0": unknown0,
                "filename": filename,
                "stored_length": stored_len,
                "pad1": pad1,
                "original_length": orig_len,
                "pad2": pad2,
                "offset": offset
            })

        # Extrair cada arquivo
        for item in files:
            fname = item["filename"]
            f.seek(item["offset"])
            data = f.read(item["original_length"])
            dest = os.path.join(out_dir, fname)
            with open(dest, "wb") as out_f:
                out_f.write(data)
            print(f"    [+] Extraido: {fname:<25} ({item['original_length'] / (1024*1024):.2f} MB)")

        # Gravar image.cfg
        cfg_path = os.path.join(out_dir, "image.cfg")
        with open(cfg_path, "w", encoding="utf-8") as cfg:
            cfg.write("[IMAGE_CFG]\n")
            cfg.write(f'magic="{magic}";\n')
            cfg.write(f"header_version=0x{header_version:08X};\n")
            cfg.write(f"header_size=0x{header_size:08X};\n")
            cfg.write(f"base_ram=0x{base_ram:08X};\n")
            cfg.write(f"format_version=0x{format_version:08X};\n")
            cfg.write(f"total_image_size=0x{total_image_size:08X};\n")
            cfg.write(f"header_size_including_alignment=0x{header_size_aligned:08X};\n")
            cfg.write(f"file_header_length=0x{file_header_length:08X};\n")
            cfg.write(f"usb_product_id=0x{usb_product_id:08X};\n")
            cfg.write(f"usb_vendor_id=0x{usb_vendor_id:08X};\n")
            cfg.write(f"hardware_id=0x{hardware_id:08X};\n")
            cfg.write(f"firmware_id=0x{firmware_id:08X};\n")
            cfg.write(f"unknown_field_1=0x{unknown1:08X};\n")
            cfg.write(f"unknown_field_2=0x{unknown2:08X};\n")
            cfg.write(f"unknown_field_3=0x{unknown3:08X};\n")
            cfg.write(f"number_of_files=0x{num_files:08X};\n\n")

            cfg.write("[FILELIST]\n")
            for item in files:
                cfg.write(f"file_{item['index']} {{\n")
                cfg.write(f"filename_length=0x{item['filename_length']:08X};\n")
                cfg.write(f"file_header_size=0x{item['file_header_size']:08X};\n")
                cfg.write(f'maintype="{item["maintype"]}";\n')
                cfg.write(f'subtype="{item["subtype"]}";\n')
                cfg.write(f"unknown0=0x{item['unknown0']:08X};\n")
                cfg.write(f'filename="{item["filename"]}";\n')
                cfg.write(f'source_path="{item["filename"]}";\n')
                cfg.write(f"stored_length=0x{item['stored_length']:08X};\n")
                cfg.write(f"pad1=0x{item['pad1']:08X};\n")
                cfg.write(f"original_length=0x{item['original_length']:08X};\n")
                cfg.write(f"pad2=0x{item['pad2']:08X};\n")
                cfg.write(f"offset=0x{item['offset']:08X};\n")
                cfg.write("}\n")
        print(f"[OK] Descompactacao concluida com sucesso em: {out_dir}")

def repack_image(dump_dir, out_img_path):
    cfg_path = os.path.join(dump_dir, "image.cfg")
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"Arquivo image.cfg nao encontrado em {dump_dir}")

    # Ler config
    cfg_lines = open(cfg_path, "r", encoding="utf-8").read().splitlines()
    hdr = {}
    files = []
    curr_file = None

    for line in cfg_lines:
        line = line.strip().rstrip(";")
        if not line or line.startswith(";"):
            continue
        if line.startswith("file_") and "{" in line:
            curr_file = {}
            continue
        if line == "}":
            if curr_file:
                files.append(curr_file)
                curr_file = None
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip()
            is_quoted = v.startswith('"') and v.endswith('"')
            v = v.strip('"')
            if not is_quoted and (v.startswith("0x") or v.startswith("0X")):
                val = int(v, 16)
            elif not is_quoted and v.isdigit():
                val = int(v)
            else:
                val = v
            if curr_file is not None:
                curr_file[k] = val
            else:
                hdr[k] = val

    num_files = len(files)
    file_header_len = hdr.get("file_header_length", 1024)
    print(f"[*] Repacotando {num_files} arquivos para: {out_img_path}...")

    # Calcular offsets e comprimentos alinhados
    offset = FILE_HEADERS_START + num_files * file_header_len
    for item in files:
        src = os.path.join(dump_dir, item.get("source_path", item["filename"]))
        size = os.path.getsize(src)
        # se for arquivo de checksum V*.fex, tamanho original e 4
        if is_checksum_file(item["filename"]):
            size = 4
        stored = (size + ALIGNMENT - 1) // ALIGNMENT * ALIGNMENT
        item["original_length"] = size
        item["stored_length"] = stored
        item["offset"] = offset
        offset += stored

    total_image_size = offset
    hdr["total_image_size"] = total_image_size

    # Preparar checksums para todos os arquivos V*.fex
    v_checksums = {}
    for item in files:
        fname = item["filename"]
        if is_checksum_file(fname):
            target_name = fname[1:] # remove 'V'
            target_path = os.path.join(dump_dir, target_name)
            if os.path.exists(target_path):
                chk = compute_checksum(target_path)
                v_checksums[fname] = chk
                print(f"    [CHK] {fname} ({target_name}) = 0x{chk:08X}")

    # Escrever cabecalho global
    out_dir = os.path.dirname(out_img_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    temp_img = out_img_path + ".tmp"
    with open(temp_img, "wb") as out:
        # Header global (1024 bytes)
        ghdr = bytearray(MAIN_HEADER_SIZE)
        ghdr[0:8] = HEADER_MAGIC
        struct.pack_into("<7I", ghdr, 8,
            hdr["header_version"],
            hdr["header_size"],
            hdr["base_ram"],
            hdr["format_version"],
            hdr["total_image_size"],
            hdr["header_size_including_alignment"],
            hdr["file_header_length"]
        )
        struct.pack_into("<8I", ghdr, 36,
            hdr["usb_product_id"],
            hdr["usb_vendor_id"],
            hdr["hardware_id"],
            hdr["firmware_id"],
            hdr["unknown_field_1"],
            hdr["unknown_field_2"],
            num_files,
            hdr["unknown_field_3"]
        )
        out.write(ghdr)

        # Escrever cabecalhos de cada arquivo
        for item in files:
            fhdr = bytearray(file_header_len)
            struct.pack_into("<II", fhdr, 0, len(item["filename"]), item.get("file_header_size", file_header_len))
            mtype = str(item.get("maintype", "")).encode("latin1")[:8]
            fhdr[8:8+len(mtype)] = mtype
            stype = str(item.get("subtype", "")).encode("latin1")[:16]
            fhdr[16:16+len(stype)] = stype
            struct.pack_into("<I", fhdr, 32, item.get("unknown0", 0))
            fn = str(item.get("filename", "")).encode("latin1")[:256]
            fhdr[36:36+len(fn)] = fn
            struct.pack_into("<IIIIQ", fhdr, 0x124,
                item["stored_length"],
                item.get("pad1", 0),
                item["original_length"],
                item.get("pad2", 0),
                item["offset"]
            )
            out.write(fhdr)

        # Escrever dados de cada arquivo
        for item in files:
            fname = item["filename"]
            src = os.path.join(dump_dir, item.get("source_path", fname))
            out.seek(item["offset"])

            if is_checksum_file(fname):
                chk_val = v_checksums.get(fname, 0)
                out.write(struct.pack("<I", chk_val))
            else:
                with open(src, "rb") as in_f:
                    while chunk := in_f.read(65536):
                        out.write(chunk)

            # Preenchimento de alinhamento
            pad = item["stored_length"] - item["original_length"]
            if pad > 0:
                out.write(b"\x00" * pad)

    if os.path.exists(out_img_path):
        os.remove(out_img_path)
    os.rename(temp_img, out_img_path)
    final_sz = os.path.getsize(out_img_path)
    print(f"[OK] Firmware repacotado com sucesso!")
    print(f"     Arquivo: {out_img_path}")
    print(f"     Tamanho: {final_sz / (1024*1024):.2f} MB ({final_sz} bytes)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python allwinner_img.py unpack <firmware.img> <pasta_saida>")
        print("     python allwinner_img.py repack <pasta_dump> <novo_firmware.img>")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "unpack":
        unpack_image(sys.argv[2], sys.argv[3])
    elif cmd == "repack":
        repack_image(sys.argv[2], sys.argv[3])
    else:
        print(f"Comando desconhecido: {cmd}")
