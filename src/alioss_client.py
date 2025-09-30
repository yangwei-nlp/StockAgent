import oss2
from typing import Optional
import os

from src.config import *

class AliyunOSSClient:
    """阿里云OSS操作工具类"""

    def __init__(self, access_key_id: str, access_key_secret: str,
                 endpoint: str, bucket_name: str):
        """
        初始化OSS客户端

        :param access_key_id: 阿里云AccessKey ID
        :param access_key_secret: 阿里云AccessKey Secret
        :param endpoint: OSS访问域名，如 'oss-cn-hangzhou.aliyuncs.com'
        :param bucket_name: 存储桶名称
        """
        self.auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)

    def upload_file(self, local_file_path: str, oss_file_path: str) -> bool:
        """
        上传文件到OSS

        :param local_file_path: 本地文件路径
        :param oss_file_path: OSS中的文件路径（对象键）
        :return: 上传成功返回True，失败返回False
        """
        try:
            # 检查本地文件是否存在
            if not os.path.exists(local_file_path):
                print(f"错误: 本地文件不存在 - {local_file_path}")
                return False

            # 上传文件
            result = self.bucket.put_object_from_file(oss_file_path, local_file_path)

            # 检查上传结果
            if result.status == 200:
                print(f"上传成功: {local_file_path} -> {oss_file_path}")
                return True
            else:
                print(f"上传失败，状态码: {result.status}")
                return False

        except Exception as e:
            print(f"上传异常: {str(e)}")
            return False

    def download_file(self, oss_file_path: str, local_file_path: str) -> bool:
        """
        从OSS下载文件

        :param oss_file_path: OSS中的文件路径（对象键）
        :param local_file_path: 本地保存路径
        :return: 下载成功返回True，失败返回False
        """
        try:
            # 确保本地目录存在
            local_dir = os.path.dirname(local_file_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)

            # 下载文件
            result = self.bucket.get_object_to_file(oss_file_path, local_file_path)

            if result.status == 200:
                print(f"下载成功: {oss_file_path} -> {local_file_path}")
                return True
            else:
                print(f"下载失败，状态码: {result.status}")
                return False

        except oss2.exceptions.NoSuchKey:
            print(f"错误: OSS中不存在该文件 - {oss_file_path}")
            return False
        except Exception as e:
            print(f"下载异常: {str(e)}")
            return False

    def get_url(self, oss_file_path: str, expires: int = 3600) -> Optional[str]:
        """
        获取文件的访问URL（签名URL）

        :param oss_file_path: OSS中的文件路径（对象键）
        :param expires: URL有效期（秒），默认3600秒（1小时）
        :return: 成功返回访问URL，失败返回None
        """
        try:
            # 生成签名URL
            url = self.bucket.sign_url('GET', oss_file_path, expires)
            print(f"获取URL成功: {oss_file_path}")
            print(f"URL有效期: {expires}秒")
            return url

        except Exception as e:
            print(f"获取URL异常: {str(e)}")
            return None

    def get_public_url(self, oss_file_path: str) -> str:
        """
        获取文件的公共访问URL（仅适用于公共读的Bucket）

        :param oss_file_path: OSS中的文件路径（对象键）
        :return: 公共访问URL
        """
        # 构建公共URL
        endpoint = self.bucket.endpoint.replace('http://', '').replace('https://', '')
        url = f"https://{self.bucket.bucket_name}.{endpoint}/{oss_file_path}"
        return url

    def file_exists(self, oss_file_path: str) -> bool:
        """
        检查文件是否存在

        :param oss_file_path: OSS中的文件路径（对象键）
        :return: 存在返回True，不存在返回False
        """
        try:
            self.bucket.get_object_meta(oss_file_path)
            return True
        except oss2.exceptions.NoSuchKey:
            return False
        except Exception as e:
            print(f"检查文件异常: {str(e)}")
            return False


# 使用示例
if __name__ == "__main__":
    # 创建OSS客户端
    oss_client = AliyunOSSClient(
        access_key_id=ACCESS_KEY_ID,
        access_key_secret=ACCESS_KEY_SECRET,
        endpoint=ENDPOINT,
        bucket_name=BUCKET_NAME
    )

    # 1. 上传文件
    print("\n=== 上传文件 ===")
    oss_client.upload_file("README.md", "folder/README.md")

    # 2. 下载文件
    print("\n=== 下载文件 ===")
    oss_client.download_file("folder/README.md", "README2.md")

    # 3. 获取URL
    print("\n=== 获取访问URL ===")
    url = oss_client.get_url("folder/README.md", expires=7200)
    if url:
        print(f"访问链接: {url}")

    # 额外功能：检查文件是否存在
    print("\n=== 检查文件 ===")
    exists = oss_client.file_exists("folder/README.md")
    print(f"文件是否存在: {exists}")