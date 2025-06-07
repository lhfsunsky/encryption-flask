import sys
import os
import tempfile
import mimetypes
import subprocess
from Crypto.Cipher import AES

KEY = b'1234567890abcdef'
IV = bytes.fromhex('00112233445566778899aabbccddeeff')

def aes_decrypt(data):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    decrypted = cipher.decrypt(data)
    pad_len = decrypted[-1]
    return decrypted[:-pad_len]

def decrypt_and_open(enc_path):
    if not os.path.isfile(enc_path):
        print("文件不存在：", enc_path)
        return

    with open(enc_path, "rb") as f:
        encrypted_data = f.read()

    try:
        decrypted = aes_decrypt(encrypted_data)
    except Exception as e:
        print("解密失败：", e)
        return

    # 推断真实文件扩展名
    if enc_path.endswith('.enc'):
        base_name = os.path.basename(enc_path)[:-4]  # 去掉 .enc
    else:
        base_name = os.path.basename(enc_path)

    ext = '.' + base_name.split('.')[-1] if '.' in base_name else ''
    guessed_type = mimetypes.guess_type(base_name)[0]

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(decrypted)
        tmp_path = tmp.name

    # 用默认程序打开
    try:
        os.startfile(tmp_path)  # 仅 Windows
    except AttributeError:
        subprocess.run(['xdg-open', tmp_path])  # Linux/Mac

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请拖入 .enc 文件或指定路径")
    else:
        decrypt_and_open(sys.argv[1])
