import os
import sys
import tarfile
import urllib.request
import io
import shutil

WORKDIR = r"D:\PROSB3000_BACKUP\server_repack"
SRC_TAR = r"D:\PROSB3000_BACKUP\prosb3000_server_custom.tar.gz"
OUT_TAR = r"D:\PROSB3000_BACKUP\prosb3000_server_custom_debloat.tar.gz"

DEB_URLS = [
    # Pillow e dependencias armhf
    "http://ftp.debian.org/debian/pool/main/p/pillow/python3-pil_9.4.0-1.1+deb12u1_armhf.deb",
    "http://ftp.debian.org/debian/pool/main/libi/libimagequant/libimagequant0_2.17.0-1_armhf.deb",
    "http://ftp.debian.org/debian/pool/main/libw/libwebp/libwebp7_1.2.4-0.2+deb12u1_armhf.deb",
    "http://ftp.debian.org/debian/pool/main/libw/libwebp/libwebpmux3_1.2.4-0.2+deb12u1_armhf.deb",
    "http://ftp.debian.org/debian/pool/main/t/tiff/libtiff6_4.5.0-6+deb12u2_armhf.deb",
    # Fontes DejaVu Monospace
    "http://ftp.debian.org/debian/pool/main/f/fonts-dejavu/fonts-dejavu-core_2.37-6_all.deb",
    # fbterm
    "http://ftp.debian.org/debian/pool/main/f/fbterm/fbterm_1.7-5_armhf.deb"
]

def extract_deb_to_dir(deb_data, target_dir):
    # Formato ar: !<arch>\n seguido de headers de 60 bytes
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
            # Extrair data.tar.*
            tar_stream = io.BytesIO(file_data)
            with tarfile.open(fileobj=tar_stream, mode="r:*") as tf:
                tf.extractall(target_dir, filter='fully_trusted')
            print(f"      [OK] Extraido: {name} para rootfs")
            return True
    return False

def main():
    print("[*] Iniciando preparacao do rootfs customizado...")
    if os.path.exists(WORKDIR):
        print(f"[*] Limpando {WORKDIR}...")
        shutil.rmtree(WORKDIR, ignore_errors=True)
    os.makedirs(WORKDIR, exist_ok=True)

    print(f"[*] Descompactando {SRC_TAR}...")
    with tarfile.open(SRC_TAR, "r:gz") as tar:
        tar.extractall(WORKDIR, filter='fully_trusted')
    print("    [OK] Tarball descompactado!")

    debian_dir = os.path.join(WORKDIR, "debian")
    os.makedirs(debian_dir, exist_ok=True)

    # 1. Baixar e extrair debs diretamente no debian chroot
    print("[*] Baixando e instalando pacotes deb (PIL, fonts, fbterm)...")
    for url in DEB_URLS:
        fname = url.split("/")[-1]
        print(f"    [-] Baixando {fname}...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            extract_deb_to_dir(data, debian_dir)
        except Exception as e:
            print(f"    [WARN] Erro ao baixar/extrair {fname}: {e}")

    # 2. Copiar server_screen.py
    src_screen = r"c:\Users\hp909\Downloads\PROSB300-SERVER\server_screen.py"
    shutil.copyfile(src_screen, os.path.join(WORKDIR, "server_screen.py"))
    
    bin_dir = os.path.join(debian_dir, "usr", "local", "bin")
    os.makedirs(bin_dir, exist_ok=True)
    shutil.copyfile(src_screen, os.path.join(bin_dir, "server_screen.py"))
    print("    [OK] server_screen.py instalado em /data e /usr/local/bin")

    # 3. Copiar scripts de inicializacao
    src_ligar = r"c:\Users\hp909\Downloads\PROSB300-SERVER\ligar-servidor.sh"
    shutil.copyfile(src_ligar, os.path.join(WORKDIR, "ligar-servidor.sh"))

    src_boot = r"c:\Users\hp909\Downloads\PROSB300-SERVER\debian-boot.sh"
    svc_dir = os.path.join(WORKDIR, "adb", "service.d")
    os.makedirs(svc_dir, exist_ok=True)
    shutil.copyfile(src_boot, os.path.join(svc_dir, "debian-boot.sh"))
    print("    [OK] ligar-servidor.sh e debian-boot.sh atualizados!")

    # 4. Criar o novo prosb3000_server_custom.tar.gz
    print(f"[*] Empacotando novo {SRC_TAR}...")
    with tarfile.open(SRC_TAR, "w:gz") as tar:
        for item in sorted(os.listdir(WORKDIR)):
            p = os.path.join(WORKDIR, item)
            tar.add(p, arcname=item)
    
    size_mb = os.path.getsize(SRC_TAR) / (1024 * 1024)
    print(f"[OK] Tarball final gerado com sucesso!")
    print(f"     Arquivo: {SRC_TAR} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    main()
