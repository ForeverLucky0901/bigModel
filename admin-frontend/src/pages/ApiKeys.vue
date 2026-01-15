<template>
  <Layout>
    <div class="h-full overflow-y-auto p-6">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-gray-800">API Key 管理</h1>
        <button @click="showCreateModal = true" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          创建 Key
        </button>
      </div>

      <div class="bg-white rounded-lg shadow overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Key</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">创建时间</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="key in apiKeys" :key="key.id">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">{{ key.key.substring(0, 20) }}...</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ key.user?.username }}</td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="['px-2 py-1 text-xs rounded-full', key.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800']">
                  {{ key.is_active ? '激活' : '禁用' }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatDate(key.created_at) }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button @click="toggleStatus(key)" class="text-blue-600 hover:text-blue-900 mr-3">{{ key.is_active ? '禁用' : '启用' }}</button>
                <button @click="deleteKey(key)" class="text-red-600 hover:text-red-900">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 创建Key模态框 -->
      <div v-if="showCreateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showCreateModal = false">
        <div class="bg-white rounded-lg p-6 w-full max-w-md">
          <h3 class="text-lg font-semibold mb-4">创建 API Key</h3>
          <form @submit.prevent="createKey">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">用户</label>
                <select v-model="newKey.user_id" required class="w-full px-3 py-2 border border-gray-300 rounded-md">
                  <option value="">选择用户</option>
                  <option v-for="user in users" :key="user.id" :value="user.id">{{ user.username }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">名称</label>
                <input v-model="newKey.name" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md" />
              </div>
            </div>
            <div class="mt-6 flex justify-end gap-3">
              <button type="button" @click="showCreateModal = false" class="px-4 py-2 border border-gray-300 rounded-md">取消</button>
              <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">创建</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Layout from '@/components/Layout.vue'
import api from '@/utils/api'

const apiKeys = ref([])
const users = ref([])
const showCreateModal = ref(false)
const newKey = ref({ user_id: '', name: '' })

onMounted(() => {
  loadApiKeys()
  loadUsers()
})

const loadApiKeys = async () => {
  try {
    const response = await api.get('/admin/api-keys')
    apiKeys.value = response.data
  } catch (error) {
    console.error('Failed to load API keys:', error)
  }
}

const loadUsers = async () => {
  try {
    const response = await api.get('/admin/users')
    users.value = response.data
  } catch (error) {
    console.error('Failed to load users:', error)
  }
}

const toggleStatus = async (key) => {
  try {
    await api.patch(`/admin/api-keys/${key.id}`, { is_active: !key.is_active })
    key.is_active = !key.is_active
  } catch (error) {
    alert('操作失败')
  }
}

const deleteKey = async (key) => {
  if (!confirm('确定要删除这个API Key吗？')) return
  try {
    await api.delete(`/admin/api-keys/${key.id}`)
    await loadApiKeys()
  } catch (error) {
    alert('删除失败')
  }
}

const createKey = async () => {
  try {
    await api.post('/admin/api-keys', newKey.value)
    showCreateModal.value = false
    newKey.value = { user_id: '', name: '' }
    await loadApiKeys()
  } catch (error) {
    alert('创建失败')
  }
}

const formatDate = (date) => {
  return new Date(date).toLocaleString('zh-CN')
}
</script>
