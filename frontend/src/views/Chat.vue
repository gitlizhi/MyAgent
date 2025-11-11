<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <div class="navbar">
      <div class="navbar-brand">
        <div class="brand-logo">
          <el-icon size="24" color="#409EFF"><ChatDotRound /></el-icon>
          <span class="brand-text">LangGraph Agent</span>
        </div>
      </div>
      <div class="navbar-actions">
        <el-button text :icon="User" @click="showUserMenu = !showUserMenu">
          {{ currentUser?.username }}
        </el-button>
        <el-dropdown v-model="showUserMenu" @command="handleUserCommand">
          <el-button text :icon="ArrowDown" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>
                个人资料
              </el-dropdown-item>
              <el-dropdown-item command="settings">
                <el-icon><Setting /></el-icon>
                设置
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="main-layout">
      <!-- 侧边栏 -->
      <div class="sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-header">
          <div class="sidebar-title">
            <el-icon><ChatLineRound /></el-icon>
            <span v-if="!sidebarCollapsed">对话历史</span>
          </div>
          <div class="sidebar-actions">
            <el-button
              type="primary"
              :icon="Plus"
              @click="createNewConversation"
              size="small"
              circle
              v-if="!sidebarCollapsed"
            />
            <el-button
              text
              :icon="sidebarCollapsed ? Expand : Fold"
              @click="sidebarCollapsed = !sidebarCollapsed"
              size="small"
            />
          </div>
        </div>

        <div class="conversation-list" v-loading="loadingConversations">
          <div
            v-for="conv in conversations"
            :key="conv.id"
            :class="['conversation-item', { active: activeConversationId === conv.id }]"
            @click="switchConversation(conv.id)"
          >
            <div class="conv-icon">
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <div class="conv-content" v-if="!sidebarCollapsed">
              <div class="conv-title">{{ conv.title }}</div>
              <div class="conv-preview">{{ getConversationPreview(conv.id) }}</div>
              <div class="conv-time">{{ formatTime(conv.updated_at) }}</div>
            </div>
            <div class="conv-actions" v-if="!sidebarCollapsed && activeConversationId === conv.id">
              <el-dropdown trigger="click" @command="handleCommand($event, conv)">
                <el-button text :icon="MoreFilled" size="small" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="rename">
                      <el-icon><Edit /></el-icon>
                      重命名
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" style="color: #F56C6C;">
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>

          <div v-if="conversations.length === 0 && !loadingConversations" class="empty-state">
            <el-icon :size="48" color="#C0C4CC"><ChatLineRound /></el-icon>
            <p>暂无对话记录</p>
            <p class="empty-hint">开始新的对话吧</p>
          </div>
        </div>
      </div>

      <!-- 主聊天区域 -->
      <div class="chat-main">
        <!-- 欢迎界面 -->
        <div v-if="!activeConversationId" class="welcome-container">
          <div class="welcome-content">
            <div class="welcome-icon">
              <el-icon size="64" color="#409EFF"><ChatDotRound /></el-icon>
            </div>
            <h1>欢迎使用 LangGraph Agent</h1>
            <p class="welcome-description">
              我是您的AI助手，可以帮您解答问题、提供信息和建议。<br>
              请选择左侧对话或创建新对话开始聊天！
            </p>
            <div class="welcome-features">
              <div class="feature-item">
                <el-icon color="#67C23A"><SuccessFilled /></el-icon>
                <span>智能对话</span>
              </div>
              <div class="feature-item">
                <el-icon color="#E6A23C"><WarningFilled /></el-icon>
                <span>上下文记忆</span>
              </div>
              <div class="feature-item">
                <el-icon color="#409EFF"><InfoFilled /></el-icon>
                <span>多工具支持</span>
              </div>
            </div>
            <el-button type="primary" :icon="Plus" @click="createNewConversation" size="large">
              开始新对话
            </el-button>
          </div>
        </div>

        <!-- 聊天界面 -->
        <div v-else class="chat-container">
          <div class="chat-header">
            <div class="header-title">
              <h3>{{ getActiveConversationTitle() }}</h3>
              <el-tag type="info" size="small">AI Assistant</el-tag>
            </div>
          </div>

          <div class="messages-container" ref="messagesContainer">
            <div
              v-for="message in currentMessages"
              :key="message.id"
              :class="['message', message.role]"
            >
              <div class="message-avatar">
                <el-avatar
                  :icon="message.role === 'user' ? User : ChatDotRound"
                  :style="message.role === 'user' ? 'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'background: linear-gradient(135deg, #409EFF 0%, #67C23A 100%)'"
                />
              </div>
              <div class="message-content">
                <div class="message-text" v-html="formatMessageContent(message.content)"></div>
                <div class="message-time">{{ formatMessageTime(message.timestamp) }}</div>
              </div>
            </div>

            <!-- 加载状态 -->
            <div v-if="loading && activeConversationId" class="message assistant">
              <div class="message-avatar">
                <el-avatar :icon="ChatDotRound" style="background: linear-gradient(135deg, #409EFF 0%, #67C23A 100%)" />
              </div>
              <div class="message-content">
                <div class="message-text">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <span class="thinking-text">AI正在思考中...</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 输入区域 -->
          <div class="input-container">
            <div class="input-wrapper">
              <el-input
                v-model="inputMessage"
                type="textarea"
                :rows="3"
                placeholder="输入您的问题..."
                :disabled="loading"
                @keydown.enter.exact.prevent="sendMessage"
                resize="none"
                class="message-input"
              />
              <div class="input-actions">
                <el-tooltip content="发送消息 (Enter)" placement="top">
                  <el-button
                    type="primary"
                    :loading="loading"
                    :disabled="!inputMessage.trim()"
                    @click="sendMessage"
                    class="send-btn"
                    circle
                  >
                    <el-icon><Promotion /></el-icon>
                  </el-button>
                </el-tooltip>
              </div>
            </div>
            <div class="input-footer">
              <span class="tip-text">LangGraph Agent 可能会犯错误，请核实重要信息</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted} from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router' // 添加这行

