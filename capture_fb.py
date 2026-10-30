import subprocess
from PIL import Image

def capture_fb():
    res = subprocess.run(["adb", "-s", "192.168.1.49:5555", "shell", "su", "-c", "dd if=/dev/graphics/fb0 count=1 bs=3686400 2>/dev/null > /data/fb_dump.raw"], capture_output=True)
    subprocess.run(["adb", "-s", "192.168.1.49:5555", "pull", "/data/fb_dump.raw", "fb_dump.raw"], capture_output=True)
    with open("fb_dump.raw", "rb") as f:
        data = f.read(1280 * 720 * 4)
    if len(data) == 1280 * 720 * 4:
        img = Image.frombytes("RGBA", (1280, 720), data)
        # Convert BGRA to RGBA
        b, g, r, a = img.split()
        img_rgb = Image.merge("RGBA", (r, g, b, a))
        img_rgb.save("fb_screenshot.png")
        print("Captured fb_screenshot.png successfully!")
    else:
        print(f"Warning: data len is {len(data)}")

if __name__ == "__main__":
    capture_fb()
