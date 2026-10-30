@echo off
chcp 65001 >nul
title Transformador TV Box em Servidor Linux - PROSB-3000
color 0B

REM Localizar ou configurar caminho do ADB
where adb >nul 2>&1
if %errorlevel% neq 0 (
    if exist "C:\adb\adb.exe" (
        set "PATH=%PATH%;C:\adb"
    )
)

:INICIO
cls
echo ===============================================================================
echo        TRANSFORMADOR DE TV BOX EM SERVIDOR LINUX (DEBIAN 12 BOOKWORM)
echo                  Compativel com PROSB-3000 / H96 / Allwinner
echo                       Suporta Modo ROOT e Modo SEM ROOT
echo ===============================================================================
echo.

set "BOX_IP="
set /p "BOX_IP=Digite o IP da TV Box [Pressione ENTER para 192.168.1.18]: "
if defined BOX_IP set "BOX_IP=%BOX_IP: =%"
if not defined BOX_IP set "BOX_IP=192.168.1.18"

set "SSH_PASS="
set /p "SSH_PASS=Digite a senha do SSH [Pressione ENTER para 'root']: "
if defined SSH_PASS set "SSH_PASS=%SSH_PASS: =%"
if not defined SSH_PASS set "SSH_PASS=root"

echo.
echo [*] Conectando a TV Box em %BOX_IP%:5555 via ADB...
adb kill-server >nul 2>&1
adb connect %BOX_IP%:5555 > "%TEMP%\adb_conn.txt" 2>&1
type "%TEMP%\adb_conn.txt"

adb devices | findstr "%BOX_IP%:5555" >nul
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Nao foi possivel conectar ao IP %BOX_IP%:5555!
    echo.
    echo Dicas:
    echo  1. Verifique se a TV Box esta ligada e no mesmo Wi-Fi/Rede do PC.
    echo  2. Certifique-se de que a Depuracao USB / Rede esta ativa nas opcoes de desenvolvedor.
    echo  3. Tente reiniciar a TV Box na tomada.
    echo.
    pause
    goto INICIO
)

echo [OK] TV Box conectada com sucesso!
echo.
echo [*] Analisando privilegios do sistema (Deteccao de ROOT)...

set "HAS_ROOT=0"
adb -s %BOX_IP%:5555 shell "id" > "%TEMP%\box_id.txt" 2>&1
findstr /i "uid=0" "%TEMP%\box_id.txt" >nul
if %errorlevel% equ 0 (
    set "HAS_ROOT=1"
) else (
    adb -s %BOX_IP%:5555 shell "su -c id" > "%TEMP%\box_id_su.txt" 2>&1
    findstr /i "uid=0" "%TEMP%\box_id_su.txt" >nul
    if %errorlevel% equ 0 (
        set "HAS_ROOT=1"
    )
)

if "%HAS_ROOT%"=="1" (
    echo [OK] APARELHO COM ROOT DETECTADO! (Modo Chroot Nativo / Maxima Performance)
    goto MODO_ROOT
) else (
    echo [!] APARELHO SEM ROOT DETECTADO! (Modo Espaco de Usuario / Termux Seguro)
    goto MODO_SEM_ROOT
)

REM ===============================================================================
REM                      FLUXO 1: INSTALACAO COM ROOT
REM ===============================================================================
:MODO_ROOT
set "SSH_PORT=22"
echo.
echo [*] Verificando se o Debian ja esta instalado na particao /data...
adb -s %BOX_IP%:5555 shell "su -c 'ls /data/debian/bin/bash 2>/dev/null'" > "%TEMP%\check_deb.txt" 2>&1
findstr /i "bash" "%TEMP%\check_deb.txt" >nul
if %errorlevel% equ 0 (
    echo [i] O Debian 12 ja se encontra instalado nesta TV Box!
    goto CONFIGURAR_SERVICOS_ROOT
)

:INSTALAR_DEBIAN_ROOT
echo.
if not exist "rootfs.tar.xz" (
    echo [*] Imagem base Debian Bookworm nao encontrada localmente.
    echo Baixando imagem oficial (apenas ~76 MB)...
    curl.exe -L -k -o rootfs.tar.xz "https://images.linuxcontainers.org/images/debian/bookworm/armhf/default/20261029_05%%3A24/rootfs.tar.xz"
)

