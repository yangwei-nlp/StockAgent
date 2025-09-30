#!/usr/bin/env python3
"""
知识库管理系统主启动文件

这是一个集成了媒体文件管理和AI对话功能的知识库软件。
主要功能包括：
- 媒体文件管理（视频合并、删除等）
- 知识库对话系统
- 多模态知识库支持
"""

import sys
from src.knowledge_base_main import KnowledgeBaseMain


def main():
    """主启动函数"""
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        
        # 设置应用程序信息
        app.setApplicationName("知识库管理系统")
        app.setApplicationVersion("1.0.0")
        
        # 创建并显示主窗口
        window = KnowledgeBaseMain()
        window.show()
        
        print("知识库管理系统已启动")
        print("功能说明:")
        print("- 媒体文件管理: 管理视频文件，支持合并和删除操作")
        print("- 知识库对话: 与AI助手进行对话，获取投资相关知识")
        
        # 运行应用程序
        return app.exec_()
        
    except ImportError as e:
        print(f"错误: 缺少必要的依赖包 - {e}")
        print("请安装PyQt5: pip install PyQt5")
        return 1
    except Exception as e:
        print(f"启动错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())