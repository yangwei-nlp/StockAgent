import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QStackedWidget, QWidget)
from PyQt5.QtCore import Qt
from media_manager_ui import MediaManagerUI

from src.knowledge_chat_ui import KnowledgeBaseChatUI, KnowledgeManagementUI


class KnowledgeBaseMain(QMainWindow):
    """知识库软件主界面 - 集成媒体文件管理和知识库对话功能"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("知识库管理系统")
        self.setFixedSize(900, 700)
        self.center_window()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # 标题区域
        title_label = QLabel("知识库管理系统")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 功能导航区域
        nav_layout = QHBoxLayout()
        self.media_btn = QPushButton("媒体文件管理")
        self.media_btn.setStyleSheet("font-size: 14px; padding: 8px; background-color: #e3f2fd;")
        self.media_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        self.km_btn = QPushButton("知识管理")
        self.km_btn.setStyleSheet("font-size: 14px; padding: 8px; background-color: #e8f5e8;")
        self.km_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        self.kb_btn = QPushButton("知识库对话")
        self.kb_btn.setStyleSheet("font-size: 14px; padding: 8px; background-color: #f3e5f5;")
        self.kb_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

        nav_layout.addWidget(self.media_btn)
        nav_layout.addWidget(self.km_btn)
        nav_layout.addWidget(self.kb_btn)
        nav_layout.addStretch()
        layout.addLayout(nav_layout)

        # 堆叠布局 - 包含三个功能页面
        self.stacked_widget = QStackedWidget()
        
        # 页面1: 媒体文件管理
        self.media_page = MediaManagerUI()
        self.stacked_widget.addWidget(self.media_page)
        
        # 页面2: 知识管理
        self.km_page = KnowledgeManagementUI()
        self.stacked_widget.addWidget(self.km_page)

        # 页面3: 知识库对话
        self.chat_page = KnowledgeBaseChatUI()
        self.stacked_widget.addWidget(self.chat_page)

        layout.addWidget(self.stacked_widget)
        central_widget.setLayout(layout)

    def center_window(self):
        """将窗口居中显示"""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = KnowledgeBaseMain()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()