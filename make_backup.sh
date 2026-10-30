#!/system/bin/sh
cd /data
tar --exclude='debian/proc/*' \
    --exclude='debian/proc' \
    --exclude='debian/sys/*' \
    --exclude='debian/sys' \
    --exclude='debian/dev/*' \
    --exclude='debian/dev' \
    --exclude='debian/run/*' \
    --exclude='debian/run' \
    --exclude='debian/tmp/*' \
    -czf /cache/prosb3000_server_custom.tar.gz \
    debian \
    debian-mount.sh \
    entrar-linux.sh \
    ligar-servidor.sh \
    ligar-tv.sh \
    adb/service.d

mkdir -p /data/debian/proc /data/debian/sys /data/debian/dev /data/debian/run /data/debian/tmp
chmod 1777 /data/debian/tmp
ls -lh /cache/prosb3000_server_custom.tar.gz
