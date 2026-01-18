import re
import json
import sys
import time
import traceback
# 导入UUID模块，用于生成唯一标识符
import uuid
import uvicorn
import logging
# 用于定义异步上下文管理器
from contextlib import asynccontextmanager
# 用于类型提示，定义列表和可选参数
from typing import Tuple, List, Dict, Any
from model import Message, ChatCompletionRequest, Token, User, ConversationCreate, MessageCreate, \
    ChatCompletionResponseChoice, ChatCompletionResponse, UserRegister, UserLogin, ConversationRename
from fastapi import FastAPI, HTTPException, Depends, status
# 用于返回JSON和流式响应
from fastapi.responses import JSONResponse, StreamingResponse
from concurrent_log_handler import ConcurrentRotatingFileHandler
from auth import create_access_token, get_current_user,  verify_password
from database import UserDB, ConversationDB
# 从自定义的库中引入函数
from ragAgent import (
    ToolConfig,
    create_graph,
    save_graph_visualization,
    get_llm,
    get_tools,
    Config,
    ConnectionPool,
    ConnectionPoolError,
    monitor_connection_pool,
)
# 导入向量存储相关库
from langchain_chroma import Chroma
from chromadb.config import Settings
from chromadb import Client as ChromaClient
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

# 全局向量存储实例
vector_store = None
llm_embedding = None


# 设置LangSmith环境变量 进行应用跟踪，实时了解应用中的每一步发生了什么
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_API_KEY"] = ""

# 设置日志基本配置，级别为DEBUG或INFO
logger = logging.getLogger(__name__)
# 设置日志器级别为DEBUG
logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.INFO)
logger.handlers = []  # 清空默认处理器

# 降低httpx库的日志级别，减少心跳请求日志
logging.getLogger("httpx").setLevel(logging.WARNING)
# 使用ConcurrentRotatingFileHandler
handler = ConcurrentRotatingFileHandler(
    # 日志文件
    Config.LOG_FILE,
    # 日志文件最大允许大小为5MB，达到上限后触发轮转
    maxBytes = Config.MAX_BYTES,
    # 在轮转时，最多保留3个历史日志文件
    backupCount = Config.BACKUP_COUNT
)
# 设置处理器级别为DEBUG
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
logger.addHandler(handler)


def format_response(response):
    """对输入的文本进行段落分隔、添加适当的换行符，以及在代码块中增加标记，以便生成更具可读性的输出。

    Args:
        response: 输入的文本。

    Returns:
        具有清晰段落分隔的文本。
    """
    # 使用正则表达式 \n{2, }将输入的response按照两个或更多的连续换行符进行分割。这样可以将文本分割成多个段落，每个段落由连续的非空行组成
    paragraphs = re.split(r'\n{2,}', response)
    # 空列表，用于存储格式化后的段落
    formatted_paragraphs = []
    # 遍历每个段落进行处理
    for para in paragraphs:
        # 检查段落中是否包含代码块标记
        if '```' in para:
            # 将段落按照```分割成多个部分，代码块和普通文本交替出现
            parts = para.split('```')
            for i, part in enumerate(parts):
                # 检查当前部分的索引是否为奇数，奇数部分代表代码块
                if i % 2 == 1:  # 这是代码块
                    # 将代码块部分用换行符和```包围，并去除多余的空白字符
                    parts[i] = f"\n```\n{part.strip()}\n```\n"
            # 将分割后的部分重新组合成一个字符串
            para = ''.join(parts)
        else:
            # 否则，将句子中的句点后面的空格替换为换行符，以便句子之间有明确的分隔
            para = para.replace('. ', '.\n')
        # 将格式化后的段落添加到formatted_paragraphs列表
        # strip()方法用于移除字符串开头和结尾的空白字符（包括空格、制表符 \t、换行符 \n等）
        formatted_paragraphs.append(para.strip())
    # 将所有格式化后的段落用两个换行符连接起来，以形成一个具有清晰段落分隔的文本
    return '\n\n'.join(formatted_paragraphs)


