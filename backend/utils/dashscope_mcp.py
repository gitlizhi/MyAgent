# -*- coding: utf-8 -*-
import os
from qwen_agent.agents import Assistant
from langchain_core.tools import tool
from dotenv import load_dotenv
load_dotenv()


@tool(description="web搜索互联网信息查询, 搜索资料")
def webSearch(query):
    """互联网信息搜索"""
    # 检查环境变量
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        print("错误：请设置环境变量 DASHSCOPE_API_KEY")
        print("例如：export DASHSCOPE_API_KEY=your_api_key")
        return

    llm_cfg = {'model': 'qwen-max', 'timeout': 60, 'retry_count': 2}
    system = (
        '你是一个web搜索智能体。你将调用名为 WebSearch 的 MCP 服务来查询互联网信息。'
    )

    # 配置MCP工具
    tools = [{
        "mcpServers": {
            "WebSearch": {
                "url": "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
                "headers": {
                    "Authorization": f"Bearer {api_key}"
                }
            }
        }
    }]

    # 创建智能体
    bot = Assistant(
        llm=llm_cfg,
        name='web搜索智能体',
        description='web搜索互联网信息查询',
        system_message=system,
        function_list=tools,
    )

    messages = []
    messages.append({'role': 'user', 'content': query})

    # 执行查询并收集所有响应
    all_responses = []
    for response in bot.run(messages):
        all_responses.append(response)

    # 提取最终的assistant回复内容
    final_content = ""
    if all_responses:
        last_response = all_responses[-1]
        if isinstance(last_response, list):
            for item in last_response:
                if isinstance(item, dict) and item.get('role') == 'assistant' and 'content' in item:
                    final_content = item['content']
        elif isinstance(last_response, dict) and 'content' in last_response:
            final_content = last_response['content']
    # print(final_content)
    # 输出最终结果
    return final_content


@tool(description="该工具提供全场景覆盖的地理信息服务，包括地理编码、逆地理编码、IP定位、实时天气查询、骑行路径规划、步行路径规划、驾车路径规划、公交路径规划、距离测量、关键词搜索、周边搜索、详情搜索等。")
def amap_maps(query):
    """高德地图mcp"""
    # 检查环境变量
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        print("错误：请设置环境变量 DASHSCOPE_API_KEY")
        print("例如：export DASHSCOPE_API_KEY=your_api_key")
        return

    llm_cfg = {'model': 'qwen-max', 'timeout': 60, 'retry_count': 2}
    system = (
        '你是一个智能体。你将调用名为 amap-maps 的 MCP 服务来获取信息。'
        '该服务提供全场景覆盖的地理信息服务，包括地理编码、逆地理编码、IP定位、天气查询、骑行路径规划、步行路径规划、驾车路径规划、公交路径规划、距离测量、关键词搜索、周边搜索、详情搜索等。'
    )

    # 配置MCP工具
    tools = [{
        "mcpServers": {
            "amap-maps": {
                "url": "https://dashscope.aliyuncs.com/api/v1/mcps/amap-maps/sse",
                "headers": {
                    "Authorization": f"Bearer {api_key}"
                }
            }
        }
    }]

    # 创建智能体
    bot = Assistant(
        llm=llm_cfg,
        name='高德地图mcp智能体',
        description='高德地图mcp智能体',
        system_message=system,
        function_list=tools,

    )

    messages = []
    messages.append({'role': 'user', 'content': query})

    # 执行查询并收集所有响应
    all_responses = []
    for response in bot.run(messages):
        all_responses.append(response)

    # 提取最终的assistant回复内容
    final_content = ""
    if all_responses:
        last_response = all_responses[-1]
        if isinstance(last_response, list):
            for item in last_response:
                if isinstance(item, dict) and item.get('role') == 'assistant' and 'content' in item:
                    final_content = item['content']
        elif isinstance(last_response, dict) and 'content' in last_response:
            final_content = last_response['content']
    # print(final_content)
    # 输出最终结果
    return final_content


if __name__ == '__main__':
    query = "帮我规划一下从北京西站到天安门广场的驾车路线"
    amap_maps(query)