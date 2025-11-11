import uuid
import time
import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# 定义消息类，用于封装API接口返回数据
# 定义Message类
class Message(BaseModel):
    role: str
    content: str


# 定义ChatCompletionRequest类
class ChatCompletionRequest(BaseModel):
    model: str = "default"
    messages: List[Message]
    stream: bool = False
    conversation_id: Optional[str] = None


# 定义ChatCompletionResponseChoice类
class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None


# 定义ChatCompletionResponse类
class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    choices: List[ChatCompletionResponseChoice]
    system_fingerprint: Optional[str] = None


class UserRegister(BaseModel):
    username: str
    email: str
    password: str

    @field_validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 20:
            raise ValueError('用户名长度必须在3-20个字符之间')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v

    @field_validator('email')
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('邮箱格式不正确')
        return v

    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 6 or len(v) > 20:
            raise ValueError('密码长度必须在6-20个字符之间')
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('密码必须包含至少一个字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    id: str
    username: str
    email: str


class UserInDB(User):
    hashed_password: str


# 对话相关的路由
class ConversationCreate(BaseModel):
    title: str


class MessageCreate(BaseModel):
    content: str
    role: str = "user"


class ConversationRename(BaseModel):
    title: str