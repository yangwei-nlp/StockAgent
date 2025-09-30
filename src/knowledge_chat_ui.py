import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTextEdit, QLineEdit, QLabel, QComboBox, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
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