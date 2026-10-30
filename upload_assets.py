import os
import sys
import time
import json
import urllib.request
import urllib.parse
import subprocess

def get_github_token():
    p = subprocess.Popen(['git', 'credential', 'fill'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    out, _ = p.communicate('protocol=https\nhost=github.com\n\n')
    creds = dict(line.split('=', 1) for line in out.splitlines() if '=' in line)
    return creds.get('password')

token = get_github_token()
if not token:
    print("[ERRO] Token do GitHub nao encontrado!")
    sys.exit(1)

with open("release_info.json", "r", encoding="utf-8") as f:
    release_info = json.load(f)

upload_url_template = release_info["upload_url"].split("{")[0]
headers_base = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Antigravity-PROSB3000"
}

# Obter assets existentes
release_id = release_info["id"]
req = urllib.request.Request(f"https://api.github.com/repos/Mr4bb1t/prosb3000-debian-linux/releases/{release_id}/assets", headers=headers_base)
with urllib.request.urlopen(req) as resp:
    existing_assets = {a["name"]: a["id"] for a in json.loads(resp.read().decode())}
print(f"[*] Assets ja existentes no release: {list(existing_assets.keys())}")

assets_to_upload = [
    ("PhoenixUSBPro_v4.0.0.zip", r"c:\Users\hp909\Downloads\PROSB300-SERVER\tools\PhoenixUSBPro v4.0.0.zip", "application/zip"),
    ("boot_autodeploy.img", r"D:\PROSB3000_BACKUP\partitions\boot_autodeploy.img", "application/octet-stream"),
    ("prosb3000_server_custom.tar.gz", r"D:\PROSB3000_BACKUP\prosb3000_server_custom.tar.gz", "application/gzip"),
    ("PROSB3000_SERVER_LINUX_TERMINAL.zip", r"D:\PROSB3000_BACKUP\PROSB3000_SERVER_LINUX_TERMINAL.zip", "application/zip"),
    ("PROSB3000_SLIMBOX_100CLONE.zip", r"D:\PROSB3000_BACKUP\PROSB3000_SLIMBOX_100CLONE.zip", "application/zip")
]

for name, path, mime in assets_to_upload:
    if not os.path.exists(path):
        print(f"[PULADO] Arquivo nao encontrado: {path}")
        continue
    
    size_bytes = os.path.getsize(path)
    size_mb = size_bytes / (1024 * 1024)

    if name in existing_assets:
        print(f"[-] Asset {name} ja existe no GitHub Release ({size_mb:.2f} MB). Pulando...")
        continue

    print(f"\n[*] Iniciando upload de: {name} ({size_mb:.2f} MB)...")
    url = f"{upload_url_template}?name={urllib.parse.quote(name)}"
    
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": mime,
        "Content-Length": str(size_bytes),
        "User-Agent": "Antigravity-PROSB3000"
    }

    start = time.time()
    with open(path, "rb") as f:
        req = urllib.request.Request(url, data=f, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode())
                elapsed = time.time() - start
                speed = size_mb / elapsed if elapsed > 0 else 0
                print(f"[OK] Upload concluido: {name} em {elapsed:.1f}s ({speed:.2f} MB/s)!")
                print(f"     URL Download: {result.get('browser_download_url')}")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            print(f"[ERRO HTTP {e.code}] Falha no upload de {name}: {err_body}")

print("\n===============================================================================")
print(" [CONCLUIDO] Todos os assets foram processados com sucesso!")
print("===============================================================================")
