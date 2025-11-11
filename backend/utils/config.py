import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    """统一的配置类，集中管理所有常量"""
    # prompt文件路径
    # Agent模板
    PROMPT_TEMPLATE_TXT_AGENT = "prompts/prompt_template_agent.txt"
    # 评分模板
    PROMPT_TEMPLATE_TXT_GRADE = "prompts/prompt_template_grade.txt"
    # 重写模板
    PROMPT_TEMPLATE_TXT_REWRITE = "prompts/prompt_template_rewrite.txt"
    # 生成模板（RAG提示词）
    PROMPT_TEMPLATE_TXT_GENERATE = "prompts/prompt_template_generate.txt"

    # Chroma 数据库配置
    CHROMADB_DIRECTORY = "chromaDB"
    CHROMADB_COLLECTION_NAME = "demo001"

    # 日志持久化存储
    LOG_FILE = "output/app.log"
    MAX_BYTES = 5*1024*1024,        # 日志文件单个最大5M
    BACKUP_COUNT = 3                # 备份3个文件

    # 数据库 URI，默认值
    DB_URI = os.getenv("DB_URI")

    # openai:调用gpt模型, qwen:调用阿里通义千问大模型, oneapi:调用oneapi方案支持的模型, ollama:调用本地开源大模型
    LLM_TYPE = os.getenv("LLM_TYPE")

    # API服务地址和端口
    HOST = os.getenv("HOST")
    PORT = os.getenv("PORT")