import os
import sys
from ncmdump import dump

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def convert(ncm_path, output_dir):
    try:
        print(f"正在转换: {os.path.basename(ncm_path)}")
        filename = dump(ncm_path, output_dir)
        print(f"  [OK] {filename}")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

def main():
    search_dirs = [
        os.path.join(BASE_DIR, "网易云下载文件"),
        os.path.join(BASE_DIR, "网易云下载文件", "VipSongsDownload")
    ]
    output_dir = os.path.join(BASE_DIR, "转化")
    
    ncm_files = []
    for d in search_dirs:
        if os.path.isdir(d):
            for root, _, files in os.walk(d):
                ncm_files.extend(os.path.join(root, f) for f in files if f.lower().endswith('.ncm'))
    
    if not ncm_files:
        print("没有找到 NCM 文件")
        return
    
    print(f"找到 {len(ncm_files)} 个文件\n{'-'*40}")
    success = sum(convert(f, output_dir) for f in ncm_files)
    print(f"{'-'*40}\n完成: {success}/{len(ncm_files)}")

if __name__ == '__main__':
    main()
