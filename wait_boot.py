import socket
import time
import subprocess

def wait_for_online(host="192.168.1.49", port_adb=5555, port_ssh=22, timeout=90):
    print(f"Waiting for {host} to reboot (timeout {timeout}s)...")
    start = time.time()
    adb_ready = False
    ssh_ready = False

    while time.time() - start < timeout:
        if not adb_ready:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.5)
                s.connect((host, port_adb))
                s.close()
                adb_ready = True
                print(f"ADB port 5555 is UP ({int(time.time() - start)}s)!")
            except:
                pass

        if not ssh_ready:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.5)
                s.connect((host, port_ssh))
                s.close()
                ssh_ready = True
                print(f"SSH port 22 is UP ({int(time.time() - start)}s)!")
            except:
                pass

        if adb_ready and ssh_ready:
            print("Both ADB and SSH are UP!")
            return True

        time.sleep(2)

    print(f"Timed out after {timeout}s (ADB={adb_ready}, SSH={ssh_ready})")
    return False

if __name__ == "__main__":
    wait_for_online()