const messagesContainer = ref()
const inputMessage = ref('')
const loading = ref(false)
const loadingConversations = ref(false)

// 对话管理 - 关键修改：确保对话ID的一致性
const conversations = ref([])
const activeConversationId = ref(null) // 当前活跃的对话ID
const currentMessages = ref([]) // 当前活跃对话的消息
const conversationMessagesMap = ref(new Map()) // 存储所有对话的消息
import {
  Plus,
  User,
  ChatDotRound,
  Loading,
  MoreFilled,
  Edit,
  Delete,
  ChatLineRound,
  ArrowDown,
  Setting,
  SwitchButton,
  Expand,
  Fold,
  SuccessFilled,
  WarningFilled,
  InfoFilled,
  Promotion
} from '@element-plus/icons-vue'
const sidebarCollapsed = ref(false)
const showUserMenu = ref(false)

// 获取当前用户信息
// 添加路由实例
const router = useRouter()
const authStore = useAuthStore()
const currentUser = computed(() => authStore.user)

// 获取活跃对话的标题
const getActiveConversationTitle = () => {
  const conv = conversations.value.find(c => c.id === activeConversationId.value)
  return conv ? conv.title : '未知对话'
}

// 格式化消息内容（支持简单的Markdown）
const formatMessageContent = (content) => {
  if (!content) return ''
  // 简单的换行处理
  return content.replace(/\n/g, '<br>')
}

const handleUserCommand = (command) => {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  } else if (command === 'profile') {
    // 跳转到个人资料页面
    ElMessage.info('个人资料功能开发中...')
  } else if (command === 'settings') {
    // 跳转到设置页面
    ElMessage.info('设置功能开发中...')
  }
}

// 获取对话预览
const getConversationPreview = (conversationId) => {
  const messages = conversationMessagesMap.value.get(conversationId) || []
  const lastMessage = messages[messages.length - 1]
  return lastMessage ? lastMessage.content.substring(0, 30) + (lastMessage.content.length > 30 ? '...' : '') : '暂无消息'
}

// 加载用户对话历史
const loadConversations = async () => {
  loadingConversations.value = true
  try {
    const response = await axios.get('/api/conversations')
    conversations.value = response.data.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
    console.log('加载对话历史:', conversations.value)
  } catch (error) {
    console.error('加载对话历史失败:', error)
    ElMessage.error('加载对话历史失败')
  } finally {
    loadingConversations.value = false
  }
}

// 加载特定对话的消息
const loadConversationMessages = async (conversationId) => {
  try {
    const response = await axios.get(`/api/conversations/${conversationId}/messages`)
    const messages = response.data.map((msg, index) => ({
      id: `${conversationId}-${index}-${msg.timestamp}`,
      role: msg.role,
      content: msg.content,
      timestamp: msg.timestamp
    }))

    // 保存到消息映射中
    conversationMessagesMap.value.set(conversationId, messages)
    currentMessages.value = messages

    console.log(`加载对话 ${conversationId} 的消息:`, messages)
    scrollToBottom()
  } catch (error) {
    console.error('加载消息失败:', error)
    ElMessage.error('加载消息失败')
  }
}

