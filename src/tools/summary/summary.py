import os, sys
from langchain_core.tools import tool
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate

sys.path.append(os.getcwd())

from src.tools.reader.reader import ReaderTool
from src.core.prompts.summary import SummaryPrompts


class SummaryTool:
    """文本摘要工具类"""

    def __init__(self, api_key: str = "sk-a7ae2e3f427d4dc5a57e0bab79c162d2",
                 model_name: str = "deepseek-chat",
                 window_size: int = 50,
                 overlap: int = 5,
                 group_size: int = 3):
        """
        初始化摘要工具

        Args:
            api_key: DeepSeek API密钥
            model_name: 使用的模型名称
            window_size: 文本窗口大小
            overlap: 窗口重叠大小
            group_size: 每n个总结进行进一步总结
        """
        os.environ["DEEPSEEK_API_KEY"] = api_key

        self.window_size = window_size
        self.overlap = overlap
        self.group_size = group_size

        # 在原文上总结的提示词
        prompt1 = ChatPromptTemplate.from_messages([
            ("system", SummaryPrompts.get_prompt(1)),
            ("user", "{input}")
        ])

        # 对总结进行再总结的提示词
        prompt2 = ChatPromptTemplate.from_messages([
            ("system", SummaryPrompts.get_prompt(2)),
            ("user", "{input}")
        ])

        # 最后对所有总结进行总结的提示词
        prompt3 = ChatPromptTemplate.from_messages([
            ("system", SummaryPrompts.get_prompt(3)),
            ("user", "{input}")
        ])

        # 初始化模型
        model = ChatDeepSeek(model=model_name)

        # 创建处理链
        self.first_chain = prompt1 | model
        self.second_chain = prompt2 | model
        self.third_chain = prompt3 | model

    # @tool
    def summarize(self, doc: str) -> str:
        """
        将长文本进行多级总结和摘要

        Args:
            doc: 输入的长文本

        Returns:
            最终摘要结果
        """
        if not doc:
            return ""

        # 第一级总结：对原始文本分块进行总结
        first_level_summaries = self._first_level_summary(doc)

        print("=== 第一级总结结果 ===")
        for i, summary in enumerate(first_level_summaries, 1):
            print(f"------- 第{i}段 -------")
            print(summary)

        # 第二级总结：每group_size个第一级总结进行进一步总结
        second_level_summaries = self._second_level_summary(first_level_summaries)

        print("\n=== 第二级总结结果 ===")
        for i, summary in enumerate(second_level_summaries, 1):
            print(f"------- 第{i}段 -------")
            print(summary)

        # 第三级总结：对所有第二级总结进行最终总结
        final_summary = self._third_level_summary(second_level_summaries)

        print("\n=== 最终总结结果 ===")
        print(final_summary)

        return final_summary

    def _first_level_summary(self, doc: str) -> list:
        """
        第一级总结：将长文本分块并进行总结

        Args:
            doc: 输入的长文本

        Returns:
            第一级总结列表
        """
        # 每隔window_size个字符串得到一个子字符串
        substrings = []
        step = self.window_size - self.overlap

        for i in range(0, len(doc), step):
            substring = doc[i:i + self.window_size]
            if substring:
                substrings.append(substring)
            if i + self.window_size >= len(doc):
                break

        batch_inputs = [{"input": s} for s in substrings]
        response = self.first_chain.batch(batch_inputs)

        # 提取总结内容
        summaries = [r.content for r in response]
        return summaries

    def _second_level_summary(self, first_level_summaries: list) -> list:
        """
        第二级总结：每group_size个第一级总结进行进一步总结（并发执行）

        Args:
            first_level_summaries: 第一级总结列表

        Returns:
            第二级总结列表
        """
        if len(first_level_summaries) <= self.group_size:
            # 如果第一级总结数量小于等于group_size，直接进行最终总结
            return first_level_summaries

        # 将第一级总结分组
        groups = []
        for i in range(0, len(first_level_summaries), self.group_size):
            group = first_level_summaries[i:i + self.group_size]
            combined_text = "\n\n".join(group)
            groups.append(combined_text)

        # 并发批量执行第二级总结
        batch_inputs = [{"input": group_text} for group_text in groups]
        response = self.second_chain.batch(batch_inputs)

        # 提取总结内容
        second_level_summaries = [r.content for r in response]
        return second_level_summaries

    def _third_level_summary(self, second_level_summaries: list) -> str:
        """
        第三级总结：对所有第二级总结进行最终总结

        Args:
            second_level_summaries: 第二级总结列表

        Returns:
            最终总结结果
        """
        if len(second_level_summaries) == 1:
            # 如果只有一个第二级总结，直接返回
            return second_level_summaries[0]

        # 合并所有第二级总结
        combined_text = "\n\n".join(second_level_summaries)

        # 进行最终总结
        response = self.third_chain.invoke({"input": combined_text})

        return response.content



if __name__ == "__main__":
    # 读取文件
    reader = ReaderTool()
    text = reader.read_txt(
        "/Users/yangwei/Desktop/code/StockAgent/src_refactor/tools/test.txt",
        prefix="发言人",
    )

    # 使用类的示例
    summary_tool = SummaryTool(
        window_size=500,
        overlap=50
    )
    result = summary_tool.summarize(text)
    print(result)
