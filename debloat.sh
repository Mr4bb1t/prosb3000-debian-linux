#!/system/bin/sh
# Debloat seguro focado em servidor para PROSB-3000

PKGS="
org.smarttube.stable
com.lonelycatgames.Xplore
ru.fmplay
mark.via.gp
cm.aptoidetv.pt
ru.tiardev.kinotrend
ru.yourok.torrserve
com.ruet_cse_1503050.ragib.appbackup.pro
com.neilturner.aerialviews
mobi.zona
ru.littlevictor.powermenu
net.gtvbox.videoplayer
com.softmedia.receiver
com.google.android.gms
com.google.android.gsf
com.google.android.gsf.login
com.android.vending
com.google.android.katniss
com.google.android.backdrop
com.google.android.tungsten.setupwraith
com.google.android.deskclock
com.google.android.tv.remote.service
com.google.android.syncadapters.contacts
com.google.android.syncadapters.calendar
com.softwinner.miracastReceiver
com.android.camera2
com.android.gallery3d
com.android.printspooler
com.android.wallpapercropper
com.android.wallpaperbackup
com.ugoos.suggestions
ru.soundamplifier
com.waterdaaan.cpufloat
com.yxt.memoryclean
com.softwinner.provision
com.softwinner.awlogsettings
com.softwinner.settingsassist
com.android.providers.tv
com.android.providers.calendar
com.android.providers.contacts
slim.box.tv.customizer
slim.box.tv.project
tv.autostart
com.qstar.powerui
name.boyle.chris.keytest
com.android.app.cus.aging
com.hcy.myapplication
org.liskovsoft.androidtv.rukeyboard
com.android.dreams.basic
"

for p in $PKGS; do
    pm disable-user --user 0 "$p" 2>/dev/null
    pm uninstall --user 0 "$p" 2>/dev/null
done

# CPU Performance
for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance > "$g" 2>/dev/null
done

# Otimizacoes de kernel
echo 3 > /proc/sys/vm/drop_caches
echo 10 > /proc/sys/vm/swappiness

echo "[OK] Debloat e otimizacoes aplicadas com sucesso!"
