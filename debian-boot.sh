#!/system/bin/sh
# Auto-inicializacao do Servidor Linux PROSB-3000

# 1. Configurar Governador de CPU para Performance Maxima
for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance > "$g" 2>/dev/null
done
echo 3 > /proc/sys/vm/drop_caches
echo 10 > /proc/sys/vm/swappiness

# 2. Montar particoes do Debian 12
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

# Garantir scripts de controle de HDMI em /sbin e /data
cp /data/hdmi-off /sbin/hdmi-off 2>/dev/null
cp /data/hdmi-on /sbin/hdmi-on 2>/dev/null
cp /data/grafico-off /sbin/grafico-off 2>/dev/null
cp /data/grafico-on /sbin/grafico-on 2>/dev/null
chmod 755 /sbin/hdmi* /sbin/grafico* 2>/dev/null

# 3. Iniciar OpenSSH Server na porta 22
if ! pgrep -f "/usr/sbin/sshd" >/dev/null; then
    /vendor/xbin/chroot /data/debian /usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin /usr/sbin/sshd
fi

# 4. Permissoes Magisk ROOT para o Terminal
/sbin/magisk --sqlite 'UPDATE policies SET policy=2, logging=0, notification=0 WHERE uid=10056;' 2>/dev/null

# 5. Configurar arquivo de preferencias do terminal com dono correto
TERM_PREFS="/data/data/jackpal.androidterm/shared_prefs/jackpal.androidterm_preferences.xml"
if [ -f "$TERM_PREFS" ]; then
    chown -R u0_a56:u0_a56 /data/data/jackpal.androidterm 2>/dev/null
    chmod 660 "$TERM_PREFS" 2>/dev/null
fi

# 6. Desativar teclado virtual na tela para terminal ficar 100% limpo
ime disable com.android.inputmethod.latin/.LatinIME 2>/dev/null

# 7. Desativar suspensao e abrir Terminal na TV
(
    while [ "$(getprop sys.boot_completed)" != "1" ]; do
        sleep 1
    done

    # NUNCA DESLIGAR O HDMI / NUNCA DORMIR
    svc power stayon true 2>/dev/null
    settings put global stay_on_while_plugged_in 3 2>/dev/null
    settings put system screen_off_timeout 2147483647 2>/dev/null
    settings put secure screensaver_enabled 0 2>/dev/null
    settings put secure doze_enabled 0 2>/dev/null

    # Aguardar 4 segundos apos boot para o launcher inicial assentar
    sleep 4

    # Abrir Terminal em tela cheia na TV se nao estiver bloqueado
    if [ ! -f /data/hdmi_disabled ]; then
        am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n jackpal.androidterm/.Term 2>/dev/null
    fi

    # Watchdog continuo: garante que o terminal fica sempre no topo
    while true; do
        sleep 5
        if [ ! -f /data/hdmi_disabled ]; then
            TOP=$(dumpsys activity top 2>/dev/null | grep ACTIVITY | head -1 | awk '{print $2}')
            if [ "$TOP" != "jackpal.androidterm/.Term" ]; then
                am start -a android.intent.action.MAIN -n jackpal.androidterm/.Term 2>/dev/null
            fi
        fi
    done
) &
