import sys
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QWidget,
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt


class LoginApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle("黄金浪电商erp")
        self.resize(800, 600)

        # 设置背景图片
        self.background_label = QLabel(self)
        self.background_pixmap = QPixmap(r"C:\\Users\\Administrator\\Desktop\\未命名(6).png")  # 替换为你的背景图片路径
        self.background_label.setPixmap(self.background_pixmap)
        self.background_label.setScaledContents(True)  # 自适应窗口大小
        self.background_label.setGeometry(self.rect())  # 设置为整个窗口

        # 主布局
        main_layout = QHBoxLayout()  # 水平布局

        # 功能部分布局（左侧）
        function_layout = QVBoxLayout()
        function_layout.addStretch(2)  # 增加顶部空白，进一步下移组件

        # 用户名输入
        username_label = QLabel("用户名：")
        username_label.setFont(QFont("Arial", 12))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setFixedWidth(300)

        # 密码输入
        password_label = QLabel("密码：")
        password_label.setFont(QFont("Arial", 12))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedWidth(300)

        # 记住我
        self.remember_checkbox = QCheckBox("记住")
        self.remember_checkbox.setFont(QFont("Arial", 12))

        # 登录按钮
        login_button = QPushButton("登录")
        login_button.setFont(QFont("Arial", 14))
        login_button.setFixedWidth(100)
        login_button.clicked.connect(self.on_login)

        # 将功能组件加入布局
        function_layout.addWidget(username_label, alignment=Qt.AlignmentFlag.AlignCenter)
        function_layout.addWidget(self.username_input, alignment=Qt.AlignmentFlag.AlignCenter)
        function_layout.addWidget(password_label, alignment=Qt.AlignmentFlag.AlignCenter)
        function_layout.addWidget(self.password_input, alignment=Qt.AlignmentFlag.AlignCenter)
        function_layout.addWidget(self.remember_checkbox, alignment=Qt.AlignmentFlag.AlignCenter)
        function_layout.addWidget(login_button, alignment=Qt.AlignmentFlag.AlignCenter)
        function_layout.addStretch(1)  # 添加底部空白，调整组件位置

        # 右侧图片
        image_label = QLabel(self)
        image_pixmap = QPixmap("logo.png")  # 替换为你的右侧图像路径
        image_pixmap = image_pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio)
        image_label.setPixmap(image_pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 将子布局加入主布局
        main_layout.addLayout(function_layout)  # 功能布局在左侧
        main_layout.addWidget(image_label)  # 图片在右侧

        # 设置主布局
        self.setLayout(main_layout)

    def resizeEvent(self, event):
        """
        重写 resizeEvent，让背景图片自适应窗口大小
        """
        self.background_label.setGeometry(self.rect())  # 调整背景图片大小
        super().resizeEvent(event)

    def on_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        print(f"用户名：{username}, 密码：{password}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginApp()
    window.show()
    sys.exit(app.exec())
