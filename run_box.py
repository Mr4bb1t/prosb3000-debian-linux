import sys
import subprocess

box_ip = "192.168.1.49:5555"

def run_adb(cmd_str):
    # Pass command via stdin to 'adb shell su'
    p = subprocess.Popen(["adb", "-s", box_ip, "shell", "su"],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         text=True,
                         encoding="utf-8",
                         errors="replace")
    stdout, stderr = p.communicate(input=cmd_str + "\nexit\n")
    if stdout:
        print(stdout.strip())
    if stderr:
        print("[ERR]", stderr.strip(), file=sys.stderr)
    return p.returncode

def run_chroot(cmd_str):
    wrapper = f"/vendor/xbin/chroot /data/debian /usr/bin/env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin {cmd_str}"
    return run_adb(wrapper)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--chroot":
            cmd = " ".join(sys.argv[2:])
            sys.exit(run_chroot(cmd))
        else:
            cmd = " ".join(sys.argv[1:])
            sys.exit(run_adb(cmd))
    else:
        cmd = sys.stdin.read().strip()
        if cmd:
            sys.exit(run_adb(cmd))
