import os
import sys
import tempfile
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QFileDialog, QMessageBox, QSlider, QStyle)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QIcon, QFont

class DecryptionPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("加密视频播放器")
        self.setGeometry(100, 100, 900, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
            QLineEdit {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #7f8c8d;
                border-radius: 4px;
                padding: 8px;
            }
            QLabel {
                font-weight: bold;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #34495e;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #3498db;
                border-radius: 4px;
            }
        """)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("加密视频播放器")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title_label)
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        self.file_label.setFont(QFont("Arial", 10))
        self.file_label.setStyleSheet("border: 1px solid #7f8c8d; padding: 8px; border-radius: 4px;")
        file_layout.addWidget(self.file_label, 4)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setFixedWidth(100)
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_btn, 1)
        
        self.layout.addLayout(file_layout)
        
        # 密码输入区域
        password_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("输入视频密码")
        password_layout.addWidget(self.password_input, 4)
        
        self.decrypt_btn = QPushButton("解密并播放")
        self.decrypt_btn.setFixedWidth(120)
        self.decrypt_btn.clicked.connect(self.decrypt_and_play)
        self.decrypt_btn.setEnabled(False)
        password_layout.addWidget(self.decrypt_btn, 1)
        
        self.layout.addLayout(password_layout)
        
        # 视频播放区域
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(400)
        self.layout.addWidget(self.video_widget)
        
        # 播放控制区域
        control_layout = QHBoxLayout()
        
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.play_video)
        control_layout.addWidget(self.play_btn)
        
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        control_layout.addWidget(self.position_slider, 5)
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setFixedWidth(120)
        control_layout.addWidget(self.time_label)
        
        self.layout.addLayout(control_layout)
        
        # 状态栏
        self.status_label = QLabel("准备就绪")
        self.status_label.setFont(QFont("Arial", 9))
        self.layout.addWidget(self.status_label)
        
        # 媒体播放器
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.stateChanged.connect(self.media_state_changed)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        
        # 临时文件路径
        self.temp_file_path = None
        
        # 设置窗口图标
        self.setWindowIcon(QIcon(self.style().standardIcon(QStyle.SP_MediaPlay)))
        
        # 状态更新计时器
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.clear_status)
        self.status_timer.setSingleShot(True)
        
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择加密视频文件", "", "加密视频文件 (*.bin *.enc);;所有文件 (*.*)"
        )
        
        if file_path:
            self.file_label.setText(os.path.basename(file_path))
            self.encrypted_file_path = file_path
            self.decrypt_btn.setEnabled(True)
            self.status_label.setText(f"已选择文件: {os.path.basename(file_path)}")
            self.status_timer.start(3000)
    
    def decrypt_and_play(self):
        password = self.password_input.text()
        if not password:
            QMessageBox.warning(self, "输入错误", "请输入密码")
            return
        
        if not hasattr(self, 'encrypted_file_path'):
            QMessageBox.warning(self, "文件错误", "请先选择加密视频文件")
            return
        
        self.status_label.setText("正在解密视频...")
        QApplication.processEvents()  # 更新UI
        
        try:
            # 解密视频到临时文件
            self.temp_file_path = self.decrypt_video(self.encrypted_file_path, password)
            
            # 加载视频到播放器
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.temp_file_path)))
            self.play_btn.setEnabled(True)
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.status_label.setText("解密完成！点击播放按钮开始播放")
            self.status_timer.start(5000)
            
        except Exception as e:
            QMessageBox.critical(self, "解密失败", f"解密过程中发生错误:\n{str(e)}")
            self.status_label.setText("解密失败")
            self.status_timer.start(3000)
    
    def decrypt_video(self, input_path, password):
        # 读取加密文件
        with open(input_path, 'rb') as f:
            salt = f.read(16)
            iv = f.read(16)
            ciphertext = f.read()
        
        # 派生密钥
        key = PBKDF2(password, salt, dkLen=32, count=1000000)
        
        # 创建解密器
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # 解密数据
        decrypted_data = cipher.decrypt(ciphertext)
        
        # 移除填充
        padding = decrypted_data[-1]
        if padding <= 16:
            decrypted_data = decrypted_data[:-padding]
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_file.write(decrypted_data)
        temp_file.close()
        
        return temp_file.name
    
    def play_video(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            self.media_player.play()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
    
    def media_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
    
    def position_changed(self, position):
        self.position_slider.setValue(position)
        
        # 更新时间显示
        duration = self.media_player.duration()
        if duration > 0:
            current_time = self.format_time(position)
            total_time = self.format_time(duration)
            self.time_label.setText(f"{current_time} / {total_time}")
    
    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
    
    def set_position(self, position):
        self.media_player.setPosition(position)
    
    def format_time(self, ms):
        seconds = ms // 1000
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def clear_status(self):
        self.status_label.setText("准备就绪")
    
    def closeEvent(self, event):
        # 清理临时文件
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.unlink(self.temp_file_path)
            except:
                pass
        
        # 停止媒体播放
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.stop()
        
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = DecryptionPlayer()
    player.show()
    sys.exit(app.exec_())