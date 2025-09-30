import os
import json
import glob
import subprocess

from fastmcp import FastMCP
from typing import List, Dict

BASE_DIR = "/Users/younger/Movies/抖音/"

# 创建FastMCP实例
mcp = FastMCP(name="VideoProcessingServer")

@mcp.tool()
def merge_video_with_ffmpeg(input_files: List[str]) -> str:
    """使用FFmpeg合并FLV视频文件

    参数:
        input_files: 输入文件列表，如['video1.flv', 'video2.flv']

    返回:
        合并结果信息
    """
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

        filename = input_files[0][0:-4]
        output_file = BASE_DIR + filename + "_merged.flv"
        # 执行FFmpeg命令
        cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', filelist_path, '-c', 'copy', output_file]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            # 检查文件大小是否超过50MB
            file_size = os.path.getsize(output_file)
            if file_size > 50 * 1024 * 1024:  # 50MB in bytes
                # 合并成功，删除输入文件
                for file_path in input_files:
                    abs_path = BASE_DIR + file_path
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                print(f"合并成功: {output_file}")
                return "合并成功"
            else:
                print(f"合并失败: 输出文件大小不足50MB")
                return "合并失败"
        else:
            print(f"合并失败: {result.stderr}")
            return "合并失败"

    finally:
        if os.path.exists(filelist_path):
            os.remove(filelist_path)


@mcp.tool()
def search_flv_files(directory_name: str, keyword: str) -> str:
    """搜索指定目录和关键字的FLV文件

    参数:
        directory_name: 子目录名称，如'焦刚来了'
        keyword: 文件名中包含的关键字，如'2025-09-18'

    返回:
        匹配文件的相对路径列表（JSON格式）
    """
    # 构建搜索路径
    search_pattern = os.path.join(BASE_DIR, directory_name, f"*{keyword}*.flv")

    # 搜索匹配的文件
    matched_files = glob.glob(search_pattern)

    # 转换为相对路径（相对于BASE_DIR）
    relative_paths = [os.path.relpath(file, BASE_DIR) for file in matched_files]

    # 按文件名排序
    relative_paths.sort()

    return json.dumps(relative_paths, ensure_ascii=False)



if __name__ == "__main__":
    # 启动FastMCP服务器
    mcp.run(transport="sse")
