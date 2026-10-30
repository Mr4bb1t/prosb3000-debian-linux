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
    print("[ERRO] Nao foi possivel obter o token do Git Credential Manager!")
    sys.exit(1)

REPO = "Mr4bb1t/prosb3000-debian-linux"
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Antigravity-PROSB3000"
}

# 1. Verificar se o release v1.0.0 ja existe
req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/tags/v1.0.0", headers=headers)
release = None
try:
    with urllib.request.urlopen(req) as resp:
        release = json.loads(resp.read().decode())
        print(f"[*] Release v1.0.0 ja existente (ID: {release['id']})")
except urllib.error.HTTPError as e:
    if e.code == 404:
        pass
    else:
        raise

if not release:
    body = """# 🚀 PROSB-3000 / Allwinner H313 - Debian 12 Bookworm Enterprise Server

Firmware customizado de alta performance para TV Box Allwinner H313 (`sun50iw9p1`). Transforma a TV Box em um micro-servidor Linux headless e console interativo na TV.

---

### 📦 Conteúdo dos Arquivos Desta Release:
1. **`PROSB3000_SERVER_LINUX_TERMINAL.zip`** (~968 MB):
   - Imagem de firmware completa (.img descompacta em 2.34 GB) pronta para gravação via **PhoenixUSBPro**.
   - Inicialização em ~14s com console direto na TV (`root@localhost:/#`).
   - OpenSSH v9.2p1 ativo na porta 22 (`root@<IP>`, senha: `root`).
   - Comandos globais `hdmi-off` / `grafico-off` e `hdmi-on` / `grafico-on`.
   - Mais de **1.45 GB de RAM livre** e **10.3 GB de armazenamento livre**.
2. **`PROSB3000_SLIMBOX_100CLONE.zip`** (~962 MB):
   - Imagem original de backup 100% clone do SlimBOX TV Android 10 para restauração de fábrica.
3. **`prosb3000_server_custom.tar.gz`** (~147 MB):
   - Payload de autodeploy contendo o rootfs do Debian 12 Bookworm, configs do Magisk e scripts de boot.
4. **`boot_autodeploy.img`** (~33 MB):
   - Partição de boot Allwinner H313 patcheada com Magisk 25.2 Systemless Root.
5. **`PhoenixUSBPro v4.0.0.zip`** (~4.6 MB):
   - Ferramenta oficial para gravação do firmware via cabo USB Macho x Macho.

---

### ⚡ Como Gravar com PhoenixUSBPro:
1. Baixe e extraia o `PROSB3000_SERVER_LINUX_TERMINAL.zip`.
2. Abra o `PhoenixUSBPro.exe`.
3. Carregue o arquivo `.img` descompactado e clique em **Start**.
4. Pressione o botão Reset (dentro da porta AV da TV Box com palito).
5. Conecte o cabo USB Macho-Macho na porta USB 2 (OTG) da TV Box e no computador.
6. Aguarde a barra verde atingir 100% ("Finish"). Conecte a fonte de alimentação 5V e o cabo de rede/HDMI!

---

### 🔑 Acesso Remoto SSH:
```bash
ssh root@<IP_DA_TV_BOX>
# Senha padrao: root
```
"""

    rel_payload = {
        "tag_name": "v1.0.0",
        "target_commitish": "main",
        "name": "PROSB-3000 Linux Server Debian 12 (Bookworm) - Release Oficial",
        "body": body,
        "draft": False,
        "prerelease": False
    }
    
    print("[*] Criando Release v1.0.0 no GitHub...")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/releases",
        data=json.dumps(rel_payload).encode(),
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        release = json.loads(resp.read().decode())
        print(f"[OK] Release criada com sucesso! ID: {release['id']}, URL: {release['html_url']}")

print(f"[*] Upload URL base: {release['upload_url']}")
with open("release_info.json", "w", encoding="utf-8") as f:
    json.dump(release, f, indent=2)
