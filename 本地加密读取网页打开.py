from flask import Flask, send_file, render_template, jsonify, Response, abort, request
import os
from Crypto.Cipher import AES
import re
app = Flask(__name__)
KEY = b'1234567890abcdef'
IV = bytes.fromhex('00112233445566778899aabbccddeeff')
##ENCRYPTED_FOLDER = "encrypted_files"
ENCRYPTED_FOLDER = "F:\\加密"
def try_int(s):
    try:
        return int(s)
    except:
        return s

def natural_sort_key(s):
    # 分割字符串成数字和非数字部分，数字部分转int方便自然排序
    return [try_int(c) for c in re.split(r'(\d+)', s)]
def aes_decrypt(data):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    decrypted = cipher.decrypt(data)
    pad_len = decrypted[-1]
    return decrypted[:-pad_len]

@app.route('/')
def index():
    folders = []
    files = []
    for entry in os.listdir(ENCRYPTED_FOLDER):
        full_path = os.path.join(ENCRYPTED_FOLDER, entry)
        if os.path.isdir(full_path):
            folders.append(entry)
        elif os.path.isfile(full_path):
            files.append(entry)
    folders.sort(key=natural_sort_key)
    files.sort(key=natural_sort_key)
    return render_template("index.html", folders=folders, files=files)

@app.route('/browse/<path:folder>')
def browse(folder):
    abs_path = os.path.join(ENCRYPTED_FOLDER, folder)
    if not os.path.isdir(abs_path):
        abort(404)
    files = []
    folders = []

    for file in os.listdir(abs_path):
        full_path = os.path.join(abs_path, file)
        if os.path.isfile(full_path):
            files.append(os.path.join(folder, file))  # 相对路径
    folders.sort(key=natural_sort_key)
    files.sort(key=natural_sort_key)
    return render_template("folder.html", files=files, folder=folder)

@app.route('/preview/<path:path>')
def preview(path):
    return render_template("preview.html", path=path)

@app.route('/file/<path:path>')
def get_file(path):
    file_path = os.path.join(ENCRYPTED_FOLDER, path)
    if not os.path.isfile(file_path):
        abort(404)
    with open(file_path, "rb") as f:
        encrypted_data = f.read()
    try:
        decrypted_data = aes_decrypt(encrypted_data)
    except Exception as e:
        return f"解密失败: {e}", 500
    lower = path.lower()
    if lower.endswith('.mp4.enc'):
        mimetype = 'video/mp4'
    elif lower.endswith('.mp3.enc'):
        mimetype = 'audio/mpeg'
    elif lower.endswith(('.png.enc', '.jpg.enc', '.jpeg.enc')):
        ext = lower.split('.')[-2]
        mimetype = f'image/{ext if ext != "jpg" else "jpeg"}'
    elif lower.endswith('.pdf.enc'):
        mimetype = 'application/pdf'
    elif lower.endswith('.txt.enc'):
        mimetype = 'text/plain'
    else:
        mimetype = 'application/octet-stream'
    return Response(decrypted_data, mimetype=mimetype)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