// 创建新对话 - 关键修改：确保正确设置活跃对话ID
const createNewConversation = async () => {
  try {
    console.log('创建新对话...')
    const response = await axios.post('/api/conversations', {
      title: '新对话'
    })

    const newConversation = response.data
    console.log('新对话创建成功:', newConversation)

    // 添加到对话列表
    conversations.value.unshift(newConversation)
    conversationMessagesMap.value.set(newConversation.id, [])

    // 切换到新对话 - 关键：设置活跃对话ID
    activeConversationId.value = newConversation.id
    currentMessages.value = []

    ElMessage.success('新对话已创建')
  } catch (error) {
    console.error('创建对话失败:', error)
    ElMessage.error('创建对话失败')
  }
}

// 切换对话 - 关键修改：确保正确设置活跃对话ID
const switchConversation = async (conversationId) => {
  console.log('切换到对话:', conversationId)

  // 设置当前活跃对话ID
  activeConversationId.value = conversationId

  // 如果已经加载过该对话的消息，直接使用
  if (conversationMessagesMap.value.has(conversationId)) {
    currentMessages.value = conversationMessagesMap.value.get(conversationId)
    scrollToBottom()
  } else {
    // 否则从服务器加载
    await loadConversationMessages(conversationId)
  }
}

// 处理下拉菜单命令
const handleCommand = async (command, conversation) => {
  if (command === 'rename') {
    await renameConversation(conversation)
  } else if (command === 'delete') {
    await deleteConversation(conversation.id)
  }
}

// 重命名对话
const renameConversation = async (conversation) => {
  try {
    const { value: newTitle } = await ElMessageBox.prompt('请输入新的对话标题', '重命名', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: conversation.title,
      inputValidator: (value) => {
        if (!value || value.trim().length === 0) {
          return '对话标题不能为空'
        }
        if (value.length > 50) {
          return '对话标题不能超过50个字符'
        }
        return true
      }
    })

    if (newTitle && newTitle.trim() !== conversation.title) {
      const response = await axios.put(`/api/conversations/${conversation.id}/rename`, {
        title: newTitle.trim()
      })

      // 更新对话列表
      const index = conversations.value.findIndex(c => c.id === conversation.id)
      if (index !== -1) {
        conversations.value[index] = response.data
      }

      ElMessage.success('重命名成功')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重命名对话失败:', error)
      ElMessage.error('重命名失败')
    }
  }
}

// 删除对话
const deleteConversation = async (conversationId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？删除后无法恢复。', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await axios.delete(`/api/conversations/${conversationId}`)
    ElMessage.success('对话删除成功')

    // 从对话列表中移除
    conversations.value = conversations.value.filter(c => c.id !== conversationId)

    // 从消息映射中移除
    conversationMessagesMap.value.delete(conversationId)

    // 如果删除的是当前对话，清空当前对话
    if (activeConversationId.value === conversationId) {
      activeConversationId.value = null
      currentMessages.value = []
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除对话失败:', error)
      ElMessage.error('删除对话失败')
    }
  }
}

// 时间格式化
const formatTime = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()

  // 如果是今天，显示时间
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // 如果是昨天
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) {
    return '昨天'
  }

  // 如果是今年，显示月日
  if (date.getFullYear() === now.getFullYear()) {
    return date.toLocaleDateString('zh-CN', {
      month: '2-digit',
      day: '2-digit'
    })
  }

  // 其他情况显示年月日
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const formatMessageTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 发送消息 - 关键修改：确保使用同一个对话ID
const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value || !activeConversationId.value) return

  const userMessage = {
    id: `user-${Date.now()}`,
    role: 'user',
    content: inputMessage.value.trim(),
    timestamp: new Date().toISOString()
  }

  // 立即添加用户消息到当前消息列表
  currentMessages.value.push(userMessage)

  // 更新消息映射
  conversationMessagesMap.value.set(activeConversationId.value, [...currentMessages.value])

  const currentInput = inputMessage.value
  inputMessage.value = ''
  loading.value = true

  scrollToBottom()

  try {
    console.log('发送消息到对话:', activeConversationId.value)

    // 构建发送给后端的消息 - 关键：始终使用当前活跃的对话ID
    const requestData = {
      messages: [{ role: 'user', content: currentInput }],
      stream: false,
      conversation_id: activeConversationId.value // 使用同一个对话ID
    }

    console.log('请求数据:', requestData)

    const response = await axios.post('/api/v1/chat/completions', requestData)
    console.log('收到AI回复:', response.data)

    const assistantMessage = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: response.data.choices[0].message.content,
      timestamp: new Date().toISOString()
    }

    // 添加助手消息到当前消息列表
    currentMessages.value.push(assistantMessage)

    // 更新消息映射
    conversationMessagesMap.value.set(activeConversationId.value, [...currentMessages.value])

    // 更新对话列表（获取最新更新时间）
    await loadConversations()

  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送失败，请重试')

    // 添加错误消息
    const errorMessage = {
      id: `error-${Date.now()}`,
      role: 'assistant',
      content: '抱歉，我暂时无法回复您的消息。请稍后重试。',
      timestamp: new Date().toISOString()
    }
    currentMessages.value.push(errorMessage)
    conversationMessagesMap.value.set(activeConversationId.value, [...currentMessages.value])
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 初始化 - 关键修改：确保有默认的活跃对话
onMounted(async () => {
  console.log('初始化聊天界面...')
  await loadConversations()

  // 如果有历史对话，默认加载第一个
  if (conversations.value.length > 0) {
    await switchConversation(conversations.value[0].id)
  } else {
    // 如果没有历史对话，创建第一个对话
    await createNewConversation()
  }
})
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f8fafc;
}

