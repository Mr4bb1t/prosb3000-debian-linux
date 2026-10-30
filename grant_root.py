import sqlite3
import os

db_path = "/data/adb/magisk.db"
print("Connecting to:", db_path)
con = sqlite3.connect(db_path)
cur = con.cursor()

tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print("Tables:", tables)

# Inserir ou atualizar política de root para jackpal.androidterm (UID 10056)
cur.execute("""
CREATE TABLE IF NOT EXISTS policies (
    uid INTEGER,
    package_name TEXT,
    policy INTEGER,
    until INTEGER,
    logging INTEGER,
    notification INTEGER,
    PRIMARY KEY(uid)
);
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT,
    value INTEGER,
    PRIMARY KEY(key)
);
""")

cur.execute("INSERT OR REPLACE INTO policies (uid, package_name, policy, until, logging, notification) VALUES (10056, 'jackpal.androidterm', 2, 0, 0, 0);")
cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('root_access', 3);")
cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('su_auto_response', 1);")
con.commit()

print("Policies:", cur.execute("SELECT * FROM policies;").fetchall())
print("Settings:", cur.execute("SELECT * FROM settings;").fetchall())
con.close()
print("[OK] Magisk root granted permanently!")
