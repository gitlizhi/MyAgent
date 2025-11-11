<template>
  <div class="auth-page">
    <div class="auth-background">
      <div class="background-pattern"></div>
    </div>

    <div class="auth-container">
      <!-- 左侧品牌展示 -->
      <div class="auth-brand">
        <div class="brand-content">
          <div class="brand-logo">
            <el-icon size="48" color="#409EFF"><ChatDotRound /></el-icon>
          </div>
          <h1 class="brand-title">LangGraph Agent</h1>
          <p class="brand-description">
            智能对话助手，让沟通更高效
          </p>
          <div class="feature-list">
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
        </div>
      </div>

      <!-- 右侧注册表单 -->
      <div class="auth-form-container">
        <div class="auth-form-wrapper">
          <div class="form-header">
            <h2>创建账号</h2>
            <p>开启智能对话之旅</p>
          </div>

          <el-form
            :model="registerForm"
            :rules="registerRules"
            ref="registerFormRef"
            label-width="0"
            class="auth-form"
            size="large"
            @submit.prevent="handleRegister"
          >
            <el-form-item prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="用户名"
                prefix-icon="User"
                clearable
                class="auth-input"
              />
            </el-form-item>

            <el-form-item prop="email">
              <el-input
                v-model="registerForm.email"
                placeholder="邮箱地址"
                prefix-icon="Message"
                clearable
                class="auth-input"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="密码"
                prefix-icon="Lock"
                show-password
                clearable
                class="auth-input"
              />
            </el-form-item>

            <el-form-item prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="确认密码"
                prefix-icon="Lock"
                show-password
                clearable
                class="auth-input"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="handleRegister"
                :loading="loading"
                class="auth-button"
              >
                {{ loading ? '注册中...' : '立即注册' }}
              </el-button>
            </el-form-item>

            <div class="auth-footer">
              <span>已有账号？</span>
              <el-link type="primary" @click="goToLogin" class="auth-link">立即登录</el-link>
            </div>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  User,
  Message,
  Lock,
  ChatDotRound,
  SuccessFilled,
  WarningFilled,
  InfoFilled
} from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()
const registerFormRef = ref()
const loading = ref(false)

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 表单验证规则（保持不变）
const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const registerRules = reactive({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为6位', trigger: 'blur' },
    { pattern: /^(?=.*[A-Za-z])(?=.*\d).+$/, message: '密码必须包含字母和数字', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
})

// 处理注册（保持不变）
const handleRegister = async () => {
  if (!registerFormRef.value) return

  try {
    const valid = await registerFormRef.value.validate()
    if (!valid) {
      ElMessage.warning('请完善表单信息')
      return
    }

    loading.value = true

    const registerData = {
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password
    }

    const response = await axios.post('/api/register', registerData)

    if (response.data.success) {
      ElMessage.success('注册成功！')
      setTimeout(() => {
        router.push('/login')
      }, 1500)
    } else {
      ElMessage.error(response.data.message || '注册失败')
    }
  } catch (error) {
    console.error('注册失败:', error)
    if (error.response) {
      ElMessage.error('服务器错误，请稍后重试')
    } else if (error.request) {
      ElMessage.error('网络错误，请检查网络连接')
    } else {
      ElMessage.error('注册失败，请重试')
    }
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
}

.auth-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.background-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.2) 0%, transparent 50%);
}

.auth-container {
  display: flex;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  background: white;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  margin: 40px 20px;
  min-height: calc(100vh - 80px);
}

.auth-brand {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 60px 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-content {
  text-align: center;
  max-width: 400px;
}

.brand-logo {
  margin-bottom: 24px;
}

.brand-title {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 16px;
}

.brand-description {
  font-size: 18px;
  opacity: 0.9;
  margin-bottom: 40px;
  line-height: 1.6;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 16px;
  opacity: 0.9;
}

.auth-form-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.auth-form-wrapper {
  width: 100%;
  max-width: 400px;
}

.form-header {
  text-align: center;
  margin-bottom: 40px;
}

.form-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 8px;
}

.form-header p {
  color: #64748b;
  font-size: 16px;
}

.auth-form {
  width: 100%;
}

.auth-input :deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  box-shadow: none;
}

.auth-input :deep(.el-input__wrapper:hover) {
  border-color: #cbd5e1;
}

.auth-input :deep(.el-input__wrapper.is-focus) {
  border-color: #409EFF;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

.auth-button {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  background: linear-gradient(135deg, #409EFF 0%, #67C23A 100%);
  border: none;
  margin-top: 8px;
}

.auth-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.auth-footer {
  text-align: center;
  margin-top: 24px;
  color: #64748b;
}

.auth-link {
  font-weight: 500;
  margin-left: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .auth-container {
    flex-direction: column;
    margin: 20px;
    min-height: calc(100vh - 40px);
  }

  .auth-brand {
    padding: 40px 20px;
  }

  .auth-form-container {
    padding: 40px 20px;
  }

  .brand-title {
    font-size: 24px;
  }

  .brand-description {
    font-size: 16px;
  }
}
</style>