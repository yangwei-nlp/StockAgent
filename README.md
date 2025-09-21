项目介绍：

股市Agent，涵盖知识库（主播分析、历史行情）、RAG、MCP（如数据分析等）

功能：

- 自动录制视频
- 自动或手动分析视频，形成知识文档
- 聊天过程中知识入库
- 聊天过程中知识查询

Function Calling:


问题：

- 使用MCP还是Tool use？

- 设计agent还是工作流？

- agent如何确定step数？如何停止？

- LLM如何与Tool的输出进行交互？

[链接](https://help.aliyun.com/zh/model-studio/qwen-function-calling?spm=a2c4g.11186623.help-menu-2400256.d_0_7_1.636c5177KsgT8A&scm=20140722.H_2862208._.OR_help-T_cn~zh-V_1)
```text
[
  System Message -- 指引模型调用工具的策略
  User Message -- 用户的问题
  Assistant Message -- 模型返回的工具调用信息
  Tool Message -- 工具的输出信息
  Assistant Message -- 模型总结的工具调用信息
  User Message -- 用户第二轮的问题
]
```
