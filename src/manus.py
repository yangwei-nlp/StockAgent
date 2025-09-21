"""
视频处理Agent - 基于my_workflow的工具创建交互式Agent，使用真实LLM调用
"""

import os
import subprocess
import json
import asyncio
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from openai import OpenAI

BASE_DIR = "/Users/younger/Movies/抖音/"


def merge_video_with_ffmpeg(arguments):
    """
    使用FFmpeg合并FLV视频文件

    参数:
        arguments: 包含input_files和output_file的字典
    """
    input_files = arguments["input_files"]
    output_file = arguments["output_file"]
    
    # 检查文件是否存在
    for file_path in input_files:
        if not os.path.exists(BASE_DIR + file_path):
            print(f"文件不存在: {file_path}")
            return "文件不存在"

    # 创建文件列表
    filelist_path = "temp_filelist.txt"
    try:
        with open(filelist_path, 'w', encoding='utf-8') as f:
            for file_path in input_files:
                abs_path = BASE_DIR + file_path
                f.write(f"file '{abs_path}'\n")

        # 执行FFmpeg命令
        cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', filelist_path, '-c', 'copy', output_file]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"合并成功: {output_file}")
            return "合并成功"
        else:
            print(f"合并失败: {result.stderr}")
            return "合并失败"

    finally:
        if os.path.exists(filelist_path):
            os.remove(filelist_path)


def search_flv_files(arguments):
    """
    在BASE_DIR目录下搜索指定目录名和关键字的FLV文件，返回相对路径

    参数:
        arguments: 包含directory_name和keyword的字典

    返回:
        匹配文件的相对路径列表
    """
    import glob
    
    directory_name = arguments["directory_name"]
    keyword = arguments["keyword"]

    # 构建搜索路径
    search_pattern = os.path.join(BASE_DIR, directory_name, f"*{keyword}*.flv")

    # 搜索匹配的文件
    matched_files = glob.glob(search_pattern)

    # 转换为相对路径（相对于BASE_DIR）
    relative_paths = [os.path.relpath(file, BASE_DIR) for file in matched_files]

    # 按文件名排序
    relative_paths.sort()

    return json.dumps(relative_paths, ensure_ascii=False)


# ==================== Agent 相关类 ====================

class BaseTool(ABC, BaseModel):
    """基础工具类"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    parameters: Optional[dict] = Field(default=None, description="工具参数定义")

    class Config:
        arbitrary_types_allowed = True

    async def execute(self, **kwargs) -> str:
        """执行工具"""
        raise NotImplementedError("子类必须实现execute方法")

    def to_param(self) -> Dict:
        """转换为函数调用格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class MergeVideoTool(BaseTool):
    """视频合并工具"""
    
    def __init__(self):
        super().__init__(
            name="merge_video_with_ffmpeg",
            description="使用FFmpeg合并FLV视频文件",
            parameters={
                "type": "object",
                "properties": {
                    "input_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "输入文件列表，如['video1.flv', 'video2.flv']"
                    },
                    "output_file": {
                        "type": "string",
                        "description": "输出文件名，如'merged.flv'"
                    }
                },
                "required": ["input_files", "output_file"]
            }
        )

    async def execute(self, **kwargs) -> str:
        return merge_video_with_ffmpeg(kwargs)


class SearchFLVTool(BaseTool):
    """FLV文件搜索工具"""
    
    def __init__(self):
        super().__init__(
            name="search_flv_files",
            description="搜索指定目录和关键字的FLV文件",
            parameters={
                "type": "object",
                "properties": {
                    "directory_name": {
                        "type": "string",
                        "description": "子目录名称，如'焦刚来了'"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "文件名中包含的关键字，如'2025-09-18'"
                    }
                },
                "required": ["directory_name", "keyword"]
            }
        )

    async def execute(self, **kwargs) -> str:
        return search_flv_files(kwargs)


