import os

class ReaderTool:
    """文档读取工具类"""

    def __init__(self) -> None:
        pass

    def read_txt(
        self,
        path: str,
        prefix,
    ) -> list[str]:
        """
        读取txt文件，返回文本内容
        
        Args:
            path: 文件路径
            prefix: 单个前缀字符串
        Returns:
            过滤后的行列表
        """
        if not path:
            raise ValueError("文件路径不能为空")
        if not os.path.isfile(path):
            raise FileNotFoundError(f"文件不存在: {path}")

        lines: list[str] = []

        def process_line(raw: str) -> None:
            line = raw.strip()
            if not line or prefix in line:
                return
            lines.append(line)

        # 优先尝试utf-8，其次gbk，最后在utf-8忽略错误
        try:
            with open(path, "r", encoding="utf-8") as f:
                for raw in f:
                    process_line(raw)
            return "\n".join(lines)
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="gbk") as f:
                    for raw in f:
                        process_line(raw)
                return "\n".join(lines)
            except UnicodeDecodeError:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for raw in f:
                        process_line(raw)
                return "\n".join(lines)


if __name__ == "__main__":
    reader = ReaderTool()
    text = reader.read_txt(
        "/Users/yangwei/Desktop/code/StockAgent/src_refactor/tools/test.txt",
        prefix="发言人",
    )
    print(text)
