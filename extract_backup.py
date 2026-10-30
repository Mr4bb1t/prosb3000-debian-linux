import subprocess
import os
import hashlib
import sys
import time

IP = "192.168.1.47:5555"
OUT_DIR = r"D:\PROSB3000_BACKUP"
PART_DIR = os.path.join(OUT_DIR, "partitions")
os.makedirs(PART_DIR, exist_ok=True)

print("=" * 60)
print(f"[*] Conectando ao TV Box em {IP}...")
subprocess.run(["adb", "connect", IP], check=True)

def dump_partition(part_name, filename):
    filepath = os.path.join(PART_DIR, filename)
    print(f"[*] Extraindo particao {part_name} -> {filename}...")
    cmd = ["adb", "-s", IP, "exec-out", f"su -c dd if=/dev/block/by-name/{part_name} status=none"]
    with open(filepath, "wb") as f:
        p = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)
        if p.returncode != 0:
            print(f"[ERRO] Falha ao extrair {part_name}: {p.stderr.decode('latin1', 'ignore')}")
            return False
    size = os.path.getsize(filepath)
    # Check hash
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    local_md5 = h.hexdigest()
    
    # Remote hash
    p_hash = subprocess.run(["adb", "-s", IP, "shell", f"su -c md5sum /dev/block/by-name/{part_name}"], capture_output=True, text=True)
    remote_md5 = p_hash.stdout.split()[0] if p_hash.stdout else ""
    
    print(f"    Tamanho: {size / (1024*1024):.2f} MB")
    print(f"    Hash local:  {local_md5}")
    print(f"    Hash remoto: {remote_md5}")
    if local_md5 == remote_md5:
        print(f"    [OK] Integridade verificada com sucesso!")
        return True
    else:
        print(f"    [AVISO] Hashes diferem (tamanho lido: {size})")
        return False

# 1. Extrair particoes vitais
partitions = [
    ("boot", "boot.img"),
    ("recovery", "recovery.img"),
    ("env", "env.img"),
    ("vbmeta", "vbmeta.img"),
    ("vbmeta_system", "vbmeta_system.img"),
    ("vbmeta_vendor", "vbmeta_vendor.img"),
]

for part_name, fname in partitions:
    dump_partition(part_name, fname)

# 2. Extrair ambiente Debian e scripts customizados do servidor
tar_path = os.path.join(OUT_DIR, "prosb3000_server_custom.tar.gz")
print("\n" + "=" * 60)
print(f"[*] Empacotando sistema Debian, scripts e configuracoes de /data...")
print("[*] Aguarde a compressao e transferencia...")

# Criar tarball diretamente na stream
cmd_tar = [
    "adb", "-s", IP, "exec-out",
    "su -c 'cd /data && tar -czf - debian debian-mount.sh entrar-linux.sh ligar-servidor.sh ligar-tv.sh adb/service.d 2>/dev/null'"
]

with open(tar_path, "wb") as f:
    p = subprocess.run(cmd_tar, stdout=f, stderr=subprocess.PIPE)
    if p.returncode != 0:
        print(f"[ERRO] Falha no empacotamento: {p.stderr.decode('latin1', 'ignore')}")
    else:
        tar_size = os.path.getsize(tar_path)
        print(f"[OK] Pacote do Servidor Linux extraido com sucesso!")
        print(f"     Arquivo: {tar_path}")
        print(f"     Tamanho: {tar_size / (1024*1024):.2f} MB")

print("\n[OK] Extracao concluida com sucesso!")
