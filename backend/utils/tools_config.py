import os
from langchain_chroma import Chroma
from langchain.tools.retriever import create_retriever_tool
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
import re
import json
import requests
from langchain.tools import Tool
from .config import Config
from .dashscope_mcp import webSearch, amap_maps


class AMapTools:
    """高德地图工具类 - 增强参数解析版本"""

    def __init__(self):
        self.api_key = os.getenv("AMAP_API_KEY")
        self.base_url = "https://restapi.amap.com/v3"

    def geocode(self, address):
        """地理编码：将地址转换为坐标"""
        # 如果输入是字典，提取address字段
        if isinstance(address, dict):
            address = address.get('address', address.get('__arg1', ''))

        url = f"{self.base_url}/geocode/geo"
        params = {
            'key': self.api_key,
            'address': address,
            'output': 'json'
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if data['status'] == '1' and data['geocodes']:
                location = data['geocodes'][0]['location']  # 格式: "经度,纬度"
                return location
            else:
                return f"地理编码失败: {data.get('info', '未知错误')}"

        except Exception as e:
            return f"请求失败: {str(e)}"

    def driving_route(self, input_data):
        """驾车路径规划 - 增强参数解析"""
        origin, destination = self._parse_route_input(input_data)
        if not origin or not destination:
            return "错误：需要提供起点和终点，格式如：'从北京西站到天安门广场' 或 {'origin': '北京西站', 'destination': '天安门广场'}"

        # 地理编码
        origin_coords = self._ensure_coordinates(origin)
        destination_coords = self._ensure_coordinates(destination)

        if not origin_coords or not destination_coords:
            return "错误：无法解析起点或终点的坐标"

        url = f"{self.base_url}/direction/driving"
        params = {
            'key': self.api_key,
            'origin': origin_coords,
            'destination': destination_coords,
            'output': 'json',
            'extensions': 'base'
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if data['status'] == '1' and data['route']['paths']:
                path = data['route']['paths'][0]
                distance = path['distance']
                duration = path['duration']
                steps = path['steps']

                # 格式化路线信息
                route_info = {
                    'distance': f"{int(distance) / 1000:.1f}公里",
                    'duration': f"{int(duration) // 60}分钟",
                    'route': f"从 {origin} 到 {destination}",
                    'steps': [step['instruction'] for step in steps[:8]]  # 前8个步骤
                }
                return json.dumps(route_info, ensure_ascii=False, indent=2)
            else:
                return f"路径规划失败: {data.get('info', '未知错误')}"

        except Exception as e:
            return f"请求失败: {str(e)}"

    def walking_route(self, input_data):
        """步行路径规划 - 增强参数解析"""
        origin, destination = self._parse_route_input(input_data)
        if not origin or not destination:
            return "错误：需要提供起点和终点"

        origin_coords = self._ensure_coordinates(origin)
        destination_coords = self._ensure_coordinates(destination)

        if not origin_coords or not destination_coords:
            return "错误：无法解析起点或终点的坐标"

        url = f"{self.base_url}/direction/walking"
        params = {
            'key': self.api_key,
            'origin': origin_coords,
            'destination': destination_coords,
            'output': 'json'
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if data['status'] == '1' and data['route']['paths']:
                path = data['route']['paths'][0]
                distance = path['distance']
                duration = path['duration']
                steps = path['steps']

                route_info = {
                    'distance': f"{int(distance) / 1000:.1f}公里",
                    'duration': f"{int(duration) // 60}分钟",
                    'route': f"从 {origin} 到 {destination}",
                    'steps': [step['instruction'] for step in steps[:8]]
                }
                return json.dumps(route_info, ensure_ascii=False, indent=2)
            else:
                return f"步行路径规划失败: {data.get('info', '未知错误')}"

        except Exception as e:
            return f"请求失败: {str(e)}"

    def bicycling_route(self, input_data):
        """骑行路径规划 - 增强参数解析"""
        origin, destination = self._parse_route_input(input_data)
        if not origin or not destination:
            return "错误：需要提供起点和终点"

        origin_coords = self._ensure_coordinates(origin)
        destination_coords = self._ensure_coordinates(destination)

        if not origin_coords or not destination_coords:
            return "错误：无法解析起点或终点的坐标"

        url = f"{self.base_url}/direction/bicycling"
        params = {
            'key': self.api_key,
            'origin': origin_coords,
            'destination': destination_coords,
            'output': 'json'
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if data['status'] == '1' and data['route']['paths']:
                path = data['route']['paths'][0]
                distance = path['distance']
                duration = path['duration']
                steps = path['steps']

                route_info = {
                    'distance': f"{int(distance) / 1000:.1f}公里",
                    'duration': f"{int(duration) // 60}分钟",
                    'route': f"从 {origin} 到 {destination}",
                    'steps': [step['instruction'] for step in steps[:8]]
                }
                return json.dumps(route_info, ensure_ascii=False, indent=2)
            else:
                return f"骑行路径规划失败: {data.get('info', '未知错误')}"

        except Exception as e:
            return f"请求失败: {str(e)}"

    def _parse_route_input(self, input_data):
        """智能解析路线规划输入，支持多种格式"""
        # print(f"解析输入数据: {input_data} (类型: {type(input_data)})")

        origin = None
        destination = None

        # 情况1：输入是字典
        if isinstance(input_data, dict):
            origin = input_data.get('origin') or input_data.get('__arg1') or input_data.get('address')
            destination = input_data.get('destination') or input_data.get('__arg2')

        # 情况2：输入是JSON字符串
        elif isinstance(input_data, str):
            try:
                # 尝试解析JSON
                parsed = json.loads(input_data)
                if isinstance(parsed, dict):
                    origin = parsed.get('origin') or parsed.get('__arg1') or parsed.get('address')
                    destination = parsed.get('destination') or parsed.get('__arg2')
                else:
                    # 如果不是字典，当作普通字符串处理
                    origin, destination = self._extract_locations_from_text(input_data)
            except json.JSONDecodeError:
                # 如果不是JSON，当作普通字符串处理
                origin, destination = self._extract_locations_from_text(input_data)

        # 情况3：其他类型（如列表等）
        else:
            origin = str(input_data)

        # print(f"解析结果 - 起点: {origin}, 终点: {destination}")
        return origin, destination

    def _extract_locations_from_text(self, text):
        """从文本中智能提取起点和终点"""
        if not text:
            return None, None

        # 多种分隔符模式
        patterns = [
            r'从(.+?)(?:到|至|->|→)(.+)',  # 从A到B
            r'(.+?)(?:到|至|->|→)(.+)',  # A到B
            r'(.+)\s+到\s+(.+)',  # A 到 B
            r'(.+)\s+至\s+(.+)',  # A 至 B
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                origin = match.group(1).strip()
                destination = match.group(2).strip()

                # 清理可能的标点符号
                origin = re.sub(r'^从', '', origin).strip()
                origin = re.sub(r'[。，,\.\s]+$', '', origin)
                destination = re.sub(r'[。，,\.\s]+$', '', destination)

                return origin, destination

        # 如果没有匹配到模式，返回整个文本作为起点
        return text, None

    def _ensure_coordinates(self, location):
        """确保位置是坐标格式，如果不是则进行地理编码"""
        if self._is_coordinate(location):
            return location

        # 进行地理编码
        coords = self.geocode(location)
        if self._is_coordinate(coords):
            return coords
        else:
            print(f"地理编码失败: {coords}")
            return None

    def _is_coordinate(self, text):
        """检查字符串是否是坐标格式（经度,纬度）"""
        if not isinstance(text, str):
            return False
        parts = text.split(',')
        if len(parts) != 2:
            return False
        try:
            float(parts[0])
            float(parts[1])
            return True
        except:
            return False

    def get_tools(self):
        """获取所有工具 - 更新描述以引导AI正确调用"""
        tools = [
            Tool(
                name="maps_geo",
                description="将地址转换为经纬度坐标。输入应为地址字符串，如：'北京西站'",
                func=self.geocode
            ),
            Tool(
                name="maps_direction_driving",
                description="驾车路径规划。输入应为包含起点和终点的字符串，如：'从北京西站到天安门广场' 或 JSON格式 {'origin': '起点', 'destination': '终点'}",
                func=self.driving_route
            ),
            Tool(
                name="maps_direction_walking",
                description="步行路径规划。输入应为包含起点和终点的字符串，如：'从北京西站到天安门广场' 或 JSON格式 {'origin': '起点', 'destination': '终点'}",
                func=self.walking_route
            ),
            Tool(
                name="maps_direction_bicycling",
                description="骑行路径规划。输入应为包含起点和终点的字符串，如：'从北京西站到天安门广场' 或 JSON格式 {'origin': '起点', 'destination': '终点'}",
                func=self.bicycling_route
            )
        ]
        return tools


def get_tools(llm_embedding):
    """
    创建并返回工具列表

    Args:
        llm_embedding: 嵌入模型实例，用于初始化向量存储

    Returns:
        list: 工具列表
    """

    # 创建 Chroma 向量存储实例
    vectorstore = Chroma(
        persist_directory=Config.CHROMADB_DIRECTORY,
        collection_name=Config.CHROMADB_COLLECTION_NAME,
        embedding_function=llm_embedding,
    )
    # 将向量存储转换为检索器
    retriever = vectorstore.as_retriever()
    # 创建检索工具
    retriever_tool = create_retriever_tool(
        retriever,
        name="retrieve",
        description="这是健康档案查询工具，搜索并返回有关用户的健康档案信息。"
    )

    # 自定义 multiply 工具
    @tool
    def multiply(a: float, b: float) -> float:
        """这是计算两个数的乘积的工具，返回最终的计算结果"""
        return a * b

    tools_list = [retriever_tool, multiply, webSearch, amap_maps]
    # 返回工具列表
    return tools_list