#!/system/bin/sh
# Script de Inicializacao e Modo Servidor Linux Puro para PROSB-3000
# Antigravity Linux Server Engine

echo "[+] Ativando Modo Servidor Linux..."

# 1. Encerrar completamente a Interface Grafica do Android (libera 1.6 GB de RAM)
stop

# 2. Configurar Governador da CPU para Performance Maxima em todos os 4 nucleos
for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance > "$g" 2>/dev/null || true
done

# 3. Otimizacoes de Memoria do Kernel
echo 3 > /proc/sys/vm/drop_caches
echo 10 > /proc/sys/vm/swappiness
echo 50 > /proc/sys/vm/vfs_cache_pressure

# 4. Montar ambiente Debian 12 Bookworm
mount -o remount,rw /data

grep -q '/data/debian/dev ' /proc/mounts || mount --bind /dev /data/debian/dev
grep -q '/data/debian/dev/pts ' /proc/mounts || mount --bind /dev/pts /data/debian/dev/pts
grep -q '/data/debian/proc ' /proc/mounts || mount -t proc proc /data/debian/proc
grep -q '/data/debian/sys ' /proc/mounts || mount -t sysfs sys /data/debian/sys

mkdir -p /data/debian/run/sshd /data/debian/tmp
chmod 0755 /data/debian/run/sshd
chmod 1777 /data/debian/tmp

# 5. Iniciar OpenSSH Server
if ! pgrep -f "/usr/sbin/sshd" >/dev/null; then
    /vendor/xbin/chroot /data/debian /usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin /usr/sbin/sshd
fi

# 6. Iniciar Console Terminal HDMI no Framebuffer (/dev/graphics/fb0)
pkill -f server_screen.py 2>/dev/null || true
sleep 1
nohup /vendor/xbin/chroot /data/debian /usr/bin/env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin python3 /usr/local/bin/server_screen.py >/dev/null 2>&1 &

echo "[OK] Servidor Linux e Terminal HDMI Ativos!"
