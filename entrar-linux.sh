#!/system/bin/sh
sh /data/debian-mount.sh

while true; do
    clear
    echo "==============================================================================="
    echo "        PROSB-3000 ENTERPRISE LINUX SERVER (DEBIAN 12 BOOKWORM)"
    echo "                   Console Terminal HDMI Direto na TV"
    echo "==============================================================================="
    echo ""
    IP=$(ip addr show wlan0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
    [ -z "$IP" ] && IP=$(ip addr show eth0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
    [ -z "$IP" ] && IP="Aguardando IP / Conecte o cabo de rede ou Wi-Fi..."
    echo "  [+] Status:       ONLINE"
    echo "  [+] Endereco IP:  $IP"
    echo "  [+] Conexao SSH:  ssh root@$IP  (Porta 22 | Senha: root)"
    echo "  [+] Memoria:      $(free -m 2>/dev/null | grep Mem | awk '{print $7}') MB Livres"
    echo "  [+] Espaco /data: $(df -h /data 2>/dev/null | tail -1 | awk '{print $4}') Disponiveis"
    echo ""
    echo "==============================================================================="
    echo "  Terminal Interativo Root Ativo. Comandos Debian 12 disponiveis."
    echo "==============================================================================="
    echo ""

    export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
    export HOME=/root
    export TERM=xterm-256color
    export LANG=C.UTF-8

    /vendor/xbin/chroot /data/debian /bin/bash -i
    echo "[!] Sessao terminada. Reiniciando terminal do servidor..."
    sleep 2
done
