import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout,
                             QHBoxLayout)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class LoginPage(QWidget):
    def __init__(self):
        super().__init__()
        self.background_label = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('D小秘')

        # 获取屏幕的尺寸，设置窗口初始大小
        screen = QApplication.primaryScreen().availableGeometry()
        window_width = int(screen.width() * 0.6)
        window_height = int(screen.height() * 0.8)

        # 设置固定大小窗口
        self.setFixedSize(window_width, window_height)
        self.center()

        layout = QVBoxLayout()

        # 设置背景标签
        self.background_label = QLabel(self)
        pixmap = QPixmap(r'C:\Users\Administrator\Desktop\未命名(6).png')
        self.set_background(pixmap)  # 设置背景图片并适应窗口

        layout.addWidget(self.background_label)

        # 登录表单
        self.username_label = QLabel('用户名:')
        self.username_input = QLineEdit()
        self.password_label = QLabel('密码:')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton('登录')
        self.login_button.clicked.connect(self.handleLogin)

        form_layout = QVBoxLayout()
        form_layout.addWidget(self.username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_label)
        form_layout.addWidget(self.password_input)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.login_button)
        button_layout.addStretch()

        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def set_background(self, pixmap):
        """根据窗口大小设置背景图片"""
        # 获取窗口的当前大小
        window_size = self.size()
        # 根据窗口大小调整图片尺寸，保持比例
        pixmap = pixmap.scaled(window_size, Qt.AspectRatioMode.KeepAspectRatio)
        self.background_label.setPixmap(pixmap)
        self.background_label.setScaledContents(True)

    def center(self):
        """使窗口居中"""
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def handleLogin(self):
        """处理登录逻辑"""
        username = self.username_input.text()
        password = self.password_input.text()

        if username == 'admin' and password == '1234':
            QMessageBox.information(self, '成功', '登录成功！')
        else:
            QMessageBox.warning(self, '失败', '用户名或密码错误！')

    def resizeEvent(self, event):
        """当窗口大小改变时，更新背景图片"""
        if self.background_label:
            pixmap = QPixmap(r'C:\Users\Administrator\Desktop\未命名(6).png')
            self.set_background(pixmap)
        super().resizeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login = LoginPage()
    login.show()
    sys.exit(app.exec())
