import uuid
from typing import Optional
from auth import get_password_hash
from model import UserInDB, User
import logging

logger = logging.getLogger(__name__)


class UserDB:
    def __init__(self, connection_pool):
        self.connection_pool = connection_pool

    def create_user_table(self):
        """创建用户表"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id VARCHAR(36) PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        hashed_password VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                conn.commit()
                logger.info("Users table created or already exists")
        except Exception as e:
            logger.error(f"Error creating users table: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """根据用户名获取用户"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:  # 使用普通游标
                cursor.execute(
                    "SELECT id, username, email, hashed_password FROM users WHERE username = %s AND is_active = TRUE",
                    (username,)
                )
                result = cursor.fetchone()
                if result:
                    # 通过索引访问结果
                    return UserInDB(
                        id=result[0],                   # id
                        username=result[1],             # username
                        email=result[2],                # email
                        hashed_password=result[3]       # hashed_password
                    )
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
        finally:
            if conn:
                self.connection_pool.putconn(conn)
        return None

    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """根据邮箱获取用户"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:  # 使用普通游标
                cursor.execute(
                    "SELECT id, username, hashed_password FROM users WHERE email = %s AND is_active = TRUE",
                    (email,)
                )
                result = cursor.fetchone()
                if result:
                    # 通过索引访问结果
                    return UserInDB(
                        id=result[0],                   # id
                        username=result[1],             # username
                        email=email,                    # email
                        hashed_password=result[2]       # hashed_password
                    )
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
        finally:
            if conn:
                self.connection_pool.putconn(conn)
        return None

    def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """根据用户ID获取用户"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:  # 使用普通游标
                cursor.execute(
                    "SELECT id, username, email, hashed_password FROM users WHERE id = %s AND is_active = TRUE",
                    (user_id,)
                )
                result = cursor.fetchone()
                if result:
                    # 通过索引访问结果
                    return UserInDB(
                        id=result[0],                   # id
                        username=result[1],             # username
                        email=result[2],                # email
                        hashed_password=result[3]       # hashed_password
                    )
        except Exception as e:
            logger.error(f"Error getting user by id: {e}")
        finally:
            if conn:
                self.connection_pool.putconn(conn)
        return None

    # 添加检查邮箱是否已存在的方法
    def check_email_exists(self, email: str) -> bool:
        """检查邮箱是否已注册"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s AND is_active = True", (email,))
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Error checking email existence: {e}")
            return False
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    # 添加检查用户名是否已存在的方法
    def check_username_exists(self, username: str) -> bool:
        """检查用户名是否已注册"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE username = %s AND is_active = True", (username,))
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Error checking username existence: {e}")
            return False
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    # 修改现有的创建用户方法，添加验证
    def create_user(self, username: str, email: str, password: str):
        """创建新用户"""
        conn = None
        try:
            # 检查用户名是否已存在
            if self.check_username_exists(username):
                raise ValueError("用户名已存在")

            # 检查邮箱是否已存在
            if self.check_email_exists(email):
                raise ValueError("邮箱已注册")

            # 生成用户ID和哈希密码
            user_id = str(uuid.uuid4())
            hashed_password = get_password_hash(password)

            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (id, username, email, hashed_password) VALUES (%s, %s, %s, %s) RETURNING id, username, email, created_at",
                    (user_id, username, email, hashed_password)
                )
                result = cursor.fetchone()
                conn.commit()

                if result:
                    user = User(
                        id=result[0],
                        username=result[1],
                        email=result[2],
                        created_at=result[3]
                    )
                    logger.info(f"User created successfully: {username}")
                    return user
                else:
                    raise ValueError("用户创建失败")
        except ValueError as ve:
            # 重新抛出验证错误
            raise ve
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise ValueError("用户注册失败，请稍后重试")
        finally:
            if conn:
                self.connection_pool.putconn(conn)


