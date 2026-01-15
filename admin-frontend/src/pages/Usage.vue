<template>
  <Layout>
    <div class="h-full overflow-y-auto p-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-6">用量统计</h1>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div class="bg-blue-50 p-6 rounded-lg">
          <div class="text-sm text-gray-600 mb-2">总请求数</div>
          <div class="text-3xl font-bold text-blue-600">{{ formatNumber(totalRequests) }}</div>
        </div>
        <div class="bg-green-50 p-6 rounded-lg">
          <div class="text-sm text-gray-600 mb-2">总Token数</div>
          <div class="text-3xl font-bold text-green-600">{{ formatNumber(totalTokens) }}</div>
        </div>
        <div class="bg-purple-50 p-6 rounded-lg">
          <div class="text-sm text-gray-600 mb-2">活跃用户</div>
          <div class="text-3xl font-bold text-purple-600">{{ activeUsers }}</div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">请求数</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Token数</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">日期</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="record in usageRecords" :key="record.id">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ record.user?.username }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ record.total_requests }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatNumber(record.total_tokens) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ record.date }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Layout from '@/components/Layout.vue'
import api from '@/utils/api'

const usageRecords = ref([])
const totalRequests = ref(0)
const totalTokens = ref(0)
const activeUsers = ref(0)

onMounted(() => loadUsage())

const loadUsage = async () => {
  try {
    const response = await api.get('/admin/usage')
    usageRecords.value = response.data.records || []
    totalRequests.value = response.data.total_requests || 0
    totalTokens.value = response.data.total_tokens || 0
    activeUsers.value = response.data.active_users || 0
  } catch (error) {
    console.error('Failed to load usage:', error)
  }
}

const formatNumber = (num) => {
  return new Intl.NumberFormat('zh-CN').format(num)
}
</script>
