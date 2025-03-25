import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QListWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextCursor

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle("客服集成软件")
        self.setGeometry(100, 100, 600, 400)

        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 统计信息
        self.stats_label = QLabel("今日在线时长: 00:29 | 今日服务: 1")
        layout.addWidget(self.stats_label)

        # 消息列表
        self.message_list = QListWidget()
        layout.addWidget(self.message_list)

        # 输入框
        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("在此处输入消息内容，按回车键以发送消息，按 Ctrl + Enter 键执行")
        layout.addWidget(self.input_box)

        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)

        # 定时器更新统计信息
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)  # 每秒更新一次

    def send_message(self):
        # 获取输入内容
        message = self.input_box.toPlainText().strip()
        if message:
            # 添加到消息列表
            self.message_list.addItem(f"你: {message}")
            self.input_box.clear()

    def update_stats(self):
        # 模拟更新统计信息
        self.stats_label.setText("今日在线时长: 00:30 | 今日服务: 1")

    def keyPressEvent(self, event):
        # 监听键盘事件
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Ctrl + Enter 换行
            self.input_box.insertPlainText("\n")
        elif event.key() == Qt.Key.Key_Return:
            # Enter 发送消息
            self.send_message()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())