import run_box

commands = [
    "mount -o remount,rw /",
    "mount -o remount,rw /product",
    "mount -o remount,rw /vendor",
    # Remove system bloat
    "rm -rf /system/priv-app/Phonesky",
    "rm -rf /system/priv-app/Katniss",
    "rm -rf /system/priv-app/SBXlauncher_9",
    "rm -rf /system/priv-app/SBXcustomizer",
    "rm -rf /system/priv-app/SBXproject",
    "rm -rf /system/priv-app/SetupWizard",
    "rm -rf /system/priv-app/USearch",
    "rm -rf /system/priv-app/WallpaperCropper",
    "rm -rf /system/priv-app/CalendarProvider",
    "rm -rf /system/priv-app/ContactsProvider",
    "rm -rf /system/priv-app/Recents_9",
    "rm -rf /system/app/Aging",
    "rm -rf /system/app/BasicDreams",
    "rm -rf /system/app/GoogleCalendarSyncAdapter",
    "rm -rf /system/app/GoogleContactsSyncAdapter",
    "rm -rf /system/app/HTMLViewer",
    "rm -rf /system/app/MiracastReceiver",
    "rm -rf /system/app/PrintSpooler",
    "rm -rf /system/app/WallpaperBackup",
    "rm -rf /system/app/webview",
    "rm -rf /system/media/sbxtv",
    # Remove product bloat
    "rm -rf /product/app/AutostartApp",
    "rm -rf /product/app/AwlogSettings",
    "rm -rf /product/app/Backdrop",
    "rm -rf /product/app/Camera2",
    "rm -rf /product/app/CpuFloat",
    "rm -rf /product/app/Gallery2",
    "rm -rf /product/app/KeyTest",
    "rm -rf /product/app/MemoryClean",
    "rm -rf /product/app/ModuleMetadata",
    "rm -rf /product/app/SoundAmplifier",
    "rm -rf /product/app/Terminal",
    "rm -rf /product/priv-app/AwTvProvision",
    "rm -rf /product/priv-app/OneTimeInitializer",
    "rm -rf /product/priv-app/SettingsIntelligence",
    "rm -rf /product/priv-app/WallpaperCropper",
    # Clean dalvik-cache and log files
    "rm -rf /data/dalvik-cache/*",
    "rm -rf /data/media/awlog/*",
    "rm -rf /data/anr/*",
    "rm -rf /data/tombstones/*"
]

script = " && ".join(commands)
print("Executing debloat...")
res = run_box.run_adb(script)
print(f"Result code: {res}")