# ConversationDB 类
class ConversationDB:
    def __init__(self, connection_pool):
        self.connection_pool = connection_pool

    def create_conversation_tables(self):
        """创建对话相关的表"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                # 对话表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        title VARCHAR(200) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_deleted BOOLEAN DEFAULT FALSE
                    )
                """)

                # 消息表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id VARCHAR(36) PRIMARY KEY,
                        conversation_id VARCHAR(36) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                        role VARCHAR(20) NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 创建索引
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")

                conn.commit()
                logger.info("Conversation tables created or already exist")
        except Exception as e:
            logger.error(f"Error creating conversation tables: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def create_conversation(self, user_id: str, title: str) -> str:
        """创建新对话"""
        conn = None
        try:
            conversation_id = str(uuid.uuid4())
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO conversations (id, user_id, title) VALUES (%s, %s, %s) RETURNING id",
                    (conversation_id, user_id, title)
                )
                result = cursor.fetchone()
                conn.commit()
                logger.info(f"Created conversation: {conversation_id} for user: {user_id}")
                return conversation_id
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def add_message(self, conversation_id: str, role: str, content: str):
        """添加消息到对话 - 确保消息正确保存"""
        conn = None
        try:
            message_id = str(uuid.uuid4())
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                # 插入消息
                cursor.execute(
                    "INSERT INTO messages (id, conversation_id, role, content) VALUES (%s, %s, %s, %s)",
                    (message_id, conversation_id, role, content)
                )

                # 更新对话的更新时间
                cursor.execute(
                    "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (conversation_id,)
                )

                conn.commit()
                logger.info(f"Saved message to conversation {conversation_id}: {role} - {content[:50]}...")
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def get_conversation_messages(self, conversation_id: str) -> list:
        """获取对话的所有消息"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT role, content, timestamp 
                    FROM messages 
                    WHERE conversation_id = %s 
                    ORDER BY timestamp ASC
                """, (conversation_id,))
                results = cursor.fetchall()

                messages = []
                for result in results:
                    messages.append({
                        'role': result[0],
                        'content': result[1],
                        'timestamp': result[2].isoformat() if result[2] else None
                    })
                logger.info(f"Loaded {len(messages)} messages for conversation: {conversation_id}")
                return messages
        except Exception as e:
            logger.error(f"Error getting conversation messages: {e}")
            return []
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def update_conversation_title(self, conversation_id: str, title: str, user_id: str) -> bool:
        """更新对话标题"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE conversations 
                    SET title = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s AND user_id = %s AND is_deleted = FALSE
                """, (title, conversation_id, user_id))
                conn.commit()

                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Updated conversation title: {conversation_id} -> {title}")
                return success
        except Exception as e:
            logger.error(f"Error updating conversation title: {e}")
            return False
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """软删除对话"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE conversations 
                    SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s AND user_id = %s
                """, (conversation_id, user_id))
                conn.commit()

                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Deleted conversation: {conversation_id}")
                return success
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def get_conversation_preview(self, conversation_id: str) -> str:
        """获取对话的最后一条消息作为预览"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT content 
                    FROM messages 
                    WHERE conversation_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, (conversation_id,))
                result = cursor.fetchone()

                if result:
                    preview = result[0]
                    # 截取前30个字符作为预览
                    if len(preview) > 30:
                        return preview[:30] + "..."
                    return preview
                return "暂无消息"
        except Exception as e:
            logger.error(f"Error getting conversation preview: {e}")
            return "暂无消息"
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def add_message_with_timestamp(self, conversation_id: str, role: str, content: str, timestamp: str = None):
        """添加消息并指定时间戳（用于前端同步）"""
        conn = None
        try:
            message_id = str(uuid.uuid4())
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                if timestamp:
                    cursor.execute(
                        "INSERT INTO messages (id, conversation_id, role, content, timestamp) VALUES (%s, %s, %s, %s, %s)",
                        (message_id, conversation_id, role, content, timestamp)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO messages (id, conversation_id, role, content) VALUES (%s, %s, %s, %s)",
                        (message_id, conversation_id, role, content)
                    )

                # 更新对话的更新时间
                cursor.execute(
                    "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (conversation_id,)
                )

                conn.commit()
                logger.info(f"Saved message with timestamp to conversation {conversation_id}: {role}")
        except Exception as e:
            logger.error(f"Error adding message with timestamp: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def get_conversations_with_preview(self, user_id: str) -> list:
        """获取用户的对话列表，包含最后一条消息预览"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        c.id, 
                        c.title, 
                        c.created_at, 
                        c.updated_at,
                        m.content as last_message
                    FROM conversations c
                    LEFT JOIN messages m ON m.id = (
                        SELECT id FROM messages 
                        WHERE conversation_id = c.id 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    )
                    WHERE c.user_id = %s AND c.is_deleted = FALSE 
                    ORDER BY c.updated_at DESC
                """, (user_id,))
                results = cursor.fetchall()

                conversations = []
                for result in results:
                    last_message = result[4]
                    preview = last_message[:30] + "..." if last_message and len(last_message) > 30 else last_message

                    conversations.append({
                        'id': result[0],
                        'title': result[1],
                        'created_at': result[2],
                        'updated_at': result[3],
                        'preview': preview or "暂无消息"
                    })
                logger.info(f"Loaded {len(conversations)} conversations with preview for user: {user_id}")
                return conversations
        except Exception as e:
            logger.error(f"Error getting conversations with preview: {e}")
            return []
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def get_conversation_by_id(self, conversation_id: str, user_id: str) -> dict:
        """根据ID获取对话详情"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, title, created_at, updated_at 
                    FROM conversations 
                    WHERE id = %s AND user_id = %s AND is_deleted = FALSE
                """, (conversation_id, user_id))
                result = cursor.fetchone()

                if result:
                    conversation = {
                        'id': result[0],
                        'title': result[1],
                        'created_at': result[2].isoformat() if result[2] else None,
                        'updated_at': result[3].isoformat() if result[3] else None
                    }
                    return conversation
                return None
        except Exception as e:
            logger.error(f"Error getting conversation by id: {e}")
            return None
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def get_user_conversations(self, user_id: str) -> list:
        """获取用户的所有对话"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, title, created_at, updated_at 
                    FROM conversations 
                    WHERE user_id = %s AND is_deleted = FALSE 
                    ORDER BY updated_at DESC
                """, (user_id,))
                results = cursor.fetchall()

                conversations = []
                for result in results:
                    conversations.append({
                        'id': result[0],
                        'title': result[1],
                        'created_at': result[2].isoformat() if result[2] else None,
                        'updated_at': result[3].isoformat() if result[3] else None
                    })
                logger.info(f"Loaded {len(conversations)} conversations for user: {user_id}")
                return conversations
        except Exception as e:
            logger.error(f"Error getting user conversations: {e}")
            return []
        finally:
            if conn:
                self.connection_pool.putconn(conn)