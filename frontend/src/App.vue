<template>
  <div id="app">
    <el-container class="layout-container" v-if="$route.name !== 'Login' && $route.name !== 'Register'">
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
    <router-view v-else />
  </div>
</template>

<script setup>
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'
import { User, ArrowDown } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const router = useRouter()

const handleCommand = (command) => {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.user-info {
  display: flex;
  align-items: center;
}

.el-dropdown-link {
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.main-content {
  padding: 0;
  background-color: #f5f7fa;
}
</style>