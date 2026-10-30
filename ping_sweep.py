import subprocess
import concurrent.futures

def ping_ip(ip):
    res = subprocess.run(["ping", "-n", "1", "-w", "300", ip], capture_output=True, text=True)
    if "TTL=" in res.stdout:
        return ip
    return None

ips = [f"192.168.1.{i}" for i in range(1, 255)]
active = []
with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
    futures = {ex.submit(ping_ip, ip): ip for ip in ips}
    for f in concurrent.futures.as_completed(futures):
        res = f.result()
        if res:
            active.append(res)
print("Active IPs:", sorted(active, key=lambda x: int(x.split(".")[-1])))