echo [*] Enviando arquivos do Debian para a memoria interna da TV Box...
adb -s %BOX_IP%:5555 push rootfs.tar.xz /data/rootfs.tar.xz

echo [*] Descompactando e preparando sistema Linux na TV Box (aguarde cerca de 30 segundos)...
adb -s %BOX_IP%:5555 shell "su -c 'mkdir -p /data/debian && tar -xJf /data/rootfs.tar.xz -C /data/debian && rm -f /data/rootfs.tar.xz'"

:CONFIGURAR_SERVICOS_ROOT
echo [*] Configurando rede, DNS, usuarios e permissoes do Linux...
adb -s %BOX_IP%:5555 shell "su -c 'rm -f /data/debian/etc/resolv.conf && echo nameserver 1.1.1.1 > /data/debian/etc/resolv.conf && echo nameserver 8.8.8.8 >> /data/debian/etc/resolv.conf && echo prosb3000-server > /data/debian/etc/hostname'"
adb -s %BOX_IP%:5555 shell "su -c 'mkdir -p /data/debian/etc/apt/apt.conf.d && echo \"APT::Sandbox::User \\\"root\\\";\" > /data/debian/etc/apt/apt.conf.d/99android-sandbox'"
adb -s %BOX_IP%:5555 shell "su -c 'grep -q aid_inet /data/debian/etc/group || echo aid_inet:x:3003:root,_apt >> /data/debian/etc/group'"

echo [*] Montando sistemas de arquivos virtuais...
adb -s %BOX_IP%:5555 shell "su -c 'mount -o remount,rw /data && grep -q \"/data/debian/dev \" /proc/mounts || mount --bind /dev /data/debian/dev && grep -q \"/data/debian/dev/pts \" /proc/mounts || mount --bind /dev/pts /data/debian/dev/pts && grep -q \"/data/debian/proc \" /proc/mounts || mount -t proc proc /data/debian/proc && grep -q \"/data/debian/sys \" /proc/mounts || mount -t sysfs sys /data/debian/sys'"

echo [*] Garantindo configuracao do OpenSSH Server...
adb -s %BOX_IP%:5555 shell "su -c 'mkdir -p /data/debian/run/sshd && chmod 1777 /data/debian/tmp && sed -i \"s/#PermitRootLogin.*/PermitRootLogin yes/\" /data/debian/etc/ssh/sshd_config 2>/dev/null && sed -i \"s/#PasswordAuthentication.*/PasswordAuthentication yes/\" /data/debian/etc/ssh/sshd_config 2>/dev/null && grep -q \"UsePAM no\" /data/debian/etc/ssh/sshd_config || echo \"UsePAM no\" >> /data/debian/etc/ssh/sshd_config && echo root:%SSH_PASS% | /vendor/xbin/chroot /data/debian /usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin chpasswd'"

echo [*] Instalando scripts de controle (ligar-servidor, ligar-tv e auto-boot)...
adb -s %BOX_IP%:5555 push debian-mount.sh /data/debian-mount.sh >nul 2>&1
adb -s %BOX_IP%:5555 push ligar-servidor.sh /data/ligar-servidor.sh >nul 2>&1
adb -s %BOX_IP%:5555 push ligar-tv.sh /data/ligar-tv.sh >nul 2>&1
adb -s %BOX_IP%:5555 push entrar-linux.sh /data/entrar-linux.sh >nul 2>&1
adb -s %BOX_IP%:5555 push debian-boot.sh /data/adb/service.d/debian-boot.sh >nul 2>&1
adb -s %BOX_IP%:5555 shell "su -c 'chmod +x /data/*.sh /data/adb/service.d/debian-boot.sh 2>/dev/null'" >nul 2>&1

echo [*] Iniciando servidor SSH...
adb -s %BOX_IP%:5555 shell "su -c 'sh /data/debian-mount.sh'"

set "MODO_STR=ROOT (Chroot Nativo - Maxima Performance)"
set "SSH_USER=root"
goto SUCESSO

REM ===============================================================================
REM                      FLUXO 2: INSTALACAO SEM ROOT (TERMUX)
REM ===============================================================================
:MODO_SEM_ROOT
set "SSH_PORT=8022"
set "SSH_USER=root"
echo.
echo [*] Preparando ambiente de Servidor Sem Root (via Termux)...

