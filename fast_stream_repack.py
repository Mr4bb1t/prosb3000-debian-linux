import os
import io
import time
import tarfile
import urllib.request
import shutil

SRC_TAR = r"D:\PROSB3000_BACKUP\prosb3000_server_custom.tar.gz"
TMP_OUT_TAR = r"D:\PROSB3000_BACKUP\prosb3000_server_custom_new.tar.gz"

DEB_URLS = [
    "http://ftp.debian.org/debian/pool/main/p/pillow/python3-pil_9.4.0-1.1+deb12u1_armhf.deb",
    "http://ftp.debian.org/debian/pool/main/libi/libimagequant/libimagequant0_2.17.0-1_armhf.deb",
    "http://ftp.debian.org/debian/pool/main/libw/libwebp/libwebp7_1.2.4-0.2+deb12u1_armhf.deb",
    "http://ftp.debian.org/debian/pool/main/libw/libwebp/libwebpmux3_1.2.4-0.2+deb12u1_armhf.deb",
    "http://ftp.debian.org/debian/pool/main/t/tiff/libtiff6_4.5.0-6+deb12u2_armhf.deb",
    "http://ftp.debian.org/debian/pool/main/f/fonts-dejavu/fonts-dejavu-core_2.37-6_all.deb",
    "http://ftp.debian.org/debian/pool/main/f/fbterm/fbterm_1.7-5_armhf.deb"
]

def extract_data_tar_from_deb(deb_data):
    pos = 8
    while pos < len(deb_data):
        hdr = deb_data[pos : pos + 60]
        if len(hdr) < 60:
            break
        name = hdr[:16].decode("latin1").strip()
        size = int(hdr[48:58].decode("latin1").strip())
        pos += 60
        file_data = deb_data[pos : pos + size]
        pos += size
        if pos % 2 != 0:
            pos += 1
        
        if name.startswith("data.tar"):
            return file_data
    return None

def main():
    start_time = time.time()
    print("[*] Iniciando repacotamento em fluxo ultrarrapido (streaming in-memory)...")

    # 1. Baixar pacotes deb na memoria
    deb_payloads = []
    for url in DEB_URLS:
        fname = url.split("/")[-1]
        print(f"    [-] Baixando {fname}...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                deb_bytes = resp.read()
            data_tar = extract_data_tar_from_deb(deb_bytes)
            if data_tar:
                deb_payloads.append((fname, data_tar))
                print(f"        [OK] payload data.tar extraido ({len(data_tar)} bytes)")
        except Exception as e:
            print(f"        [AVISO] Nao foi possivel baixar {fname}: {e}")

    # 2. Ler arquivos locais customizados
    with open(r"c:\Users\hp909\Downloads\PROSB300-SERVER\server_screen.py", "rb") as f:
        screen_data = f.read()
    with open(r"c:\Users\hp909\Downloads\PROSB300-SERVER\ligar-servidor.sh", "rb") as f:
        ligar_data = f.read()
    with open(r"c:\Users\hp909\Downloads\PROSB300-SERVER\debian-boot.sh", "rb") as f:
        boot_data = f.read()

    to_replace = {
        "server_screen.py",
        "debian/usr/local/bin/server_screen.py",
        "ligar-servidor.sh",
        "adb/service.d/debian-boot.sh"
    }

    # 3. Stream copy de SRC_TAR para TMP_OUT_TAR
    print(f"[*] Processando {SRC_TAR}...")
    copied_count = 0
    with tarfile.open(SRC_TAR, "r:gz") as src_tar, tarfile.open(TMP_OUT_TAR, "w:gz") as dst_tar:
        for member in src_tar:
            name_clean = member.name.lstrip("./")
            if name_clean in to_replace:
                continue
            
            f_obj = src_tar.extractfile(member) if member.isreg() else None
            dst_tar.addfile(member, f_obj)
            copied_count += 1
            if copied_count % 3000 == 0:
                print(f"    [-] {copied_count} membros copiados...")

        print(f"    [OK] {copied_count} membros base copiados!")

        # Injetar nossos scripts customizados
        def add_file(arc_name, content, mode=0o755):
            ti = tarfile.TarInfo(name=arc_name)
            ti.size = len(content)
            ti.mode = mode
            ti.mtime = int(time.time())
            ti.type = tarfile.REGTYPE
            dst_tar.addfile(ti, io.BytesIO(content))
            print(f"    [+] Injetado: {arc_name} ({len(content)} bytes)")

        add_file("server_screen.py", screen_data)
        add_file("debian/usr/local/bin/server_screen.py", screen_data)
        add_file("ligar-servidor.sh", ligar_data)
        add_file("adb/service.d/debian-boot.sh", boot_data)

        # Injetar conteudo dos pacotes deb em debian/
        for fname, data_tar in deb_payloads:
            print(f"[*] Injetando debian rootfs de {fname}...")
            with tarfile.open(fileobj=io.BytesIO(data_tar), mode="r:*") as dtar:
                for dmember in dtar:
                    sub_name = dmember.name.lstrip("./")
                    if not sub_name:
                        continue
                    dmember.name = f"debian/{sub_name}"
                    df_obj = dtar.extractfile(dmember) if dmember.isreg() else None
                    dst_tar.addfile(dmember, df_obj)

    # 4. Substituir o tarball original
    print(f"[*] Substituindo {SRC_TAR}...")
    shutil.move(TMP_OUT_TAR, SRC_TAR)
    sz_mb = os.path.getsize(SRC_TAR) / (1024 * 1024)
    print(f"[OK] Tarball final pronto em {time.time() - start_time:.1f}s!")
    print(f"     Arquivo: {SRC_TAR} ({sz_mb:.2f} MB)")

if __name__ == "__main__":
    main()
