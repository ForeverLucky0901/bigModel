<template>
  <Layout>
    <div class="h-full overflow-y-auto p-6">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-gray-800">用户管理</h1>
        <button
          @click="showCreateModal = true"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          创建用户
        </button>
      </div>

      <div class="bg-white rounded-lg shadow overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户名</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">邮箱</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">配额</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="user in users" :key="user.id">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ user.id }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ user.username }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ user.email }}</td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="['px-2 py-1 text-xs rounded-full', user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800']">
                  {{ user.is_active ? '激活' : '禁用' }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ formatNumber(user.monthly_quota_tokens) }} tokens</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button @click="toggleStatus(user)" class="text-blue-600 hover:text-blue-900 mr-3">
                  {{ user.is_active ? '禁用' : '启用' }}
                </button>
                <button @click="editUser(user)" class="text-indigo-600 hover:text-indigo-900">编辑</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 创建用户模态框 -->
      <div v-if="showCreateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showCreateModal = false">
        <div class="bg-white rounded-lg p-6 w-full max-w-md">
          <h3 class="text-lg font-semibold mb-4">创建用户</h3>
          <form @submit.prevent="createUser">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                <input v-model="newUser.username" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-md" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                <input v-model="newUser.email" type="email" required class="w-full px-3 py-2 border border-gray-300 rounded-md" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Token配额</label>
                <input v-model.number="newUser.monthly_quota_tokens" type="number" required class="w-full px-3 py-2 border border-gray-300 rounded-md" />
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

const users = ref([])
const showCreateModal = ref(false)
const newUser = ref({ username: '', email: '', monthly_quota_tokens: 1000000 })

onMounted(() => loadUsers())

const loadUsers = async () => {
  try {
    const response = await api.get('/admin/users')
    users.value = response.data
  } catch (error) {
    console.error('Failed to load users:', error)
  }
}

const toggleStatus = async (user) => {
  try {
    await api.patch(`/admin/users/${user.id}`, { is_active: !user.is_active })
    user.is_active = !user.is_active
  } catch (error) {
    alert('操作失败')
  }
}

const createUser = async () => {
  try {
    await api.post('/admin/users', newUser.value)
    showCreateModal.value = false
    newUser.value = { username: '', email: '', monthly_quota_tokens: 1000000 }
    await loadUsers()
  } catch (error) {
    alert('创建失败')
  }
}

const editUser = (user) => {
  alert('编辑功能待实现')
}

const formatNumber = (num) => {
  return new Intl.NumberFormat('zh-CN').format(num)
}
</script>