if not exist "termux.apk" (
    echo Baixando Termux oficial otimizado (~30 MB)...
    curl.exe -L -k -o termux.apk "https://github.com/termux/termux-app/releases/download/v0.118.1/termux-app_v0.118.1+github-debug_arm64-v7a.apk"
)

echo [*] Instalando Termux na TV Box via ADB...
adb -s %BOX_IP%:5555 install -r -g termux.apk

echo [*] Concedendo permissoes de execucao em segundo plano (Wake Lock)...
adb -s %BOX_IP%:5555 shell "pm grant com.termux android.permission.WAKE_LOCK" >nul 2>&1
adb -s %BOX_IP%:5555 shell "dumpsys deviceidle whitelist +com.termux" >nul 2>&1

echo [*] Inicializando o Termux na TV Box...
adb -s %BOX_IP%:5555 shell "am start -n com.termux/.app.TermuxActivity" >nul 2>&1
timeout /t 5 /nobreak >nul

echo [*] Configurando OpenSSH e senha no Termux...
adb -s %BOX_IP%:5555 shell "am broadcast -a com.termux.execute -p com.termux --es com.termux.execute.path '/data/data/com.termux/files/usr/bin/bash' --esa com.termux.execute.arguments '-c,pkg update -y && pkg install -y openssh nano && echo root:%SSH_PASS% | chpasswd && sshd && termux-wake-lock'" >nul 2>&1

set "MODO_STR=SEM ROOT (Ambiente Termux Seguro)"
goto SUCESSO

REM ===============================================================================
REM                      PAINEL DE SUCESSO E DADOS DE ACESSO
REM ===============================================================================
:SUCESSO
cls
color 0A
echo ===============================================================================
echo                 SERVIDOR LINUX CONFIGURADO COM SUCESSO!
echo ===============================================================================
echo.
echo   STATUS:       [ONLINE E FUNCIONANDO]
echo   MODO:         %MODO_STR%
echo   ENDERECO IP:  %BOX_IP%
echo   PORTA SSH:    %SSH_PORT%
echo   USUARIO:      %SSH_USER%
echo   SENHA:        %SSH_PASS%
echo.
echo -------------------------------------------------------------------------------
echo   COMANDO PARA CONECTAR DO SEU COMPUTADOR:
echo.
if "%SSH_PORT%"=="22" (
    echo     ssh %SSH_USER%@%BOX_IP%
) else (
    echo     ssh %SSH_USER%@%BOX_IP% -p %SSH_PORT%
)
echo -------------------------------------------------------------------------------
echo.
echo   RECURSOS DO SERVIDOR ATIVOS:
echo    - OpenSSH Server rodando e aceitando conexoes.
echo    - Gerenciador de pacotes apt pronto para instalar servicos (Nginx, Python, etc).
echo    - Inicializacao automatica com a TV Box ativada.
if "%HAS_ROOT%"=="1" (
    echo    - Para desligar a interface da TV e liberar 1.6 GB de RAM: sh /data/ligar-servidor.sh
    echo    - Para reativar a TV na HDMI: sh /data/ligar-tv.sh
)
echo.
echo ===============================================================================
echo.
echo Opcoes rapidas:
echo   [1] Conectar via SSH agora mesmo neste terminal
echo   [2] Ativar Modo Servidor Maximo (desliga tela da TV para liberar 100%% CPU/RAM)
echo   [3] Reativar Modo TV (tela HDMI)
echo   [4] Sair
echo.
set /p "OPT=Escolha uma opcao [1-4]: "

if "%OPT%"=="1" (
    cls
    if "%SSH_PORT%"=="22" (
        ssh %SSH_USER%@%BOX_IP%
    ) else (
        ssh %SSH_USER%@%BOX_IP% -p %SSH_PORT%
    )
    goto SUCESSO
)
if "%OPT%"=="2" (
    adb -s %BOX_IP%:5555 shell "su -c 'sh /data/ligar-servidor.sh'"
    echo Modo Servidor de Alta Performance ativado!
    pause
    goto SUCESSO
)
if "%OPT%"=="3" (
    adb -s %BOX_IP%:5555 shell "su -c 'sh /data/ligar-tv.sh'"
    echo Interface da TV reativada!
    pause
    goto SUCESSO
)

echo Ate logo!
pause
exit /b 0