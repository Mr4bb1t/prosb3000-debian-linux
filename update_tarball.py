import os
import io
import time
import tarfile
import sqlite3
import shutil

TAR_PATH = r"D:\PROSB3000_BACKUP\prosb3000_server_custom.tar.gz"
TMP_PATH = r"D:\PROSB3000_BACKUP\prosb3000_server_custom_tmp.tar.gz"

# 1. Gerar magisk.db com policy=2 pre-configurada
db_path = r"c:\Users\hp909\Downloads\PROSB300-SERVER\magisk.db"
if os.path.exists(db_path):
    try:
        os.remove(db_path)
    except Exception:
        pass

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS policies (
    uid INTEGER,
    package_name TEXT,
    policy INTEGER,
    until INTEGER,
    logging INTEGER,
    notification INTEGER,
    PRIMARY KEY(uid)
);
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT,
    value INTEGER,
    PRIMARY KEY(key)
);
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS strings (
    key TEXT,
    value TEXT,
    PRIMARY KEY(key)
);
""")
cur.execute("INSERT OR REPLACE INTO policies VALUES (10056, 'jackpal.androidterm', 2, 0, 0, 0);")
cur.execute("INSERT OR REPLACE INTO settings VALUES ('root_access', 3);")
cur.execute("INSERT OR REPLACE INTO settings VALUES ('su_request_timeout', 15);")
conn.commit()
conn.close()

with open(db_path, "rb") as f:
    magisk_db_data = f.read()

# 2. Ler outros arquivos customizados
with open(r"c:\Users\hp909\Downloads\PROSB300-SERVER\entrar-linux.sh", "rb") as f:
    entrar_data = f.read()
with open(r"c:\Users\hp909\Downloads\PROSB300-SERVER\debian-mount.sh", "rb") as f:
    mount_data = f.read()
with open(r"c:\Users\hp909\Downloads\PROSB300-SERVER\debian-boot.sh", "rb") as f:
    boot_data = f.read()
with open(r"c:\Users\hp909\Downloads\PROSB300-SERVER\hdmi-off", "rb") as f:
    hdmi_off_data = f.read()
with open(r"c:\Users\hp909\Downloads\PROSB300-SERVER\hdmi-on", "rb") as f:
    hdmi_on_data = f.read()
with open(r"c:\Users\hp909\Downloads\PROSB300-SERVER\jackpal.androidterm_preferences.xml", "rb") as f:
    term_prefs_data = f.read()

to_replace = {
    "entrar-linux.sh",
    "debian-mount.sh",
    "adb/service.d/debian-boot.sh",
    "adb/magisk.db",
    "data/jackpal.androidterm/shared_prefs/jackpal.androidterm_preferences.xml",
    "hdmi-off",
    "hdmi-on",
    "grafico-off",
    "grafico-on",
    "debian/usr/local/bin/hdmi-off",
    "debian/usr/local/bin/hdmi-on",
    "debian/usr/local/bin/grafico-off",
    "debian/usr/local/bin/grafico-on",
    "debian/bin/hdmi-off",
    "debian/bin/hdmi-on",
    "debian/bin/grafico-off",
    "debian/bin/grafico-on",
    "debian/usr/bin/hdmi-off",
    "debian/usr/bin/hdmi-on",
    "debian/usr/bin/grafico-off",
    "debian/usr/bin/grafico-on"
}

print(f"[*] Repacotando {TAR_PATH} com as configuracoes estaveis...")
start_time = time.time()
with tarfile.open(TAR_PATH, "r:gz") as src_tar, tarfile.open(TMP_PATH, "w:gz") as dst_tar:
    copied = 0
    for member in src_tar:
        name_clean = member.name.lstrip("./")
        if name_clean in to_replace:
            continue
        
        f_obj = src_tar.extractfile(member) if member.isreg() else None
        dst_tar.addfile(member, f_obj)
        copied += 1
        if copied % 3000 == 0:
            print(f"    [-] {copied} arquivos copiados...")

    def add_file(arc_name, content, mode=0o755):
        ti = tarfile.TarInfo(name=arc_name)
        ti.size = len(content)
        ti.mode = mode
        ti.mtime = int(time.time())
        ti.type = tarfile.REGTYPE
        dst_tar.addfile(ti, io.BytesIO(content))
        print(f"    [+] Injetado: {arc_name} ({len(content)} bytes)")

    add_file("entrar-linux.sh", entrar_data, mode=0o755)
    add_file("debian-mount.sh", mount_data, mode=0o755)
    add_file("adb/service.d/debian-boot.sh", boot_data, mode=0o755)
    add_file("adb/magisk.db", magisk_db_data, mode=0o600)
    add_file("data/jackpal.androidterm/shared_prefs/jackpal.androidterm_preferences.xml", term_prefs_data, mode=0o660)
    add_file("hdmi-off", hdmi_off_data, mode=0o755)
    add_file("hdmi-on", hdmi_on_data, mode=0o755)
    add_file("grafico-off", hdmi_off_data, mode=0o755)
    add_file("grafico-on", hdmi_on_data, mode=0o755)
    add_file("debian/usr/local/bin/hdmi-off", hdmi_off_data, mode=0o755)
    add_file("debian/usr/local/bin/hdmi-on", hdmi_on_data, mode=0o755)
    add_file("debian/usr/local/bin/grafico-off", hdmi_off_data, mode=0o755)
    add_file("debian/usr/local/bin/grafico-on", hdmi_on_data, mode=0o755)
    add_file("debian/usr/bin/hdmi-off", hdmi_off_data, mode=0o755)
    add_file("debian/usr/bin/hdmi-on", hdmi_on_data, mode=0o755)
    add_file("debian/usr/bin/grafico-off", hdmi_off_data, mode=0o755)
    add_file("debian/usr/bin/grafico-on", hdmi_on_data, mode=0o755)
    add_file("debian/bin/hdmi-off", hdmi_off_data, mode=0o755)
    add_file("debian/bin/hdmi-on", hdmi_on_data, mode=0o755)
    add_file("debian/bin/grafico-off", hdmi_off_data, mode=0o755)
    add_file("debian/bin/grafico-on", hdmi_on_data, mode=0o755)

print(f"[*] Substituindo {TAR_PATH}...")
shutil.move(TMP_PATH, TAR_PATH)
sz_mb = os.path.getsize(TAR_PATH) / (1024 * 1024)
print(f"[OK] Tarball atualizado com sucesso em {time.time() - start_time:.1f}s! ({sz_mb:.2f} MB)")
