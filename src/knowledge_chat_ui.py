import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTextEdit, QLineEdit, QLabel, QComboBox, QMessageBox,
                             QListWidget, QListWidgetItem, QFileDialog, QSplitter, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from openai import OpenAI
import re

from src.config import API_KEY, BASE_URL, MODEL_NAME


class ChatWorker:
    """对话工作器，负责处理用户输入并生成AI回复"""
    
    def __init__(self) -> None:
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    def get_response(self, user_input: str, knowledge_base: str, conversation_history: list[dict] = None) -> str:
        """根据用户输入、知识库和对话历史生成AI回复"""
        if self.client:
            return self._get_llm_response(user_input, knowledge_base, conversation_history)
        else:
            return "回复失败"

    def _get_llm_response(self, user_input: str, knowledge_base: str, conversation_history: list[dict] = None) -> str:
        """使用LLM生成回复，包含对话历史"""
        try:
            system_message = f"你是一个专业的股票投资助手，专注于{knowledge_base}领域。请基于该领域的专业知识回答用户问题。"
            
            # 构建消息列表
            messages = [{"role": "system", "content": system_message}]
            
            # 添加对话历史（如果有）
            if conversation_history:
                # 限制历史对话长度，避免token超限
                max_history_length = 0
                recent_history = conversation_history[-max_history_length:] if len(conversation_history) > max_history_length else conversation_history
                messages.extend(recent_history)
            
            # 添加当前用户输入
            messages.append({"role": "user", "content": user_input})
            
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error getting LLM response: {e}")
            return "回复失败"

class ChatWorkerThread(QThread):
    """后台处理对话的线程"""
    response_received = pyqtSignal(str)
    
    def __init__(self, chat_worker: ChatWorker, user_input: str, knowledge_base: str, conversation_history: list[dict] = None):
        super().__init__()
        self.chat_worker = chat_worker
        self.user_input = user_input
        self.knowledge_base = knowledge_base
        self.conversation_history = conversation_history
    
    def run(self):
        """线程运行方法"""
        response = self.chat_worker.get_response(self.user_input, self.knowledge_base, self.conversation_history)
        self.response_received.emit(response)


class KnowledgeBaseChatUI(QWidget):
    """知识库对话界面类"""
    
    def __init__(self):
        super().__init__()
        self.conversation_history = []
        self.chat_worker = ChatWorker()
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()

        # 知识库选择区域
        kb_layout = QHBoxLayout()
        kb_label = QLabel("选择知识库:")
        kb_label.setFont(QFont("Arial", 14))
        kb_layout.addWidget(kb_label)
        self.kb_combo = QComboBox()
        self.kb_combo.setFont(QFont("Arial", 12))
        self.kb_combo.addItems(["股票知识", "投资策略", "风险管理", "市场分析", "技术指标"])
        kb_layout.addWidget(self.kb_combo)
        kb_layout.addStretch()
        layout.addLayout(kb_layout)

        # 对话显示区域
        chat_label = QLabel("对话记录:")
        chat_label.setFont(QFont("Arial", 14))
        layout.addWidget(chat_label)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Arial", 13))
        self.chat_display.setStyleSheet("""
            background-color: #f8f9fa; 
            border: 1px solid #dee2e6;
            padding: 10px;
        """)
        layout.addWidget(self.chat_display)

        # 用户输入区域
        input_layout = QHBoxLayout()
        self.user_input = QLineEdit()
        self.user_input.setFont(QFont("Arial", 14))
        self.user_input.setPlaceholderText("请输入您的问题...")
        self.user_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.user_input)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFont(QFont("Arial", 14))
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)

        self.clear_btn = QPushButton("清空对话")
        self.clear_btn.setFont(QFont("Arial", 14))
        self.clear_btn.clicked.connect(self.clear_conversation)
        input_layout.addWidget(self.clear_btn)

        layout.addLayout(input_layout)

        # 状态标签
        self.status_label = QLabel("准备就绪")
        self.status_label.setFont(QFont("Arial", 14))
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # 设置窗口大小
        self.resize(800, 600)

        # 添加欢迎消息
        self.add_system_message("欢迎使用知识库对话系统！请选择知识库并开始提问。")

    def markdown_to_html(self, text):
        """将Markdown文本转换为HTML格式"""
        # 处理标题
        text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        
        # 处理粗体
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
        
        # 处理斜体
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
        
        # 处理代码块
        text = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
        
        # 处理列表
        text = re.sub(r'^\* (.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        text = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', text, flags=re.DOTALL)
        
        # 处理换行
        text = text.replace('\n', '<br>')
        
        # 处理链接
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
        
        return text

    def send_message(self):
        """发送用户消息"""
        user_text = self.user_input.text().strip()
        if not user_text:
            return

        # 添加用户消息到对话记录
        self.add_user_message(user_text)
        self.user_input.clear()

        # 更新状态
        self.status_label.setText("正在生成回复...")
        self.send_btn.setEnabled(False)

        # 启动后台线程处理AI回复
        selected_kb = self.kb_combo.currentText()
        self.chat_thread = ChatWorkerThread(self.chat_worker, user_text, selected_kb, self.conversation_history)
        self.chat_thread.response_received.connect(self.handle_ai_response)
        self.chat_thread.start()

    def handle_ai_response(self, response):
        """处理AI回复"""
        self.add_assistant_message(response)
        self.status_label.setText("回复已生成")
        self.send_btn.setEnabled(True)

    def add_user_message(self, message):
        """添加用户消息到对话记录"""
        formatted_message = f"<div style='margin: 10px; padding: 15px; background-color: #e3f2fd; border-radius: 10px; font-size: 14px;'>" \
                          f"<b style='font-size: 16px;'>您:</b><br>{message}</div>"
        self.chat_display.append(formatted_message)
        self.conversation_history.append({"role": "user", "content": message})
        self.scroll_to_bottom()

    def add_assistant_message(self, message):
        """添加助手消息到对话记录（支持Markdown）"""
        # 转换Markdown为HTML
        html_content = self.markdown_to_html(message)
        formatted_message = f"<div style='margin: 10px; padding: 15px; background-color: #f3e5f5; border-radius: 10px; font-size: 14px;'>" \
                          f"<b style='font-size: 16px;'>助手:</b><br>{html_content}</div>"
        self.chat_display.append(formatted_message)
        self.conversation_history.append({"role": "assistant", "content": message})
        self.scroll_to_bottom()

    def add_system_message(self, message):
        """添加系统消息到对话记录"""
        formatted_message = f"<div style='margin: 10px; padding: 15px; background-color: #e8f5e8; border-radius: 10px; text-align: center; font-size: 14px;'>" \
                          f"<b style='font-size: 16px;'>系统:</b><br>{message}</div>"
        self.chat_display.append(formatted_message)
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        """滚动到对话底部"""
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_conversation(self):
        """清空对话记录"""
        self.chat_display.clear()
        self.conversation_history.clear()
        self.add_system_message("对话记录已清空")


