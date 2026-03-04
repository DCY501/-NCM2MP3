import os
from Crypto.Cipher import AES

CORE_KEY = bytes.fromhex("687A4852416D736F356B496E62617857")
META_KEY = bytes.fromhex("2331346C6A6B5F215C5D2630553C2728")

def unpad(data):
    return data[:-data[-1]]

def dump(file_path, output_dir=None):
    with open(file_path, 'rb') as f:
        if f.read(8) != b'CTENFDAM':
            raise ValueError("不是有效的 NCM 文件")
        
        f.seek(2, 1)
        key_len = int.from_bytes(f.read(4), 'little')
        key_data = bytearray(f.read(key_len))
        for i in range(len(key_data)):
            key_data[i] ^= 0x64
        key_data = bytearray(unpad(AES.new(CORE_KEY, AES.MODE_ECB).decrypt(bytes(key_data))))[17:]
        
        key_box = bytearray(range(256))
        c = last = key_offset = 0
        for i in range(256):
            swap = key_box[i]
            c = (swap + last + key_data[key_offset]) & 0xff
            key_offset = (key_offset + 1) % len(key_data)
            key_box[i], key_box[c] = key_box[c], swap
            last = c
        
        meta_len = int.from_bytes(f.read(4), 'little')
        meta_data = bytearray(f.read(meta_len))
        for i in range(len(meta_data)):
            meta_data[i] ^= 0x63
        import base64, json
        meta = json.loads(unpad(AES.new(META_KEY, AES.MODE_ECB).decrypt(
            base64.b64decode(bytes(meta_data)[22:]))).decode('utf-8')[6:])
        
        f.seek(9, 1)
        f.seek(int.from_bytes(f.read(4), 'little'), 1)
        
        ext = meta.get('format', 'mp3')
        out_name = os.path.basename(file_path).rsplit('.ncm', 1)[0] + '.' + ext
        out_dir = output_dir or os.path.dirname(file_path) or '.'
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, out_name)
        
        with open(out_path, 'wb') as m:
            while chunk := f.read(0x8000):
                chunk = bytearray(chunk)
                for i in range(1, len(chunk) + 1):
                    j = i & 0xff
                    chunk[i-1] ^= key_box[(key_box[j] + key_box[(key_box[j] + j) & 0xff]) & 0xff]
                m.write(chunk)
        
        return out_name
