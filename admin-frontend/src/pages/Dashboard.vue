<template>
  <Layout>
    <div class="h-full overflow-y-auto p-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-6">管理后台概览</h1>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm text-gray-600 mb-2">总用户数</div>
          <div class="text-3xl font-bold text-blue-600">{{ stats.totalUsers }}</div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm text-gray-600 mb-2">总请求数</div>
          <div class="text-3xl font-bold text-green-600">{{ formatNumber(stats.totalRequests) }}</div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm text-gray-600 mb-2">总Token数</div>
          <div class="text-3xl font-bold text-purple-600">{{ formatNumber(stats.totalTokens) }}</div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-lg font-semibold mb-4">快速操作</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <router-link
            to="/users"
            class="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div class="font-medium text-gray-900">用户管理</div>
            <div class="text-sm text-gray-500 mt-1">查看和管理所有用户</div>
          </router-link>
          <router-link
            to="/api-keys"
            class="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div class="font-medium text-gray-900">API Key管理</div>
            <div class="text-sm text-gray-500 mt-1">管理所有API密钥</div>
          </router-link>
          <router-link
            to="/usage"
            class="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div class="font-medium text-gray-900">用量统计</div>
            <div class="text-sm text-gray-500 mt-1">查看系统使用情况</div>
          </router-link>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Layout from '@/components/Layout.vue'
import api from '@/utils/api'

const stats = ref({
  totalUsers: 0,
  totalRequests: 0,
  totalTokens: 0
})

onMounted(async () => {
  try {
    const [usersRes, usageRes] = await Promise.all([
      api.get('/admin/users'),
      api.get('/admin/usage')
    ])
    stats.value.totalUsers = usersRes.data.length
    stats.value.totalRequests = usageRes.data.total_requests || 0
    stats.value.totalTokens = usageRes.data.total_tokens || 0
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
})

const formatNumber = (num) => {
  return new Intl.NumberFormat('zh-CN').format(num)
}
</script>
