from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("黄金浪电商管理系统")
        self.resize(1280, 720)

        # 添加主界面内容
        label = QtWidgets.QLabel("李狗+高狗，我想你们了", self)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label.setGeometry(0, 0, 1280, 720)
        font = QtGui.QFont()
        font.setPointSize(24)
        label.setFont(font)


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("黄金浪电商管理系统")

        # 获取屏幕分辨率并设置窗口初始大小为屏幕的60%
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        initial_width = int(screen.width() * 0.7)
        initial_height = int(screen.height() * 0.7)
        Form.resize(initial_width, initial_height)

        # 设置窗口最小大小
        Form.setMinimumSize(int(screen.width() * 0.3), int(screen.height() * 0.3))

        # 背景Label
        self.label = QtWidgets.QLabel(parent=Form)
        self.label.setGeometry(QtCore.QRect(0, 0, initial_width, initial_height))
        self.label.setText("")
        self.label.setPixmap(
            QtGui.QPixmap("../../../../../Desktop/应用程序开发/软件图片/软件封面.png")
        )
        self.label.setScaledContents(True)
        self.label.setObjectName("label")

        # 用户名输入框
        self.lineEdit = QtWidgets.QLineEdit(parent=Form)
        self.lineEdit.setGeometry(
            QtCore.QRect(
                int(initial_width * 0.63),  # 63%宽度处
                int(initial_height * 0.36),  # 36%高度处
                int(initial_width * 0.16),  # 16%宽度
                int(initial_height * 0.06),  # 6%高度
            )
        )
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lineEdit.setFont(font)
        self.lineEdit.setObjectName("lineEdit")

        # 设置输入验证器 - 允许英文、数字和下划线
        reg_exp = QRegularExpression("^[a-zA-Z0-9_]*$")  # 添加下划线到正则表达式
        validator = QRegularExpressionValidator(reg_exp, self.lineEdit)
        self.lineEdit.setValidator(validator)
        # 禁止输入法（防止中文输入法）
        self.lineEdit.setInputMethodHints(QtCore.Qt.InputMethodHint.ImhLatinOnly)

        # 密码输入框
        self.lineEdit_2 = QtWidgets.QLineEdit(parent=Form)
        self.lineEdit_2.setGeometry(
            QtCore.QRect(
                int(initial_width * 0.63),
                int(initial_height * 0.5),
                int(initial_width * 0.16),
                int(initial_height * 0.06),
            )
        )
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lineEdit_2.setFont(font)
        self.lineEdit_2.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.lineEdit_2.setObjectName("lineEdit_2")

        self.loginButton = QtWidgets.QPushButton(parent=Form)
        self.loginButton.setGeometry(QtCore.QRect(1015, 527, 90, 57))
        self.loginButton.setStyleSheet(
            "QPushButton {\n"
            "    background-color: rgba(50, 150, 250, 0);\n"
            "    border: 1px solid rgb(50, 150, 250);\n"
            "    border-radius: 5px;\n"
            "    color: white;\n"
            "}\n"
            "QPushButton:hover {\n"
            "    background-color: rgba(50, 150, 250, 0.9);\n"
            "}"
        )
        self.loginButton.setText("")
        self.loginButton.setObjectName("loginButton")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

        # 连接窗口大小改变信号
        Form.resizeEvent = self.resizeEvent

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "黄金浪电商管理系统"))
        self.lineEdit.setPlaceholderText(
            _translate("Form", " 请输入您的账号")
        )  # 修改提示文字
        self.lineEdit_2.setPlaceholderText(_translate("Form", " 请输入您的密码"))

    def resizeEvent(self, event):
        # 获取当前窗口大小
        size = self.label.parent().size()

        # 调整背景图片大小
        self.label.setGeometry(QtCore.QRect(0, 0, size.width(), size.height()))

        # 调整输入框位置和大小（按比例）
        self.lineEdit.setGeometry(
            QtCore.QRect(
                int(size.width() * 0.63),
                int(size.height() * 0.36),
                int(size.width() * 0.16),
                int(size.height() * 0.06),
            )
        )
        self.lineEdit_2.setGeometry(
            QtCore.QRect(
                int(size.width() * 0.63),
                int(size.height() * 0.5),
                int(size.width() * 0.16),
                int(size.height() * 0.06),
            )
        )

        # 调整按钮位置和大小（按比例）
        self.loginButton.setGeometry(
            QtCore.QRect(
                int(size.width() * 0.793),  # 大约79%宽度处
                int(size.height() * 0.735),  # 大约73%高度处
                int(size.width() * 0.07),  # 7%宽度
                int(size.height() * 0.08),  # 8%高度
            )
        )

        # 调用父类的resizeEvent
        if hasattr(super(), "resizeEvent"):
            super().resizeEvent(event)


class LoginWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # 连接登录按钮点击事件
        self.ui.loginButton.clicked.connect(self.check_login)

    def check_login(self):
        username = self.ui.lineEdit.text()
        password = self.ui.lineEdit_2.text()

        # 检查用户名和密码
        if username == "huangjinlang" and password == "Qiang123":
            self.main_window = MainWindow()
            self.main_window.show()
            self.close()
        else:
            QtWidgets.QMessageBox.warning(self, "登录失败", "用户名或密码错误")


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    login_window = LoginWindow()
    login_window.show()
    app.exec()
