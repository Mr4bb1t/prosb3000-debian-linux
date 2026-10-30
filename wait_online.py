import socket
import time
import subprocess

IP = "192.168.1.49"
print(f"[*] Aguardando TV Box ({IP}) reiniciar...")

start = time.time()
while time.time() - start < 90:
    time.sleep(2)
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect((IP, 5555))
        s.close()
        print(f"[OK] ADB online na porta 5555 em {int(time.time() - start)}s!")
        break
    except:
        pass

# Agora aguarda o SSH na porta 22
ssh_ok = False
for _ in range(30):
    time.sleep(2)
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect((IP, 22))
        s.close()
        print(f"[OK] OpenSSH Server online na porta 22!")
        ssh_ok = True
        break
    except:
        pass

if not ssh_ok:
    print("[!] SSH ainda nao subiu na porta 22")