# 管理 FastAPI 应用生命周期的异步上下文管理器，负责启动和关闭时的初始化与清理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    管理 FastAPI 应用生命周期的异步上下文管理器，负责启动和关闭时的初始化与清理。

    Args:
        app (FastAPI): FastAPI 应用实例。

    Yields:
        None: 在 yield 前完成初始化，yield 后执行清理。

    Raises:
        ConnectionPoolError: 数据库连接池初始化或操作失败时抛出。
        Exception: 其他未预期的异常。
    """
    # 声明全局变量 graph 和 tool_config
    global graph, tool_config, user_db, conversation_db, vector_store, llm_embedding
    try:
        # 调用 get_llm 初始化聊天模型和嵌入模型
        llm_chat, llm_embedding = get_llm(Config.LLM_TYPE)

        # 获取工具列表，基于嵌入模型
        tools = get_tools(llm_embedding)

        # 创建工具配置实例
        tool_config = ToolConfig(tools)

        # 定义数据库连接参数：自动提交、无预准备阈值、5秒超时
        connection_kwargs = {"autocommit": True, "prepare_threshold": 0, "connect_timeout": 5}
        # 创建数据库连接池：最大20个连接，最小2个活跃连接，超时10秒
        db_connection_pool = ConnectionPool(
            conninfo=Config.DB_URI,
            max_size=20,
            min_size=2,
            kwargs=connection_kwargs,
            timeout=10
        )

        # 尝试打开数据库连接池
        try:
            # 打开连接池以启用数据库连接
            db_connection_pool.open()
            # 记录连接池初始化成功的日志（INFO 级别）
            logger.info("Database connection pool initialized")
            # 记录详细调试日志（DEBUG 级别）
            logger.debug("Database connection pool initialized")
        except Exception as e:
            # 记录连接池打开失败的错误日志
            logger.error(f"Failed to open connection pool: {e}")
            # 抛出自定义连接池异常
            raise ConnectionPoolError(f"无法打开数据库连接池: {str(e)}")

        # 启动连接池监控线程，60秒检查一次，设置为守护线程
        monitor_thread = monitor_connection_pool(db_connection_pool, interval=60)

        # 初始化用户数据库和对话数据库
        user_db = UserDB(db_connection_pool)
        conversation_db = ConversationDB(db_connection_pool)
        user_db.create_user_table()
        conversation_db.create_conversation_tables()

        # 尝试创建状态图
        try:
            # 使用数据库连接池和模型创建状态图
            graph = create_graph(db_connection_pool, llm_chat, llm_embedding, tool_config)
        except ConnectionPoolError as e:
            # 记录状态图创建失败的错误日志
            logger.error(f"Graph creation failed: {e}")
            # 退出程序，返回状态码 1
            sys.exit(1)

        # 保存状态图的可视化表示
        # save_graph_visualization(graph)

    except ConnectionPoolError as e:
        # 捕获并记录连接池相关异常
        logger.error(f"Connection pool error: {e}")
        # 退出程序，返回状态码 1
        sys.exit(1)
    except Exception as e:
        # 捕获并记录其他未预期的异常
        logger.error(f"Unexpected error: {e}")
        # 退出程序，返回状态码 1
        sys.exit(1)

    # yield 表示应用运行期间，初始化完成后进入运行状态
    yield
    # 检查并关闭数据库连接池（清理资源）
    if db_connection_pool and not db_connection_pool.closed:
        # 关闭连接池
        db_connection_pool.close()
        # 记录连接池关闭的日志
        logger.info("Database connection pool closed")
    # 记录服务关闭的日志
    logger.info("The service has been shut down")


def get_relevant_history_messages(conversation_id: str, user_input: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    获取与当前用户输入最相关的历史消息

    Args:
        conversation_id (str): 对话ID
        user_input (str): 用户当前输入
        top_k (int): 返回的相关消息数量，默认5条

    Returns:
        List[Dict[str, Any]]: 按相关性排序的历史消息列表
    """
    global llm_embedding
    
    try:
        # 加载该对话的所有历史消息
        history_messages = conversation_db.get_conversation_messages(conversation_id)
        logger.info(f"[DEBUG] Loaded {len(history_messages)} total history messages for conversation {conversation_id}")
        logger.info(f"[DEBUG] Current user input: {user_input}")
        
        if not history_messages:
            logger.info(f"[DEBUG] No history messages found for conversation {conversation_id}")
            return []
        
        # 如果历史消息不足top_k条，直接返回所有历史消息
        if len(history_messages) <= top_k:
            logger.info(f"[DEBUG] History messages ({len(history_messages)}) <= top_k ({top_k}), returning all messages")
            for i, msg in enumerate(history_messages):
                logger.info(f"[DEBUG] Message {i+1}: {msg['role']} - {msg['content'][:100]}...")
            return history_messages
        
        # 生成当前用户输入的向量嵌入
        logger.info(f"[DEBUG] Generating embedding for user input: {user_input[:100]}...")
        query_embedding = llm_embedding.embed_query(user_input)
        
        # 使用PG Vector进行相似度搜索
        logger.info(f"[DEBUG] Performing similarity search with PG Vector")
        relevant_messages = conversation_db.get_relevant_messages(conversation_id, query_embedding, top_k)
        
        # 确保相关消息按时间排序
        logger.info(f"[DEBUG] Retrieved {len(relevant_messages)} relevant messages from PG Vector:")
        for i, msg in enumerate(relevant_messages):
            logger.info(f"[DEBUG] Relevant message {i+1}: {msg['role']} - {msg['content'][:100]}... (timestamp: {msg['timestamp']})")
        
        relevant_messages.sort(key=lambda x: x['timestamp'])
        
        logger.info(f"[DEBUG] Relevant messages after time sorting (final result):")
        for i, msg in enumerate(relevant_messages):
            logger.info(f"[DEBUG] Final {i+1}: {msg['role']} - {msg['content'][:100]}... (timestamp: {msg['timestamp']})")
        
        logger.info(f"[DEBUG] Returning {len(relevant_messages)} relevant messages for conversation {conversation_id}")
        return relevant_messages
        
    except Exception as e:
        logger.error(f"[DEBUG] Error getting relevant history messages: {e}")
        # 出错时返回最近的top_k条消息作为备选
        history_messages = conversation_db.get_conversation_messages(conversation_id)
        fallback_messages = history_messages[-top_k:] if history_messages else []
        logger.info(f"[DEBUG] Using fallback: returning {len(fallback_messages)} most recent messages")
        for i, msg in enumerate(fallback_messages):
            logger.info(f"[DEBUG] Fallback {i+1}: {msg['role']} - {msg['content'][:100]}... (timestamp: {msg['timestamp']})")
        return fallback_messages

