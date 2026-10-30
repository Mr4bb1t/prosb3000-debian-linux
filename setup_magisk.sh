#!/system/bin/sh
/sbin/magisk --sqlite "INSERT OR REPLACE INTO settings (key, value) VALUES ('root_access', 3);"
/sbin/magisk --sqlite "INSERT OR REPLACE INTO settings (key, value) VALUES ('su_auto_response', 1);"
/sbin/magisk --sqlite "INSERT OR REPLACE INTO policies (uid, package_name, policy, until, logging, notification) VALUES (10056, 'jackpal.androidterm', 2, 0, 0, 0);"
/sbin/magisk --sqlite "SELECT * FROM settings;"
/sbin/magisk --sqlite "SELECT * FROM policies;"
