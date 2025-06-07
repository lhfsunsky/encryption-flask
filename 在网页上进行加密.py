import os
import uuid
from flask import Flask, render_template, request, send_file, redirect, url_for
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

app = Flask(__name__)
app.config.from_object('config.Config')

# 确保存储目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ENCRYPTED_FOLDER'], exist_ok=True)

def encrypt_video(input_path, output_path, password):
    """加密视频文件"""
    salt = get_random_bytes(16)
    key = PBKDF2(password, salt, dkLen=32, count=1000000)
    iv = get_random_bytes(16)
    
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    with open(output_path, 'wb') as f_out:
        f_out.write(salt)
        f_out.write(iv)
        
        with open(input_path, 'rb') as f_in:
            while True:
                chunk = f_in.read(1024 * 1024)  # 1MB块
                if not chunk:
                    break
                
                # 填充最后一块
                if len(chunk) % 16 != 0:
                    padding = 16 - (len(chunk) % 16)
                    chunk += bytes([padding]) * padding
                
                f_out.write(cipher.encrypt(chunk))

@app.route('/', methods=['GET'])
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    """加密上传的视频"""
    if 'video' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['video']
    password = request.form.get('password')
    
    if file.filename == '' or not password:
        return redirect(url_for('index'))
    
    # 生成唯一文件名
    original_filename = file.filename
    file_id = str(uuid.uuid4())
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{original_filename}")
    encrypted_path = os.path.join(app.config['ENCRYPTED_FOLDER'], f"{file_id}.bin")
    
    # 保存原始文件
    file.save(original_path)
    
    # 加密视频
    encrypt_video(original_path, encrypted_path, password)
    
    # 删除原始文件(可选)
    if app.config['DELETE_ORIGINAL']:
        os.remove(original_path)
    
    return render_template('download.html', 
                           file_id=file_id, 
                           original_name=original_filename)

@app.route('/download/<file_id>')
def download(file_id):
    """下载加密视频"""
    encrypted_path = os.path.join(app.config['ENCRYPTED_FOLDER'], f"{file_id}.bin")
    if not os.path.exists(encrypted_path):
        return "File not found", 404
    
    return send_file(encrypted_path, as_attachment=True, download_name=f"encrypted_{file_id}.bin")

@app.route('/player/<file_id>')
def player(file_id):
    """视频播放器页面"""
    encrypted_path = os.path.join(app.config['ENCRYPTED_FOLDER'], f"{file_id}.bin")
    if not os.path.exists(encrypted_path):
        return "File not found", 404
    
    return render_template('player.html', file_id=file_id)

@app.route('/decrypt/<file_id>', methods=['POST'])
def decrypt(file_id):
    """解密视频流(用于播放)"""
    password = request.form.get('password')
    print(password)
    encrypted_path = os.path.join(app.config['ENCRYPTED_FOLDER'], f"{file_id}.bin")
    
    if not os.path.exists(encrypted_path) or not password:
        return "Invalid request", 400
    
    # 读取文件头(盐值+IV)
    with open(encrypted_path, 'rb') as f:
        salt = f.read(16)
        iv = f.read(16)
        ciphertext = f.read()
    
    # 派生密钥
    key = PBKDF2(password, salt, dkLen=32, count=1000000)
    
    # 解密
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = cipher.decrypt(ciphertext)
    
    # 移除填充
    padding = decrypted_data[-1]
    if padding <= 16:
        decrypted_data = decrypted_data[:-padding]
    print("Decrypted data head (hex):", decrypted_data[:100].hex())
    return decrypted_data, 200, {'Content-Type': 'video/mp4'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)