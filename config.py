import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploaded')
    ENCRYPTED_FOLDER = os.path.join(basedir, 'static/encrypted')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2GB
    DELETE_ORIGINAL = True  # 加密后删除原始文件