# 创建 FastAPI 实例, lifespan参数用于在应用程序生命周期的开始和结束时执行一些初始化或清理工作
app = FastAPI(lifespan=lifespan)


# 处理非流式响应的异步函数，生成并返回完整的响应内容
async def handle_non_stream_response1(user_input, graph, tool_config, config):
    """
    处理非流式响应的异步函数，生成并返回完整的响应内容。

    Args:
        user_input (str): 用户输入的内容。
        graph: 图对象，用于处理消息流。
        tool_config: 工具配置对象，包含可用工具的名称和定义。
        config (dict): 配置参数，包含线程和用户标识。

    Returns:
        JSONResponse: 包含格式化响应的 JSON 响应对象。
    """
    # 初始化 content 变量，用于存储最终响应内容
    content = None
    try:
        # 启动 graph.stream 处理用户输入，生成事件流
        events = graph.stream({"messages": [{"role": "user", "content": user_input}], "rewrite_count": 0}, config)
        # 遍历事件流中的每个事件
        for event in events:
            # 遍历事件中的所有值
            for value in event.values():
                # 检查事件值是否包含有效消息列表
                if "messages" not in value or not isinstance(value["messages"], list):
                    # 记录警告日志，跳过无效消息
                    logger.warning("No valid messages in response")
                    continue

                # 获取消息列表中的最后一条消息
                last_message = value["messages"][-1]

                # 检查消息是否包含工具调用
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    # 遍历所有工具调用
                    for tool_call in last_message.tool_calls:
                        # 验证工具调用是否为字典且包含名称
                        if isinstance(tool_call, dict) and "name" in tool_call:
                            # 记录工具调用日志
                            logger.info(f"Calling tool: {tool_call['name']}")
                    # 跳过本次循环，继续处理下一事件
                    continue

                # 检查消息是否包含内容
                if hasattr(last_message, "content"):
                    # 将消息内容赋值给 content
                    content = last_message.content

                    # 检查是否为工具输出（基于工具名称）
                    if hasattr(last_message, "name") and last_message.name in tool_config.get_tool_names():
                        # 获取工具名称
                        tool_name = last_message.name
                        # 记录工具输出日志
                        logger.info(f"Tool Output [{tool_name}]: {content}")
                    # 处理大模型输出（非工具消息）
                    else:
                        # 记录最终响应日志
                        logger.info(f"Final Response is: {content}")
                else:
                    # 记录无内容的消息日志，跳过处理
                    logger.info("Message has no content, skipping")
    except ValueError as ve:
        # 捕获并记录值错误
        logger.error(f"Value error in response processing: {ve}")
    except Exception as e:
        # 捕获并记录其他未预期的异常
        logger.error(f"Error processing response: {e}")

    # 格式化响应内容，若无内容则返回默认值
    formatted_response = str(format_response(content)) if content else "No response generated"
    # 记录格式化后的响应日志
    logger.info(f"Results for Formatting: {formatted_response}")

    # 构造返回给客户端的响应对象
    try:
        response = ChatCompletionResponse(
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=Message(role="assistant", content=formatted_response),
                    finish_reason="stop"
                )
            ]
        )
    except Exception as resp_error:
        # 捕获并记录构造响应对象时的异常
        logger.error(f"Error creating response object: {resp_error}")
        # 构造错误响应对象
        response = ChatCompletionResponse(
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=Message(role="assistant", content="Error generating response"),
                    finish_reason="error"
                )
            ]
        )

    # 记录发送给客户端的响应内容日志
    logger.info(f"Send response content: \n{response}")
    # 返回 JSON 格式的响应对象
    return JSONResponse(content=response.model_dump())


