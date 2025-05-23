import sys
from PyQt6.QtWidgets import QApplication, QWidget
from login import Ui_Form


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 创建UI实例
        self.ui = Ui_Form()
        self.ui.setupUi(self)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    sys.exit(app.exec())
