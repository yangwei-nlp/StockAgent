import os, sys
import operator
from typing import TypedDict, Annotated, List
from langchain_deepseek import ChatDeepSeek
from langchain.tools import tool
from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

sys.path.append(os.getcwd())

from src.tools.databases.database import DatabaseTool
from src.tools.reader.reader import ReaderTool
from src.tools.summary.summary import SummaryTool

class State(TypedDict):
    query: str
    context: str
    messages: List

class MainWorkflow:

    def __init__(self) -> None:
        self.graph = StateGraph[State, None, State, State](state_schema=State)
        self.graph = self.build_graph()

        self.db_tool = DatabaseTool("src_refactor/caches/database_cache.json")
        self.reader_tool = ReaderTool()
        self.summary_tool = SummaryTool(window_size=1000, overlap=100)
        self.my_db = DatabaseTool("src_refactor/caches/my_study_cache.json")

        os.environ["DEEPSEEK_API_KEY"] = "sk-a7ae2e3f427d4dc5a57e0bab79c162d2"
        self.model = ChatDeepSeek(model="deepseek-chat")
        self.save_kb = self._create_save_kb_tool()
        self.model = self.model.bind_tools(tools=[self.save_kb])
    
    def execute(self,):
        inp = {"query": "/Users/yangwei/Desktop/code/StockAgent/src_refactor/tools/test.txt"}
        self.graph.invoke(inp)

    def build_graph(self):
        """构建工作流图"""
        # 添加节点
        self.graph.add_node("recall", self._recall_doc_node)
        self.graph.add_node("chat", self._chat_node)

        # 添加边
        self.graph.add_edge(START, "recall")
        self.graph.add_conditional_edges("recall", self._check_summary, {"SUCCESS": "chat", "FAIL": END})
        self.graph.add_edge("chat", "chat")

        chain = self.graph.compile()

        return chain
    
    def _set_message(self, state: State) -> State:
        if state.get("messages") is None:
            system_msg = SystemMessage(f"你需要依据如下信息和用户进行讨论: {state['context']}\n\n")
            messages = [system_msg]
            return {"messages": messages}
        else:
            return state

    def _recall_doc_node(self, state: State) -> State:
        key = state["query"]
        
        try:
            # 判断数据库是否存在该内容
            if self.db_tool.get(key):
                summary = self.db_tool.get(key)
            else:
                doc = self.reader_tool.read_txt(path=key, prefix="发言人")
                summary = self.summary_tool.summarize(doc)
                self.db_tool.save(key, summary)
            
            print(f"总结：\n{summary}")
            return {"context": summary}

        except Exception as e:
            print(f"error: {e}")
    
    def _check_summary(self, state: State) -> str:
        if state.get("context") is None:
            return "FAIL"
        else:
            return "SUCCESS"

    def _chat_node(self, state: State) -> State:
        if state.get("messages") is None or len(state.get("messages")) == 0:
            system_msg = SystemMessage(f"你需要依据如下信息和用户进行讨论: {state['context']}\n\n")
            messages = [system_msg]
        else:
            messages = state["messages"]
        
        user_input = input("请输入你的问题：")
        messages.append(HumanMessage(user_input))

        response = self.model.invoke(messages)
        print(response.content, response.tool_calls)
        messages.append(AIMessage(content=response.content, tool_calls=response.tool_calls))

        used_tool = False
        for tool_call in response.tool_calls:
            used_tool = True
            if tool_call['name'] == "save_kb":
                result = self.save_kb.invoke(tool_call['args'])
                tool_message = ToolMessage(
                    content=result,
                    tool_call_id=tool_call['id']
                )
                messages.append(tool_message)

        if used_tool:
            response = self.model.invoke(messages)
            print(response.content, response.tool_calls)
            messages.append(AIMessage(response.content))

        return {"messages": messages}

    def _create_save_kb_tool(self,):
        my_db = self.my_db

        @tool
        def save_kb(knowledge_point: str, knowledge_detail: str) -> State:
            """将内容存入知识库"""
            try:
                my_db.save(knowledge_point, knowledge_detail)
                return "存储成功"
            except Exception as e:
                return "存储失败"
        
        return save_kb


if __name__ == "__main__":
    workflow = MainWorkflow()
    workflow.execute()