# 处理流式响应的异步函数，生成并返回流式数据
async def handle_stream_response1(user_input, graph, config):
    """
    处理流式响应的异步函数，生成并返回流式数据。

    Args:
        user_input (str): 用户输入的内容。
        graph: 图对象，用于处理消息流。
        config (dict): 配置参数，包含线程和用户标识。

    Returns:
        StreamingResponse: 流式响应对象，媒体类型为 text/event-stream。
    """
    async def generate_stream():
        """
        内部异步生成器函数，用于产生流式响应数据。

        Yields:
            str: 流式数据块，格式为 SSE (Server-Sent Events)。

        Raises:
            Exception: 流生成过程中可能抛出的异常。
        """
        try:
            # 生成唯一的 chunk ID
            chunk_id = f"chatcmpl-{uuid.uuid4().hex}"
            # 调用 graph.stream 获取消息流
            stream_data = graph.stream(
                {"messages": [{"role": "user", "content": user_input}], "rewrite_count": 0},
                config,
                stream_mode="messages"
            )
            # 使用异步方式处理同步生成器，确保实时流式输出
            import asyncio
            for message_chunk, metadata in stream_data:
                try:
                    # 获取当前节点名称
                    node_name = metadata.get("langgraph_node") if metadata else None
                    # 仅处理 generate 和 agent 节点
                    if node_name in ["generate", "agent"]:
                        # 获取消息内容，默认空字符串
                        chunk = getattr(message_chunk, 'content', '')
                        # 记录流式数据块日志
                        logger.info(f"Streaming chunk from {node_name}: {chunk}")
                        # 产出流式数据块
                        yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'created': int(time.time()), 'choices': [{'index': 0, 'delta': {'content': chunk}, 'finish_reason': None}]})}\n\n"
                        # 添加一个小延迟，确保数据能被实时发送到客户端
                        await asyncio.sleep(0.01)
                except Exception as chunk_error:
                    # 记录单个数据块处理异常
                    logger.error(f"Error processing stream chunk: {chunk_error}")
                    continue

            # 产出流结束标记
            yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'created': int(time.time()), 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
        except Exception as stream_error:
            # 记录流生成过程中的异常
            logger.error(f"Stream generation error: {stream_error}")
            # 产出错误提示
            yield f"data: {json.dumps({'error': 'Stream processing failed'})}\n\n"

    # 返回流式响应对象
    return StreamingResponse(generate_stream(), media_type="text/event-stream")


