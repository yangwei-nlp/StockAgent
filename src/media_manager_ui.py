import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QListWidgetItem, QLabel, QFileDialog, 
                             QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt

from src.media_manager import MediaManager


class MediaManagerUI(QWidget):
    """媒体文件管理界面类"""
    
    def __init__(self, base_dir="/Users/younger/Movies/抖音/"):
        super().__init__()
        self.base_dir = base_dir
        self.media_manager = MediaManager(self.base_dir)
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()

        # 目录选择区域
        dir_layout = QHBoxLayout()
        self.dir_label = QLabel(f"当前目录: {self.base_dir}")
        self.select_dir_btn = QPushButton("选择目录")
        self.select_dir_btn.clicked.connect(self.select_directory)
        dir_layout.addWidget(self.dir_label)
        dir_layout.addWidget(self.select_dir_btn)
        dir_layout.addStretch()
        layout.addLayout(dir_layout)

        # 文件列表区域
        layout.addWidget(QLabel("媒体文件列表:"))
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.file_list)

        # 文件操作按钮区域
        file_ops_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self.refresh_file_list)
        self.delete_btn = QPushButton("删除选中文件")
        self.delete_btn.clicked.connect(self.delete_selected_files)
        self.merge_btn = QPushButton("合并选中文件")
        self.merge_btn.clicked.connect(self.merge_selected_files)
        
        file_ops_layout.addWidget(self.refresh_btn)
        file_ops_layout.addWidget(self.delete_btn)
        file_ops_layout.addWidget(self.merge_btn)
        file_ops_layout.addStretch()
        layout.addLayout(file_ops_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # 初始加载文件列表
        self.refresh_file_list()

    def select_directory(self):
        """选择目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择媒体文件目录", self.base_dir)
        if directory:
            self.base_dir = directory
            self.media_manager.set_base_dir(self.base_dir)
            self.dir_label.setText(f"当前目录: {self.base_dir}")
            self.refresh_file_list()

    def refresh_file_list(self):
        """刷新文件列表"""
        self.file_list.clear()
        try:
            file_info_list = self.media_manager.get_file_info()
            
            # 添加文件到列表
            for file_info in file_info_list:
                display_text = f"{file_info['path']} ({file_info['size']} MB)"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, file_info['full_path'])  # 保存绝对路径
                self.file_list.addItem(item)
            
            self.status_label.setText(f"找到 {len(file_info_list)} 个FLV文件")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法读取目录: {str(e)}")

    def merge_selected_files(self):
        """合并选中的文件"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要合并的视频文件")
            return

        if len(selected_items) < 2:
            QMessageBox.warning(self, "警告", "请至少选择2个文件进行合并")
            return

        # 获取选中的文件路径
        selected_files = [item.data(Qt.UserRole) for item in selected_items]
        
        # 确认对话框
        reply = QMessageBox.question(self, "确认合并", 
                                   f"确定要合并以下 {len(selected_files)} 个文件吗？\n" + 
                                   "\n".join(selected_files[:3]) + 
                                   ("\n..." if len(selected_files) > 3 else ""),
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.perform_merge(selected_files)

    def delete_selected_files(self):
        """删除选中的文件"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要删除的视频文件")
            return

        # 获取选中的文件路径
        selected_files = [item.data(Qt.UserRole) for item in selected_items]
        
        # 确认删除对话框
        reply = QMessageBox.question(self, "确认删除", 
                                   f"确定要删除以下 {len(selected_files)} 个文件吗？\n" + 
                                   "\n".join(selected_files[:3]) + 
                                   ("\n..." if len(selected_files) > 3 else "") + 
                                   "\n\n注意：此操作不可恢复！",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.perform_delete(selected_files)

    def perform_delete(self, files_to_delete):
        """执行文件删除"""
        result = self.media_manager.delete_files(files_to_delete)
        
        # 显示结果
        if result['failed_files']:
            error_msg = f"成功删除 {result['deleted_count']} 个文件，但以下文件删除失败：\n" + "\n".join(result['failed_files'])
            QMessageBox.warning(self, "删除结果", error_msg)
        else:
            QMessageBox.information(self, "成功", f"成功删除 {result['deleted_count']} 个文件")
        
        # 刷新文件列表
        self.refresh_file_list()

    def perform_merge(self, input_files):
        """执行文件合并"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在合并视频...")
        
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()

        self.progress_bar.setValue(30)
        QApplication.processEvents()

        # 调用媒体管理器进行合并
        result = self.media_manager.merge_videos(input_files)

        self.progress_bar.setValue(70)
        QApplication.processEvents()

        if result['success']:
            self.progress_bar.setValue(100)
            self.status_label.setText(result['message'])
            QMessageBox.information(self, "成功", f"视频合并成功！\n输出文件: {result.get('output_file', '')}")
            
            # 刷新文件列表
            self.refresh_file_list()
        else:
            self.status_label.setText(result['message'])
            QMessageBox.critical(self, "错误", result['message'])
        
        self.progress_bar.setVisible(False)