class ToolCollection:
    """工具集合"""
    
    def __init__(self):
        self.tools = [MergeVideoTool(), SearchFLVTool()]
        self.tool_map = {tool.name: tool for tool in self.tools}

    def to_params(self) -> List[Dict]:
        """转换为工具参数列表"""
        return [tool.to_param() for tool in self.tools]

    async def execute(self, name: str, tool_input: Dict) -> str:
        """执行指定工具"""
        if name not in self.tool_map:
            return f"Error: Unknown tool '{name}'"
        return await self.tool_map[name].execute(**tool_input)


# 初始化OpenAI客户端
client = OpenAI(
    api_key="sk-6915bffb5c834e4d9525fb3d67858f36",
    base_url="https://api.deepseek.com/v1",
)


def get_llm_response(messages, tools):
    """获取LLM响应"""
    completion = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools,
    )
    return completion


class StockManus:
    """股市Agent - 使用真实LLM调用"""
    
    def __init__(self):
        self.available_tools = ToolCollection()
        self.messages = []
        
    def add_message(self, role: str, content: str, tool_call_id: str = None, name: str = None):
        """添加消息到对话历史"""
        if tool_call_id:
            self.messages.append({
                "role": role,
                "content": content,
                "tool_call_id": tool_call_id,
                "name": name
            })
        else:
            self.messages.append({"role": role, "content": content})
    
    async def process_message(self, user_message: str) -> str:
        """处理用户消息并返回响应 - 使用真实LLM调用"""
        self.add_message("user", user_message)
        
        # 获取LLM响应
        response = get_llm_response(self.messages, self.available_tools.to_params())
        assistant_output = response.choices[0].message
        
        if assistant_output.content is None:
            assistant_output.content = ""
        
        # 添加助手消息到历史
        self.messages.append({
            "role": "assistant",
            "content": assistant_output.content,
            "tool_calls": assistant_output.tool_calls
        })
        
        # 如果不需要调用工具，直接返回内容
        if assistant_output.tool_calls is None:
            return assistant_output.content
        
        # 进入工具调用循环
        while assistant_output.tool_calls is not None:
            tool_call = assistant_output.tool_calls[0]
            tool_call_id = tool_call.id
            func_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            print(f"正在调用工具 [{func_name}]，参数：{arguments}")
            
            # 执行工具
            tool_result = await self.available_tools.execute(func_name, arguments)
            
            # 构造工具返回信息
            self.add_message("tool", tool_result, tool_call_id, func_name)
            
            print(f"工具返回：{tool_result}")
            
            # 再次调用模型，获取总结后的自然语言回复
            response = get_llm_response(self.messages, self.available_tools.to_params())
            assistant_output = response.choices[0].message
            
            if assistant_output.content is None:
                assistant_output.content = ""
            
            # 添加助手消息到历史
            self.messages.append({
                "role": "assistant",
                "content": assistant_output.content,
                "tool_calls": assistant_output.tool_calls
            })
        
        return assistant_output.content
    
    async def run_interactive(self):
        """运行交互式对话循环"""
        print("视频处理Agent已启动！输入'退出'或'quit'结束对话。")
        print("我可以帮您搜索和合并FLV视频文件。")
        
        while True:
            try:
                user_input = input("\n您: ").strip()
                if user_input.lower() in ['退出', 'quit', 'exit']:
                    print("对话结束，再见！")
                    break
                
                if user_input:
                    response = await self.process_message(user_input)
                    print(f"\nAgent: {response}")
                    
            except KeyboardInterrupt:
                print("\n对话被用户中断")
                break
            except Exception as e:
                print(f"处理消息时出错: {e}")
                # 添加错误信息到消息历史
                self.add_message("system", f"系统错误: {str(e)}")


if __name__ == '__main__':
    # 启动Agent交互模式
    print("="*50)
    print("启动视频处理Agent交互模式...")
    agent = StockManus()
    asyncio.run(agent.run_interactive())