async def handle_non_stream_response(messages, graph, tool_config, config):
    """
    处理非流式响应的异步函数，生成并返回完整的响应内容。

    Args:
        messages: 完整的消息列表（历史 + 新消息）
        graph: 图对象，用于处理消息流。
        tool_config: 工具配置对象，包含可用工具的名称和定义。
        config (dict): 配置参数，包含线程和用户标识。

    Returns:
        JSONResponse: 包含格式化响应的 JSON 响应对象。
    """
    # 初始化 content 变量，用于存储最终响应内容
    content = None
    try:
        # 启动 graph.stream 处理完整消息列表
        events = graph.stream({"messages": messages, "rewrite_count": 0}, config)
        # 遍历事件流中的每个事件
        for event in events:
            # 遍历事件中的所有值
            for value in event.values():
                # 检查事件值是否包含有效消息列表
                if "messages" not in value or not isinstance(value["messages"], list):
                    # 记录警告日志，跳过无效消息
                    logger.warning("No valid messages in response")
                    continue

                # 获取消息列表中的最后一条消息
                last_message = value["messages"][-1]

                # 检查消息是否包含工具调用
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    # 遍历所有工具调用
                    for tool_call in last_message.tool_calls:
                        # 验证工具调用是否为字典且包含名称
                        if isinstance(tool_call, dict) and "name" in tool_call:
                            # 记录工具调用日志
                            logger.info(f"Calling tool: {tool_call['name']}")
                    # 跳过本次循环，继续处理下一事件
                    continue

                # 检查消息是否包含内容
                if hasattr(last_message, "content"):
                    # 将消息内容赋值给 content
                    content = last_message.content

                    # 检查是否为工具输出（基于工具名称）
                    if hasattr(last_message, "name") and last_message.name in tool_config.get_tool_names():
                        # 获取工具名称
                        tool_name = last_message.name
                        # 记录工具输出日志
                        logger.info(f"Tool Output [{tool_name}]: {content}")
                    # 处理大模型输出（非工具消息）
                    else:
                        # 记录最终响应日志
                        logger.info(f"Final Response is: {content}")
                else:
                    # 记录无内容的消息日志，跳过处理
                    logger.info("Message has no content, skipping")
    except ValueError as ve:
        # 捕获并记录值错误
        logger.error(f"Value error in response processing: {ve}")
    except Exception as e:
        # 捕获并记录其他未预期的异常
        logger.error(f"Error processing response: {e}")

    # 格式化响应内容，若无内容则返回默认值
    formatted_response = str(format_response(content)) if content else "No response generated"
    # 记录格式化后的响应日志
    logger.info(f"Results for Formatting: {formatted_response}")

    # 构造返回给客户端的响应对象
    try:
        response = ChatCompletionResponse(
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=Message(role="assistant", content=formatted_response),
                    finish_reason="stop"
                )
            ]
        )
    except Exception as resp_error:
        # 捕获并记录构造响应对象时的异常
        logger.error(f"Error creating response object: {resp_error}")
        # 构造错误响应对象
        response = ChatCompletionResponse(
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=Message(role="assistant", content="Error generating response"),
                    finish_reason="error"
                )
            ]
        )

    # 记录发送给客户端的响应内容日志
    logger.info(f"Send response content: \n{response}")
    # 返回 JSON 格式的响应对象
    return JSONResponse(content=response.model_dump())