.navbar {
  height: 60px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.navbar-brand {
  display: flex;
  align-items: center;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.brand-text {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.navbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.main-layout {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 320px;
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 64px;
}

.sidebar-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1f2937;
}

.sidebar-actions {
  display: flex;
  gap: 4px;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 4px;
  position: relative;
}

.conversation-item:hover {
  background-color: #f8fafc;
}

.conversation-item.active {
  background: linear-gradient(135deg, #ecf5ff 0%, #f0f9ff 100%);
  border: 1px solid #409EFF;
}

.conv-icon {
  margin-right: 12px;
  color: #64748b;
}

.conv-content {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-preview {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-time {
  font-size: 11px;
  color: #94a3b8;
}

.conv-actions {
  opacity: 0;
  transition: opacity 0.3s ease;
}

.conversation-item:hover .conv-actions {
  opacity: 1;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
  color: #64748b;
}

.empty-state p {
  margin: 16px 0 0;
  font-size: 14px;
}

.empty-hint {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 8px;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
}

.welcome-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.welcome-content {
  text-align: center;
  max-width: 500px;
  padding: 40px;
}

.welcome-icon {
  margin-bottom: 24px;
}

.welcome-content h1 {
  font-size: 32px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 16px;
}

.welcome-description {
  font-size: 16px;
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 32px;
}

.welcome-features {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-bottom: 32px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #475569;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid #f1f5f9;
  background: white;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title h3 {
  margin: 0;
  color: #1f2937;
  font-size: 18px;
  font-weight: 600;
}

.messages-container {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: #f8fafc;
}

.message {
  display: flex;
  margin-bottom: 24px;
  max-width: 100%;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  margin: 0 12px;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
}

.message-text {
  padding: 16px 20px;
  border-radius: 16px;
  background: white;
  line-height: 1.5;
  word-break: break-word;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #f1f5f9;
}

.message.user .message-text {
  background: linear-gradient(135deg, #409EFF 0%, #67C23A 100%);
  color: white;
  border: none;
}

.message-time {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 6px;
  padding: 0 4px;
}

.message.user .message-time {
  text-align: right;
}

.thinking-text {
  margin-left: 8px;
  color: #64748b;
}

.input-container {
  padding: 20px 24px;
  border-top: 1px solid #f1f5f9;
  background: white;
}

.input-wrapper {
  position: relative;
  margin-bottom: 8px;
}

.message-input {
  border-radius: 12px;
}

.message-input :deep(.el-textarea__inner) {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding-right: 60px;
  transition: all 0.3s ease;
}

.message-input :deep(.el-textarea__inner:focus) {
  border-color: #409EFF;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

.input-actions {
  position: absolute;
  right: 12px;
  bottom: 12px;
}

.send-btn {
  width: 40px;
  height: 40px;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.input-footer {
  text-align: center;
}

.tip-text {
  font-size: 12px;
  color: #94a3b8;
}

/* 滚动条样式优化 */
.conversation-list::-webkit-scrollbar,
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.conversation-list::-webkit-scrollbar-track,
.messages-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.conversation-list::-webkit-scrollbar-thumb,
.messages-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.conversation-list::-webkit-scrollbar-thumb:hover,
.messages-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>