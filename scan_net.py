import socket
import concurrent.futures

def check_ip(ip):
    # Check port 5555 (ADB) or port 22 (SSH)
    for port in [5555, 22]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            s.connect((ip, port))
            s.close()
            return (ip, port)
        except:
            pass
    return None

def scan():
    base = "192.168.1."
    ips = [f"{base}{i}" for i in range(1, 255)]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futures = {ex.submit(check_ip, ip): ip for ip in ips}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                print(f"[FOUND] {res[0]} (port {res[1]})")
                results.append(res)
    print("Scan complete. Found:", results)

if __name__ == "__main__":
    scan()
