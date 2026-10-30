import os
import shutil

base_dir = r"D:\PROSB3000_BACKUP\firmware_base"

# 1. Copiar o boot_autodeploy.img para boot.fex
boot_auto = r"D:\PROSB3000_BACKUP\partitions\boot_autodeploy.img"
shutil.copyfile(boot_auto, os.path.join(base_dir, "boot.fex"))
print("[OK] boot.fex atualizado com boot_autodeploy.img")

# 2. Atualizar sys_partition.fex
sys_part_path = os.path.join(base_dir, "sys_partition.fex")
with open(sys_part_path, "r", encoding="latin1") as f:
    sp_lines = f.readlines()

new_lines = []
in_cache = False
for line in sp_lines:
    if "name" in line and "cache" in line:
        in_cache = True
        new_lines.append(line)
        continue
    if in_cache and "user_type" in line:
        new_lines.append("    downloadfile = \"cache.fex\"\n")
        new_lines.append(line)
        in_cache = False
        continue
    new_lines.append(line)

with open(sys_part_path, "w", encoding="latin1") as f:
    f.writelines(new_lines)
print("[OK] sys_partition.fex atualizado")

# 3. Criar Vcache.fex (4 bytes)
vcache_path = os.path.join(base_dir, "Vcache.fex")
with open(vcache_path, "wb") as f:
    f.write(b"\x00\x00\x00\x00")
print("[OK] Vcache.fex criado")

# 4. Atualizar image.cfg
cfg_path = os.path.join(base_dir, "image.cfg")
with open(cfg_path, "r", encoding="utf-8") as f:
    cfg_text = f.read()

if "cache.fex" not in cfg_text:
    # Contar quantos arquivos estao atualmente
    # e adicionar file_41 e file_42
    # number_of_files=0x00000028; (40 em hex) -> 0x0000002A; (42 em hex)
    cfg_text = cfg_text.replace("number_of_files=0x00000028;", "number_of_files=0x0000002A;")

    entry_cache = """
file_41 {
filename_length=0x00000009;
file_header_size=0x00000400;
maintype="RFSFAT16";
subtype="CACHE_FEX0000000";
unknown0=0x00000000;
filename="cache.fex";
source_path="cache.fex";
stored_length=0x00000000;
pad1=0x00000000;
original_length=0x00000000;
pad2=0x00000000;
offset=0x00000000;
}
file_42 {
filename_length=0x0000000A;
file_header_size=0x00000400;
maintype="RFSFAT16";
subtype="VCACHE_FEX000000";
unknown0=0x00000000;
filename="Vcache.fex";
source_path="Vcache.fex";
stored_length=0x00000000;
pad1=0x00000000;
original_length=0x00000000;
pad2=0x00000000;
offset=0x00000000;
}
"""
    cfg_text += entry_cache
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(cfg_text)
    print("[OK] image.cfg atualizado com cache.fex e Vcache.fex (total 42 arquivos)")
