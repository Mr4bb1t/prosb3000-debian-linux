import subprocess

IP = "192.168.1.49:5555"

packages_to_remove = [
    # Third party bloat
    "org.smarttube.stable",
    "com.lonelycatgames.Xplore",
    "ru.fmplay",
    "mark.via.gp",
    "cm.aptoidetv.pt",
    "ru.tiardev.kinotrend",
    "ru.yourok.torrserve",
    "com.ruet_cse_1503050.ragib.appbackup.pro",
    "com.neilturner.aerialviews",
    "mobi.zona",
    "ru.littlevictor.powermenu",
    "net.gtvbox.videoplayer",
    "com.softmedia.receiver",
    # Google bloat
    "com.google.android.gms",
    "com.google.android.gsf",
    "com.google.android.gsf.login",
    "com.android.vending",
    "com.google.android.katniss",
    "com.google.android.backdrop",
    "com.google.android.tungsten.setupwraith",
    "com.google.android.deskclock",
    "com.google.android.tv.remote.service",
    "com.google.android.syncadapters.contacts",
    "com.google.android.syncadapters.calendar",
    # TV / Media bloat
    "com.softwinner.miracastReceiver",
    "com.android.camera2",
    "com.android.gallery3d",
    "com.android.printspooler",
    "com.android.wallpapercropper",
    "com.android.wallpaperbackup",
    "com.ugoos.suggestions",
    "ru.soundamplifier",
    "com.waterdaaan.cpufloat",
    "com.yxt.memoryclean",
    "com.softwinner.provision",
    "com.softwinner.awlogsettings",
    "com.softwinner.settingsassist",
    "com.android.providers.tv",
    "com.android.providers.calendar",
    "com.android.providers.contacts",
    "com.android.launcher3",
    "com.android.sbxtv",
    "slim.box.tv.customizer",
    "slim.box.tv.project",
    "tv.autostart",
    "com.qstar.powerui",
    "name.boyle.chris.keytest",
    "com.android.app.cus.aging",
    "com.hcy.myapplication",
    "org.liskovsoft.androidtv.rukeyboard",
    "com.android.dreams.basic",
]

print(f"[*] Conectando a {IP}...")
subprocess.run(["adb", "connect", IP], check=True)

# 1. Remount RW
print("[*] Remontando particoes como RW...")
subprocess.run(["adb", "-s", IP, "shell", "su -c remount"])

# 2. Desinstalar pacotes
print(f"[*] Desinstalando {len(packages_to_remove)} pacotes desnecessarios...")
for pkg in packages_to_remove:
    cmd = ["adb", "-s", IP, "shell", f"su -c 'pm uninstall --user 0 {pkg} 2>/dev/null; pm disable-user --user 0 {pkg} 2>/dev/null'"]
    subprocess.run(cmd, capture_output=True)
    print(f"    [-] Removido: {pkg}")

# 3. Limpar pastas de apks
clean_dirs = [
    "/data/app/*",
    "/product/app/*SmartTube*",
    "/product/app/*Xplore*",
    "/product/app/*fmplay*",
    "/product/app/*via*",
    "/product/app/*aptoide*",
    "/product/app/*kino*",
    "/product/app/*torrserve*",
    "/product/app/*zona*",
    "/product/app/*powermenu*",
    "/product/app/*vimu*",
    "/product/app/*AirScreen*",
    "/product/app/*GmsCore*",
    "/product/app/*Google*",
    "/product/priv-app/*GmsCore*",
    "/product/priv-app/*Google*",
    "/product/priv-app/*Phonesky*",
    "/product/priv-app/*Vending*",
    "/system/priv-app/*GmsCore*",
    "/system/priv-app/*Google*",
    "/system/app/*Camera*",
    "/system/app/*Gallery*",
]

print("[*] Deletando APKs do sistema em disco...")
for pattern in clean_dirs:
    subprocess.run(["adb", "-s", IP, "shell", f"su -c 'rm -rf {pattern} 2>/dev/null'"])

print("[OK] Debloat completo com sucesso!")
