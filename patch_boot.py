import struct
import gzip
import time
import os

BOOT_PATH = r"D:\PROSB3000_BACKUP\partitions\boot.img"
NEW_BOOT_PATH = r"D:\PROSB3000_BACKUP\partitions\boot_autodeploy.img"

def make_cpio_entry(filename, data, mode=0o100755):
    ino = 200
    uid = 0
    gid = 0
    nlink = 1
    mtime = int(time.time())
    filesize = len(data)
    devmajor = 0
    devminor = 0
    rdevmajor = 0
    rdevminor = 0
    namesize = len(filename.encode("latin1")) + 1
    check = 0

    h_str = (
        f"070701"
        f"{ino:08X}"
        f"{mode:08X}"
        f"{uid:08X}"
        f"{gid:08X}"
        f"{nlink:08X}"
        f"{mtime:08X}"
        f"{filesize:08X}"
        f"{devmajor:08X}"
        f"{devminor:08X}"
        f"{rdevmajor:08X}"
        f"{rdevminor:08X}"
        f"{namesize:08X}"
        f"{check:08X}"
    ).encode("latin1")

    name_bytes = filename.encode("latin1") + b"\x00"
    entry = h_str + name_bytes
    if len(entry) % 4 != 0:
        entry += b"\x00" * (4 - (len(entry) % 4))
    entry += data
    if len(entry) % 4 != 0:
        entry += b"\x00" * (4 - (len(entry) % 4))
    return entry

with open(BOOT_PATH, "rb") as f:
    hdr = bytearray(f.read(1024))
    kernel_size = struct.unpack("<I", hdr[8:12])[0]
    ramdisk_size = struct.unpack("<I", hdr[16:20])[0]
    page_size = struct.unpack("<I", hdr[36:40])[0]

    k_pages = (kernel_size + page_size - 1) // page_size
    f.seek(page_size)
    kernel_data = f.read(kernel_size)

    f.seek((1 + k_pages) * page_size)
    ramdisk_gz = f.read(ramdisk_size)

decomp = gzip.decompress(ramdisk_gz)

trailer_idx = decomp.rfind(b"070701")
while trailer_idx != -1:
    h = decomp[trailer_idx : trailer_idx + 110]
    nlen = int(h[94:102], 16)
    name = decomp[trailer_idx + 110 : trailer_idx + 110 + nlen - 1].decode("latin1", "ignore")
    if name == "TRAILER!!!":
        break
    trailer_idx = decomp.rfind(b"070701", 0, trailer_idx)

if trailer_idx == -1:
    raise ValueError("TRAILER!!! nao encontrado no CPIO")

cpio_content = decomp[:trailer_idx]
trailer_part = decomp[trailer_idx:]

custom_rc = b"""
on property:sys.boot_completed=1
    start linux_deploy

service linux_deploy /sbin/linux_deploy.sh
    oneshot
    disabled
    seclabel u:r:su:s0
"""

linux_deploy_sh = b"""#!/system/bin/sh
sleep 2

# 1. Se /data/debian ainda nao foi instalado, restaura automaticamente do /cache
if [ ! -d /data/debian/bin ]; then
    if [ -f /cache/prosb3000_server_custom.tar.gz ]; then
        mkdir -p /data/adb/service.d /data/data/jackpal.androidterm/shared_prefs /data/adb/magisk
        cd /data && tar -xzf /cache/prosb3000_server_custom.tar.gz
        chmod +x /data/*.sh /data/adb/service.d/*.sh 2>/dev/null
    fi
fi

# 2. Desativar bloatwares e os launchers antigos para dar lugar ao Terminal
for p in com.android.sbxtv com.android.launcher3 org.smarttube.stable com.lonelycatgames.Xplore ru.fmplay mark.via.gp cm.aptoidetv.pt ru.tiardev.kinotrend ru.yourok.torrserve com.neilturner.aerialviews mobi.zona ru.littlevictor.powermenu net.gtvbox.videoplayer com.softmedia.receiver com.google.android.gms com.google.android.katniss com.google.android.deskclock com.softwinner.miracastReceiver com.android.camera2 com.android.gallery3d com.android.printspooler ru.soundamplifier com.waterdaaan.cpufloat com.yxt.memoryclean com.softwinner.provision com.softwinner.settingsassist slim.box.tv.customizer slim.box.tv.project tv.autostart com.qstar.powerui com.android.app.cus.aging com.hcy.myapplication org.liskovsoft.androidtv.rukeyboard; do
    pm disable-user --user 0 "$p" 2>/dev/null
done

# 3. Desativar teclado virtual na tela para o terminal ficar 100% fullscreen limpo
ime disable com.android.inputmethod.latin/.LatinIME 2>/dev/null

# 4. Configurar permissoes do terminal e Magisk root permanente
cp -a /sbin/* /data/adb/magisk/ 2>/dev/null
chown -R u0_a56:u0_a56 /data/data/jackpal.androidterm 2>/dev/null
chmod 660 /data/data/jackpal.androidterm/shared_prefs/* 2>/dev/null
/sbin/magisk --sqlite "INSERT OR REPLACE INTO settings (key, value) VALUES ('root_access', 3), ('su_auto_response', 1);" 2>/dev/null
/sbin/magisk --sqlite "INSERT OR REPLACE INTO policies (uid, package_name, policy, until, logging, notification) VALUES (10056, 'jackpal.androidterm', 2, 0, 0, 0);" 2>/dev/null

# 5. Executar script de inicializacao do servidor e terminal
if [ -f /data/adb/service.d/debian-boot.sh ]; then
    sh /data/adb/service.d/debian-boot.sh
fi
"""

entry1 = make_cpio_entry("overlay.d/custom.rc", custom_rc, mode=0o100644)
entry2 = make_cpio_entry("overlay.d/sbin/linux_deploy.sh", linux_deploy_sh, mode=0o100755)

new_cpio = cpio_content + entry1 + entry2 + trailer_part
new_ramdisk_gz = gzip.compress(new_cpio, mtime=0)

struct.pack_into("<I", hdr, 16, len(new_ramdisk_gz))

new_boot = bytearray(33554432)
new_boot[0:len(hdr)] = hdr
new_boot[page_size : page_size + len(kernel_data)] = kernel_data
rd_offset = (1 + k_pages) * page_size
new_boot[rd_offset : rd_offset + len(new_ramdisk_gz)] = new_ramdisk_gz

with open(NEW_BOOT_PATH, "wb") as f:
    f.write(new_boot)

print(f"[OK] Novo boot.img com autodeploy gerado com sucesso!")
print(f"     Arquivo: {NEW_BOOT_PATH}")