class KnowledgeManagementUI(QWidget):
    """知识管理界面类"""
    
    def __init__(self, knowledge_base_path="/Users/younger/Desktop/yw/myKB"):
        super().__init__()
        self.knowledge_base_path = knowledge_base_path
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 移除所有边距
        layout.setSpacing(0)  # 移除所有间距
        
        # 目录选择区域 - 从媒体文件管理界面添加
        dir_layout = QHBoxLayout()
        dir_layout.setContentsMargins(0, 0, 0, 0)
        dir_layout.setSpacing(5)
        
        self.dir_label = QLabel(f"当前目录: {self.knowledge_base_path}")
        self.dir_label.setFont(QFont("Arial", 10))
        dir_layout.addWidget(self.dir_label)
        
        self.select_dir_btn = QPushButton("选择目录")
        self.select_dir_btn.setFont(QFont("Arial", 10))
        self.select_dir_btn.setFixedHeight(25)
        self.select_dir_btn.clicked.connect(self.select_directory)
        dir_layout.addWidget(self.select_dir_btn)
        
        dir_layout.addStretch()
        layout.addLayout(dir_layout)
        
        # 操作按钮区域 - 最小化布局
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)  # 移除所有边距
        button_layout.setSpacing(5)  # 最小间距
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFont(QFont("Arial", 10))
        self.refresh_btn.setFixedHeight(25)  # 固定按钮高度
        self.refresh_btn.clicked.connect(self.refresh_file_list)
        button_layout.addWidget(self.refresh_btn)

        self.open_btn = QPushButton("打开文件")
        self.open_btn.setFont(QFont("Arial", 10))
        self.open_btn.setFixedHeight(25)
        self.open_btn.clicked.connect(self.open_file)
        button_layout.addWidget(self.open_btn)

        self.delete_btn = QPushButton("删除文件")
        self.delete_btn.setFont(QFont("Arial", 10))
        self.delete_btn.setFixedHeight(25)
        self.delete_btn.clicked.connect(self.delete_file)
        button_layout.addWidget(self.delete_btn)

        self.new_file_btn = QPushButton("新建文件")
        self.new_file_btn.setFont(QFont("Arial", 10))
        self.new_file_btn.setFixedHeight(25)
        self.new_file_btn.clicked.connect(self.new_file)
        button_layout.addWidget(self.new_file_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 文件列表区域 - 占据主要空间
        file_list_label = QLabel("知识文件列表:")
        file_list_label.setFont(QFont("Arial", 11))
        layout.addWidget(file_list_label)
        
        self.file_list = QListWidget()
        self.file_list.setFont(QFont("Arial", 13))
        self.file_list.itemClicked.connect(self.on_file_selected)
        self.file_list.itemDoubleClicked.connect(self.open_file)
        layout.addWidget(self.file_list)
        
        self.setLayout(layout)
        
        # 设置窗口大小
        self.resize(1200, 800)
        
        # 初始加载文件列表
        self.refresh_file_list()

    def refresh_file_list(self):
        """刷新文件列表 - 显示层级目录结构"""
        self.file_list.clear()
        
        if not os.path.exists(self.knowledge_base_path):
            QMessageBox.warning(self, "警告", f"知识库路径不存在: {self.knowledge_base_path}")
            return
        
        try:
            # 获取目录下所有文件（包括子目录）
            files = []
            for root, dirs, filenames in os.walk(self.knowledge_base_path):
                # 计算缩进级别
                level = root.replace(self.knowledge_base_path, '').count(os.sep)
                indent = "    " * level
                
                # 添加目录项（如果当前目录不是根目录）
                if level > 0:
                    dir_name = os.path.basename(root)
                    dir_item = QListWidgetItem(f"{indent}📁 {dir_name}/")
                    dir_item.setData(Qt.UserRole, os.path.relpath(root, self.knowledge_base_path))
                    dir_item.setFlags(dir_item.flags() & ~Qt.ItemIsSelectable)  # 目录不可选择
                    dir_item.setForeground(QColor("#1a73e8"))
                    dir_item.setFont(QFont("Arial", 13, QFont.Bold))
                    self.file_list.addItem(dir_item)
                
                # 添加文件项
                for filename in filenames:
                    file_item = QListWidgetItem(f"{indent}    📄 {filename}")
                    rel_path = os.path.relpath(os.path.join(root, filename), self.knowledge_base_path)
                    file_item.setData(Qt.UserRole, rel_path)
                    file_item.setFont(QFont("Arial", 13))
                    self.file_list.addItem(file_item)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取文件列表失败: {str(e)}")

    def on_file_selected(self, item):
        """文件被选中时的处理"""
        # 检查是否为目录项（不可选择）
        if not (item.flags() & Qt.ItemIsSelectable):
            return
            
        # 获取存储在UserRole中的实际文件路径
        file_path = item.data(Qt.UserRole)
        if file_path:
            self.current_selected_file = file_path

    def open_file(self):
        """打开选中的文件"""
        if not hasattr(self, 'current_selected_file'):
            QMessageBox.information(self, "提示", "请先选择一个文件")
            return
        
        file_path = os.path.join(self.knowledge_base_path, self.current_selected_file)
        
        try:
            # 在系统默认应用中打开文件
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open '{file_path}'")
            else:  # linux
                os.system(f"xdg-open '{file_path}'")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件失败: {str(e)}")

    def delete_file(self):
        """删除选中的文件"""
        if not hasattr(self, 'current_selected_file'):
            QMessageBox.information(self, "提示", "请先选择一个文件")
            return
        
        file_path = os.path.join(self.knowledge_base_path, self.current_selected_file)
        
        reply = QMessageBox.question(self, "确认删除", 
                                    f"确定要删除文件 '{self.current_selected_file}' 吗？",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(file_path)
                QMessageBox.information(self, "成功", "文件删除成功")
                self.refresh_file_list()
                self.content_display.clear()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除文件失败: {str(e)}")

    def new_file(self):
        """创建新文件"""
        file_name, ok = QInputDialog.getText(self, "新建文件", "请输入文件名（可包含子目录路径）:")
        
        if ok and file_name:
            # 确保文件名有扩展名
            if '.' not in os.path.basename(file_name):
                file_name += ".txt"
            
            file_path = os.path.join(self.knowledge_base_path, file_name)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if os.path.exists(file_path):
                QMessageBox.warning(self, "警告", "文件已存在")
                return
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("# 新文件\n\n请在此处输入内容...")
                
                QMessageBox.information(self, "成功", "文件创建成功")
                self.refresh_file_list()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建文件失败: {str(e)}")

    def select_directory(self):
        """选择目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择知识库目录", self.knowledge_base_path)
        if directory:
            self.knowledge_base_path = directory
            self.dir_label.setText(f"当前目录: {self.knowledge_base_path}")
            self.refresh_file_list()