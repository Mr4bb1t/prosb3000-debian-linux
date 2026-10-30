@echo off
chcp 65001 >nul
title Replicador Automático de Servidor Linux - PROSB-3000
color 0B

REM Localizar caminho do ADB
where adb >nul 2>&1
if %errorlevel% neq 0 (
    if exist "C:\adb\adb.exe" (
        set "PATH=%PATH%;C:\adb"
    )
)

set "BACKUP_TAR=D:\PROSB3000_BACKUP\prosb3000_server_custom.tar.gz"
if not exist "%BACKUP_TAR%" (
    if exist "prosb3000_server_custom.tar.gz" (
        set "BACKUP_TAR=prosb3000_server_custom.tar.gz"
    ) else (
        echo [ERRO] Arquivo prosb3000_server_custom.tar.gz nao encontrado!
        pause
        exit /b 1
    )
)

:MENU
cls
echo ===============================================================================
echo       REPLICADOR DE IMAGEM DO SERVIDOR LINUX - PROSB-3000 / ALLWINNER
echo ===============================================================================
echo.
echo   Este script aplica todo o sistema Debian 12 Bookworm, servicos, SSH e scripts
echo   configurados no Box de origem (192.168.1.47) para qualquer novo Box identico.
echo.
echo   Arquivo de Imagem Base: %BACKUP_TAR%
echo ===============================================================================
echo.

set "TARGET_IP="
set /p "TARGET_IP=Digite o IP do NOVO TV Box na rede (ex: 192.168.1.50): "
if not defined TARGET_IP goto MENU

echo.
echo [*] Conectando ao novo TV Box em %TARGET_IP%:5555...
adb connect %TARGET_IP%:5555

adb devices | findstr "%TARGET_IP%:5555" >nul
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Nao foi possivel conectar a %TARGET_IP%:5555!
    echo Certifique-se de que o Box esta ligado na mesma rede Wi-Fi/Cabo.
    pause
    goto MENU
)

echo.
echo [*] Verificando acesso ROOT no aparelho de destino...
adb -s %TARGET_IP%:5555 shell "su -c id" > "%TEMP%\box_target_id.txt" 2>&1
findstr /i "uid=0" "%TEMP%\box_target_id.txt" >nul
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] O novo Box ainda nao possui ROOT ativo ou permissao superusuario!
    echo Caso tenha acabado de gravar a ROM PROSB3000_SERVER_CUSTOM.img via PhoenixUSBPro,
    echo aguarde 1 minuto para inicializacao completa do Magisk e tente novamente.
    pause
    goto MENU
)

echo [OK] Acesso ROOT verificado com sucesso!
echo.
echo [*] Transferindo imagem do servidor Linux (%BACKUP_TAR%)...
adb -s %TARGET_IP%:5555 push "%BACKUP_TAR%" /data/prosb3000_server_custom.tar.gz

echo.
echo [*] Descompactando Debian 12, servicos SSH e scripts no TV Box (aguarde ~20 segundos)...
adb -s %TARGET_IP%:5555 shell "su -c 'mkdir -p /data/adb/service.d && cd /data && tar -xzf /data/prosb3000_server_custom.tar.gz && rm -f /data/prosb3000_server_custom.tar.gz'"

echo.
echo [*] Ajustando permissoes dos scripts de controle e servicos de inicializacao...
adb -s %TARGET_IP%:5555 shell "su -c 'chmod +x /data/*.sh /data/adb/service.d/*.sh 2>/dev/null'"

echo.
echo [*] Montando sistemas de arquivos virtuais e iniciando servidor SSH...
adb -s %TARGET_IP%:5555 shell "su -c 'sh /data/debian-mount.sh'"

echo.
echo [*] Verificando status do servico SSH...
adb -s %TARGET_IP%:5555 shell "su -c 'pgrep -f sshd'" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] SERVIDOR SSH ATIVO E RESPONDENDO NA PORTA 22!
) else (
    echo [!] SSH ainda inicializando...
)

echo.
echo ===============================================================================
echo                  CLONAGEM CONCLUIDA COM SUCESSO!
echo ===============================================================================
echo.
echo   NOVO SERVIDOR:
echo   IP:          %TARGET_IP%
echo   Porta SSH:   22
echo   Usuario:     root
echo   Senha:       root (ou a mesma configurada no Box original)
echo.
echo   Comando para conectar via terminal:
echo     ssh root@%TARGET_IP%
echo.
echo ===============================================================================
pause
goto MENU
