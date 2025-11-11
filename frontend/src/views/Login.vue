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
            <el-icon size="48" color="white"><ChatDotRound /></el-icon>
          </div>
          <h1 class="brand-title">LangGraph Agent</h1>
          <p class="brand-description">
            欢迎回来，继续您的智能对话之旅
          </p>
          <div class="feature-list">
            <div class="feature-item">
              <el-icon color="#a5d6a7"><SuccessFilled /></el-icon>
              <span>智能对话</span>
            </div>
            <div class="feature-item">
              <el-icon color="#ffd54f"><WarningFilled /></el-icon>
              <span>上下文记忆</span>
            </div>
            <div class="feature-item">
              <el-icon color="#90caf9"><InfoFilled /></el-icon>
              <span>多工具支持</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧登录表单 -->
      <div class="auth-form-container">
        <div class="auth-form-wrapper">
          <div class="form-header">
            <h2>欢迎回来</h2>
            <p>请登录您的账户</p>
          </div>

          <el-form
            :model="loginForm"
            :rules="loginRules"
            ref="loginFormRef"
            label-width="0"
            class="auth-form"
            size="large"
            @submit.prevent="handleLogin"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="用户名或邮箱"
                prefix-icon="User"
                clearable
                class="auth-input"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                prefix-icon="Lock"
                show-password
                clearable
                class="auth-input"
              />
            </el-form-item>

            <div class="form-options">
              <el-checkbox v-model="rememberMe">记住我</el-checkbox>
              <el-link type="primary" class="forgot-link">忘记密码？</el-link>
            </div>

            <el-form-item>
              <el-button
                type="primary"
                @click="handleLogin"
                :loading="loading"
                class="auth-button"
              >
                {{ loading ? '登录中...' : '立即登录' }}
              </el-button>
            </el-form-item>

<!--            <div class="auth-divider">-->
<!--              <span>或</span>-->
<!--            </div>-->

            <div class="social-login">
              <el-button class="social-button" circle>
                <el-icon><Message /></el-icon>
              </el-button>
              <el-button class="social-button" circle>
                <el-icon><User /></el-icon>
              </el-button>
              <el-button class="social-button" circle>
                <el-icon><ChatDotRound /></el-icon>
              </el-button>
            </div>

            <div class="auth-footer">
              <span>还没有账号？</span>
              <el-link type="primary" @click="goToRegister" class="auth-link">立即注册</el-link>
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
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loginFormRef = ref()
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = reactive({
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
})

const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return

    loading.value = true

    // 使用 authStore 的 login 方法
    const result = await authStore.login(loginForm)

    if (result.success) {
      ElMessage.success('登录成功！')
      router.push('/chat')
    } else {
      ElMessage.error(result.error || '登录失败')
    }
  } catch (error) {
    console.error('登录失败:', error)
    ElMessage.error('登录失败，请重试')
  } finally {
    loading.value = false
  }
}

const goToRegister = () => {
  router.push('/register')
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

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.forgot-link {
  font-size: 14px;
}

.auth-button {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  background: linear-gradient(135deg, #409EFF 0%, #67C23A 100%);
  border: none;
}

.auth-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.auth-divider {
  text-align: center;
  margin: 24px 0;
  position: relative;
}

.auth-divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: #e2e8f0;
}

.auth-divider span {
  background: white;
  padding: 0 16px;
  color: #64748b;
  font-size: 14px;
}

.social-login {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
}

.social-button {
  width: 48px;
  height: 48px;
  border: 1px solid #e2e8f0;
  background: white;
  transition: all 0.3s ease;
}

.social-button:hover {
  border-color: #409EFF;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.auth-footer {
  text-align: center;
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