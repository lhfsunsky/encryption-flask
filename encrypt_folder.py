# encrypt_folder.py
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

KEY = b'1234567890abcdef'
IV = bytes.fromhex('00112233445566778899aabbccddeeff')

def encrypt_file(in_path, out_path):
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV))
    encryptor = cipher.encryptor()

    with open(in_path, 'rb') as fin, open(out_path, 'wb') as fout:
        while chunk := fin.read(16 * 1024):
            if len(chunk) % 16 != 0:
                pad_len = 16 - len(chunk) % 16
                chunk += bytes([pad_len]) * pad_len
                fout.write(encryptor.update(chunk))
                break
            fout.write(encryptor.update(chunk))
        fout.write(encryptor.finalize())

def encrypt_folder(src_dir, dst_dir):
    for root, _, files in os.walk(src_dir):
        for file in files:
            in_path = os.path.join(root, file)
            rel_path = os.path.relpath(in_path, src_dir)
            out_path = os.path.join(dst_dir, rel_path + ".enc")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            encrypt_file(in_path, out_path)
            print(f"Encrypted: {rel_path}")

if __name__ == "__main__":
    encrypt_folder("raw_folder", "encrypted_files")
    ##encrypt_folder("D:\\", "D:\\")