async def handle_stream_response(messages, graph, config, conversation_id):
    """
    处理流式响应的异步函数，生成并返回流式数据。

    Args:
        messages: 完整的消息列表（历史 + 新消息）
        graph: 图对象，用于处理消息流。
        config (dict): 配置参数，包含线程和用户标识。
        conversation_id: 对话ID，用于保存助手消息到数据库。

    Returns:
        StreamingResponse: 流式响应对象，媒体类型为 text/event-stream。
    """
    async def generate_stream():
        """
        内部异步生成器函数，用于产生流式响应数据。

        Yields:
            str: 流式数据块，格式为 SSE (Server-Sent Events)。

        Raises:
            Exception: 流生成过程中可能抛出的异常。
        """
        try:
            # 生成唯一的 chunk ID
            chunk_id = f"chatcmpl-{uuid.uuid4().hex}"
            # 初始化完整的助手消息内容
            full_content = ""
            # 调用 graph.stream 获取消息流，使用完整的消息列表
            stream_data = graph.stream(
                {"messages": messages, "rewrite_count": 0},
                config,
                stream_mode="messages"
            )
            # 使用异步方式处理同步生成器，确保实时流式输出
            import asyncio
            for message_chunk, metadata in stream_data:
                try:
                    # 获取当前节点名称
                    node_name = metadata.get("langgraph_node") if metadata else None
                    # 仅处理 generate 和 agent 节点
                    if node_name in ["generate", "agent"]:
                        # 获取消息内容，默认空字符串
                        chunk = getattr(message_chunk, 'content', '')
                        # 记录流式数据块日志
                        logger.info(f"Streaming chunk from {node_name}: {chunk}")
                        # 累加完整的助手消息内容
                        full_content += chunk
                        # 产出流式数据块
                        yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'created': int(time.time()), 'choices': [{'index': 0, 'delta': {'content': chunk}, 'finish_reason': None}]})}\n\n"
                        # 添加一个小延迟，确保数据能被实时发送到客户端
                        await asyncio.sleep(0.01)
                except Exception as chunk_error:
                    logger.error(f"Error processing stream chunk: {chunk_error}")
                    continue

            # 流结束后，保存完整的助手消息到数据库
            if full_content:
                logger.info(f"Saving complete assistant message to conversation {conversation_id}: {full_content[:50]}...")
                conversation_db.add_message(conversation_id, "assistant", full_content)

            yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'created': int(time.time()), 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
        except Exception as stream_error:
            logger.error(f"Stream generation error: {stream_error}")
            yield f"data: {json.dumps({'error': 'Stream processing failed'})}\n\n"

    # 返回流式响应对象
    return StreamingResponse(generate_stream(), media_type="text/event-stream")


# 依赖注入函数，用于获取 graph 和 tool_config
async def get_dependencies() -> Tuple[any, any]:
    """
    依赖注入函数，用于获取 graph 和 tool_config。

    Returns:
        Tuple: 包含 (graph, tool_config) 的元组。

    Raises:
        HTTPException: 如果 graph 或 tool_config 未初始化，则抛出 500 错误。
    """
    if not graph or not tool_config:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return graph, tool_config


