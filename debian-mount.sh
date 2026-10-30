#!/system/bin/sh
mount -o remount,rw /data

mkdir -p /data/debian/dev /data/debian/proc /data/debian/sys /data/debian/dev/pts /data/debian/run/sshd /data/debian/tmp /data/debian/system /data/debian/apex
chmod 1777 /data/debian/tmp
chmod 0755 /data/debian/run/sshd

grep -q '/data/debian/dev ' /proc/mounts || mount --bind /dev /data/debian/dev
grep -q '/data/debian/dev/pts ' /proc/mounts || mount --bind /dev/pts /data/debian/dev/pts
grep -q '/data/debian/proc ' /proc/mounts || mount -t proc proc /data/debian/proc
grep -q '/data/debian/sys ' /proc/mounts || mount -t sysfs sys /data/debian/sys
grep -q '/data/debian/system ' /proc/mounts || mount --bind /system /data/debian/system
grep -q '/data/debian/apex ' /proc/mounts || mount --rbind /apex /data/debian/apex

if ! pgrep -f "/usr/sbin/sshd" >/dev/null; then
    /vendor/xbin/chroot /data/debian /usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin /usr/sbin/sshd
fi
