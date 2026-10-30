#!/system/bin/sh
echo "=========================================="
echo "  REATIVANDO INTERFACE SLIMBOX ANDROID TV"
echo "=========================================="
for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo schedutil > "$g" 2>/dev/null || true
done

start

echo "[OK] slimBOX reativado na saida HDMI!"
echo "(O servidor SSH continua ativo em segundo plano)"
echo "=========================================="