# 注册
@app.post("/register")
async def register(user_data: UserRegister):
    try:
        # 验证邮箱格式
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', user_data.email):
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "message": "邮箱格式不正确",
                    "error_code": "INVALID_EMAIL"
                }
            )

        # 验证用户名格式
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', user_data.username):
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "message": "用户名只能包含字母、数字和下划线，且长度为3-20个字符",
                    "error_code": "INVALID_USERNAME"
                }
            )

        # 验证密码强度
        if len(user_data.password) < 6:
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "message": "密码长度至少为6位",
                    "error_code": "WEAK_PASSWORD"
                }
            )
        if not re.search(r'[a-zA-Z]', user_data.password) or not re.search(r'[0-9]', user_data.password):
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "message": "密码必须包含字母和数字",
                    "error_code": "WEAK_PASSWORD"
                }
            )

        user = user_db.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )

        if user:
            return {
                "success": True,
                "message": "注册成功",
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }
        else:
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "message": "用户注册失败",
                    "error_code": "REGISTRATION_FAILED"
                }
            )

    except ValueError as e:
        error_msg = str(e)
        if "用户名已存在" in error_msg:
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "message": "用户名已存在",
                    "error_code": "USERNAME_EXISTS"
                }
            )
        elif "邮箱已注册" in error_msg:
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "message": "邮箱已注册",
                    "error_code": "EMAIL_EXISTS"
                }
            )
        else:
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "message": error_msg,
                    "error_code": "VALIDATION_ERROR"
                }
            )

    except Exception as e:
        logger.error(f"Registration error: {e}")
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "message": "注册失败，请稍后重试",
                "error_code": "SERVER_ERROR"
            }
        )


@app.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    if "@" in user_data.username:
        # 邮箱登录
        user = user_db.get_user_by_email(user_data.username)
    else:
        user = user_db.get_user_by_username(user_data.username)
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.id})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id
    )


@app.get("/users/me", response_model=User)
async def read_users_me(current_user_id: str = Depends(get_current_user)):
    user = user_db.get_user_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(id=user.id, username=user.username, email=user.email)


@app.get("/conversations", response_model=List[dict])
async def get_conversations(current_user_id: str = Depends(get_current_user)):
    """获取用户的所有对话"""
    try:
        conversations = conversation_db.get_user_conversations(current_user_id)
        return conversations
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail="获取对话列表失败")


@app.get("/conversations/{conversation_id}/messages", response_model=List[dict])
async def get_conversation_messages(conversation_id: str, current_user_id: str = Depends(get_current_user)):
    """获取对话的所有消息"""
    try:
        # 验证用户是否有权访问这个对话
        conversation = conversation_db.get_conversation_by_id(conversation_id, current_user_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")

        messages = conversation_db.get_conversation_messages(conversation_id)
        return messages
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation messages: {e}")
        raise HTTPException(status_code=500, detail="获取消息失败")


@app.post("/conversations")
async def create_conversation(conversation: ConversationCreate, current_user_id: str = Depends(get_current_user)):
    """创建新对话"""
    try:
        conversation_id = conversation_db.create_conversation(current_user_id, conversation.title)
        new_conversation = conversation_db.get_conversation_by_id(conversation_id, current_user_id)
        return new_conversation
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="创建对话失败")


