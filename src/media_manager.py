import os
from typing import List, Dict
import subprocess


class MediaManager:
    """媒体文件管理器 - 处理视频文件的业务逻辑"""
    
    def __init__(self, base_dir: str = "/Users/younger/Movies/抖音/"):
        self.base_dir = base_dir

    def set_base_dir(self, base_dir: str):
        """设置基础目录"""
        self.base_dir = base_dir

    def get_file_info(self) -> List[Dict]:
        """获取目录下所有FLV文件的信息"""
        file_info_list = []
        try:
            for root, dirs, files in os.walk(self.base_dir):
                for file in files:
                    if file.lower().endswith('.flv'):
                        relative_path = os.path.relpath(os.path.join(root, file), self.base_dir)
                        abs_path = os.path.join(self.base_dir, relative_path)
                        file_size = os.path.getsize(abs_path) if os.path.exists(abs_path) else 0
                        file_size_mb = round(file_size / (1024 * 1024), 2)
                        file_info_list.append({
                            'path': relative_path,
                            'size': file_size_mb,
                            'name': file,
                            'full_path': abs_path
                        })
            
            # 按文件名排序
            file_info_list.sort(key=lambda x: x['name'])
            return file_info_list
            
        except Exception as e:
            raise Exception(f"无法读取目录: {str(e)}")

    def merge_videos(self, input_files: List[str]) -> Dict:
        """合并视频文件
        
        参数:
            input_files: 输入文件相对路径列表
            
        返回:
            包含状态和消息的字典
        """
        try:
            # 检查文件是否存在
            for file_path in input_files:
                abs_path = os.path.join(self.base_dir, file_path)
                if not os.path.exists(abs_path):
                    return {
                        'success': False,
                        'message': f"文件不存在: {file_path}"
                    }

            # 创建文件列表
            filelist_path = "temp_filelist.txt"
            try:
                with open(filelist_path, 'w', encoding='utf-8') as f:
                    for file_path in input_files:
                        abs_path = os.path.join(self.base_dir, file_path)
                        f.write(f"file '{abs_path}'\n")

                # 生成输出文件名
                filename = os.path.splitext(input_files[0])[0]
                output_file = os.path.join(self.base_dir, filename + "_merged.flv")

                # 执行FFmpeg命令
                cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', filelist_path, '-c', 'copy', output_file]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    # 检查文件大小是否超过50MB
                    file_size = os.path.getsize(output_file)
                    if file_size > 50 * 1024 * 1024:  # 50MB in bytes
                        # 合并成功，删除输入文件
                        for file_path in input_files:
                            abs_path = os.path.join(self.base_dir, file_path)
                            if os.path.exists(abs_path):
                                os.remove(abs_path)
                        
                        return {
                            'success': True,
                            'message': f"合并成功: {os.path.basename(output_file)}",
                            'output_file': output_file
                        }
                    else:
                        # 删除不满足条件的输出文件
                        if os.path.exists(output_file):
                            os.remove(output_file)
                        return {
                            'success': False,
                            'message': "合并失败: 输出文件大小不足50MB"
                        }
                else:
                    return {
                        'success': False,
                        'message': f"合并失败: {result.stderr}"
                    }

            finally:
                if os.path.exists(filelist_path):
                    os.remove(filelist_path)

        except Exception as e:
            return {
                'success': False,
                'message': f"合并过程中发生错误: {str(e)}"
            }

    def delete_files(self, file_paths: List[str]) -> Dict:
        """删除文件
        
        参数:
            file_paths: 要删除的文件路径列表
            
        返回:
            包含删除结果和消息的字典
        """
        deleted_count = 0
        failed_files = []
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                else:
                    failed_files.append(f"文件不存在: {file_path}")
            except Exception as e:
                failed_files.append(f"删除失败 {file_path}: {str(e)}")
        
        return {
            'deleted_count': deleted_count,
            'failed_files': failed_files,
            'success': len(failed_files) == 0
        }