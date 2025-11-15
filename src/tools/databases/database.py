
import json
import os
from typing import Optional


class DatabaseTool:
    """数据库工具类"""

    def __init__(self, cache_file_path: str = "database_cache.json") -> None:
        """
        初始化数据库工具

        Args:
            cache_file_path: 缓存JSON文件路径
        """
        self.cache_file_path = cache_file_path
        self.cache_data = {}

        # 如果缓存文件存在，则读取数据
        if os.path.exists(self.cache_file_path):
            try:
                with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                    self.cache_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load cache file {self.cache_file_path}: {e}")
                self.cache_data = {}

    def save(self, key: str, value: str) -> bool:
        """
        存储key-value对到JSON文件

        Args:
            key: 文件名或ID
            value: 字符串内容

        Returns:
            bool: 是否保存成功
        """
        try:
            # 先读取现有数据，避免覆盖
            existing_data = {}
            if os.path.exists(self.cache_file_path):
                with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

            # 更新或添加新的key-value
            existing_data[key] = value

            # 确保目录存在
            dir_path = os.path.dirname(self.cache_file_path)
            if dir_path:  # 只有在有目录路径时才创建
                os.makedirs(dir_path, exist_ok=True)

            # 写入更新后的数据
            with open(self.cache_file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

            # 同时更新内存中的数据
            self.cache_data[key] = value
            return True
        except (IOError, TypeError, json.JSONDecodeError) as e:
            print(f"Error: Failed to save data to {self.cache_file_path}: {e}")
            return False

    def get(self, key: str) -> Optional[str]:
        """
        从JSON文件中取出对应的字符串内容

        Args:
            key: 文件名或ID

        Returns:
            Optional[str]: 对应的字符串内容，如果key不存在则返回None
        """
        return self.cache_data.get(key)
    