import socket
import concurrent.futures

def scan(ip):
    # check port 5555 (ADB)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.4)
        if s.connect_ex((ip, 5555)) == 0:
            s.close()
            return (ip, 5555)
        s.close()
    except:
        pass

    # check port 22 (SSH)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.4)
        if s.connect_ex((ip, 22)) == 0:
            s.close()
            return (ip, 22)
        s.close()
    except:
        pass
    return None

ips = [f"192.168.1.{i}" for i in range(1, 255)]
with concurrent.futures.ThreadPoolExecutor(max_workers=64) as ex:
    results = [r for r in ex.map(scan, ips) if r]

print("DISCOVERED TARGETS:")
for ip, port in results:
    print(f"  {ip}:{port}")
