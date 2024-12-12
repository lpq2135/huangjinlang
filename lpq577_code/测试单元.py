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
        self.setWindowTitle('登录页面')
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
        self.center()

        layout = QVBoxLayout()
        self.background_label = QLabel(self)
        pixmap = QPixmap('background.jpg')
        self.background_label.setPixmap(pixmap)
        self.background_label.setScaledContents(True)
        layout.addWidget(self.background_label)

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

    def center(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def handleLogin(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if username == 'admin' and password == '1234':
            QMessageBox.information(self, '成功', '登录成功！')
        else:
            QMessageBox.warning(self, '失败', '用户名或密码错误！')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login = LoginPage()
    login.show()
    sys.exit(app.exec())