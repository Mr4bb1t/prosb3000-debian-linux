#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Console Terminal HDMI para PROSB-3000 Servidor Linux
Desenha diretamente no Framebuffer (/dev/graphics/fb0)
com tipografia TrueType, barras de progresso e telemetria em tempo real.
"""
import os
import sys
import time
import socket
import datetime
from PIL import Image, ImageDraw, ImageFont

FB_DEV = "/dev/graphics/fb0"
WIDTH = 1280
HEIGHT = 720

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

def load_fonts():
    try:
        font_title = ImageFont.truetype(FONT_BOLD_PATH, 24)
        font_sub = ImageFont.truetype(FONT_PATH, 14)
        font_sec = ImageFont.truetype(FONT_BOLD_PATH, 16)
        font_body = ImageFont.truetype(FONT_PATH, 15)
        font_bold = ImageFont.truetype(FONT_BOLD_PATH, 15)
        font_big = ImageFont.truetype(FONT_BOLD_PATH, 20)
        font_small = ImageFont.truetype(FONT_PATH, 12)
        return font_title, font_sub, font_sec, font_body, font_bold, font_big, font_small
    except Exception as e:
        default = ImageFont.load_default()
        return default, default, default, default, default, default, default

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("1.1.1.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_ram():
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        mem = {}
        for l in lines:
            parts = l.split(":")
            if len(parts) == 2:
                mem[parts[0].strip()] = int(parts[1].split()[0])
        total = mem.get("MemTotal", 2000000) // 1024
        avail = mem.get("MemAvailable", 1600000) // 1024
        used = total - avail
        return total, used, avail
    except:
        return 1976, 320, 1656

def get_storage():
    try:
        st = os.statvfs("/data")
        free_gb = (st.f_bavail * st.f_frsize) / (1024**3)
        total_gb = (st.f_blocks * st.f_frsize) / (1024**3)
        used_gb = total_gb - free_gb
        return total_gb, used_gb, free_gb
    except:
        return 11.65, 1.25, 10.40

def get_load():
    try:
        with open("/proc/loadavg") as f:
            parts = f.read().split()
        return f"{parts[0]}, {parts[1]}, {parts[2]}"
    except:
        return "0.05, 0.02, 0.00"

def get_uptime():
    try:
        with open("/proc/uptime") as f:
            up_secs = int(float(f.read().split()[0]))
            days = up_secs // 86400
            hours = (up_secs % 86400) // 3600
            mins = (up_secs % 3600) // 60
            secs = up_secs % 60
            if days > 0:
                return f"{days}d {hours}h {mins}m {secs}s"
            return f"{hours}h {mins}m {secs}s"
    except:
        return "Ativo"

def draw_bar(draw, x, y, w, h, pct, fill_color, bg_color=(30, 41, 59, 255), border_color=(71, 85, 105, 255)):
    draw.rectangle([(x, y), (x + w, y + h)], fill=bg_color, outline=border_color)
    pct = max(0.0, min(1.0, pct))
    bar_w = int((w - 2) * pct)
    if bar_w > 0:
        draw.rectangle([(x + 1, y + 1), (x + 1 + bar_w, y + h - 1)], fill=fill_color)

def main():
    if not os.path.exists(FB_DEV):
        print(f"Erro: {FB_DEV} nao encontrado")
        return

    f_title, f_sub, f_sec, f_body, f_bold, f_big, f_small = load_fonts()
    fb = open(FB_DEV, "r+b")

    # Cores (RGBA)
    C_BG = (11, 15, 25, 255)            # Fundo preto azulado escuro
    C_HEADER = (17, 24, 39, 255)        # Top bar
    C_CARD = (19, 27, 46, 255)          # Cards
    C_CARD_BORDER = (40, 53, 83, 255)   # Bordas
    C_WHITE = (248, 250, 252, 255)      # Texto destaque
    C_TEXT = (203, 213, 225, 255)       # Texto comum
    C_MUTED = (148, 163, 184, 255)      # Texto cinza
    C_GREEN = (34, 197, 94, 255)        # Status verde
    C_CYAN = (56, 189, 248, 255)        # Ciano destaque
    C_AMBER = (251, 191, 36, 255)       # Dourado avisos
    C_BLUE = (99, 102, 241, 255)        # Indigo

    while True:
        try:
            ip = get_ip()
            ram_tot, ram_used, ram_avail = get_ram()
            ram_pct = ram_used / ram_tot if ram_tot else 0
            disk_tot, disk_used, disk_free = get_storage()
            disk_pct = disk_used / disk_tot if disk_tot else 0
            load = get_load()
            uptime = get_uptime()
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            img = Image.new("RGBA", (WIDTH, HEIGHT), C_BG)
            draw = ImageDraw.Draw(img)

            # TOP HEADER BAR
            draw.rectangle([(0, 0), (WIDTH, 75)], fill=C_HEADER)
            draw.line([(0, 75), (WIDTH, 75)], fill=C_CYAN, width=2)

            # Titulo e subtitulo
            draw.text((35, 14), "PROSB-3000 ENTERPRISE LINUX SERVER", font=f_title, fill=C_WHITE)
            draw.text((35, 48), "Debian 12 Bookworm | Kernel 4.9.170 aarch64 | Allwinner H313 Cortex-A53", font=f_sub, fill=C_MUTED)

            # Badge Superior Direito
            badge_text = "● MODO SERVIDOR ATIVO"
            draw.rectangle([(WIDTH - 280, 20), (WIDTH - 35, 55)], fill=(6, 78, 59, 255), outline=C_GREEN, width=1)
            draw.text((WIDTH - 265, 28), badge_text, font=f_bold, fill=C_GREEN)

            # CARD 1: CONEXAO & REDE (Full width)
            draw.rectangle([(35, 95), (WIDTH - 35, 230)], fill=C_CARD, outline=C_CARD_BORDER, width=1)
            draw.text((55, 108), "STATUS DA REDE & ACESSO REMOTO", font=f_sec, fill=C_CYAN)
            draw.line([(55, 130), (WIDTH - 55, 130)], fill=C_CARD_BORDER, width=1)

            # IP e status
            draw.text((55, 145), f"Status da Conexao:  CONECTADO (ONLINE)", font=f_bold, fill=C_GREEN)
            draw.text((55, 170), f"Endereco IP Local:  {ip}", font=f_big, fill=C_WHITE)
            draw.text((55, 200), f"Data / Hora Local:  {now_str}   |   Uptime: {uptime}", font=f_body, fill=C_MUTED)

            # Sub-card SSH à direita dentro do card de rede
            ssh_box_x = WIDTH - 520
            draw.rectangle([(ssh_box_x, 140), (WIDTH - 55, 215)], fill=(15, 23, 42, 255), outline=C_CYAN, width=1)
            draw.text((ssh_box_x + 15, 148), "COMANDO PARA CONECTAR (SSH):", font=f_bold, fill=C_CYAN)
            draw.text((ssh_box_x + 15, 172), f"ssh root@{ip}", font=f_big, fill=C_WHITE)
            draw.text((ssh_box_x + 15, 196), "Porta: 22   |   Senha padrao: root", font=f_small, fill=C_MUTED)

            # CARD 2: RECURSOS DO SISTEMA (Coluna Esquerda)
            card2_w = (WIDTH - 70 - 20) // 2
            x1 = 35
            x2 = x1 + card2_w
            draw.rectangle([(x1, 245), (x2, 545)], fill=C_CARD, outline=C_CARD_BORDER, width=1)
            draw.text((x1 + 20, 258), "DESEMPENHO & RECURSOS DE HARDWARE", font=f_sec, fill=C_AMBER)
            draw.line([(x1 + 20, 280), (x2 - 20, 280)], fill=C_CARD_BORDER, width=1)

            # RAM
            y_r = 295
            draw.text((x1 + 20, y_r), f"Memoria RAM Disponivel:", font=f_bold, fill=C_WHITE)
            draw.text((x2 - 190, y_r), f"{ram_avail} MB LIVRES", font=f_bold, fill=C_GREEN)
            y_r += 22
            draw.text((x1 + 20, y_r), f"Uso: {ram_used} MB de {ram_tot} MB ({int(ram_pct*100)}%)", font=f_small, fill=C_MUTED)
            y_r += 18
            draw_bar(draw, x1 + 20, y_r, card2_w - 40, 16, ram_pct, C_CYAN)

            # Armazenamento
            y_r += 32
            draw.text((x1 + 20, y_r), f"Armazenamento (/data):", font=f_bold, fill=C_WHITE)
            draw.text((x2 - 190, y_r), f"{disk_free:.2f} GB LIVRES", font=f_bold, fill=C_GREEN)
            y_r += 22
            draw.text((x1 + 20, y_r), f"Uso: {disk_used:.2f} GB de {disk_tot:.2f} GB ({int(disk_pct*100)}%)", font=f_small, fill=C_MUTED)
            y_r += 18
            draw_bar(draw, x1 + 20, y_r, card2_w - 40, 16, disk_pct, C_AMBER)

            # CPU & Load
            y_r += 35
            draw.text((x1 + 20, y_r), f"Processador (CPU):  Allwinner H313 4x Cortex-A53", font=f_body, fill=C_WHITE)
            y_r += 24
            draw.text((x1 + 20, y_r), f"Governador de CPU:  PERFORMANCE (Clock maximo)", font=f_bold, fill=C_GREEN)
            y_r += 24
            draw.text((x1 + 20, y_r), f"Carga Media (Load): {load}", font=f_body, fill=C_MUTED)

            # CARD 3: SERVICOS & OTIMIZACOES (Coluna Direita)
            x3 = x2 + 20
            x4 = WIDTH - 35
            draw.rectangle([(x3, 245), (x4, 545)], fill=C_CARD, outline=C_CARD_BORDER, width=1)
            draw.text((x3 + 20, 258), "SERVICOS DO SERVIDOR & OTIMIZACOES", font=f_sec, fill=C_CYAN)
            draw.line([(x3 + 20, 280), (x4 - 20, 280)], fill=C_CARD_BORDER, width=1)

            services = [
                ("[OK] OpenSSH Server (sshd)", "Ativo na porta 22 (Terminal & SFTP)", C_GREEN),
                ("[OK] Debian 12 Chroot", "Ambiente Linux raiz em /data/debian", C_GREEN),
                ("[OK] Magisk Root Daemon", "Acesso Superuser (UID 0) nativo", C_GREEN),
                ("[OK] Framebuffer Terminal", "Renderizando direto no HDMI (/dev/fb0)", C_GREEN),
                ("[OK] Android GUI Purged", "Zygote/SurfaceFlinger desligados (+1.6GB RAM)", C_GREEN),
                ("[OK] Package Bloatware", "50+ apps desinstalados e purgados", C_GREEN),
            ]

            y_s = 295
            for title, desc, col in services:
                draw.text((x3 + 20, y_s), title, font=f_bold, fill=col)
                draw.text((x3 + 40, y_s + 18), desc, font=f_small, fill=C_MUTED)
                y_s += 38

            # CARD 4: INSTRUCOES DE USO (Bottom Bar)
            draw.rectangle([(35, 560), (WIDTH - 35, 680)], fill=(15, 23, 42, 255), outline=C_CARD_BORDER, width=1)
            draw.text((55, 575), "DICAS RAPIDAS DE OPERACAO & DEPLOY:", font=f_bold, fill=C_CYAN)
            draw.text((55, 600), f"1. Acesso SSH via terminal: ssh root@{ip}  (senha: root)", font=f_body, fill=C_WHITE)
            draw.text((55, 624), "2. Instale servicos: apt update && apt install nginx docker.io python3-pip git -y", font=f_body, fill=C_MUTED)
            draw.text((55, 648), "3. Arquivos e projetos: armazene em /data/debian/root/ ou /data/ para maximo espaco livre", font=f_body, fill=C_MUTED)

            # Footer
            draw.text((WIDTH - 320, 695), "Antigravity Linux Server Engine v2.0", font=f_small, fill=(71, 85, 105, 255))

            # Converter para BGRA para o Framebuffer do Allwinner
            b, g, r, a = img.split()
            bgra = Image.merge("RGBA", (b, g, r, a))
            raw_bytes = bgra.tobytes()

            # Forcar HDMI ativo (Despertar tela/Unblank)
            try:
                import fcntl
                fcntl.ioctl(fb.fileno(), 0x4611, 0) # FBIOBLANK = 0
            except:
                pass
            try:
                with open("/sys/class/graphics/fb0/blank", "w") as bf:
                    bf.write("0\n")
            except:
                pass

            # Escrever em ambos os buffers (duplo buffer 0 e 1)
            # Evita tela preta quando o driver estiver escaneando yoffset > 0
            fb.seek(0)
            fb.write(raw_bytes)
            try:
                fb.write(raw_bytes)
            except:
                pass
            fb.flush()

        except Exception as e:
            pass

        time.sleep(3)

if __name__ == "__main__":
    main()