@app.put("/conversations/{conversation_id}/rename")
async def rename_conversation(conversation_id: str, rename_data: ConversationRename,
                              current_user_id: str = Depends(get_current_user)):
    """重命名对话"""
    try:
        success = conversation_db.update_conversation_title(conversation_id, rename_data.title, current_user_id)
        if not success:
            raise HTTPException(status_code=404, detail="对话不存在")

        updated_conversation = conversation_db.get_conversation_by_id(conversation_id, current_user_id)
        return updated_conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renaming conversation: {e}")
        raise HTTPException(status_code=500, detail="重命名对话失败")


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, current_user_id: str = Depends(get_current_user)):
    """删除对话"""
    try:
        success = conversation_db.delete_conversation(conversation_id, current_user_id)
        if not success:
            raise HTTPException(status_code=404, detail="对话不存在")
        return {"message": "对话删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail="删除对话失败")


@app.post("/conversations/{conversation_id}/messages")
async def add_message_to_conversation(
        conversation_id: str,
        message: MessageCreate,
        current_user_id: str = Depends(get_current_user)
):
    """添加消息到对话"""
    try:
        # 验证用户是否有权访问这个对话
        conversation = conversation_db.get_conversation_by_id(conversation_id, current_user_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")

        conversation_db.add_message(conversation_id, message.role, message.content)
        return {"message": "消息添加成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding message to conversation: {e}")
        raise HTTPException(status_code=500, detail="添加消息失败")


# 添加获取对话详情的接口
@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, current_user_id: str = Depends(get_current_user)):
    """获取对话详情"""
    try:
        conversation = conversation_db.get_conversation_by_id(conversation_id, current_user_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail="获取对话失败")


@app.post("/v1/chat/completions")
async def chat_completions(
        request: ChatCompletionRequest,
        current_user_id: str = Depends(get_current_user),
        dependencies: Tuple[any, any] = Depends(get_dependencies)
):
    try:
        graph, tool_config = dependencies
        if not request.messages:
            logger.error("Invalid request: Empty messages")
            raise HTTPException(status_code=400, detail="Messages cannot be empty")

        # 获取用户输入
        user_input = request.messages[-1].content if request.messages else ""

        # 获取对话ID - 关键：从前端获取
        conversation_id = getattr(request, 'conversation_id', None)
        logger.info(f"Received conversation_id: {conversation_id}")

        # 如果没有对话ID，说明是全新对话，创建新对话
        if not conversation_id:
            title = user_input[:20] + ("..." if len(user_input) > 20 else "") if user_input else "新对话"
            conversation_id = conversation_db.create_conversation(current_user_id, title)
            logger.info(f"Created new conversation: {conversation_id}")
        else:
            # 验证用户是否有权访问这个对话
            conversation = conversation_db.get_conversation_by_id(conversation_id, current_user_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="对话不存在或无权访问")
            logger.info(f"Using existing conversation: {conversation_id}")

        # 保存用户消息到当前对话
        for msg in request.messages:
            if msg.role == "user":  # 只保存用户消息
                logger.info(f"Saving user message to conversation {conversation_id}: {msg.content[:50]}...")
                # 生成消息的向量嵌入
                message_embedding = llm_embedding.embed_query(msg.content)
                # 保存消息并包含向量嵌入
                conversation_db.add_message(conversation_id, msg.role, msg.content, message_embedding)

        # 加载与当前用户输入最相关的历史消息作为上下文（最多5条）
        relevant_messages = get_relevant_history_messages(conversation_id, user_input, top_k=5)
        logger.info(f"Loaded {len(relevant_messages)} relevant history messages for conversation {conversation_id}")

        # 构建完整的消息列表：相关历史消息 + 当前用户输入
        all_messages = []
        for msg in relevant_messages:
            all_messages.append({
                "role": msg['role'],
                "content": msg['content']
            })

        logger.info(f"User {current_user_id} input with {len(all_messages)} total messages")

        config = {
            "configurable": {
                "thread_id": f"{current_user_id}@@{conversation_id}",
                "user_id": current_user_id
            }
        }

        # 使用完整的消息列表（所有历史消息）调用AI
        if request.stream:
            response = await handle_stream_response(all_messages, graph, config, conversation_id)
            return response

        # 非流式输出
        response = await handle_non_stream_response(all_messages, graph, tool_config, config)

        # 立即保存助手消息到数据库
        if hasattr(response, 'body'):
            import json
            response_data = json.loads(response.body.decode())
            assistant_content = response_data['choices'][0]['message']['content']
            logger.info(f"Saving assistant message to conversation {conversation_id}: {assistant_content[:50]}...")
            # 生成助手消息的向量嵌入
            assistant_embedding = llm_embedding.embed_query(assistant_content)
            # 保存助手消息并包含向量嵌入
            conversation_db.add_message(conversation_id, "assistant", assistant_content, assistant_embedding)

        # 返回对话ID和更新后的对话信息
        response_data = json.loads(response.body.decode())
        response_data['conversation_id'] = conversation_id

        # 获取更新后的对话信息
        updated_conversation = conversation_db.get_conversation_by_id(conversation_id, current_user_id)
        response_data['conversation'] = updated_conversation

        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"Error handling chat completion: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    logger.info(f"Start the server on host {Config.HOST}, port {Config.PORT}")
    # uvicorn是一个用于运行ASGI应用的轻量级、超快速的ASGI服务器实现
    # 用于部署基于FastAPI框架的异步PythonWeb应用程序
    uvicorn.run(app, host=Config.HOST, port=int(Config.PORT))


