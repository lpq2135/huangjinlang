from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.uic import loadUi


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 加载登录页面的 UI
        loadUi(r'C:\Users\Administrator\PycharmProjects\pythonProject\huangjinlang\lpq577_code\应用程序文件\黄金浪电商管理系统\login_window.ui', self)

        # 绑定登录按钮点击事件
        self.loginButton.clicked.connect(self.handle_login)

    def handle_login(self):
        # 获取用户名和密码
        username = self.usernameLineEdit.text()
        password = self.passwordLineEdit.text()

        # 简单验证逻辑
        if username == "admin" and password == "123456":
            self.go_to_main_window()
        else:
            QMessageBox.warning(self, "登录失败", "用户名或密码错误！")

    def go_to_main_window(self):
        # 跳转到主窗口
        self.main_window = MainWindow()  # 创建主窗口实例
        self.main_window.show()
        self.close()  # 关闭登录窗口


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 加载主页面的 UI
        loadUi(r'C:\Users\Administrator\PycharmProjects\pythonProject\huangjinlang\lpq577_code\应用程序文件\黄金浪电商管理系统\main_window.ui', self)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())
